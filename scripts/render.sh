#!/bin/zsh
# 背景輸出一支 AI 肢體語言分析影片（1080×1920，30fps，含原聲）
# 用法：scripts/render.sh <影片路徑> <人名> [鎖定位置 x,y]
#   鎖定位置是主角頭部在原影片的相對座標（0～1），例如 0.73,0.35；不給就自動挑畫面中間最大的人
# 成品：output/AI分析-<人名>-<時間>.mp4，完成後印出路徑
set -e
setopt NULL_GLOB
ROOT=${0:A:h:h}
SRC=$1; NAME=$2; LOCK=$3
PORT=${SPEECH_HUD_PORT:-8830}
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
PROFILE=${TMPDIR:-/tmp}/speech-hud-chrome
OUT=$ROOT/output
[[ -z $SRC || -z $NAME ]] && { echo "用法：$0 <影片路徑> <人名> [x,y]"; exit 1; }
[[ -f $SRC ]] || { echo "找不到影片：$SRC"; exit 1; }
mkdir -p $ROOT/input $OUT

# 網頁只能讀伺服器底下的檔案，影片不在工具資料夾裡就先複製進 input/
SRC=${SRC:A}
if [[ $SRC != $ROOT/* ]]; then cp "$SRC" "$ROOT/input/${SRC:t}"; SRC=$ROOT/input/${SRC:t}; fi
REL=${SRC#$ROOT/}

# 伺服器沒開就開
if ! curl -s -o /dev/null "http://localhost:$PORT/"; then
  (cd $ROOT && nohup python3 server.py $PORT >/dev/null 2>&1 &)
  for i in {1..20}; do sleep 0.5; curl -s -o /dev/null "http://localhost:$PORT/" && break; done
fi

enc() { python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$1"; }
URL="http://localhost:$PORT/?src=$(enc $REL)&name=$(enc $NAME)&auto=1"
[[ -n $LOCK ]] && URL="$URL&lock=$LOCK"

pkill -f "$PROFILE" 2>/dev/null || true; sleep 1
before=$(ls $OUT/*.mp4 | wc -l)
"$CHROME" --headless=new --user-data-dir=$PROFILE --window-size=1400,1000 \
  --autoplay-policy=no-user-gesture-required --no-first-run --no-default-browser-check "$URL" >/dev/null 2>&1 &

# 大約每秒 13 格；等新檔出現，再等 ffmpeg 寫完
for i in {1..120}; do sleep 5; (( $(ls $OUT/*.mp4 | wc -l) > before )) && break; done
f=$(ls -t $OUT/*.mp4 | head -1)
if (( $(ls $OUT/*.mp4 | wc -l) <= before )); then pkill -f "$PROFILE"; echo "逾時：10 分鐘內沒有產出影片"; exit 1; fi
until ffprobe -v error "$f" >/dev/null 2>&1; do sleep 2; done
pkill -f "$PROFILE" || true
rmdir $OUT/.jobs 2>/dev/null || true
echo "$f"
