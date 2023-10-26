import pytz
import json
from datetime import datetime
import csv
from pathlib import Path

from bson.objectid import ObjectId

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery import shared_task
from celery.utils.log import get_task_logger

from taicat.utils import (
    save_calculation,
    apply_search_filter,
)

logger = get_task_logger(__name__)

from taicat.models import (
    Image,
    Image_info,
    Deployment,
    DeploymentJournal,
    DownloadLog,
    ParameterCode,
    Contact,
)
from base.models import UploadHistory
from .utils import (
    set_image_annotation,
    calculated_data,
    calc_output_file,
)

@shared_task
def process_image_annotation_task(deployment_journal_id, data):
    # aware datetime object
    utc_tz = pytz.timezone(settings.TIME_ZONE)

    datetime_from = datetime.fromtimestamp(data['image_list'][0][3], utc_tz)
    datetime_to = datetime.fromtimestamp(data['image_list'][0][3], utc_tz)
    species_list = []
    is_save_calculation = False
    deployment_journal = DeploymentJournal.objects.get(pk=deployment_journal_id)
    deployment_journal.upload_status = 'start-annotation'
    next_status = 'start-media'

    # find if is specific_bucket
    bucket_name = data.get('bucket_name', '')
    specific_bucket = ''
    if bucket_name != settings.AWS_S3_BUCKET:
        specific_bucket = bucket_name

    folder_name = data.get('folder_name', '')

    for i in data['image_list']:
        #print(datetime_to, datetime_from, 'iiii')
        img_info_payload = None
        # prevent json load error
        exif_str = i[9].replace('\\u0000', '') if i[9] else '{}'
        exif = json.loads(exif_str)
        anno = json.loads(i[7]) if i[7] else '{}'
        if image_id := i[11]:
            next_status = 'finished' # re-upload

            try:
                img = Image.objects.get(pk=image_id)
            except Image.DoesNotExist:
                print ('Does Not Exist!')
                continue

            # only update annotation
            img.annotation = anno
            img.source_data.update({'id': i[0]})
            img.last_updated = datetime.now()

        else:
            is_save_calculation = True
            for a in anno:
                if sp := a.get('species', ''):
                    if sp not in species_list:
                        species_list.append(sp)

            dt_ = datetime.fromtimestamp(i[3], utc_tz)
            if dt_ < datetime_from:
                datetime_from = dt_
            elif dt_ > datetime_to:
                datetime_to = dt_

            image_uuid = str(ObjectId())
            img = Image(
                deployment_id=deployment_journal.deployment_id,
                source_data={'id': i[0]},
                filename=i[2],
                datetime=dt_,
                image_hash=i[6],
                annotation=anno,
                memo=data['key'],
                image_uuid=image_uuid,
                has_storage='N',
                folder_name=folder_name,
                deployment_journal_id=deployment_journal.id,
            )

            if specific_bucket != '':
                img.specific_bucket = specific_bucket

            img_info_payload = {
                'source_data': i,
                'exif': exif,
                'image_uuid': image_uuid
            }
            if pid := deployment_journal.project_id:
                img.project_id = pid
            if said := deployment_journal.studyarea_id:
                img.studyarea_id = said

            # seperate image_info
            img_info = Image_info(
                image_uuid=img_info_payload['image_uuid'],
                source_data=img_info_payload['source_data'],
                exif=img_info_payload['exif'],
            )
            img_info.save()


        img.save()
        #image_map[i[0]] = [img.id, img.image_uuid]
        set_image_annotation(img)

    # done
    deployment_journal.upload_status = next_status
    deployment_journal.save()

    #print(datetime_from, datetime_to, 'xxxx')
    #save_calculation(species_list, datetime_from, datetime_to, deployment_journal.deployment)
    if is_save_calculation:
        months = (datetime_to.year - datetime_from.year) * 12 + (datetime_to.month - datetime_from.month)
        yx = datetime_from.year
        mx = datetime_from.month
        #print(months, yx, mx)
        for m in range(0, months+1):
            #print(species_list, yx, mx, deployment_journal.deployment, m)
            dt = datetime(yx, mx, 1)
            save_calculation(species_list, yx, mx, deployment_journal.deployment)
            mx += 1
            if mx > 12:
                yx += 1
                mx = 1


@shared_task
def process_download_data_task(email, filter_dict, member_id, host, verbose):
    download_dir = Path(settings.MEDIA_ROOT, 'download')
    filename = f'download_{str(ObjectId())}_{datetime.now().strftime("%Y-%m-%d")}.csv'
    query = apply_search_filter(filter_dict)
    query = query.values_list('project_id', 'project__name', 'image_uuid', 'studyarea__name', 'deployment__name', 'filename', 'datetime', 'species', 'life_stage', 'sex', 'antler', 'animal_id', 'remarks')
    header = ['計畫ID', '計畫名稱', '影像ID', '樣區/子樣區', '相機位置', '檔名', '拍攝時間', '物種', '年齡', '性別', '角況', '個體ID', '備註']
    with open(Path(download_dir, filename), 'w') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(header)
        for row in query.all():
            ''' much slower
        for i in query.all():
            row = [
                i.project_id,
                i.project.name,
                i.image_uuid,
                i.studyarea.name,
                i.deployment.name,
                i.filename,
                i.datetime.strftime('%Y-%m-%d %H:%M:%S') if i.datetime else '',
                i.species,
                i.life_stage,
                i.sex,
                i.antler,
                i.animal_id,
                i.remarks
            ]
            row = i
            '''
            spamwriter.writerow(row)

    download_url = "https://{}{}{}".format(
        host,
        settings.MEDIA_URL,
        Path('download', filename))

    user_role = ''
    if contact := Contact.objects.get(id=member_id):
        if role := ParameterCode.objects.filter(parametername=contact.identity).first():
            user_role = role.name

    #condition_log = f'''專案名稱:{project_name}, 日期：{date_filter}。樣區 / 相機位置：{conditions} 。物種：{spe_conditions} 。時間：{time_filter}。縣市：{county_filter}。保護留區：{protectarea_filter}。資料夾：{folder_filter} 。'''

    download_log_sql = DownloadLog(
        user_role=user_role,
        condition=verbose,
        file_link=download_url)
    download_log_sql.save()

    email_subject = '[臺灣自動相機資訊系統] 下載資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])


@shared_task
def process_download_calculated_data_task(email, filter_dict, calc_dict, calc_type, out_format, calc_data, host, member_id, verbose, available_project_ids):
    results = calculated_data(filter_dict, calc_dict, available_project_ids)

    download_dir = Path(settings.MEDIA_ROOT, 'download')
    ext = 'csv' if out_format == 'csv' else 'xlsx'
    filename = f'download_calculated_{str(ObjectId())}_{datetime.now().strftime("%Y-%m-%d")}.{ext}'
    target_file = Path(download_dir, filename)
    content = calc_output_file(results, out_format, json.dumps(filter_dict), json.dumps(calc_dict), target_file)

    #with open(Path(download_dir, filename), 'wb') as outfile:
    #    outfile.write(content)
    #print('===============')

    download_url = "https://{}{}{}".format(
        host,
        settings.MEDIA_URL,
        Path('download', filename))

    user_role = ''
    if contact := Contact.objects.get(id=member_id):
        if role := ParameterCode.objects.filter(parametername=contact.identity).first():
            user_role = role.name
    download_log_sql = DownloadLog(
        user_role=user_role,
        condition=verbose,
        file_link=download_url)
    download_log_sql.save()

    email_subject = '[臺灣自動相機資訊系統] 下載計算資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    # print('email', email_subject, email_body, email, download_url)
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])
