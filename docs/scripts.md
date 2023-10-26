# Scripts

`count-projectoversight-species-images-cache.py` 產生管考頁: 標註物種/全部照片 的 redis cache


`scripts/count-project-stats.py` 產生計畫的管考需要的資料 (stats)
```python
project.find_and_create_deployment_journal_gap() # 產生 “缺失” 的資料
project.get_or_count_stats(force=True) #  產生暫存檔
```
