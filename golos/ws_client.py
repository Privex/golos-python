# -*- coding: utf-8 -*-
"""

Copyright::
    
    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Privex's Golos Library                     |
    |        License: X11/MIT                           |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

    Privex's Golos Python Library
    Copyright (c) 2019    Privex Inc. ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import functools
import random
from typing import Union, List, Iterator, Optional

import websocket
import ssl
import json
import logging

from privex.helpers import retry_on_err

from golos import storage
from golos.extras import new_node_on_err
from .storage import api_total
from time import sleep
from pprint import pprint
from itertools import cycle
from .exceptions import GolosException, APINotFound, RetriesExceeded, TransactionNotFound, KnownGolosError

log = logging.getLogger(__name__)


def _find_exception(msg):
    if 'could not find api' in msg.lower():
        raise APINotFound(msg)
    
    if 'missing transaction with id' in msg.lower():
        raise TransactionNotFound(msg)

    raise GolosException(msg)


def error_handler(data: dict = None, msg: str = None):
    """
    Extracts and renders the format string inside of a Graphene JSON error object, then
    raises the appropriate exception using :py:func:`._find_exception`
    
    **Example usage**:
    
    With a Graphene error result:
    
        >>> response = dict(
        ...     error=dict(
        ...         message="Could not find API ${api}", data=dict(api='market_history'), code=-381
        ...     )
        ... )
        >>> error_handler(data=response)
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
        APINotFound: 'Error Code -381: Could not find API "market_history"'
    
    With a plain string error message:
    
        >>> error_handler(msg='random error msg')
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
        GolosException: 'random error msg'
        
    
    :param dict data: The original graphene JSON dict response, containing the ``error`` key
    :param str msg: If specified, will not parse ``data``, instead will directly pass ``msg`` to
                    :py:func:`._find_exception` - raising the appropriate exception based on your message.
    """
    if msg is not None or data is None:
        msg = 'Unknown Golos Error...' if msg is None else msg
        return _find_exception(msg=msg)

    err = data.get("error", {})
    msg, errdata = err.get("message", 'Unknown Golos Error...'), err.get("data", {})

    # Replace format variables such as ${api} with data['api']
    for k, d in errdata.items():
        fmtvar = '${' + k + '}'
        while fmtvar in msg:
            msg = msg.replace('${' + k + '}', f'"{d}"')

    msg = f"Error Code {err.get('code', 'n/a')}: {msg}"
    log.error('GOLOS Error: %s', msg)
    log.error('Raw error: %s', err)

    return _find_exception(msg=msg)


class WsClient:
    """
    Simple Golos JSON-WebSocket-RPC API
    This class serves as an abstraction layer for easy use of the Golos API.

    With manually specified nodes:
    
            >>> rpc = WsClient(nodes=['wss://golosd.privex.io'])
    
    With no arguments (use the default nodes):
    
            >>> rpc = WsClient()
    
    Args:
        nodes (list): A list of Golos WebSocket RPC nodes to connect to.

    Any call available to that node can be issued using the instance
    
        >>> rpc.call('command', 'my_param1', 'other_param2')
    
    """
    nodes: Iterator[str]
    report: bool
    api_total: dict
    url: str
    ws: Optional[websocket.WebSocket]

    MAX_RETRIES = 5
    RETRY_DELAY = 1

    sslopt_ca_certs = {'cert_reqs': ssl.CERT_NONE}

    def __init__(self, report=False, nodes: Union[List[str], str] = None, **kwargs):
        """
        Constructor for WsClient (GOLOS JSON-WebSocket-RPC Client)
        
        :param bool report: If ``True`` - enables more verbose logging output
        :param list nodes:  A ``List[str]`` of nodes to use, each formatted like: ``wss://golosd.privex.io``
        :param kwargs:      Any additional keyword arguments, e.g. ``num_retries``
        """
        self.report = report
        self.num_retries = kwargs.get("num_retries", 20)
        nodes = [nodes] if type(nodes) is str else nodes
        default_nodes = list(storage.nodes)
        random.shuffle(default_nodes)
        self.nodes = cycle(default_nodes if nodes is None else nodes)  # Перебор нод
        self.api_total = api_total
        self.url = ''
        self.ws = None
        self.ws_connect()  # Подключение к ноде

    @retry_on_err(fail_on=[KeyboardInterrupt])
    def next_node(self):
        self.url = next(self.nodes)
        self.node_connect(self.url)
    
    def node_connect(self, url: str = None):
        if not url:
            url = self.url
        if self.report:
            log.info("Trying to connect to node %s", url)
            
        self.ws = websocket.WebSocket(sslopt=self.sslopt_ca_certs) if self.url[:3] == "wss" else websocket.WebSocket()
        self.ws.connect(url)
        return True
    
    @retry_on_err(max_retries=10, fail_on=[KeyboardInterrupt])
    def ws_connect(self):
        """
        Attempt to connect to a working GOLOS WebSockets node.
        """
        self.url = next(self.nodes)
        self.node_connect(self.url)

    # @new_node_on_err(max_retries=MAX_RETRIES, delay=RETRY_DELAY, fail_on=[KeyboardInterrupt])
    @retry_on_err(max_retries=2, delay=1, fail_on=[KeyboardInterrupt, KnownGolosError, TransactionNotFound])
    def call(self, name, *args) -> Union[dict, list, bool]:
        """
        Make a JsonRPC call to the current working WS node.
        
        **Basic Usage**:
        
            >>> accs = WsClient().call('get_accounts', ['someguy123'])
            >>> accs[0]['owner']
            'someguy123'

        
        :param str name: The API method to call, e.g. ``get_accounts``
        :param Any args: Any extra positional args will be passed as parameters to the JsonRPC call
        :raises RetriesExceeded: When too many failures occurred while re-trying the JsonRPC call / WS connection.
        :return dict|list result: The result from the call, generally as a ``dict`` or ``list``
        :return bool result: In the event of minor errors, ``False`` or ``None`` may be returned.
        """
        # Определяем для name своё api
        api = self.api_total[name]
        if api:
            body_dict = {"id": 1, "method": "call", "jsonrpc": "2.0", "params": [api, name, args]}
            body = json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        else:
            if self.report:
                log.warning('not find api in api_total')
            raise GolosException("API not found...")

        response, result = None, []
        cnt = 0
        while True:
            cnt += 1

            try:
                self.ws.send(body)
                response = self.ws.recv()
                # pprint(response)
                break
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                if -1 < self.num_retries < cnt:  # возможно сделать return False
                    raise RetriesExceeded(f"Failed to make call '{name}' after {cnt} tries...")
                sleeptime = (cnt - 1) * 2 if cnt < 10 else 10
                if sleeptime:
                    log.info("Lost connection to node during call(): %s (%d/%d) ", self.url, cnt, self.num_retries)
                    log.info("Retrying in %d seconds", sleeptime)
                    sleep(sleeptime)

                # retry
                try:
                    self.ws.close()
                    sleep(sleeptime)
                    self.ws_connect()
                except:
                    pass

        if not response:
            if self.report:
                log.error('not response')
            raise GolosException("No response...")

        rj = response_json = json.loads(response)  # Нет проверки на ошибки при загрузке данных

        if 'error' in response_json:
            return error_handler(rj)
        if 'result' not in response_json:
            if self.report:
                log.error("No 'result' key found in response...")
            raise GolosException("No 'result' key found in response...")

        return response_json.get("result")

    def close(self):
        """Close the connection on the :class:`websocket.WebSocket` object"""
        if self.ws is not None:
            self.ws.close()

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.close()

    def __del__(self):
        """Clean-up when an instance of this object is deleted"""
        self.close()


# ----- main -----
if __name__ == '__main__':
    log.debug('connect')
    rpc = WsClient()
    log.debug('try call')

    i = rpc.call('get_dynamic_global_properties')
    # i = rpc.call('get_accounts', ['koss'])
    # i = rpc.call('get_block', '20005000')
    pprint(i)

    log.debug('yet')
