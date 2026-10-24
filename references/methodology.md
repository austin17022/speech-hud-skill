# 技術原理

Speech HUD 分成三層：**感知層**用 Google MediaPipe 視覺模型量出臉、手、身體的位置與表情數值；**聲學層**用自行實作的語音訊號處理量出音高、語速、停頓；**判讀層**依照非語言溝通研究，將 17 項底層訊號加權組合成六種狀態。

Google 的模型負責量測，六種狀態的判讀規則由本工具訂定。

```
影片 ──┬─ 畫面 ─→ MediaPipe（臉 478 點、手 21×2 點、身體 33 點、52 組表情係數）─┐
       │                                                                      ├─→ 17 項底層訊號 ─→ 六種狀態 ─→ 雷達圖／報告
       └─ 聲音 ─→ 語音訊號處理（音高、語調起伏、語速、停頓、音量）───────────┘
```

全部在瀏覽器內以 WebAssembly 與顯示卡運算，影片不上傳任何伺服器。

---

## 一、感知層：Google MediaPipe Tasks Vision（v0.10.14）

| 模型 | 輸出 | 本工具量測的項目 |
|---|---|---|
| **Face Landmarker** | 478 個 3D 臉部特徵點（臉部網格 468 點＋虹膜 10 點），以及 52 組表情係數（blendshapes，規格與 Apple ARKit 相容，概念源自 FACS 臉部動作編碼系統） | 頭部轉向（yaw）與俯仰（pitch）、眼神接觸、眨眼頻率、抿嘴、皺眉、真笑 |
| **Hand Landmarker** | 每隻手 21 個 3D 關節點 | 手勢幅度與速度、手勢強調、摸臉與撥頭髮 |
| **Pose Landmarker**（BlazePose，full 版） | 全身 33 個關節點與可見度 | 雙手開合、聳肩、身體晃動、主角鎖定與追蹤 |

### 使用到的表情係數
| 量測項目 | blendshapes |
|---|---|
| 眨眼 | `eyeBlinkLeft`、`eyeBlinkRight` |
| 抿嘴 | `mouthPressLeft/Right`、`mouthRollLower/Upper` |
| 皺眉 | `browDownLeft/Right`、`browInnerUp` |
| 真笑 | `mouthSmileLeft/Right` 必須搭配 `cheekSquintLeft/Right`、`eyeSquintLeft/Right` 一起出現 |

### 主角追蹤
多人畫面中，每一格先在全畫面偵測所有人，再對主角附近裁出窄框放大重新偵測，提升小目標的偵測率。辨識主角依據三項特徵：位置連續性、肩寬比例、上衣與褲子的平均顏色。細節見 [`tracking.md`](tracking.md)。

---

## 二、聲學層：語音訊號處理

| 指標 | 方法 |
|---|---|
| 音高（F0） | 時域正規化自相關（normalized autocorrelation），搜尋範圍 75～400 Hz，相關係數低於 0.55 視為無聲 |
| 語調起伏 | 最近 5 秒音高第 10 到第 90 百分位的差距，單位為半音 |
| 語速 | 音量包絡的局部波峰估算音節數，換算為每秒字數 |
| 停頓比例 | 最近數秒內音量低於說話門檻的時間比例 |
| 長停頓 | 連續沉默超過 1.2 秒記為一次 |
| 聲音穩定度 | 相鄰音高跳動的平均幅度，跳動越小越穩定 |
| 語氣加重 | 音量瞬間明顯高於近期平均值 |

---

## 三、判讀層：六種狀態

### 底層訊號與研究依據

| 訊號 | 主要影響的狀態 | 研究依據 |
|---|---|---|
| 真笑（嘴角加眼角同時收縮） | 熱情、自信 | Ekman, Davidson & Friesen（1990）：只有眼輪匝肌一起收縮的 Duchenne smile，才與真實正向情緒相關 |
| 摸臉、撥頭髮 | 壓力 | Ekman & Friesen（1969）：自我接觸型動作（adaptors）與焦慮、不自在相關 |
| 眨眼頻率升高 | 壓力 | Harrigan & O'Connell（1996）：受試者焦慮時眨眼次數顯著增加 |
| 停頓、說話中斷 | 遲疑、壓力 | Mahl（1956）：說話中斷與遲疑的頻率和焦慮程度相關 |
| 語調起伏大 | 熱情 | Rosenberg & Hirschberg（2009）：音高變化越大，聽眾越傾向認為講者有魅力 |
| 眼神接觸、抬頭 | 自信、從容 | 視線迴避與低頭是常見的退縮與不確定訊號 |
| 雙手收在身前、低頭 | 防備 | 常見的封閉姿態指標 |

