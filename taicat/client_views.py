import json
from datetime import datetime
import pytz
import zipfile
import io
import re

from django.shortcuts import render
from django.http import (
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404
from django.conf import settings

import requests
from bson.objectid import ObjectId

from taicat.models import (
    Image,
    Project,
    Deployment,
    DeploymentJournal,
    Image_info,
    Contact,
    InfoLog,
    ProjectMember,
    StudyArea
)
from base.models import (
    Announcement,
    UploadHistory,
)
from .utils import (
    set_image_annotation,
    set_deployment_journal,
    get_my_project_list,
    check_image_storage,
)
from taicat.tasks import process_image_annotation_task

def index(request):
    project_list = Project.objects.filter(mode='test').all()
    return render(request, 'index.html', {'project_list': project_list})

# def project_detail(request, pk):
#     dep_id = request.GETu.get('deployment', '')

#     project = Project.objects.get(pk=pk)
#     d = project.get_deployment_list()
#     #id_list = []
#     #for i in d:
#     #    for j in i['deployments']:
#     #        id_list.append(j['deployment_id'])

#     image_list = []
#     if dep_id:
#         image_list = Image.objects.filter(deployment_id=dep_id).all()

#     return render(request, 'project_detail.html',{
#         'project':project,
#         'deployment': d,
#         'image_list': image_list,
#     })

def get_user_info(request, user_id):
    try:
        user = Contact.objects.get(pk=user_id)
    except Contact.DoesNotExist:
        raise Http404

    plist = get_my_project_list(user_id)
    projects = Project.objects.filter(id__in=plist).all()
    ret = {
        'results': {
            'projects': [],
            'user': {
                'name': user.name,
                'id': user.id,
                'email': user.email,
            },
        }
    }
    for p in projects:
        is_contractor = ProjectMember.objects.filter(project_id=p.id, member_id=user_id, role='contractor').exists()
        contractor_sa = StudyArea.objects.filter(projectmember__project_id=p.id, projectmember__member_id=user_id, projectmember__role='contractor')
        contractor_sa_list = [int(s.id) for s in contractor_sa]
        if is_contractor:
            item = {
                'project_id': p.id,
                'name': p.name,
                'studyareas': p.get_deployment_list(False, contractor_sa_list),
            }
        else:
            item = {
                'project_id': p.id,
                'name': p.name,
                'studyareas': p.get_deployment_list(),
            }
        ret['results']['projects'].append(item)

    return JsonResponse(ret)

def get_project_list(request):
    projects = Project.objects.all()
    ret = {
        'results': [{
            'project_id': x.id,
            'name': x.name,
        } for x in projects]
    }
    return JsonResponse(ret)

def get_project(request, project_id):
    proj = get_object_or_404(Project, pk=project_id)
    data = {
        'project_id': proj.id,
        'name': proj.name,
        'studyareas': proj.get_deployment_list()
    }
    #return HttpResponse(data, content_type="application/json")
    return JsonResponse(data)

@csrf_exempt
def post_image_annotation(request):
    ret = {}
    if request.method == 'POST':
        data = json.loads(request.body)

        deployment = Deployment.objects.get(pk=data['deployment_id'])
        if deployment:
            res = {}
            # aware datetime object
            utc_tz = pytz.timezone(settings.TIME_ZONE)

            # find if is specific_bucket
            bucket_name = data.get('bucket_name', '')
            specific_bucket = ''
            if bucket_name != settings.AWS_S3_BUCKET:
                specific_bucket = bucket_name

            folder_name = ''


            folder_name = data['folder_name']

            # create or update DeploymentJournal
            deployment_journal = set_deployment_journal(data, deployment)
            deployment_journal_id = deployment_journal.id


            for i in data['image_list']:
                img_info_payload = None
                # prevent json load error
                exif_str = i[9].replace('\\u0000', '') if i[9] else '{}'
                exif = json.loads(exif_str)
                anno = json.loads(i[7]) if i[7] else '{}'
                if i[11]:
                    is_new_image = False
                    img = Image.objects.get(pk=i[11])
                    # only update annotation
                    img.annotation = anno
                    img.last_updated = datetime.now()
                else:
                    image_uuid = str(ObjectId())
                    img = Image(
                        deployment_id=deployment.id,
                        filename=i[2],
                        datetime=datetime.fromtimestamp(i[3], utc_tz),
                        image_hash=i[6],
                        annotation=anno,
                        memo=data['key'],
                        image_uuid=image_uuid,
                        has_storage='N',
                        folder_name=folder_name,
                    )

                    if deployment_journal_id != '':
                        img.deployment_journal_id = deployment_journal_id
                    if specific_bucket != '':
                        img.specific_bucket = specific_bucket

                    img_info_payload = {
                        'source_data': i,
                        'exif': exif,
                        'image_uuid': image_uuid
                    }
                    if pid := deployment.project_id:
                        img.project_id = pid
                    if said := deployment.study_area_id:
                        img.studyarea_id = said

                img.save()
                res[i[0]] = [img.id, img.image_uuid]

                set_image_annotation(img)

                if img_info_payload != None:
                    # seperate image_info
                    img_info = Image_info(
                        image_uuid=img_info_payload['image_uuid'],
                        source_data=img_info_payload['source_data'],
                        exif=img_info_payload['exif'],
                    )
                    img_info.save()

            ret['saved_image_ids'] = res
            ret['deployment_journal_id'] = deployment_journal_id
        else:
            ret['error'] = 'ct-server: no deployment key'

    return JsonResponse(ret)

@csrf_exempt
def sync_upload(request, pk):
    response = {}
    '''
    querystring:
    - has_storage # return has_storage data
    - check_storage
    actions:
    - A: check storage status
    - set UploadHistory status to 'finished'
    '''
    actions = request.GET.get('actions', '')
    dry_run = request.GET.get('dry-run', '')

    #action_map = a
    if dj := DeploymentJournal.objects.get(pk=pk):
        images = Image.objects.values('id', 'image_uuid', 'has_storage').filter(deployment_journal_id=dj.id).all()

        #data = {
        #    'deployment_journal_id': dj.id,
        #    'not_uploaded_server_id': [x['id'] for x in images if x['has_storage'] == 'N'],
        #}
        #if 'A' in actions:
        #  TODO wait too long
        #    check_and_update_fimage_storage(not_uploaded)
        # if 'B' in actions:
        # NOT tested yet
        #     if len(not_uploaded) == 0:
        #         if uh := UploadHistory.objects.filter(deployment_journal=dj.id).exclude(status='finished').first():
        #             uh.status = UploadHistory.STATUS_CHOICES[0][1]
        #             if 'log' not in uh.data:
        #                 uh.data['log'] = []

        #             uh.data['log'].append({
        #                 'datetime': str(datetime.now()),
        #                 'action': 'sync-update-status',
        #             })
        #             uh.save()
        res= []
        stats = {
            'Y': 0,
            'N': 0,
            'N-y': 0,
        }
        images_to_y = []
        is_server_updated = False
        for x in images:
            res.append([x['id'], x['has_storage']])
            if x['has_storage'] == 'Y':
                stats['Y'] += 1
            elif x['has_storage'] == 'N':
                stats['N'] += 1
                if real_storage := check_image_storage(x):
                    #print(real_storage, x['id'])
                    if real_storage:
                        stats['N-y'] += 1
                        images_to_y.append(x['id'])

        if not dry_run:
            if uh := UploadHistory.objects.filter(deployment_journal=dj.id).first():
                if stats['N-y'] == stats['N']:
                    uh.set_upload_ok(True)
                    is_server_updated = True
                else:
                    uh.set_upload_ok(False)

            for image_id in images_to_y:
                img = Image.objects.get(pk=image_id)
                img.has_storage = 'Y'
                img.save()

        dj_ah = dj.action_history
        action_data = {
            'stats': stats,
            'images_to_y': images_to_y,
            'is_server_updated': is_server_updated,
            'timestamp': str(datetime.now()),
        }
        dj_ah.append(action_data)
        dj.action_history = dj_ah
        dj.save()

        response = {
            'deployment_journal_id': dj.id,
            'images': res,
            'num_images': len(images),
            'stats': stats,
            'images_to_y': images_to_y,
            'is_server_updated': is_server_updated,
        }
    return JsonResponse(response)

@csrf_exempt
def check_deployment_journal_upload_status(request, pk):
    response = {}
    if dj := DeploymentJournal.objects.get(pk=pk):
        response.update({
            'deployment_journal_id': dj.id,
            'upload_status': dj.upload_status,
        })
        if dj.upload_status != 'start-image-annotation':
            rows = Image.objects.values('id', 'source_data', 'image_uuid').filter(deployment_journal_id=dj.id).all()
            img_ids = {}
            for i in rows:
                if id_ := i['source_data'].get('id', ''):
                    # cloned image has no source_data
                    img_ids[id_] = [i['id'], i['image_uuid']]
            response.update({
                'saved_image_ids': img_ids,
            })
    return JsonResponse(response)

@csrf_exempt
def post_image_annotation1_1(request):
    ret = {}
    if request.method == 'POST':
        data = {}

        # upload zipped file instead of json body
        memory_file = io.BytesIO(request.FILES['file'].read())
        with zipfile.ZipFile(memory_file, 'r') as zip_ref:
            txt = zip_ref.namelist()[0]
            with zip_ref.open(txt) as json_file:
                data = json.loads(json_file.read())
        #data = json.loads(request.body)

        #is_available = False
        #upload_key = data.get('key', '')
        #if upload_key:
        #    keys = upload_key.split('/')
        #    for available_version in settings.AVAILABLE_CLIENT_VERSIONS:
        #        if available_version in keys[2]:
        #            is_available = True

        #if is_available == False:
        #    ret['error'] = f'目前上傳界面版本已經淘汰: {keys[2]}，無法上傳，請更新至最新版本'
        #    ilog = InfoLog(name=upload_key, value=data['deployment_id'])
        #    ilog.save()
        #    return JsonResponse(ret)

        if deployment := Deployment.objects.get(pk=data['deployment_id']):
            # create or update DeploymentJournal
            deployment_journal = set_deployment_journal(data, deployment)
            if deployment_journal and data:
                process_image_annotation_task.delay(deployment_journal.id, data)
                #res.get()
                ret['deployment_journal_id'] = deployment_journal.id

                return JsonResponse(ret)

        else:
            ret['error'] = 'ct-server: arguments error (deployment_id)'

        return JsonResponse(ret)

@csrf_exempt
def update_image(request):
    res = {}
    if request.method == 'POST':
        data = json.loads(request.body)
        if pk := data['pk']:
            image = Image.objects.get(pk=pk)

            if image:
                # limited update field
                if has_storage := data.get('has_storage', ''):
                    image.has_storage = has_storage
                    image.save()

                # "複製一列" 的資料也要處理
                related_annotation_images = Image.objects.filter(filename=image.filename, deployment_journal_id=image.deployment_journal_id, annotation_seq__gt=0).all()
                for i in related_annotation_images:
                    if has_storage := data.get('has_storage', ''):
                        i.has_storage = has_storage
                        i.save()

        res = {
            'text': 'update-image'
        }
    return JsonResponse(res)


@csrf_exempt
def check_update(request, version=''):
    res = {
        'version': {
            'latest': '',
            'client': version,
        },
        'is_latest': False,
    }

    latest_version = Announcement.objects.order_by('-created').values_list('version', flat=True).first()
    latest_version = latest_version.replace('v', '')
    res['version']['latest'] = latest_version
    if m := re.match(r'([0-9]+\.[0-9]+\.[0-9]+)', version):
        version_number = m.group(1)
        if latest_version == version_number:
            res['is_latest'] = True

    return JsonResponse(res)

@csrf_exempt
def check_folder(request, name=''):
    res = {
        'is_exist': False,
    }
    if dj := DeploymentJournal.objects.filter(folder_name=name).first():
        res['is_exist'] = True
        res['deployment_journal'] = {
            'id': dj.id,
            'folder_name': dj.folder_name,
            'project_id': dj.project_id,
            'deployment_id': dj.deployment_id,
        }
    return JsonResponse(res)
