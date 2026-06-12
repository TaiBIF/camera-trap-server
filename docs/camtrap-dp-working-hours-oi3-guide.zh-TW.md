# 使用下載的 Camtrap DP 計算「相機工作時數」與「OI3」

本文件給**研究團隊**使用。你不需要了解 TaiCAT 的資料庫，只要有從圖台下載的
Camtrap DP 資料夾，就能依本文件自行計算每個相機位置的**工作時數**與各物種的
**OI3（相對豐富度指數）**。

> 若你想了解這些公式背後與系統內部計算的對應關係，可參考
> [`calculate-oi-from-camtrap-dp.zh-TW.md`](./calculate-oi-from-camtrap-dp.zh-TW.md)
> （含 OI1／OI2／POD）。本文件只聚焦在最常用的**工作時數**與 **OI3**，並可直接執行。

---

## 1. 下載的資料夾裡有什麼

解壓縮後，每個計畫是一個資料夾，裡面有：

| 檔案 | 內容 | 本文件會用到 |
|------|------|--------------|
| `deployments.csv` | 每段「相機工作期間」一列（含起訖時間、相機位置、經緯度） | ✅ 算工作時數 |
| `observations.csv` | 每張已辨識照片一列（含拍攝時間、物種名稱） | ✅ 算 OI3 |
| `media.csv` | 每張照片的檔案資訊（連結、檔名） | 本文件不需要 |
| `datapackage.json` | 整個資料集的說明（標題、授權、計畫資訊） | 參考用 |

### 三個重要名詞（白話版）

- **deployment（一段工作期間）**：相機在某個位置、某段時間內連續運作的紀錄。
  欄位 `deploymentID` 是它的編號（例如 `j-1024`）。同一台相機若分多次回收資料，
  會有**多列** deployment。
- **locationID（相機位置／樣點）**：實體的相機架設點（例如 `loc-58`）。
  **同一個 `locationID` 可能對應多列 deployment**（多段工作期間）。
  > 計算某個樣點的工作時數或 OI 時，請**以 `locationID` 來歸戶**，把屬於它的所有
  > deployment 期間加總。
- **observation（一筆辨識）**：一張照片的辨識結果。`scientificName` 是物種名稱，
  `observationType = animal` 表示有動物、`blank` 表示空拍。

所有時間欄位（`deploymentStart`、`deploymentEnd`、`timestamp`）都已經是
**台灣時間（+08:00）**，可以直接使用，不需要再做時區換算。

---

## 2. 相機工作時數怎麼算

**原則**：把某相機位置（`locationID`）底下所有 deployment 的工作期間，
換算成「有運作的天數」，再乘以 24 小時。

步驟：

1. 從 `deployments.csv` 找出同一個 `locationID` 的所有列。
2. 對每一列，列出 `deploymentStart` 到 `deploymentEnd` 之間（含頭尾）的每一天。
3. 把這些日期收集起來、**去除重複**（避免期間重疊被重複計算）。
4. 工作天數 = 不重複的日期數量；**工作時數 = 工作天數 × 24**。

> 若你只想算某一個月份（例如 2024 年 3 月）的工作時數，就在步驟 2 只保留落在該月份
> 內的日期即可。

---

## 3. OI3 怎麼算

**OI3 的意義**：每 1 000 個相機工作小時，某物種出現的「獨立有效照片」數。

```
OI3 = (獨立有效照片數 / 工作時數) × 1000
```

**什麼是「獨立有效照片」？**
連拍的照片若彼此間隔太近，會被視為同一次出現。規則是：

- 第一張物種照片算 1 張。
- 之後每張照片，累計距離上一張「計入」照片的時間；
  當累計時間 **≥ `image_interval`（影像間隔，通常設 60 分鐘）** 時，才算新的一張，
  並把累計時間歸零。

例如把 `image_interval` 設為 60 分鐘：同一隻動物在 10 分鐘內被連拍 20 張，只算 1 張；
若牠 2 小時後又出現，才算第 2 張。

> `image_interval` 由研究團隊自行決定（常見為 30 或 60 分鐘）。**改變這個值，
> OI3 也會跟著改變**，所以報告時請一併註明你用的間隔。

---

## 4. 直接可執行的程式

把下面內容存成 `calc_oi3.py`，放在某個計畫資料夾旁邊（或修改最上面的 `DATA_DIR`
指到資料夾），用 Python 3 執行即可。只需內建套件，不必安裝任何東西。

