# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')

amount = '0'	# GOLOS
account = 'ksantoprotein'
wif = '5...'

tx = b4.withdraw_vesting(account, amount, wif)
pprint(tx)
input('end')
