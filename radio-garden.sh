#!/bin/bash
# https://github.com/jonasrmichel/radio-garden-openapi

# curl --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
    # -X "GET" "http://radio.garden/api/ara/content/places" \
    # -H "Accept: application/json" > places.json
# ID=$(jq -r '.data.list[] | "\(.id), \(.title)"' places.json | fzf | sed 's/,.*//')
# echo $ID # place id


ID=`curl -s --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
    -X "GET" "http://radio.garden/api/search?q=$1" \
    -H "Accept: application/json" | jq -r '.hits.hits[]._source | "\(.title), \(.url)"' | fzf | tail -c 9`
if [ -n "$ID" ]; then
    echo "$ID"
else
    echo "No se encontraron radios"
    exit
fi
echo $ID
STREAM=`curl -s --user-agent "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0" \
    -X "GET" "http://radio.garden/api/ara/content/listen/$ID/channel.mp3" \
    -H "Accept: application/json" | cut -d'"' -f2`

copyq add "$STREAM"
vlc "$STREAM"&
