import json
from datetime import datetime
from django.utils.timezone import make_aware

from taicat.models import DeploymentJournal, StudyArea, Project, Deployment

# FIXED DATA
project_id = 287
sa_map = {
    '羅東處': 1729,
    '新竹處': 1730,
    '東勢處': 1731,
    '南投處': 1732,
    '嘉義處': 1733,
    '屏東處': 1734,
    '台東處': 1735,
    '花蓮處': 1736,
}

fin = open('deployment_journals.json')
data = fin.read()
res = json.loads(data)
#total = 0
for sa, info in res.items():
    print (sa, info['total'])
    #total += items['total']
    sa_id = sa_map[sa]
    for i in info['deployments']:
        #print (i)
        dep = Deployment.objects.filter(project_id=project_id, study_area_id=sa_id, name=i).first()
        if dep:
            range_list = info['deployments'][i]['ranges']
            for j in range_list:
                dj = DeploymentJournal(
                    project_id=project_id,
                    studyarea_id=sa_id,
                    deployment_id=dep.id)
                try:
                    native_datetime1 = datetime(int(j[0][0:4]), int(j[0][4:6]), int(j[0][6:8]))
                    aware_datetime1 = make_aware(native_datetime1)
                    native_datetime2 = datetime(int(j[1][0:4]), int(j[1][4:6]), int(j[1][6:8]))
                    aware_datetime2 = make_aware(native_datetime2)
                    #print (project_id, sa_id, dep.id, j, aware_datetime)
                    dj.working_start = aware_datetime1
                    dj.working_end = aware_datetime2

                    if aware_datetime1 > aware_datetime2:
                        dj.is_effective = False
                except:
                    dj.working_unformat = '{}-{}'.format(j[0], j[1])
                    dj.is_effective = False

                dj.save()

        else:
            print ('not found', i)


#print(total)
