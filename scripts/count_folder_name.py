from taicat.models import Image, ImageFolder, Project
from django.utils import timezone
from django.db.models import Max

project_id = Project.objects.all().values('id')

for p in project_id:
    print(p['id'])
    now = timezone.now()
    folder_name = Image.objects.exclude(folder_name='').filter(project_id=p['id']).order_by('folder_name').distinct('folder_name').values('folder_name')
    for f in folder_name:
        name = f['folder_name']
        print(name)
        # get last_updated
        last_updated = Image.objects.filter(project_id=p['id'], folder_name=name).aggregate(Max('last_updated'))['last_updated__max']
        new = ImageFolder(
            project_id=p['id'],
            folder_name=name,
            folder_last_updated=last_updated
        )
        new.save()
