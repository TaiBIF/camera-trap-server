import statistics
import math
from datetime import datetime

import pandas as pd
import numpy as np

from .utils import (
    apply_search_filter_projects,
    find_named_area,
    find_taiwan_area,
    find_year_month_range,
)

from taicat.models import (
    Calculation,
    timezone_utc_to_tw,
)

def calc_chart(calc_dict, species_list, project_filters):
    #print(calc_dict, species_list)
    query = Calculation.objects.filter(
        species=species_list[0],
        image_interval=calc_dict.get('imageInterval'),
        event_interval=calc_dict.get('eventInterval')
    )

    rows_other = {}
    # data->5: OI3 value
    if calc_dict['chartType'] == 'fig6':
        query = query.values('id' ,'deployment_id', 'data__7', 'datetime_from', 'deployment__name', 'deployment__longitude', 'deployment__latitude', 'deployment__geodetic_datum', 'deployment__altitude', 'studyarea__name')
    elif calc_dict['chartType'] == 'fig8':
        query = query.values('id' ,'deployment_id', 'data__5', 'datetime_from', 'deployment__name', 'deployment__altitude', 'studyarea__name', 'species')
        query_dog = Calculation.objects.filter(
            species='狗',
            image_interval=calc_dict.get('imageInterval'),
            event_interval=calc_dict.get('eventInterval')
        ).values('id' ,'deployment_id', 'data__5', 'datetime_from', 'deployment__name', 'deployment__altitude', 'studyarea__name')
        query_cat = Calculation.objects.filter(
            species='貓',
            image_interval=calc_dict.get('imageInterval'),
            event_interval=calc_dict.get('eventInterval')
        ).values('id' ,'deployment_id', 'data__5', 'datetime_from', 'deployment__name', 'deployment__altitude', 'studyarea__name')
        query_dog = apply_search_filter_projects(project_filters, query_dog)
        query_cat = apply_search_filter_projects(project_filters, query_cat)
        rows_other = {
            'dog': query_dog.all(),
            'cat': query_cat.all(),
        }
    elif calc_dict['chartType'] == 'fig9':
        query = query.values('id' ,'deployment_id', 'data__5', 'datetime_from', 'deployment__name', 'studyarea__name')
    else:
        query = query.values('id' ,'deployment_id', 'data__5', 'datetime_from', 'deployment__name', 'deployment__longitude', 'deployment__latitude', 'deployment__geodetic_datum', 'deployment__altitude', 'studyarea__name')

    query = apply_search_filter_projects(project_filters, query)
    #print(query.query)
    rows = query.all()
    if len(rows) == 0:
        return None

    if calc_dict.get('chartType') == 'fig1':
        return chart_fig1(rows)
    if calc_dict.get('chartType') == 'fig2':
        return chart_fig2(rows)
    if calc_dict.get('chartType') == 'fig3':
        return chart_fig3(rows)
    if calc_dict.get('chartType') == 'fig4':
        return chart_fig4(rows)
    if calc_dict.get('chartType') == 'fig6':
        return chart_fig6(rows)
    if calc_dict.get('chartType') == 'fig7':
        return chart_fig7(rows)
    if calc_dict.get('chartType') == 'fig8':
        return chart_fig8(rows, rows_other)
    if calc_dict.get('chartType') == 'fig9':
        return chart_fig9(rows)


def get_default_chart_data(part):
    if part == 'responsive':
        return {
            'rules': [{
                'condition': {
                    'maxWidth': 500
                },
                'chartOptions': {
                    'legend': {
                        'layout': 'horizontal',
                        'align': 'center',
                        'verticalAlign': 'bottom'
                    }
                }
            }]
        }
    return {}


def check_sanity(data):
    # TODO: only test fig1
    print(data)
    oi3 = data.get('data__5', None)
    if oi3 is None or oi3 == 'N/A':
        return False

    # must have deployment_id
    dep_id = data.get('deployment_id')
    if not dep_id:
        return False

    return True


