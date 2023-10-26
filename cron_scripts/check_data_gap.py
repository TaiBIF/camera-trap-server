import datetime

from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count

from taicat.utils import half_year_ago, get_project_member
from taicat.models import (
    DeploymentJournal,
    Contact,
    Project,
)
from base.models import (
    UploadNotification,
)


now = datetime.datetime.now()

# test
#range_list = half_year_ago(2022, 8)
range_list = half_year_ago(now.year, now.month)

rows = DeploymentJournal.objects.values_list('project_id').annotate(total=Count('id')).filter(working_end__gt=range_list[0]).all()

# rows = [[141]]

for i in rows:
    project_id = i[0]
    proj = Project.objects.get(pk=project_id)
    results = proj.count_deployment_journal([range_list[1].year-1, range_list[1].year])
    output = {'count': 0, 'studyareas': {}}
    for year, data in results.items():
        for sa in data:
            for dep in sa['items']:
                for gap in dep['gaps']:
                    gap_start = datetime.datetime.fromtimestamp(gap['range'][0])
                    gap_end = datetime.datetime.fromtimestamp(gap['range'][1])
                    gap_end_condition = gap_end
                    # 一年的最後一天，拉成明年第一天，把前年 gap_end 是 12/31 有空缺的也拉出來
                    if gap_end.month == 12 and gap_end.day == 31:
                        gap_end_condition = datetime.datetime.strptime('{}-01-01'.format(gap_end.year+1), '%Y-%m-%d')
                    #print(range_list, gap_start, gap_end)
                    if gap_end_condition >= range_list[0] and gap_start <= range_list[1]:
                        if sa['name'] not in output['studyareas']:
                            output['studyareas'][sa['name']] = {}

                        if dep['id'] not in output['studyareas'][sa['name']]:
                            output['studyareas'][sa['name']][dep['id']] = {
                               'items': [],
                               'name': dep['name'],
                            }
                            output['count'] += 1

                        gap_title = '* {}/{}\n'.format(gap_start.strftime('%Y-%m-%d'), gap_end.strftime('%Y-%m-%d'))
                        # print(year, dep['name'], gap_title)
                        output['studyareas'][sa['name']][dep['id']]['items'].append(gap_title)

    #print(output)

    email_subject = '[臺灣自動相機資訊系統] | {} | 資料缺失: 尚未填寫列表 | 篩選範圍：{}/{}'.format(proj.name, range_list[0].strftime('%Y-%m-%d'), range_list[1].strftime('%Y-%m-%d'))
    email_body = '資料缺失: 尚未填寫列表\n----------------------'
    if output['count'] > 0 :
        for sa_name in output['studyareas']:
            email_body += '\n\n# 樣區名稱: {}\n'.format(sa_name)
            for _, d in output['studyareas'][sa_name].items():
                email_body += '\n## 相機位置: {}\n'.format(d['name'])
                for x in d['items']:
                    email_body += x
    else:
        email_body += '\n目前無資料缺失。'

    project_members = get_project_member(project_id)
    email_list = [x.email for x in Contact.objects.filter(id__in=project_members)]

    # create notification
    for m in project_members:
        # print (m.id, m.name)
        un = UploadNotification(
            contact_id = m,
            category='gap',
            project_id = project_id
        )
        un.save()

    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, email_list)

    #print(email_subject)
    #print(email_body)

