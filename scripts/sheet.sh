#!/bin/zsh
# 縮圖總覽：每隔幾秒取一格拼成一張圖，用來看鏡頭切換、畫面裡有誰、追蹤有沒有跟好
# 用法：scripts/sheet.sh <影片> <輸出.jpg> [每秒幾張，預設 0.5] [起始秒] [長度秒]
IN=$1; OUTF=$2; FPS=${3:-0.5}; SS=${4:-0}; T=${5:-600}
ffmpeg -v error -y -ss $SS -t $T -i "$IN" -vf "fps=$FPS,scale=320:-1,tile=6x5" -frames:v 1 "$OUTF" && echo "$OUTF"
