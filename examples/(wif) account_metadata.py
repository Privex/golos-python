# -*- coding: utf-8 -*-

import json
from pprint import pprint

from tgolosbase.api import Api


print('connect')
b4 = Api()

account = 'ksantoprotein'
wif = '5...'
json_metadata = {"profile": {
					"profile_image": 'https://thumb.ibb.co/e929Gv/av_543.gif',
					"name": 'Протеюшко',
					"about": 'кафедра биоинженерии и биоинформатики',
					"gender": 'male',
					"location": 'Волгоград',
					"website": 'https://golos.io/@sci-populi',
					"pinnedPosts": [],
					}}
					
tx = b4.get_accounts([account])[0]
print(tx["json_metadata"])
input('try call?')
					

tx = b4.account_metadata(account, json_metadata,  wif)
pprint(tx)

input('end')