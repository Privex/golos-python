import functools
from typing import List, Union

from privex.helpers import retry_on_err
import logging

log = logging.getLogger(__name__)


def dict_sort(data: dict) -> List[tuple]:
    """
    Convert a ``dict`` into a sorted ``List[tuple]`` for safely comparing multiple ``dict``'s
    
    **Basic Usage**:
    
        >>> x = dict(a=1, c=2, b=3)
        >>> y = dict(a=1, b=3, c=2)
        >>> dict_sort(x) == dict_sort(y)
        True
    
    """
    return sorted(tuple(dict(data).items()))


def new_node_on_err(max_retries: int = 3, delay: Union[int, float] = 3, **retry_conf):
    fail_on = tuple(retry_conf.get('fail_on', (KeyboardInterrupt,)))
    import golos.api, golos.ws_client
    
    def _decorator(f: callable):
        def _change_node(args):
            new_node = "UNKNOWN"
            if isinstance(args[0], (golos.api.Api, golos.ws_client.WsClient)):
                s: Union[golos.api.Api, golos.ws_client.WsClient] = args[0]
                if hasattr(s, 'next_node'):
                    log.warning("Calling %s.next_node()", s.__class__.__name__)
                    s.next_node()
                    new_node = s.url
                elif hasattr(s, 'rpc'):
                    log.warning("Calling %s.rpc.next_node()", s.__class__.__name__)
                    s.rpc.next_node()
                    new_node = s.rpc.url
                log.warning("Current GOLOS node is: '%s'...", new_node)
        
            return new_node
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            def _change_retry(max_changes=3, tries=0):
                new_node = _change_node(args)
                try:
                    log.warning("Retrying %s with new Golos RPC node '%s'...", f.__name__, new_node)
                    return f(*args, **kwargs)
                except Exception as e:
                    if isinstance(e, fail_on) or tries >= max_changes:
                        raise e
                    return _change_retry(max_changes, tries + 1)
            
            rt = retry_on_err(max_retries=max_retries, delay=delay, **retry_conf)(f)
            try:
                return rt(*args, **kwargs)
            except Exception as e:
                if isinstance(e, fail_on):
                    raise e
                return _change_retry((max_retries // 2) + 1)
        return wrapper

    return _decorator

