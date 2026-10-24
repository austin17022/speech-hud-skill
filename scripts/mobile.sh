#!/bin/zsh
# 壓一份手機／聊天軟體用的小檔（約 8～11MB），畫質發 Threads 夠用
# 用法：scripts/mobile.sh <成品.mp4> [輸出路徑]
IN=$1; OUTF=${2:-${IN:r}-手機版.mp4}
ffmpeg -v error -y -i "$IN" -c:v libx264 -crf 26 -preset medium -c:a aac -b:a 128k -movflags +faststart "$OUTF" && echo "$OUTF"
