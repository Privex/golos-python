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
memo = 'test1'

#[to, amount, asset, memo]
raw_ops = [[to, amount, 'GOLOS', 'test GOLOS'], [to, amount, 'GBG', 'test GBG']]

from_account = 'ksantoprotein'
wif = '5...'

tx = b4.transfers(raw_ops, from_account, wif)
pprint(tx)
input('end')
