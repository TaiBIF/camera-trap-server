# 從 Camtrap DP 資料集計算 OI1 / OI2 / OI3 / POD

本文件說明 TaiCAT 所回報的相對豐富度指數，並示範如何**從匯出的 Camtrap DP 套件**
（由 [`scripts/export-camtrap-dp.py`](../scripts/export-camtrap-dp.py) 產生的目錄）
重新計算這些指數，而非從正式資料庫計算。

參考實作為 `taicat/models.py` 中的
[`Deployment.calculate`](../taicat/models.py)。以下公式與其相同，僅有*資料來源*
不同——從 Django ORM 改為三個 CSV 檔（`deployments.csv`、`media.csv`、
`observations.csv`）。

---

## 1. 各指數的意義

三個「OI」（Occurrence Index／相對豐富度指數）值都具有相同的形式：

```
OI = (獨立有效照片數 / 有效相機工作時數) × 1000
```

亦即**每 1 000 相機工作時數中某物種的獨立有效照片數**。三者的差別僅在於
*如何計算一張「獨立有效照片」*：

| 指數 | 計數規則 | 是否使用個體 ID？ |
|------|----------|-------------------|
| **OI1** | 當動物個體改變、**或**同一個體在超過 `image_interval` 後再次出現時，視為一筆新的有效照片 | 是（`individualID` / `animal_id`） |
| **OI2** | 只要距離上一筆計入的照片之間隔 ≥ `image_interval`，即計為一筆新照片（純以時間判斷，忽略個體） | 否 |
| **OI3** | 與 OI2 相同的時間規則，但只套用於**沒有**個體 ID 的照片 | 否 |

`POD` 則是另一種類型的指標：

```
POD = (該物種出現的不同天數) / (相機工作天數)
```

——即在所有工作天當中，有拍攝到該物種的天數比例（photographic occurrence days，
出現日數比例）。

有兩個間隔參數控制計數方式（兩者傳入 `calculate` 時皆以**分鐘**為單位）：

- `image_interval`——兩張照片要被視為*不同*獨立有效照片所需的最小間隔
  （常見值：30 或 60 分鐘）。
- `event_interval`——區隔兩個*事件（event）*的間隔（用於 `event_count`，
  不影響 OI 值本身）。

程式碼中註記的預設 occasion／session 設定：

> POD：occasion（回合）= 1 天，session（期間）= 1 月
> APOA：occasion = 1 小時

---

## 2. 各項輸入在 Camtrap DP 套件中的來源

`Deployment.calculate` 從資料庫讀取三類資料。以下為其在匯出套件中的對應來源：

| `calculate` 所需 | 來自正式資料庫 | 來自 Camtrap DP 套件 |
|------------------|----------------|----------------------|
| 物種照片（時間、個體 id） | `Image` 中該 deployment／物種、且 `is_duplicated != 'Y'` 的列 | `observations.csv` 中以 `scientificName` 篩選的列（重複照片已於匯出時排除） |
| 拍攝時間 | `Image.datetime`（以 UTC 儲存，程式中位移為 +08:00） | `observations.csv.timestamp`——**已是 `+08:00`**，無需位移 |
| 個體 id | `Image.animal_id` | `observations.csv.individualID` |
| 相機工作時間 | 由 `DeploymentJournal` 透過 `Deployment.count_working_day()` 計算（已排除缺失） | `deployments.csv` 的 `deploymentStart` / `deploymentEnd` 區間 |

### 主要欄位對照

**`observations.csv`**（每張已鑑定照片一列，`observationLevel = media`）：

| 欄位 | 意義 | `calculate` 對應 |
|------|------|------------------|
| `deploymentID` | `j-<journal_id>`（舊計畫為 `dep-<id>`） | 用以將照片依相機工作期間分組 |
| `mediaID` | 影像 uuid | `Image.image_uuid` |
| `timestamp` / `eventStart` | 拍攝時間，`+08:00` | `Image.datetime`（位移為台灣時間後） |
| `scientificName` | 物種名稱 | `Image.species` |
| `individualID` | 動物個體 id | `Image.animal_id` |
| `observationType` | `animal` 或 `blank` | `'animal' if species else 'blank'` |

**`deployments.csv`**（每段相機工作期間一列）：

| 欄位 | 意義 |
|------|------|
| `deploymentID` | `j-<journal_id>`——對應 `observations.deploymentID` |
| `locationID` | `loc-<deployment_id>`——實體相機位置（樣點） |
| `deploymentStart` / `deploymentEnd` | 工作區間，`+08:00`（缺失已切分為不同列／已排除） |

