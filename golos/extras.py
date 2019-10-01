from typing import List


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