def chart_fig9(rows):
    current_year = datetime.today().year

    deployments = {}
    year_map = {}
    for r in rows:
        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year
        did = r['deployment_id']
        if did not in deployments:
            deployments[did] = {}
        if r['year'] not in year_map:
            year_map[r['year']] = {'count': 0, 'deployments': {}, 'acc': 0}
        if did not in year_map[r['year']]['deployments']:
            year_map[r['year']]['deployments'][did] = 0
        year_map[r['year']]['deployments'][did] += 1
        year_map[r['year']]['count'] += 1

    df_rows = pd.DataFrame(data=rows)
    if len(df_rows):
        df_rows.set_index('id')

    #print(deployments)
    years = df_rows['year'].drop_duplicates().values
    years = sorted(years)

    series = [{
        'name': '當年出現樣點數',
        'data': [],
    }, {
        'name': '累計出現樣點數',
        'data': [],
    }]

    sum_acc = 0
    for y in years:
        sum_acc += year_map[y]['count']
        year_map[y]['acc'] = sum_acc
        series[0]['data'].append(year_map[y]['count'])
        series[1]['data'].append(year_map[y]['acc'])

    #print(series)
    #print(year_map)
    chart_data = {
        'chart': {
            'type': 'column',
        },
        'yAxis': {
            'min': 0,
            'title': {
                'text': '出現樣點數',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': 'Range: 00 to 23'
            },
            'categories': [int(y) for y in years],
            'crosshair': True,
            'title': {
                'text': '年',
            }
        },
        'plotOptions': {
            'column': {
            'pointPadding': 0.2,
            'borderWidth': 0
            }
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data

def chart_fig8(rows, rows_other):
    exist_deployment_map = {}
    sp_name = ''
    data = []
    data_dog = []
    data_cat = []
    for r in rows:
        if r['data__5'] == 'N/A':
            continue

        if sp_name == '':
            sp_name = r['species']

        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year

        did = exist_deployment_map.get(r['deployment_id'])
        if not did:
            exist_deployment_map[r['deployment_id']] = r['deployment__altitude']

        data.append(r)

    for r in rows_other['dog']:
        if r['data__5'] == 'N/A':
            continue

        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year
        did = exist_deployment_map.get(r['deployment_id'])
        if not did:
            exist_deployment_map[r['deployment_id']] = r['deployment__altitude']

        data_dog.append(r)

    for r in rows_other['cat']:
        if r['data__5'] == 'N/A':
            continue

        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year

        did = exist_deployment_map.get(r['deployment_id'])
        if not did:
            exist_deployment_map[r['deployment_id']] = r['deployment__altitude']

        data_cat.append(r)

    df_rows = pd.DataFrame(data=data)
    if len(df_rows):
        df_rows.set_index('id')
        pivoted = df_rows.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')
    df_rows_dog = pd.DataFrame(data=data_dog)
    if len(df_rows_dog):
        df_rows_dog.set_index('id')
        pivoted_dog = df_rows_dog.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')
    df_rows_cat = pd.DataFrame(data=data_cat)
    if len(df_rows_cat):
        df_rows_cat.set_index('id')
        pivoted_cat = df_rows_cat.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')

    #print(pivoted, pivoted_dog)
    # 整理相機位置
    #df_deployments = df_rows[['deployment_id', 'deployment__name', 'studyarea__name', 'deployment__altitude']].drop_duplicates()
    #df_deployments.index = df_deployments['deployment_id']

    series = [{
        'id': 'species',
        'name': sp_name,
        'marker': {
            'symbol': 'circle',
        },
        'data': [],
    }, {
    'name': '狗',
        'id': 'dog',
        'marker': {
            'symbol': 'square',
        },
        'data': [],
    },{
        'name': '貓',
        'id': 'cat',
        'marker': {
            'symbol': 'triangle',
        },
        'data': [],
    }]
    #print(exist_deployment_map)
    if len(df_rows):
        for index, oi3 in pivoted.mean(axis=1).items():
            series[0]['data'].append([exist_deployment_map[index], oi3])
    if len(df_rows_dog):
        for index, oi3 in pivoted_dog.mean(axis=1).items():
            series[1]['data'].append([exist_deployment_map[index], oi3])
    if len(df_rows_cat):
        for index, oi3 in pivoted_cat.mean(axis=1).items():
            series[2]['data'].append([exist_deployment_map[index], oi3])

    chart_data = {
        'chart': {
            'type': 'scatter',
            'zoomType': 'xy',
        },
        'yAxis': {
            'title': {
                'text': f'{sp_name}的相對豐度(OI_3)',
            }
        },
        'xAxis': {
            'title': {
                'text': '海拔',
            },
            'labels': {
                'format': '{value} m',
            },
            'startOnTick': True,
            'endOnTick': True,
            'showLastLabel': True,
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle'
        },
        'plotOptions': {
            'scatter': {
                'marker': {
                    'radius': 2.5,
                    'symbol': 'circle',
                    'states': {
                        'hover': {
                            'enabled': True,
                            'lineColor': 'rgb(100,100,100)'
                        }
                    }
                },
                'states': {
                    'hover': {
                        'marker': {
                            'enabled': False,
                        }
                    }
                },
                'jitter': {
                    'x': 0.005
                }
            }
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': 0,
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data


def chart_fig7(rows):
    exist_deployment_map = {}
    data = []
    for r in rows:
        if r['data__5'] == 'N/A':
            continue

        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year

        did = exist_deployment_map.get(r['deployment_id'])
        if not did:
            exist_deployment_map[r['deployment_id']] = r['deployment__altitude']

    if len(data) == 0:
        return None

    df_rows = pd.DataFrame(data=data)
    if len(df_rows):
        df_rows.set_index('id')

    pivoted = df_rows.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')

    # 整理相機位置
    #df_deployments = df_rows[['deployment_id', 'deployment__name', 'studyarea__name', 'deployment__altitude']].drop_duplicates()
    #df_deployments.index = df_deployments['deployment_id']

    series = [{
        'name': 'OI_3',
        'marker': {
            'symbol': 'circle',
        },
        'data': [],
    }]
    #print(exist_deployment_map)
    for index, oi3 in pivoted.mean(axis=1).items():
        series[0]['data'].append([exist_deployment_map[index], oi3])
    chart_data = {
        'chart': {
            'type': 'scatter',
            'zoomType': 'xy',
        },
        'yAxis': {
            'title': {
                'text': '歷年平均 OI_3',
            }
        },
        'xAxis': {
            #'categories': [0, 500, 1000, 1500, 2000, 2500, 3000],
            'title': {
                'text': '海拔',
            },
            'labels': {
                'format': '{value} m',
            },
            'startOnTick': True,
            'endOnTick': True,
            'showLastLabel': True,
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle'
        },
        'plotOptions': {
            'scatter': {
                'marker': {
                    'radius': 2.5,
                    'symbol': 'circle',
                    'states': {
                        'hover': {
                            'enabled': True,
                            'lineColor': 'rgb(100,100,100)'
                        }
                    }
                },
                'states': {
                    'hover': {
                        'marker': {
                            'enabled': False,
                        }
                    }
                },
                'jitter': {
                    'x': 0.005
                }
            }
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': 0,
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data

def chart_fig6(rows):
    by_hour = {}
    total = 0
    for h in range(0, 24):
        by_hour[h] = {
            'count': 0,
            'poa': 0,
        }

    for r in rows:
        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year

        for x in r['data__7']:
            for h in by_hour:
                r[f'poa:{h}'] = x[1][h]
                if x[1][h] > 0:
                    by_hour[h]['count'] += 1
                    total += 1

    series = [{
        'name': 'poa',
        'data': [],
    }]

    for h in by_hour:
        #by_hour[h]['poa'] = float(by_hour[h]['count'] / total)
        if total > 0:
            poa = float(by_hour[h]['count'] / total)
            series[0]['data'].append([f"計算: {by_hour[h]['count']} / {total}", poa])
        else:
            series[0]['data'].append([f"計算: 0", 0])

    chart_data = {
        'chart': {
            'type': 'column',
        },
        'yAxis': {
            'min': 0,
            'title': {
                'text': '出現機率',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': 'Range: 00 to 23'
            },
            'categories': ['{0:02d}'.format(h) for h in range(0, 24)],
            'crosshair': True,
            'title': {
                'text': '小時',
            }
        },
        'plotOptions': {
            'column': {
            'pointPadding': 0.2,
            'borderWidth': 0
            }
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data


def chart_fig4(rows):

    for r in rows:
        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year

    df_rows = pd.DataFrame(data=rows)
    if len(df_rows):
        df_rows.set_index('id')

    pivoted = df_rows.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')

    # 整理相機位置
    df_deployments = df_rows[['deployment_id', 'deployment__name', 'studyarea__name']].drop_duplicates()
    df_deployments.index = df_deployments['deployment_id']

    years = df_rows['year'].drop_duplicates().values
    years = sorted(years)
    series = []

    by_year = {
        'main': {
            'name': f'',
            'data': [],
        },
        'errorbar': {
            'name': f'',
            'data': [],
            'type': 'errorbar',
        },
    }
    for y in years:
        oi3_mean = 0
        oi3_sem = 0
        if not pivoted.stack()[y].empty:
            oi3_mean = pd.to_numeric(pivoted.stack()[y], errors='coerce').mean()
            if pd.isna(oi3_mean):
                oi3_mean = 0

            oi3_sem = pd.to_numeric(pivoted.stack()[y], errors='coerce').sem()
            if pd.isna(oi3_sem):
                oi3_sem = 0

        by_year['main']['data'].append(oi3_mean)
        by_year['errorbar']['data'].append([oi3_mean - oi3_sem,oi3_mean + oi3_sem])

    series.append(by_year['main'])
    series.append(by_year['errorbar'])

    chart_data = {
        'yAxis': {
            'title': {
                'text': 'OI_3',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': f'Range: {years[0]} to {years[-1]}'
            },
            'categories': [int(y) for y in years]
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': int(years[0]),
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data


def chart_fig3(rows):
    df_rows = pd.DataFrame(data=rows)
    if len(df_rows):
        df_rows.set_index('id')

    months = [m for m in range(1, 13)]
    data = {m: [] for m in months}
    for i in df_rows.itertuples():
        if m := timezone_utc_to_tw(i.datetime_from):
            if i.data__5 != 'N/A':
                data[m.month].append(i.data__5)

    series = []
    by_month = {
        'main': {
            'name': f'',
            'data': [],
        },
        'errorbar': {
            'name': f'',
            'data': [],
            'type': 'errorbar',
        },
    }

    for m in months:
        oi3_mean = 0
        oi3_sem = 0

        if len(data[m]):
            oi3_mean = statistics.mean(data[m])
            oi3_sem = np.std(data[m], ddof=1) / np.sqrt(np.size(data[m]))
            if pd.isna(oi3_sem):
                oi3_sem = 0
        by_month['main']['data'].append(oi3_mean)
        by_month['errorbar']['data'].append([oi3_mean - oi3_sem,oi3_mean + oi3_sem])

    series.append(by_month['main'])
    series.append(by_month['errorbar'])

    chart_data = {
        'yAxis': {
            'title': {
                'text': 'OI_3',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': 'Range: 1 to 12'
            },
            'text': '月份',
            'categories': [int(m) for m in months],
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': 1,
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data


def chart_fig2(rows):
    altitude_limiter = [0, 1000, 2000]
    exist_deployment_map = {}
    data = []

    def find_alt_type(alt):
        if alt:
            alt = int(alt)
            if alt >= altitude_limiter[0] and alt < altitude_limiter[1]:
                return 'L'
            elif alt >= altitude_limiter[1] and alt <= altitude_limiter[2]:
                return 'M'
            elif alt > altitude_limiter[2]:
                return 'H'

        return ''

    for r in rows:
        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year
        if alt_type := exist_deployment_map.get(r['deployment_id']):
            r['alt_type'] = alt_type
        else:
            alt = r['deployment__altitude']
            r['alt_type'] = find_alt_type(alt)
            exist_deployment_map[r['deployment_id']] = r['alt_type']

    df_rows = pd.DataFrame(data=rows)
    if len(df_rows):
        df_rows.set_index('id')

    pivoted = df_rows.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')

    # 整理相機位置
    df_deployments = df_rows[['deployment_id', 'deployment__name', 'studyarea__name', 'deployment__altitude', 'alt_type']].drop_duplicates()
    df_deployments.index = df_deployments['deployment_id']

    years = df_rows['year'].drop_duplicates().values
    years = sorted(years)
    series = []

    alt_type_label = {
        'L': '低海拔',
        'M': '中海拔',
        'H': '高海拔',
    }
    for alt_type in ['L', 'M', 'H']:
        dep_ids = df_deployments[df_deployments['alt_type'] == alt_type]['deployment_id'].values
        by_alt = {
            'main': {
                'name': alt_type_label[alt_type],
                'data': [],
            },
            'errorbar': {
                'name': f'{alt_type_label[alt_type]} 標準誤',
                'data': [],
                'type': 'errorbar',
            },
        }
        for y in years:
            #print(y, dep_ids)
            oi3_mean = 0
            oi3_sem = 0
            if not pivoted[pivoted.index.isin(dep_ids)].stack()[y].empty:
                oi3_mean = pd.to_numeric(pivoted[pivoted.index.isin(dep_ids)].stack()[y], errors='coerce').mean()
                if pd.isna(oi3_mean):
                    oi3_mean = 0
                oi3_sem = pd.to_numeric(pivoted[pivoted.index.isin(dep_ids)].stack()[y], errors='coerce').sem()
                if pd.isna(oi3_sem):
                    oi3_sem = 0

            by_alt['main']['data'].append(oi3_mean)
            by_alt['errorbar']['data'].append([oi3_mean - oi3_sem,oi3_mean + oi3_sem])

        series.append(by_alt['main'])
        series.append(by_alt['errorbar'])

    chart_data = {
        'yAxis': {
            'title': {
                'text': '歷年曾拍到的該物種樣點之平均 OI_3',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': f'Range: {years[0]} to {years[-1]}'
            },
            'categories': [int(y) for y in years]
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle'
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': int(years[0]),
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    return chart_data

def chart_fig1(rows):
    # 年月欄位
    #year_month_range = find_year_month_range([r['datetime_from'] for r in rows])
    exist_deployment_area = {}
    data = []

    for r in rows:
        if not check_sanity(r):
            continue

        dt = timezone_utc_to_tw(r['datetime_from'])
        r['yearmonth'] = f'ym:{dt.year}.{dt.month}'
        r['year'] = dt.year
        r['taiwan_area'] = ''
        if area := exist_deployment_area.get(r['deployment_id']):
            r['taiwan_area'] = area
        else:
            if county := find_named_area(r['deployment__longitude'], r['deployment__latitude'], r['deployment__geodetic_datum']):
                if county:
                    area = find_taiwan_area(county)
                    exist_deployment_area[r['deployment_id']] = area
                    r['taiwan_area'] = area

        data.append(r)
    df_rows = pd.DataFrame(data=data)
    if len(df_rows):
        df_rows.set_index('id')

    pivoted = df_rows.pivot(index='deployment_id', columns=['year', 'yearmonth'], values='data__5')
    #print(pivoted)

    # 整理相機位置
    df_deployments = df_rows[['deployment_id', 'deployment__name', 'studyarea__name', 'taiwan_area']].drop_duplicates()
    df_deployments.index = df_deployments['deployment_id']
    # 算月平均, pivoted 不要用multi-index
    #df_data = pivoted.join(df_deployments, on='deployment_id')

    # re-order columns
    #ym_columns = [f'ym:{x[0]}.{x[1]}' for x in year_month_range]
    #df_data = df_data[['deployment_id', 'studyarea__name', 'deployment__name', 'taiwan_area']+ ym_columns]

    # 各區月平均OI
    #for i in ym_columns:
    #    print(df_data.groupby(['taiwan_area'])[[i]].mean())

    # 各區年平均OI, sem
    years = df_rows['year'].drop_duplicates().values
    years = sorted(years)
    series = []
    errorbar = []
    area_map = {
        'N': '北部',
        'S': '南部',
        'C': '中部',
        'E': '東部',
    }
    for area_key in ['N', 'C', 'S', 'E']:
        dep_ids = df_deployments[df_deployments['taiwan_area'] == area_key]['deployment_id'].values
        by_area = {
            'main': {
                'name': f'{area_map[area_key]}',
                'data': [],
            },
            'errorbar': {
                'name': f'{area_map[area_key]} 標準誤',
                'data': [],
                'type': 'errorbar',
            },
        }
        for y in years:
            oi3_mean = 0
            oi3_sem = 0
            if not pivoted[pivoted.index.isin(dep_ids)].stack()[y].empty:
                oi3_mean = pd.to_numeric(pivoted[pivoted.index.isin(dep_ids)].stack()[y], errors='coerce').mean()
                if pd.isna(oi3_mean):
                    oi3_mean = 0

                oi3_sem = pd.to_numeric(pivoted[pivoted.index.isin(dep_ids)].stack()[y], errors='coerce').sem()
                if pd.isna(oi3_sem):
                    oi3_sem = 0

            by_area['main']['data'].append(oi3_mean)
            by_area['errorbar']['data'].append([oi3_mean - oi3_sem,oi3_mean + oi3_sem])


        series.append(by_area['main'])
        series.append(by_area['errorbar'])

    chart_data = {
        'yAxis': {
            'title': {
                'text': '年平均OI3',
            }
        },
        'xAxis': {
            'accessibility': {
                'rangeDescription': f'Range: {years[0]} to {years[-1]}'
            },
            'categories': [int(y) for y in years]
        },
        'legend': {
            'layout': 'vertical',
            'align': 'right',
            'verticalAlign': 'middle'
        },
        'plotOptions': {
            'series': {
                'label': {
                    'connectorAllowed': False,
                },
                'pointStart': int(years[0]),
            },
        },
        'series': series,
        'responsive': get_default_chart_data('responsive'),
    }
    #print(chart_data)
    return chart_data
