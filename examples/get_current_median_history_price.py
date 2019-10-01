# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')


tx = b4.get_current_median_history_price()

pprint(tx)
input()