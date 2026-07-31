# 首頁地圖 — 相機位置顯示權限

首頁（index）地圖上的**相機位置（綠色 marker）**不是所有人都看得到。本文說明目前的規則與實作位置。

## 資料來源

首頁地圖是三層的互動：

1. 點擊縣市 → `/api/stat_county`（`base/views.stat_county`）回傳該縣市的**樣區圖釘**
2. 點擊樣區圖釘 → `/api/stat_studyarea`（`base/views.stat_studyarea`）回傳該樣區的**相機位置 marker** 與「影像累積筆數」長條圖
3. 前端繪製：`static/js/home.js`（`DeploymentIcon` 綠色 marker，約在 443 行）

## 規則一：只顯示 project_id = 329

樣區圖釘與相機位置都只取 `project_id = 329` 的資料，其他計畫不會出現在首頁地圖上。

- 樣區圖釘：`stat_county` 的 SQL 加上 `AND sa.project_id = 329`
- 相機位置：`stat_studyarea` 的 SQL 加上 `AND project_id = 329`

## 規則二：相機位置只給有權限的登入者看

由 `base/views.can_view_studyarea_deployment(request, project_id, studyarea_id)` 判斷。**樣區圖釘不受此規則限制**，未登入者仍看得到樣區圖釘。

| 使用者 | 看得到相機位置嗎 | 說明 |
| --- | --- | --- |
| 未登入 | ✗ | 一律看不到 |
| 系統管理員（`Contact.is_system_admin`） | ✓ 全部 | |
| 計畫總管理人（`Contact.is_organization_admin`） | ✓ 全部 | 需其所屬 organization 包含該計畫 |
| 計畫成員，且有指定樣區 | △ 只有自己的樣區 | 即使是同一個計畫，別人的樣區也看不到 |
| 計畫成員，但沒有指定樣區 | ✓ 全部 | |
| 已登入但非計畫成員 | ✗ | 與未登入相同 |

「指定樣區」指的是 `ProjectMember.pmstudyarea`（多對多，指向 `StudyArea`）。同一位使用者在該計畫下所有 `ProjectMember` 的 `pmstudyarea` 聯集就是他能看到的樣區範圍。

登入狀態判斷用 session：`request.session['is_login']` 與 `request.session['id']`（contact id），與 `base/utils.session_login_required` 一致。

## 沒有權限時的行為

`stat_studyarea` 會直接跳過相機位置的查詢，回傳空的 `deployment_points`：

- 地圖上沒有綠色 marker
- 右側「影像累積筆數」長條圖也是空的（與 marker 使用同一份資料）
- `center`（地圖置中座標）仍會回傳，所以點擊樣區時地圖不會出錯

## 相關檔案

| 檔案 | 內容 |
| --- | --- |
| `base/views.py` | `can_view_studyarea_deployment`、`stat_county`、`stat_studyarea` |
| `base/urls.py` | `/api/stat_county`、`/api/stat_studyarea` |
| `static/js/home.js` | 地圖繪製、marker 圖示 |
| `taicat/models.py` | `ProjectMember.pmstudyarea`、`Contact.is_system_admin` / `is_organization_admin` |

## 已知未處理

- 首頁右側的縣市統計數字（`num_project`、`num_deployment`、`num_image`、`species` …）來自 `GeoStat`，仍包含**所有計畫**，未依 329 或權限過濾。
- 圖例「相機位置」（綠色 marker 圖片）對所有人都會顯示，包含看不到 marker 的未登入者。
