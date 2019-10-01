# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

tx = b4.get_dynamic_global_properties()
pprint(tx)
input()

