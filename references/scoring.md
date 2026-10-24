# 計分方式

全部在 `index.html` 的 `STATES`（權重）和 `metrics()` 後段（打折、放大）。

## 底層訊號（0～1）
| 訊號 | 來源 |
|---|---|
| eye／away | 臉朝向鏡頭的比例（轉頭看主持人會算 away） |
| headUp／headDown | 頭部俯仰角 |
| open／closed | 兩手腕張開幅度；雙手收在身前算 closed；拿麥克風那隻手不算 |
| gesture／still | 手腕移動速度 |
| smile | 嘴角上揚＋眼角一起動才算真笑 |
| tone | 語調起伏（半音）÷ 8 |
| pace／slow／fast | 語速（用音量波峰估音節，字／秒），4.5 最自然 |
| steady／tremor | 聲音穩定度 |
| blink | 每分鐘眨眼數，14 次以上開始加分，36 次滿分 |
| touch | 手碰到臉或頭髮 |
| lip／brow | 抿嘴、皺眉 |
| shrug | 耳朵到肩膀的距離比基準短 |
| sway | 身體左右晃動 |
| pause | 最近幾秒沒在說話的比例 × 1.6 |
| longPause | 停頓超過 1.2 秒時設為 1，之後慢慢衰減 |
| emph | 語氣突然加重 |

## 六種狀態權重（! 代表反向）
- 自信：eye .22、headUp .12、open .14、gesture .12、steady .1、tone .1、pace .1、smile .1、!pause .15
- 壓力：blink .16、lip .12、shrug .12、sway .12、tremor .12、touch .16、brow .1、fast .1、pause .16、longPause .14
- 遲疑：pause .25、longPause .2、slow .15、away .15、headDown .1、still .1、touch .05
- 防備：closed .3、lip .15、brow .15、headDown .15、away .1、!open .15
- 熱情：gesture .25、tone .2、smile .2、emph .15、open .1、fast .1
- 從容：steady .2、!sway .15、!blink .15、pace .1、!touch .1、!lip .1、eye .15、!pause .22、!longPause .15

## 兩道後處理
1. **說話卡頓打折**：`dis = pause×0.7 + longPause×0.3`
   從容 ×(1−0.6×dis)、自信 ×(1−0.35×dis)、壓力 += 0.35×dis×(1−壓力)
   由來：蔣萬安哈佛英文訪談停頓比例 54%，一直「um、uh」，但坐姿端正、不摸臉、不晃，只用加權平均時從容拿 71 分，跟肉眼印象相反
2. **放大差距**：六種分數以平均為中心 ×2.6，再加 48，限制在 6～97。沒有這步，分數全擠在 20～70，雷達圖圓圓的看不出個性

## 實測參考
| 影片 | 判讀 | 關鍵數字 |
|---|---|---|
| 蔣萬安 哈佛英文訪談 | 壓力為主，帶點遲疑 | 停頓 54%、壓力 82、從容 26 |
| 沈伯洋 德國國會英文發言 | 從容為主，帶點自信 | 停頓約 13%、從容 94、自信 72 |
| 沈伯洋 台灣造勢現場 | 熱情為主，帶點從容 | 熱情 78、手勢強調 9 次 |

調權重後三支都重跑，確認三種結果仍然各自合理再交付。
