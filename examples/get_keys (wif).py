# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api

print('connect')
b4 = Api()
print('try call')

login = 'ksantoprotein'
password = 'P5...'

paroles = b4.key.get_keys(login, password)

pprint(paroles)

f = open('keys.json', 'w')
f.write(json.dumps(paroles))
f.close()

input()
