# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')

title = 'delete'
body = 'delete'
author = 'ksantoprotein'
wif = '5...'

url = 'https://golos.id/thallid/@ksantoprotein/test-1568630110'
permlink = 'test-1568630267'

tx = b4.replace(title, body, author, wif, url = url, permlink = permlink)
pprint(tx)
input('end')