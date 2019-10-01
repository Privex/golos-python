# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

account = 'ksantoprotein'
wif = '5...'
password = 'P5...'


tx = b4.account_update_password(account, password, wif)
pprint(tx)

input()

