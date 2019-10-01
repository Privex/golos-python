# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

for account in ['ksantoprotein', 'sci-populi']:
	tx = b4.get_accounts([account])[0]
	pprint(tx)

	file = 'get_account.json'
	with open(file, 'w', encoding = 'utf8') as f:
		json.dump(tx, f, ensure_ascii = False)

	input('next')
