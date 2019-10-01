# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

account = 'ksantoprotein'
type_op = ['vote']
age = 1 * 24 * 60 * 60 		#aka sec

#tx = b4.get_account_history(account)
tx = b4.get_account_history(account, type_op = type_op, age = age)
#pprint(tx)
print('find', len(tx))

input('end')