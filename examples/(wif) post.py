# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')

title = 'test'
body = 'test'
author = 'ksantoprotein'
wif = '5...'
curation = 'max'

tx = b4.post(title, body, author, wif, curation = curation)
pprint(tx)
input('end')