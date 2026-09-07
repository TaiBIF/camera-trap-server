# Calculation

## Policy & Rules

### 相機有效工作

用行程來判定，這段時間都算相機正常工作
理想上，相機每天會拍測試照，有測試照的就算當天有工作，但實際上不是每台相機都有設定。


### 活動機率`

ex: （五月有三十一天，其中有五天下午兩點到三點被拍攝到，則在下午兩點到三點的活動機率為 5/31）

## API

主要計算:

### Deployment.calculate

*Parameters*

year: int
month: int
species: str
image_interval: int
event_interval: int

*Returns*

list:

[working_days, image_count, event_count, None, None, oi3, pod, mdh]

### Deployment.count_working_day

*Parameters*

year: int
month: int

*Returns*

list:

month_stat: a list to describe each camera has working `1` or not `0`, ex: [0, 1, 0 ...]
working_range: a list to describe working start and end in this month (overlaped filtered DeploymentJournal)



### Download
Source: `taicat.utils` calc, calc_output

calc -> Deployment.calculate


### Cache

有效照片間隔: 30, 60

目擊事件間隔: 2, 5, 10, 30, 60

```
key = f'{dep.id}/{year}/{month}/{species_name}/{img_int}/{e_int}'
```

Models: Deployment.calculate(year, month, species, image_interval, event_interval)
```
[working_days, image_count, event_count, None, None, oi3, pod, mdh]
```

mdh: 這個月的每天，出現在幾點 => 活動機率(propability of activity, POA)


OI1/2/3 如果沒有工作時數會用 "N/A" 表示

pod: 分母是工作天數，但分子是**該格的照片數**，不是有拍到的天數 —
`by_day.count()` 是在 queryset 還沒被求值的狀態下呼叫的，Django 會把 GROUP BY
折掉直接數 row。所以 pod 可能大於 1。現有資料都是這個算法算出來的，`taicat/calc_core.py`
照樣保留；要改成「有拍到的天數 / 工作天數」的話，全部 11.8M 列的值都會變，得另外決定。

oi2: 原本的迴圈沒有更新自己的時間變數，實際上只要該格有照片就是 1 (再除以工作時數)。
同樣照原樣保留。
