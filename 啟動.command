#!/bin/zsh
# 雙擊啟動 AI 演講分析 HUD：開本機伺服器，再用 Chrome 打開工具頁
cd "$(dirname "$0")"
if ! curl -s -o /dev/null http://localhost:8830/; then
  python3 server.py 8830 >/dev/null 2>&1 &
  sleep 1
fi
open -a "Google Chrome" "http://localhost:8830/"
echo "工具已在 Chrome 打開，成品會存在：$(pwd)/output"
