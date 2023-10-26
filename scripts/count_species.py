from django.utils import timezone
from django.db.models import Count
from taicat.models import Species, Image
from taicat.utils import get_species_list

ret = get_species_list(True)
now = timezone.now()
for i in ret['all']:
    if sp := Species.objects.filter(name=i[0]).first():
        sp.count = i[1]
        sp.last_updated = now
        sp.save()
    else:
        sp = Species(name=i[0], last_updated=now, count=i[1])
        if i[0] in Species.DEFAULT_LIST:
            sp.is_default = True
        sp.save()


# 2022 version
now = timezone.now()

query = Image.objects.all().values('species').annotate(total=Count('species')).order_by('-total')

for i in query:
    print(i['species'])
    if sp := Species.objects.filter(name=i['species']).first():
        sp.count = i['total']
        sp.last_updated = now
        sp.save()
    else:
        sp = Species(name=i['species'], last_updated=now, count=i['total'])
        if i['species'] in Species.DEFAULT_LIST:
            sp.is_default = True
        sp.save()
