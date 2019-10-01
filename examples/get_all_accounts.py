# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

tx = b4.get_all_accounts()
file = 'get_all_accounts.csv'
with open(file, 'w', encoding = 'utf8') as f:
	for login, value in tx.items():
		f.write(';'.join( [login, json.dumps(value) + '\n'] ))

input('next')
