#!/usr/bin/env python3
# https://github.com/alexmercerind/youtube-search-python

from youtubesearchpython import VideosSearch

videosSearch = VideosSearch('soda stereo', limit = 2)
print(videosSearch.result())
res = videosSearch.result()
print(res['result'][0]['id'])
print(res['result'][0]['title'])
print(res['result'][0]['duration'])
print(res['result'][0]['viewCount']['short'])
