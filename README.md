# Speech HUD：AI 演講肢體語言分析

丟一支名人演講或訪談影片，自動做出一支鋼鐵人 HUD 風格的直式分析影片，適合發 Threads、Reels、短影音。

- 開頭 1 秒原始畫面，讓觀眾認出是誰
- 鎖定主角：臉部 478 點網格、手部與全身骨架、臉部放大特寫
- 六種狀態即時雷達圖：自信、壓力、遲疑、防備、熱情、從容
- 底部 8 個數據：眼神接觸、眨眼、語速、停頓比例、手勢強調、摸臉、語調起伏、身體晃動
- 結尾分析報告：整體判讀、各狀態平均、關鍵次數、時間軸
- 全部在自己電腦上跑，影片不上傳

只分析肢體語言與說話節奏，不做測謊。

## 技術原理

| 層 | 技術 | 量測內容 |
|---|---|---|
| 感知層 | **Google MediaPipe Tasks Vision**：Face Landmarker（478 點＋52 組表情係數）、Hand Landmarker（每手 21 點）、Pose Landmarker／BlazePose（33 點） | 頭部角度、眼神接觸、眨眼、抿嘴、皺眉、真笑、手勢、摸臉、雙手開合、聳肩、晃動 |
| 聲學層 | 自行實作的語音訊號處理：正規化自相關音高偵測、音量包絡 | 語調起伏（半音）、語速、停頓比例、長停頓、聲音穩定度、語氣加重 |
| 判讀層 | 依非語言溝通研究設計的加權模型（Ekman & Friesen 1969、Ekman et al. 1990、Harrigan & O'Connell 1996、Mahl 1956、Rosenberg & Hirschberg 2009） | 17 項訊號組合成六種狀態，加上流暢度修正與差異放大 |

Google 的模型負責量測，六種狀態的判讀規則由本工具訂定。完整說明、每項訊號的研究依據與參考文獻見 [`references/methodology.md`](references/methodology.md)。

## 需要
- macOS、Google Chrome
- `ffmpeg`（`brew install ffmpeg`）、Python 3

## 安裝成 Claude Code skill
```bash
git clone https://github.com/austin17022/speech-hud-skill.git ~/speech-hud
ln -s ~/speech-hud ~/.claude/skills/speech-hud
```
之後在 Claude Code 說「幫我分析這支影片的肢體語言」並貼上連結即可。

## 自己手動用
雙擊 `啟動.command`，在 Chrome 裡拖入影片、點一下要分析的人、按輸出，成品在 `output/`。

## 指令列
```bash
scripts/render.sh 影片.mp4 人名 0.73,0.35   # 最後的座標是主角頭部位置（0～1），可省略
scripts/mobile.sh output/AI分析-人名-xxxx.mp4  # 壓一份手機版
```

## 檔案
| 檔案 | 用途 |
|---|---|
| `SKILL.md` | 給 Claude 的操作流程 |
| `index.html` | 分析與畫面（MediaPipe Tasks Vision） |
| `server.py` | 本機伺服器：收畫格、用 ffmpeg 合成影片 |
| `scripts/` | 背景輸出、手機版、縮圖總覽 |
| `references/methodology.md` | 技術原理與參考文獻 |
| `references/scoring.md` | 六種狀態的完整權重 |
| `references/tracking.md` | 追蹤主角的踩坑紀錄與除錯方法 |
