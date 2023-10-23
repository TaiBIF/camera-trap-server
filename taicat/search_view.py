import json
import math
import time
from datetime import datetime
import re
import operator
from functools import reduce

from django.shortcuts import render, redirect
from django.http import (
    JsonResponse,
    FileResponse,
    HttpResponse,
)
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import make_aware
from django.db import connection
from django.conf import settings
from django.db.models import (
    OuterRef,
    Subquery,
    Q,
)

from taicat.models import (
    Image,
    Project,
    Deployment,
    StudyArea,
    Species,
    ParameterCode,
    Calculation,
)
from .utils import (
    get_species_list,
    calc,
    calc_output_file,
    calc_output2,
    calc_from_cache,
    calculated_data,
    get_my_project_list,
    apply_search_filter,
    humen_readable_filter,
)
from .utils_calc import (
    calc_chart,
)
# from .views import (
#     check_if_authorized,
#     check_if_authorized_create,
# )

from taicat.tasks import (
    process_download_data_task,
    process_download_calculated_data_task,
)

def index(request):
    context = {
        'env': settings.ENV,
        #'JS_BUNDLE_VERSION': settings.JS_BUNDLE_VERSION
    }
    return render(request, 'search/search_index.html', context)

def api_named_areas(request):
    data = {
        'county': [],
        'protectedarea': [],
    }

    county_list = ParameterCode.objects.filter(type='county').all()
    protectedarea_list = ParameterCode.objects.filter(type='protectedarea').all()
    for i in county_list:
        data['county'].append({
            'id': i.id,
            'parametername': i.parametername,
            'name': i.name,
        })
    for i in protectedarea_list:
        data['protectedarea'].append({
            'id': i.id,
            'parametername': i.parametername,
            'name': i.name,
            'category': i.pmajor,
        })
    return JsonResponse({
        'category': 'named_areas',
        'data': data
    })


def api_get_species(request):
    species_list = [x.to_dict() for x in Species.objects.filter(is_default=True).all()]
    return JsonResponse({
        'category': 'species',
        'data': species_list,
        'total': len(species_list)
    })

def api_get_projects(request):
    public_projects = []
    my_projects = []

    # code from views.project_overview
    # is_authorized_create = check_if_authorized(request)
    # public_species_data = []
    # 公開計畫 depend on publish_date date
    with connection.cursor() as cursor:
        # q = "SELECT taicat_project.id FROM taicat_project \
        #     WHERE taicat_project.mode = 'official' AND (CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval);"
        q = "SELECT taicat_project.id FROM taicat_project \
             WHERE taicat_project.mode = 'official' AND taicat_project.is_public = 't';"
        cursor.execute(q)
        public_project_list = [l[0] for l in cursor.fetchall()]


    if public_project_list:
        #public_project, public_species_data = get_project_info(public_project_list)
        for p in Project.objects.filter(id__in=public_project_list).all():
            x = p.to_dict()
            x['group_by'] = '公開計畫'
            public_projects.append(x)

    # ---------------我的計畫
    # my project
    # my_project = []
    # my_species_data = []
    if member_id := request.session.get('id', None):
        if my_project_list := get_my_project_list(member_id,[]):
            # my_project, my_species_data = get_project_info(my_project_list)
            for p in Project.objects.filter(id__in=my_project_list).all():
                x = p.to_dict()
                x['group_by'] = '我的計畫'
                my_projects.append(x)

    projects = public_projects + my_projects
    return JsonResponse({
        'category': 'projects',
        'data': projects,
        'total': len(projects)
    })

def api_deployments(request):
    query = StudyArea.objects.filter()
    resp = {
        'data': [],
    }
    if project_id := request.GET.get('project_id'):
        proj = Project.objects.get(id=project_id)
        project_deployment_list = proj.get_deployment_list()
        query = query.filter(project_id=project_id)
        resp['data'] = project_deployment_list
    return JsonResponse(resp)

