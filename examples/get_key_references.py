# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
print('try call')

public_key = 'GLS7FwMN7kPDz7Wz1T2KvhUs4srUjzoXBTZ1H6BT1Jya7PsKfVydM'

tx = b4.get_key_references(public_key)

print(tx)
input()