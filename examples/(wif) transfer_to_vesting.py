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
wif = '5...'


tx = b4.transfer_to_vesting(to, amount, from_account, wif)
pprint(tx)
input('end')