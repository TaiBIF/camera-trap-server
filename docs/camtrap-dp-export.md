# Camtrap DP 匯出說明

> 對象：計畫管理者（PM）
> 程式：`scripts/export-camtrap-dp.py`
> 規範：[Camtrap DP 1.0](https://camtrap-dp.tdwg.org/)

---

## 一、什麼是 Camtrap DP

Camtrap DP（Camera Trap Data Package）是 TDWG 制定的**自動相機資料標準格式**，
讓不同來源的相機資料可以彼此交換、整合分析。每個計畫匯出後是一個資料夾，內含 4 個檔案：

| 檔案 | 內容 | 一列代表 |
|------|------|----------|
| `datapackage.json` | 計畫描述、授權、聯絡人、統計 | （整包的詮釋資料）|
| `deployments.csv` | 相機佈設紀錄 | 一台相機在某地點、某段期間的運作 |
| `media.csv` | 影像檔 | 一張照片 |
| `observations.csv` | 物種辨識結果 | 一筆辨識（一張照片一筆）|

三者的關聯：**一個 deployment 包含多張 media，每張 media 對應一筆 observation**。

---

## 二、三個層級的對應關係（重要觀念）

TaiCAT 的資料結構，對應到 Camtrap DP 與 DarwinCore 如下：

| TaiCAT | Camtrap DP | DarwinCore | 白話 |
|--------|-----------|-----------|------|
| `Deployment`（相機位置點，有經緯度、樣點名如 CF-09） | **deployment** | ≈ Event（採樣事件）| 「哪一台相機、架在哪裡、架多久」|
| `DeploymentJournal`（一次回收作業的工作期間） | **deployment**（更細）| ≈ Event | 「這次架設從何時到何時」|
| `Image`（一張已辨識的照片） | **media** + **observation** | ≈ Occurrence（出現紀錄）| 「拍到什麼」|

**核心原則：deployment 是「採樣事件」層級，不是「單張照片」層級。**
就像 DarwinCore 裡，許多 Occurrence 共用一個 Event；
這裡也是**許多照片共用一個 deployment**，不會一張照片就開一個 deployment。

---

## 三、兩種匯出規則

程式會先判斷該計畫**有沒有 DeploymentJournal 資料**，再決定走哪一套規則。

```
有 DeploymentJournal 紀錄？
 ├─ 有  → 走【新版規則】（以工作期間為單位）
 └─ 沒有 → 走【舊版規則】（以相機位置點為單位）
```

### 規則 A — 新版計畫（有 DeploymentJournal）

近期計畫透過桌機上傳工具，每次回收資料都會建立一筆 `DeploymentJournal`，
記錄該次架設的**起訖時間**（working_start ～ working_end）。

- **一筆 DeploymentJournal = 一個 deployment**
- `deploymentID` 格式：`j-{紀錄編號}`（例：`j-12914`）
- 工作期間：直接採用紀錄中的起訖時間（台灣時間）
- 同一個樣點若有多次架設，會拆成**多個 deployment**（較精確）

### 規則 B — 舊版計畫（沒有 DeploymentJournal）

早期計畫只有照片（occurrence）資料，**沒有架設作業的起訖時間紀錄**，
只有相機位置點（`Deployment`）。

- **一個相機位置點 = 一個 deployment**
- `deploymentID` 格式：`dep-{位置點編號}`（例：`dep-11559`）
- 工作期間：用該位置點**所有照片的最早與最晚拍攝時間**推算
- 所有屬於該位置點的照片，都歸到這一個 deployment 底下

#### 為什麼舊版這樣設計？

我們曾考慮過另外兩種極端做法，但都不正確：

| 做法 | 問題 |
|------|------|
| 整個計畫當成 1 個 deployment | Camtrap DP 規定每個 deployment 只能有**一組經緯度**，但一個計畫有很多樣點、各在不同地點。合併後座標失去意義，無法做空間分析。❌ |
| 每張照片各當成 1 個 deployment | deployment 應是「一段連續監測期間」，不是一個瞬間。會產生大量起訖時間相同（長度為 0）的 deployment，採樣天數全部算成 0。❌ |
| **一個相機位置點 = 1 個 deployment** | 保留各樣點真實座標、給出合理的監測期間。✅ 採用此法 |

#### 已知限制

舊版規則用「最早～最晚照片時間」當作監測期間。
若同一個樣點其實跨越**多次回收作業**（中間有停機空檔），
這些作業會被合併成一段連續期間，可能**略為高估實際運作天數**。

> 這是缺乏 DeploymentJournal 時的合理折衷。若日後需要更精確，
> 可依照片時間軸上的「長空檔」（例如超過 30～60 天）自動切分成多段 deployment。

---

## 四、相機型號（cameraModel）

兩種規則都會嘗試補上**相機廠牌與型號**，資料來源為 `taicat_image_info` 資料表的 `exif` 欄位
（照片上傳時記錄的 EXIF 詮釋資料）。

- 每個 deployment 取**一張代表照片**讀取其 EXIF 的 `Make`（廠牌）與 `Model`（型號）
- 輸出格式為 `廠牌-型號`，例如：
  - `RECONYX-HC500 HYPERFIRE`
  - `Panasonic-DMC-GX7MK2`
- 若該代表照片沒有可用的 EXIF，欄位會留白（屬正常情況，非錯誤）

> 說明：`cameraID`（相機序號）多數照片的 EXIF 並未記錄，故維持留白。

---

## 五、測試照、空拍與人員照的處理

TaiCAT 沒有獨立欄位記錄「這是不是測試照」，而是把這類標記寫在**物種（species）欄位**裡
（例如「測試」「空拍」「工作照」）。匯出時不能把所有非空白的標籤都當成動物，
否則數百萬筆「測試／空拍」會被誤標成 `animal`，污染下游的物種分析。

Camtrap DP 對這些情況有現成的處理方式：

- **`observationType`**（觀測類型）：受控字彙 `animal` / `human` / `vehicle` / `blank` / `unknown` / `unclassified`，**沒有** `test`／`setup` 這個值。
- **`cameraSetupType`**（注意：欄位名是 `cameraSetupType`，不是 `cameraSetup`，也不是布林）：受控字彙只有兩個值 —— `setup`（架設／回收動作）與 `calibration`（校正動作）；留空表示非設定照。
- **`media.captureMethod`**：`activityDetection`（位移觸發）或 `timeLapse`（定時拍攝）。

> 為什麼測試照的 `cameraSetupType` 留空？「測試」是定時自拍的「相機還活著」確認幀，
> 用 `captureMethod=timeLapse` 標記就夠了；Camtrap DP 的 `calibration` 指的是「校正動作」
> （例如拿距離標桿在鏡頭前比對），跟定時測試幀不是同一件事，而且會跟 `timeLapse` 重複，
> 所以留空。`setup`（工作照／收相機）則一定要保留——這些是位移觸發（`activityDetection`），
> `media` 那邊看不出來是架設／回收，只有 `cameraSetupType=setup` 能標記。

### 對應規則

| TaiCAT species 標籤 | 是否匯出 | observationType | cameraSetupType | captureMethod |
|---|---|---|---|---|
| 真實物種（水鹿、山羌…）| ✅ | `animal` | （留空）| activityDetection |
| 空拍 / 錯誤空拍 / 空拍(黑) | ✅ | `blank` | （留空）| activityDetection |
| 測試 / 曠時攝影測試… / test（定時測試幀）| ✅ | `blank` | （留空）| **timeLapse** |
| 工作照 / 收相機 / 研究人員到點結束片（架設回收人員照）| ✅ | `human` | **`setup`** | activityDetection |
| **人 / 獵人 / 研究人員…（`Species.EXCLUDE_LIST`）** | **❌ 不匯出** | — | — | — |

### 三個重點

1. **真實人員照不公開（隱私），但仍用於計算工作期間**：`Species.EXCLUDE_LIST` 中的標籤
   （人、人（有槍）、人＋狗、狗＋人、獵人、砍草工人、研究人員、研究人員自己、除草工人）
   屬於偶然入鏡的真實人物，**不匯出為 media／observation**。
   但在**舊版規則**中，這些照片**仍會計入 `deploymentStart`／`deploymentEnd` 的最早～最晚時間**
   ——因為它們同樣證明相機當時在運作。也就是說，EXCLUDE_LIST 資料**只用來界定工作期間，不對外公開**。
   （新版規則的工作期間取自 DeploymentJournal 的起訖時間，與照片無關。）

2. **測試照／人員架設照保留，但加註記**：這些照片**不刪除**，因為它們界定了相機的工作期間
   （第一張架設照、最後一張收相機照剛好是工作期間兩端）。透過 `cameraSetupType` 與
   `captureMethod` 標記後，使用者做物種分析時可以濾掉，但仍能用它們計算相機工作時間。

3. **原始中文標籤逐字保留**：凡是沒有對到拉丁學名的列（測試、空拍、工作照、收相機，以及
   對不到 TaiCOL 的動物標籤），原始的中文 `species` 標籤都會**原樣寫進 `observationComments`**
   （若原本就有備註，則接在備註前面），等同 Darwin Core 的 verbatim 概念，方便回溯原始辨識。
   已對到學名的動物則不重複——其中文名已放在 `taxonomic[].vernacularNames`。

> 補充：Camtrap DP 不直接儲存「工作天數」，而是由使用者從 `deploymentStart → deploymentEnd`
> 推算。所以測試照的角色就是去界定這段期間，而非自己攜帶工作天數。

---

## 六、學名（scientificName）與俗名（vernacularName）

TaiCAT 的 `species` 欄位存的是**中文俗名**（山羌、水鹿…），但 Camtrap DP 規定
`observations.scientificName` 必須放**拉丁學名**，中文俗名要另外放在資料包詮釋資料裡。
所以匯出時會做一次名稱對應。

### 對應來源：TaiCOL

用 [TaiCOL](https://taicol.tw/) 的 taxon API（`common_name` 查詢）把中文俗名對到學名與
TaiCOL taxon id，整理成對照表 `species-taicol-map.csv`（欄位：`name, taicol_taxon_id,
is_valid, scientific_name`），再經人工校正。匯出程式用 `--species-map` 讀這份對照表。

### 寫到哪裡

| 名稱 | Camtrap DP 欄位 | 來源 |
|------|----------------|------|
| 拉丁學名 | `observations.scientificName` | 對照表 `scientific_name` |
| TaiCOL ID | `datapackage.json` → `taxonomic[].taxonID` | 對照表 `taicol_taxon_id` |
| 中文俗名 | `datapackage.json` → `taxonomic[].vernacularNames.zho` | 原始 `species` 標籤 |

`taxonomic[]` 是資料包層級的物種清單，每個出現過的學名一筆，例如：

```json
{
  "scientificName": "Muntiacus reevesi",
  "kingdom": "Animalia",
  "taxonID": "t0096460",
  "vernacularNames": { "zho": "山羌" }
}
```

（俗名語言代碼 `zho` 是 ISO 639-3 的中文。）

### 對不到學名的標籤

有些標籤對不到 TaiCOL（例如「獼猴」這種泛稱、TaiCOL 只收「臺灣獼猴」全名；或
「白腹秧雞(白胸秧雞)」這種帶註解的字串）。這時：

- `observationType` 仍維持 `animal`（確實是動物，只是沒對到學名）
- `scientificName` 留空（不能塞中文，否則違規）
- 原始中文標籤保留到 `observationComments`（若原本就有備註，則接在備註前面），避免辨識結果遺失

---

## 七、其他匯出規則摘要

- **時間**：照片時間以 UTC 儲存，輸出時轉為台灣時間（+08:00）；DeploymentJournal 起訖時間本就是台灣時間。
- **排除**：標記為重複（`is_duplicated = Y`）的照片不匯出；已停用（deprecated）的位置點不匯出；
  `Species.EXCLUDE_LIST` 的真實人員照不匯出（見第五節）。
- **必填欄位保護**：Camtrap DP 規定 deployment 必須有經緯度與工作起訖時間、media 必須有時間戳。
  若資料缺漏（例：行程沒有工作期間、位置點完全沒有照片、照片沒有拍攝時間），
  該筆 deployment／照片會**整筆略過不匯出**，以確保產出的資料包符合規範、能通過驗證。
- **授權 / 聯絡人**：取自計畫的授權設定、主持人、執行單位等欄位。

---

## 八、使用方式

```bash
# 單一計畫
python scripts/export-camtrap-dp.py --project-id 280

# 多個計畫
python scripts/export-camtrap-dp.py --project-id 280,141 -o /tmp/dp

# 所有已公開計畫
python scripts/export-camtrap-dp.py --all-published

# 指定學名對照表（預設 species-taicol-map.csv）
python scripts/export-camtrap-dp.py --project-id 280 --species-map species-taicol-map.csv

# 同時打包成可直接上傳 IPT 的 zip
python scripts/export-camtrap-dp.py --project-id 280 --zip
```

執行後會在輸出資料夾（預設 `camtrap-dp-export/`）下，
為每個計畫建立一個 `project-{編號}-{名稱}` 子資料夾。

> 學名對照表 `species-taicol-map.csv` 由 `scripts/export-species-taicol.py` 產生
> （透過 TaiCOL API 查詢），再人工校正。若不提供，`scientificName` 會全部留空。

---

## 上傳到 GBIF IPT 的注意事項

- **`datapackage.json` 必須在 zip 的「最上層」**：IPT 是從 zip 根目錄找 `datapackage.json`，
  若外面包了一層資料夾（例如 `project-280-xxx/datapackage.json`）就會讀不到 metadata，
  出現 `getDataPackageMetadata() == null` → `HV000116: The object to be validated must not be null`。
  用 `--zip` 產生的壓縮檔，四個檔案都放在根目錄，可直接上傳。
- **必要的詮釋資料**：`datapackage.json` 的 `spatial`（GeoJSON 範圍）、`temporal`（起訖日期）、
  `taxonomic`（物種清單）都放在**最上層**（不是放在 `project` 裡），且至少要有一位 `contributors`。
  匯出程式會自動從 deployment 的座標與工作期間推算 `spatial`／`temporal`。
- **不要放非標準欄位**：曾經放過自訂的 `_stats`，IPT 解析時會失敗，已移除。

---

## 九、實際輸出範例

**舊版計畫**（規則 B，project 280）：

| deploymentID | locationName | cameraModel |
|---|---|---|
| dep-11559 | CF-09 | G4-CUDDEBACK |
| dep-11560 | CF-11 | G4-CUDDEBACK |
| dep-11563 | CF-16 | （留白）|

**新版計畫**（規則 A，project 141）：

| deploymentID | locationName | cameraModel |
|---|---|---|
| j-12914 | 桌機相機位置CL01 | RECONYX-HYPERFIRE 2 COVERT |
| j-13587 | 456 | Panasonic-DMC-GX7MK2 |
