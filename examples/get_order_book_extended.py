# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

limit = 3

tx = b4.get_order_book_extended(limit)

pprint(tx)
input()