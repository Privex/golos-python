# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

start = 'a'
limit = '100'
tx = b4.lookup_witness_accounts(start, limit)

pprint(tx)
input()