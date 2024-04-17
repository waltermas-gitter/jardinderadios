#!/bin/bash
# https://github.com/jonasrmichel/radio-garden-openapi
cd /home/waltermas/MEGAsync/scripts/radio-garden
# curl --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
#     -X "GET" "http://radio.garden/api/ara/content/places" \
#     -H "Accept: application/json" > places.json
PLACEID=$(jq -r '.data.list[] | "\(.id), \(.title)"' places.json | fzf | sed 's/,.*//')
echo "placeid $PLACEID" # place id
ID=`curl -s --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
    -X "GET" "http://radio.garden/api/ara/content/page/$PLACEID" \
    -H "Accept: application/json" | jq -r '.data.content[].items[].page | "\(.title), \(.url)"' | fzf | tail -c 9`

STREAM=`curl -s --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
    -X "GET" "http://radio.garden/api/ara/content/listen/$ID/channel.mp3" \
    -H "Accept: application/json" | cut -d'"' -f2`

echo $STREAM
copyq add "$STREAM"
vlc "$STREAM"&
