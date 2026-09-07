# Scripts

`count-projectoversight-species-images-cache.py` 產生管考頁: 標註物種/全部照片 的 redis cache


`scripts/count-project-stats.py` 產生計畫的管考需要的資料 (stats)
```python
project.find_and_create_deployment_journal_gap() # 產生 “缺失” 的資料
project.get_or_count_stats(force=True) #  產生暫存檔
```

`/db-task <folder>` (Claude Code skill, `.claude/skills/db-task/`) 整理後台調整的待辦清單

輸入一個 task 資料夾，裡面放客戶給的 TSV 表格 (欄位: 資料夾名稱 / 正確相機編號 /
傳錯相機編號 / 上傳者 / 備註) 或中文需求文字。Agent 讀完檔案後直接查 production 資料庫
(`ssh ct-prod` 進 postgres container，本機 dump 不算數)，輸出 `<folder>/action-list.csv`:

```
index, folder_name, deployment_journal_id, action, swap_from_deployment, swap_to_deployment
```

`action` 是 `delete` 或 `swap`；`swap_from_deployment` / `swap_to_deployment` 是
`{deployment_name} [{deployment_id}]`，delete 兩欄留空。

正確相機編號 填 `刪除資料夾` 表示刪除；其他情況是 swap，相機編號在該資料夾所屬的
project 內解析成 deployment id。`swap_from` 取的是資料庫裡 journal 目前的位置，表格的
傳錯相機編號只拿來核對；對不上或已經在正確位置 (「照片先前已修正過位置」) 的資料夾會被
擋下來，不會被移動第二次。擋下來的原因寫在 `<folder>/action-list-problems.txt`。

清單確認後才執行，一樣在 prod 上跑，而且只照 `action-list.csv` 跑、不重查 id:
delete 用 `make delete-folder FOLDER=... [DRY_RUN=1]`，swap 用 `ssh ct-prod` 進 django
container 跑 `scripts/swap-deployment.py` (預設 dry run，`--commit` 才寫入；swap 保留
它自己的 cross-project 檢查)。

動手前先把要動的 journal 整列 (`SELECT *`) 撈成快照 — delete 之後就查不到了。跑完再查
一次資料庫驗證 (delete = id 不存在 / swap = `deployment_id` 等於目標)，工作紀錄寫到
`<folder>/result.csv`: DeploymentJournal 全部欄位 (動作前的快照) + `process` (delete/swap)
+ `is_success` + `process_time` + `note` (失敗原因)。

`adjust` (修改影像日期年份) 目前**沒有**對應的 script。