```python
"""
從下載的 Camtrap DP 資料夾，計算每個相機位置每月的工作時數與各物種 OI3。
輸出一個 oi3_result.csv。

用法：
    python calc_oi3.py /path/to/project-287-xxxxx
"""

import csv
import sys
from datetime import datetime, timedelta
from collections import defaultdict

IMAGE_INTERVAL_MIN = 60   # 影像間隔（分鐘）— 獨立有效照片的判定門檻，可自行調整


def parse_iso(s):
    # 匯出時間為帶 +08:00 的 ISO-8601，例如 2024-03-05T14:23:00+08:00
    return datetime.fromisoformat(s)


def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def working_days_by_location_month(deployments):
    """回傳 {(locationID, year, month): 工作天數}。"""
    days = defaultdict(set)   # (loc, y, m) -> set of date
    for d in deployments:
        if not d.get('deploymentStart') or not d.get('deploymentEnd'):
            continue
        loc = d['locationID']
        start = parse_iso(d['deploymentStart']).date()
        end = parse_iso(d['deploymentEnd']).date()
        day = start
        while day <= end:
            days[(loc, day.year, day.month)].add(day)
            day += timedelta(days=1)
    return {k: len(v) for k, v in days.items()}


def count_independent(timestamps, interval_min):
    """獨立有效照片數：間隔 < interval 的照片併為同一張。timestamps 需已排序。"""
    threshold = interval_min * 60
    count = 0
    last = None
    delta_acc = 0      # 距離上一張「計入」照片累積的秒數
    for t in timestamps:
        if last is None:
            count = 1
        else:
            delta_acc += (t - last).total_seconds()
            if delta_acc >= threshold:
                count += 1
                delta_acc = 0
        last = t
    return count


def main(data_dir):
    deployments = load(f'{data_dir}/deployments.csv')
    observations = load(f'{data_dir}/observations.csv')

    # deploymentID -> locationID 對照
    dep_to_loc = {d['deploymentID']: d['locationID'] for d in deployments}

    # 工作天數
    wdays = working_days_by_location_month(deployments)

    # 收集每個 (locationID, year, month, 物種) 的照片時間
    photos = defaultdict(list)   # key -> [datetime, ...]
    for o in observations:
        if o.get('observationType') != 'animal':
            continue
        species = (o.get('scientificName') or '').strip()
        if not species:
            continue
        loc = dep_to_loc.get(o['deploymentID'])
        if loc is None:
            continue
        t = parse_iso(o['timestamp'])
        photos[(loc, t.year, t.month, species)].append(t)

    rows = []
    for (loc, year, month, species), ts in photos.items():
        ts.sort()
        wd = wdays.get((loc, year, month), 0)
        hours = wd * 24
        n_independent = count_independent(ts, IMAGE_INTERVAL_MIN)
        oi3 = (n_independent / hours) * 1000 if hours > 0 else None
        rows.append({
            'locationID': loc,
            'year': year,
            'month': month,
            'species': species,
            'working_days': wd,
            'working_hours': hours,
            'independent_photos': n_independent,
            'OI3': round(oi3, 4) if oi3 is not None else 'N/A',
        })

    rows.sort(key=lambda r: (r['locationID'], r['year'], r['month'], r['species']))

    out = f'{data_dir}/oi3_result.csv'
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=[
            'locationID', 'year', 'month', 'species',
            'working_days', 'working_hours', 'independent_photos', 'OI3'])
        w.writeheader()
        w.writerows(rows)

    print(f'影像間隔（image_interval）= {IMAGE_INTERVAL_MIN} 分鐘')
    print(f'共輸出 {len(rows)} 列 → {out}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法：python calc_oi3.py /path/to/計畫資料夾')
        sys.exit(1)
    main(sys.argv[1])
```

### 執行結果

會在資料夾內產生 `oi3_result.csv`，欄位如下：

| 欄位 | 意義 |
|------|------|
| `locationID` | 相機位置 |
| `year` / `month` | 年 / 月 |
| `species` | 物種名稱 |
| `working_days` | 該月工作天數 |
| `working_hours` | 該月工作時數（天數 × 24） |
| `independent_photos` | 獨立有效照片數 |
| `OI3` | 相對豐富度指數 |

用 Excel 開啟（已加 UTF-8 BOM，中文不會亂碼）即可進一步分析或繪圖。

---

## 5. 注意事項

1. **記得標註 `image_interval`。** OI3 會隨此參數變動，報告時請註明（本程式預設 60 分鐘，
   可在程式最上方 `IMAGE_INTERVAL_MIN` 調整）。
2. **以 `locationID` 為樣點單位。** 同一相機位置的多段工作期間已自動加總；請勿改用
   `deploymentID` 當作樣點，否則同一樣點會被拆開。
3. **空拍與未鑑定不計入。** 程式只取 `observationType = animal` 且有 `scientificName`
   的照片。
4. **跨月份。** 一段橫跨數月的工作期間，其天數會分別歸入各月份；OI3 也是逐月計算。
   若你需要「整段期間」或「整年」的 OI3，可自行把對應月份的 `independent_photos` 與
   `working_hours` 分別加總後再相除 × 1000。
5. **時間已是台灣時間。** 不需要再做 +8 時區轉換。
