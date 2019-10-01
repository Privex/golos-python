# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()
input('try call?')

url = 'https://golos.id/solox/@ddd-005/top-week-received-vesting-shares-golos-15-09-2019'
voters = ['ksantoprotein']
weight = 10000
wif = '5...'


tx = b4.vote(url, weight, voters, wif)
pprint(tx)
input('end')