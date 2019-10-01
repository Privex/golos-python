# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

limit = 10

tx = b4.get_recent_trades(limit)

pprint(tx)
input()