> **重要的分組說明。** 在匯出資料中，一筆 Camtrap *deployment*
> （`j-<journal_id>`）= 一筆 `DeploymentJournal` = 一段連續的相機工作期間。
> 單一實體相機位置（`locationID = loc-<deployment_id>`）可能對應**多列** deployment。
> 若要重現以*實體 deployment* 為單位運作的 `Deployment.calculate`，必須
> **以 `locationID` 分組**，而非以 `deploymentID` 分組。

---

## 3. 有效相機工作時數（分母）

在 `calculate` 中：

```python
working_days = self.count_working_day(year, month)[0]   # 該月每一天 0/1 的清單
sum_working_hours = sum(working_days) * 24
```

`count_working_day` 會把每個有任何有效（非缺失）`DeploymentJournal` 覆蓋的日曆日
標記為 `1`，然後工作時數 =（工作天數）× 24。**解析度是「整天」，並非部分小時。**

要從 `deployments.csv` 針對某位置與某目標月份重現此值：

1. 取出所有 `locationID` 等於該相機位置的 `deployments.csv` 列。
2. 對每一列，取得介於 `deploymentStart` 與 `deploymentEnd`（含兩端）之間、
   且落在目標月份內的**日曆日**集合。
3. 將各列的日期集合做聯集（避免重疊的工作期間被重複計算）。
4. `working_days = 不同日期的數量`；`有效相機工作時數 = working_days × 24`。

```python
from datetime import date, timedelta

def working_days_in_month(dep_rows, year, month):
    days = set()
    for r in dep_rows:                       # 同一 locationID 的各列
        start = parse_iso(r['deploymentStart']).date()
        end   = parse_iso(r['deploymentEnd']).date()
        d = start
        while d <= end:
            if d.year == year and d.month == month:
                days.add(d)
            d += timedelta(days=1)
    return len(days)
```

> **舊計畫** 匯出時 `deploymentID = dep-<id>`，其 `deploymentStart`/`deploymentEnd`
> 是由照片時間的最小／最大值推導而來（見 `write_deployments_legacy`）。此時工作時數
> 只是真實工作期間的近似值——由舊套件計算出的任何指數都應標註為近似。

---

## 4. 獨立有效照片計數（分子）

這是 `Deployment.calculate` 的核心。OI3／OI2 的分子是通過「將間隔小於
`image_interval` 的照片合併」規則後所剩下的照片數。以下是以 `observations.csv`
列為對象、符合模型意圖的乾淨參考實作。

### OI3——以時間判斷，不使用個體 ID

```python
def count_oi3(obs, image_interval_min):
    """obs：某物種的列（observationType='animal'），已依 timestamp 排序。"""
    threshold = image_interval_min * 60
    count = 0
    last = None
    delta_acc = 0          # 自上一筆「計入」照片以來累積的秒數
    for o in obs:
        t = parse_iso(o['timestamp'])
        if last is None:
            count = 1               # 第一張照片必定計入
        else:
            delta_acc += (t - last).total_seconds()
            if delta_acc >= threshold:
                count += 1
                delta_acc = 0       # 只有在計入新照片時才歸零
        last = t
    return count
```

在模型中，OI3 **只針對沒有 `individualID` 的照片**遞增（迴圈的 `else` 分支）。
若你的資料從不填寫 `individualID`（最常見的情況），OI3 會在間隔規則下計入每一張
物種照片——這是大多數計畫實際使用的值。

### OI1——考慮個體

```python
def count_oi1(obs, image_interval_min):
    """obs 依 timestamp 排序；使用 individualID。"""
    threshold = image_interval_min * 60
    count = 0
    last = None
    delta_acc = 0
    prev_individual = None
    for o in obs:
        t = parse_iso(o['timestamp'])
        ind = (o.get('individualID') or '').strip()
        if last is None:
            count = 1 if ind else 0     # 第一張照片只有在有 id 時才計入
            prev_individual = ind or None
        else:
            delta_acc += (t - last).total_seconds()
            if ind:
                if prev_individual is not None:
                    if ind != prev_individual:      # 不同個體 → 新的有效照片
                        count += 1
                    elif delta_acc >= threshold:    # 同一個體，間隔後再次出現
                        count += 1
                        delta_acc = 0
                else:
                    prev_individual = ind
                    count += 1
        last = t
    return count
```

### OI2——以時間判斷，忽略個體

