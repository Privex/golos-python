# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api(report = True)
print('try call')

#master_key
accounts = {
			"toto-cosmos": 'P5...',
			}


recovery_account = 'ksantoprotein'

for account, password in accounts.items():

	tx = b4.get_accounts([account])[0]
	print(tx["name"], tx["recovery_account"], tx["golos_power"], 'СГ')
	
	if tx["recovery_account"] != recovery_account:

		input('ready?')
		
		paroles = b4.key.get_keys(account, password)

		tx = b4.change_recovery_account(account, recovery_account, paroles["private"]["owner"])
		pprint(tx)

input('end')

