#!/bin/bash

# CALIDAD=`yt-dlp 'https://www.youtube.com/watch?v=jD5goQbS_w0' --list-formats | grep Default | awk '{print $1}'`
# yt-dlp -f $CALIDAD -g $1
BESTAUDIO=`yt-dlp "$1" --list-formats | grep "audio only" | tac | head -n 1 | awk '{print $1}'`
yt-dlp -f $BESTAUDIO -g "$1"
