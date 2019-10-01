# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

block = 30333333

tx = b4.get_ops_in_block(block)

pprint(tx)
input()