概念上，OI2 是把 OI3 *套用到所有物種照片，不論是否有個體 ID*。
（註：`Deployment.calculate` 中的正式 OI2 迴圈有已知的 bug——它重用了已過時的
`image_dt`，導致時間差實際上為零、計數塌陷。正確的意圖就是把 `count_oi3` 套用在
*所有*物種列上，而非僅限沒有 id 的列。）

```python
def count_oi2(obs, image_interval_min):
    return count_oi3(obs, image_interval_min)   # 同一規則，套用於所有物種照片
```

### 由計數換算為指數

```python
def oi(count, working_days):
    hours = working_days * 24
    return (count / hours) * 1000 if hours > 0 else None   # 模型中為 'N/A'
```

---

## 5. POD——出現日數比例

```python
def count_pod(obs, working_days):
    days_with_species = {parse_iso(o['timestamp']).date() for o in obs}
    return len(days_with_species) / working_days if working_days > 0 else None
```

模型中此值為 `by_day.count() / sum(working_days)`——該物種出現的不同天數，
除以總工作天數。

---

## 6. 活動模式格點（`mdh`）

`calculate` 回傳結果的最後一個元素，是用於活動模式（POA）繪圖的「月×日×時」
出現格點：

```
mdh[day] = [當日是否出現該物種(0/1), [第0時是否出現, ... 第23時]]
```

由 `observations.csv` 計算時非常簡單：對每張物種照片，標記
`mdh[timestamp.day-1][0] = 1` 及 `mdh[timestamp.day-1][1][timestamp.hour] = 1`。

> 模型會把小時數從 UTC 位移到台灣時間（`utc_hour + 8`），因為 `Image.datetime`
> 以 UTC 儲存。**在 Camtrap DP 匯出資料中，`timestamp` 已是 `+08:00`，因此不需要
> 任何小時位移**——直接使用 `timestamp.hour` 即可。

---

## 7. 完整範例（單一物種、單一位置、單一月份）

```python
import csv
from datetime import datetime

def parse_iso(s):
    return datetime.fromisoformat(s)   # 匯出資料使用帶 +08:00 的 ISO-8601

def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

deployments  = load('deployments.csv')
observations = load('observations.csv')

location_id   = 'loc-12345'
species       = '山羌'
year, month   = 2024, 3
image_interval = 30        # 分鐘
event_interval = 60        # 分鐘（僅用於 event_count）

# 1. 此實體相機位置的 deployment 列
dep_rows = [d for d in deployments if d['locationID'] == location_id]
dep_ids  = {d['deploymentID'] for d in dep_rows}

# 2. 有效相機工作時數
wdays = working_days_in_month(dep_rows, year, month)

# 3. 此位置、目標月份內的物種照片，依時間排序
obs = [
    o for o in observations
    if o['deploymentID'] in dep_ids
    and o['observationType'] == 'animal'
    and o['scientificName'] == species
    and parse_iso(o['timestamp']).year == year
    and parse_iso(o['timestamp']).month == month
]
obs.sort(key=lambda o: o['timestamp'])

# 4. 各指數
oi1 = oi(count_oi1(obs, image_interval), wdays)
oi2 = oi(count_oi2(obs, image_interval), wdays)
oi3 = oi(count_oi3(obs, image_interval), wdays)
pod = count_pod(obs, wdays)

print(year, month, species, 'OI1', oi1, 'OI2', oi2, 'OI3', oi3, 'POD', pod)
```

---

## 8. 與正式 `Deployment.calculate` 的差異

從套件重現的結果會*接近、但不會與資料庫完全逐位元相符*。已知原因如下：

1. **工作時數解析度。** 兩者都以 `working_days × 24` 計算工作時數。只要缺失在匯出
   時被正確排除（匯出時已透過 `is_gap` 過濾），工作日集合應該相符。舊版（`dep-*`）
   套件以照片最小／最大時間推導工作區間，僅為近似。
2. **月份邊界／時區。** 模型以對應台灣月份的 UTC 區間挑選照片；套件的時間戳已是
   `+08:00`，因此直接以 `timestamp.month` 篩選即為自然對應，並可避免 UTC↔台灣時間
   的邊界處理。
3. **OI2 bug。** 正式 OI2 是壞的（過時的 `image_dt`）；上述範例採用其應有的定義
   （對所有物種列套用 OI3 規則）。
4. **重複照片。** `is_duplicated = 'Y'` 的影像*在匯出時*即已排除，因此套件已與模型的
   `.exclude(is_duplicated='Y')` 相符。
5. **個體 ID。** 只有在 `individualID` 有填值時，`OI1` 才會與 `OI2`／`OI3` 分歧；
   對多數計畫而言此欄為空，三者的分子會收斂一致。