### 六種狀態的組成

| 狀態 | 正向訊號 | 反向訊號 |
|---|---|---|
| 自信 | 眼神接觸、抬頭、手勢張開、手勢、聲音穩定、語調起伏、語速適中、真笑 | 停頓 |
| 壓力 | 眨眼、抿嘴、聳肩、晃動、聲音顫抖、摸臉、皺眉、語速過快、停頓、長停頓 | |
| 遲疑 | 停頓、長停頓、語速過慢、視線移開、低頭、手不動、摸臉 | |
| 防備 | 雙手收在身前、抿嘴、皺眉、低頭、視線移開 | 手勢張開 |
| 熱情 | 手勢、語調起伏、真笑、語氣加重、手勢張開、語速快 | |
| 從容 | 聲音穩定、眼神接觸、語速適中 | 晃動、眨眼、摸臉、抿嘴、停頓、長停頓 |

完整權重見 [`scoring.md`](scoring.md)。

### 兩道後處理
1. **流暢度修正**：卡頓指數 = 停頓 × 0.7 ＋ 長停頓 × 0.3。從容 × (1 − 0.6 × 卡頓)、自信 × (1 − 0.35 × 卡頓)，壓力依卡頓程度往上加。避免「坐姿端正但一直卡詞」被判成從容
2. **差異放大**：六種分數以平均值為中心放大 2.6 倍，範圍限制在 6～97，讓雷達圖清楚呈現個人特徵

畫面上的數值經過時間平滑；結尾報告取全片平均，並標出壓力最高的時間點。

---

## 適用範圍
- 本工具量測的是可觀察的行為訊號，分數代表「訊號強弱」，不代表內心真實情緒
- 判讀規則依文獻設計，未經臨床或實驗驗證；不做測謊
- 講者的文化背景、母語與否、場合（質詢、訪談、造勢）都會影響基準，跨場合比較時要一併考量
- 描述成果時建議寫「AI 從肢體與聲音量出的訊號」，不寫成「AI 判定某人說謊或緊張」

---

## 參考文獻

**模型**
- Kartynnik, Y., Ablavatski, A., Grishchenko, I., & Grundmann, M. (2019). *Real-time Facial Surface Geometry from Monocular Video on Mobile GPUs.* arXiv:1907.06724
- Zhang, F., Bazarevsky, V., Vakunov, A., et al. (2020). *MediaPipe Hands: On-device Real-time Hand Tracking.* arXiv:2006.10214
- Bazarevsky, V., Grishchenko, I., Raveendran, K., et al. (2020). *BlazePose: On-device Real-time Body Pose Tracking.* arXiv:2006.10204
- Google AI Edge, MediaPipe Solutions：https://ai.google.dev/edge/mediapipe/solutions/guide

**行為科學**
- Ekman, P., & Friesen, W. V. (1969). The repertoire of nonverbal behavior: Categories, origins, usage, and coding. *Semiotica, 1*(1), 49–98.
- Ekman, P., & Friesen, W. V. (1978). *Facial Action Coding System.* Consulting Psychologists Press.
- Ekman, P., Davidson, R. J., & Friesen, W. V. (1990). The Duchenne smile: Emotional expression and brain physiology II. *Journal of Personality and Social Psychology, 58*(2), 342–353.
- Harrigan, J. A., & O'Connell, D. M. (1996). How do you look when feeling anxious? Facial displays of anxiety. *Personality and Individual Differences, 21*(2), 205–212.
- Mahl, G. F. (1956). Disturbances and silences in the patient's speech in psychotherapy. *Journal of Abnormal and Social Psychology, 53*(1), 1–15.
- Rosenberg, A., & Hirschberg, J. (2009). Charisma perception from text and speech. *Speech Communication, 51*(7), 640–655.