def api_search(request):
    rows = []
    #request.is_ajax() and
    if request.method == 'GET':
        start_time = time.time()
        start = 0
        end = 20
        query_start = datetime(2014, 1, 1)
        query_end = datetime.now()
        query = Image.objects.filter()

        # project auth
        available_project_ids = Project.objects.filter(mode='official', is_public=True).values_list('id', flat=True)
        available_project_ids = list(available_project_ids)

        if member_id := request.session.get('id', None):
            if my_project_list := get_my_project_list(member_id,[]):
                available_project_ids.extend(my_project_list)

        if request.GET.get('filter'):
            filter_dict = json.loads(request.GET['filter'])
            query = apply_search_filter(filter_dict)
        query = query.filter(project_id__in=available_project_ids)

        if request.GET.get('pagination'):
            pagination = json.loads(request.GET['pagination'])
            start = pagination['pageIndex'] * pagination['perPage']
            end = start + pagination['perPage']

        download = request.GET.get('download', '')
        calc_data = request.GET.get('calc', '')
        downloadData = request.GET.get('downloadData', '')
        calc_dict = {}
        if calc_data:
            calc_dict = json.loads(calc_data)

        if calc_dict.get('calcType') == 'chart' and calc_dict.get('chartType'):
            results = calc_chart(
                calc_dict,
                filter_dict.get('species'),
                filter_dict.get('projects'),
            )
            return JsonResponse(results)

        if download and calc_data:
            calc_dict = json.loads(request.GET['calc'])
            out_format = calc_dict['fileFormat']
            calc_type = calc_dict['calcType']

            # direct download
            '''
            # results = calc(query, calc_data, query_start, query_end)
            results = calculated_data(filter_dict, calc_data)
            # print(results, out_format, calc_type)
            #results = calc_from_cache(filter_dict, calc_dict)
            #content = calc_output2(results, out_format, request.GET.get('filter'), request.GET.get('calc'))
            content = calc_output(results, out_format, request.GET.get('filter'), request.GET.get('calc'))

            response = HttpResponse(content)
            response['Content-Type'] = 'text/plain'
            response['Content-Disposition'] = 'attachment; filename=camera-trap-calculation-{}.{}'.format(
                calc_type,
                'csv' if out_format == 'csv' else 'xlsx')

            return response
            '''
            email = request.GET.get('email', '')
            message = 'processing'

            ''' save to media
            results = calculated_data(filter_dict, calc_data)
            from pathlib import Path
            content = calc_output(results, out_format, json.dumps(filter_dict), json.dumps(calc_data))
            download_dir = Path(settings.MEDIA_ROOT, 'download')

            with open(Path(download_dir, 'foo.xlsx'), 'wb') as outfile:
                outfile.write(content)
                #print('===============')
            '''
            if member_id := request.session.get('id', None):
                host = request.META['HTTP_HOST']
                verbose_log = humen_readable_filter(filter_dict)
                process_download_calculated_data_task.delay(email, filter_dict, calc_dict, calc_type, out_format, calc_data, host, member_id, verbose_log, available_project_ids)
                #results = calculated_data(filter_dict, calc_data, available_project_ids)
                #print(results)
            else:
                message = 'no member_id'

            return JsonResponse({
                'message': message
            })
        elif downloadData:
            email = request.GET.get('email', '')
            message = 'processing'
            if member_id := request.session.get('id', None):
                host = request.META['HTTP_HOST']

                verbose_log = humen_readable_filter(filter_dict)
                process_download_data_task.delay(email, filter_dict, member_id, host, verbose_log)
            else:
                message = 'no member_id'

            return JsonResponse({
                'message': message
            })
        else:
            total = query.values('id').order_by('id').count()
            rows = query.all()[start:end]
            #print(query.query, start, end)
            end_time = time.time() - start_time
            return JsonResponse({
                'data': [x.to_dict() for x in rows],
                'total': total,
                'query': str(query.query) if query and query.query else '',
                'elapsed': end_time,
            })
