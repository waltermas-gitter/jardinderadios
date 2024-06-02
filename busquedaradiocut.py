#!/usr/bin/env python3

import requests
# from pyquery import PyQuery
import re

my_base_url = "https://ar.radiocut.fm/search/?type=cut&search_term=juan+junco"
r = requests.get(my_base_url)
# pq = PyQuery(r.content)
# seconds = pq('li.audio_seconds').text()
# items = pq('a')
# for item in items:
#     print(item.keys())
#     print(PyQuery(item).text())

# print(PyQuery(items[5]).text())

x = re.findall("ar.radiocut.fm\/audiocut", r.text)
print(x)
