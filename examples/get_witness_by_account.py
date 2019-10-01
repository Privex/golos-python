# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

account = 'lex'
tx = b4.get_witness_by_account(account)

pprint(tx)
input()