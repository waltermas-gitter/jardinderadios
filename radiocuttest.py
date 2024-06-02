#!/usr/bin/env python3
# https://github.com/mgaitan/radiocut_downloader/blob/master/radiocut/__init__.py
import requests
from pyquery import PyQuery
import base64
import tempfile
from moviepy.editor import AudioFileClip, ImageClip, concatenate_audioclips

# my_base_url = "https://ar.radiocut.fm/audiocut/agradecimiento-radial/"
my_base_url = "https://ar.radiocut.fm/audiocut/juan-junco-hablo-a-espaldas-del-turco-lotuf/"


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0',
}

def get_chunks_url(base_url, station, start_folder):
    """
    Computes first the (not too) 'obfuscated' code that the new chunks server requires
    and returns the final URL.
    """
    code = base64.b64encode('andaa{}|{}cagar'.format(station, start_folder).encode('ascii'))
    code = code.decode('ascii').replace('=', '~').replace('/', '_').replace('+', '-')
    url = '{}/server/gec/www/{}/'.format(base_url, code)
    return url

def get_mp3(chunk):
    url = chunk['base_url'] + '/' + chunk['filename']
    r = requests.get(url, stream=True, headers=HEADERS)
    if r.status_code == 200:
        _, p = tempfile.mkstemp('.mp3')
        with open(p, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return AudioFileClip(p)



r = requests.get(my_base_url)
pq = PyQuery(r.content)
seconds = pq('li.audio_seconds').text()
station = pq('li.audio_station').text()
duration = float(pq('li.audio_duration').text())

base_url = pq('li.audio_base_url').text()
start_folder = int(seconds[:6])
code = base64.b64encode('andaa{}|{}cagar'.format(station, start_folder).encode('ascii'))
code = code.decode('ascii').replace('=', '~').replace('/', '_').replace('+', '-')
url = '{}/server/gec/www/{}/'.format(base_url, code)

chunks = []
while True:
    chunks_url = get_chunks_url(base_url, station, start_folder)
    chunks_json = requests.get(chunks_url, headers=HEADERS).json()[str(start_folder)]
    for chunk_data in chunks_json['chunks']:
        # set the base_url if isnt defined
        chunk_data['base_url'] = chunk_data.get('base_url', chunks_json['baseURL'])
        chunks.append(chunk_data)
    c = chunks[-1]
    if c['start'] + c['length'] > float(seconds) + float(duration):
        break
    # if the last chunk isn't in this index, get the next one
    start_folder += 1

for item in chunks:
    print(item['base_url'] + '/' + item['filename'])

for i, c in enumerate(chunks):
    if c['start'] + c['length'] > float(seconds):
        first_chunk = i
        break
for i, c in enumerate(chunks[first_chunk:]):
    if c['start'] + c['length'] > float(seconds) + float(duration):
        last_chunk = min(len(chunks), first_chunk + i + 1)
        break

audios = [get_mp3(chunk) for chunk in chunks[first_chunk:last_chunk]]
start_offset = float(seconds) - chunks[first_chunk]['start']
cut = concatenate_audioclips(audios)
cut = cut.subclip(start_offset, start_offset + float(duration))
cut.write_audiofile("/tmp/cut.mp3")
