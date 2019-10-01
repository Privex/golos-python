# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')

to = 'thallid'
amount = '1.000'
from_account = 'ksantoprotein'
rate = 4500
wif = '5...'

tx = b4.delegate_vesting_shares_with_interest(to, amount, from_account, rate, wif)
pprint(tx)
input('next?')

amount = '0.000'
tx = b4.delegate_vesting_shares(to, amount, from_account, wif)
pprint(tx)
input('end')
