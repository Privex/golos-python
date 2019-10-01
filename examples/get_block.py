# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

block = 30000910

tx = b4.get_block(block)

pprint(tx)
input()