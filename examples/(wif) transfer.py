# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')


to = 'thallid'
amount = '0.001'
asset = 'GOLOS'
memo = 'test'
from_account = 'ksantoprotein'
wif = '5...'

tx = b4.transfer(to, amount, asset, from_account, wif, memo = memo)
pprint(tx)
input('end')
