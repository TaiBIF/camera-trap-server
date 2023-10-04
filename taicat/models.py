from pathlib import Path
from datetime import (
    timedelta,
    datetime,
    date,
)
import time
from calendar import (
    monthrange,
    monthcalendar
)
import json

from django.db import models
from django.db import connection  # for executing raw SQL
from django.db.models import (
    Q,
    Max,
    Min,
    Count,
)
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.postgres.indexes import GinIndex
from django.conf import settings
from django.core.cache import cache, caches

# put this function in utils will cause circular import
def timezone_utc_to_tw(ts):
    '''apply +8 time delta
    '''
    if ts:
        return ts + timedelta(hours=8)
    return 0

def timezone_tw_to_utc(ts):
    if ts:
        return ts + timedelta(hours=-8)
    return 0

def find_the_gap(year, array):
    # print (year, array,'----')
    gap_list = []
    gap_list_date = []
    has_gap = False
    if array[0] == 0:
        gap_list.append([0, None])
        has_gap = True

    for i, v in enumerate(array[1:]):
        if has_gap and v == 1:
            gap_list[-1][1] = i
            has_gap = False
        elif not has_gap and v == 0:
            gap_list.append([i+1, None])
            has_gap = True

    if len(gap_list) and gap_list[-1][1] == None:
        gap_list[-1][1] = len(array) - 1

    for x in gap_list:
        gap_list_date.append([
            (datetime(year, 1, 1) + timedelta(days=x[0])).timestamp(),
            (datetime(year, 1, 1) + timedelta(days=x[1])).timestamp(),
        ])
    return gap_list_date


class Species(models.Model):
    DEFAULT_LIST = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                    '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']
    name = models.CharField(max_length=1000, db_index=True)
    count = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    # is_default = models.CharField(max_length=4, default='', null=True, blank=True, db_index=True)
    is_default = models.BooleanField(default=False, blank=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Contact(models.Model):
    name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000, blank=True, null=True)
    orcid = models.CharField(max_length=1000, blank=True, null=True, unique=True)
    organization = models.ForeignKey('Organization', on_delete=models.SET_NULL, null=True, blank=True)
    # is_login = models.BooleanField('登入狀態', default=True)
    is_organization_admin = models.BooleanField('是否為計畫總管理人', default=False)
    # is_forestry_bureau = models.BooleanField('是否能進入林務局管考系統', default=False)
    is_system_admin = models.BooleanField('是否為系統管理員', default=False)
    identity = models.CharField(max_length=1000, blank=True, null=True)
    desktop_login = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return '<Contact {}> {}'.format(self.id, self.name)



class Organization(models.Model):
    name = models.CharField(max_length=1000)
    projects = models.ManyToManyField('Project')

    def __str__(self):
        return '<Organization {}> {}'.format(self.id, self.name)


class PublishedProjectManager(models.Manager):
    def get_queryset(self):
        today = timezone.now().date()
        five_years_ago = today - timedelta(days=1825)
        # 5_years_ago = today - timedelta(days=1825) # 365*5
        return super(
            PublishedProjectManager, self).get_queryset().filter(
            Q(publish_date__lte=today) | Q(end_date__lte=five_years_ago))


class Project(models.Model):
    MODE_CHOICES = (
        ('test', '測試'),
        ('official', '正式'),
    )

    # Project Name
    name = models.CharField('計畫名稱', max_length=1000)

    # Project Objectives
    description = models.TextField('計畫摘要', default='', blank=True)
    short_title = models.CharField('計畫簡稱', max_length=1000, blank=True, null=True)
    keyword = models.CharField('計畫關鍵字', max_length=1000, blank=True, null=True)
    start_date = models.DateField('計畫時間-開始', null=True, blank=True)
    end_date = models.DateField('計畫時間-結束', null=True, blank=True)

    # Project People
    executive_unit = models.CharField('執行單位', max_length=100, blank=True, null=True)
    code = models.CharField('計畫編號', max_length=100, blank=True, null=True)
    principal_investigator = models.CharField('計畫主持人', max_length=1000, blank=True, null=True)
    funding_agency = models.CharField('委辦單位', max_length=100, blank=True, null=True)
    region = models.CharField('計畫地區', max_length=1000, null=True, blank=True)
    note = models.CharField('備註', max_length=1000, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)
    mode = models.CharField(max_length=8, blank=True, null=True, default='official', choices=MODE_CHOICES)
    #members = models.ManyToManyField('Contact', )

    # License
    is_public = models.BooleanField(default=False, blank=True)
    publish_date = models.DateField('公開日期', null=True, blank=True)
    interpretive_data_license = models.CharField('詮釋資料', max_length=10, blank=True, null=True)
    identification_information_license = models.CharField('鑑定資訊', max_length=10, blank=True, null=True)
    video_material_license = models.CharField('影像資料', max_length=10, blank=True, null=True)

    objects = models.Manager()
    published_objects = PublishedProjectManager()
    # OrganizationName

    def __str__(self):
        return '<Project {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def get_deployment_list(self, as_object=False, studyarea_ids=[]):
        res = []
        if len(studyarea_ids) > 0:
            sa = self.studyareas.filter(parent__isnull=True, id__in=studyarea_ids).all()
        else:
            sa = self.studyareas.filter(parent__isnull=True).all()

        for i in sa:
            children = []
            for j in StudyArea.objects.filter(parent_id=i.id).all():
                sa_deployments = []
                for x in j.deployment_set.exclude(deprecated=True).all():
                    item = {
                        'name': x.name,
                        'deployment_id': x.id
                    }
                    if as_object is True:
                        item['object'] = x
                    sa_deployments.append(item)

                children.append({
                    'studyarea_id': j.id,
                    'name': j.name,
                    'deployments': sa_deployments
                })

            deployments = []
            for x in i.deployment_set.exclude(deprecated=True).all():
                item = {
                    'name': x.name,
                    'deployment_id': x.id
                }
                if as_object is True:
                    item['object'] = x
                deployments.append(item)

            res.append({
                'studyarea_id': i.id,
                ''
                'name': i.name,
                'substudyarea': children,
                'deployments': deployments
            })
        return res

    def get_sa_list(self):
        res = []
        sa = self.studyareas.filter().all()
        for i in sa:
            # children = []
            if not i.parent_id:
                res.append({
                    'value': i.id,
                    'label': i.name,
                })
            else:
                parent_name = self.studyareas.get(id=i.parent_id).name
                res.append({
                    'value': i.id,
                    'label': f"{parent_name}_{i.name}",
                })
        return res

    def get_sa_d_list(self):
        res = {}
        sa = self.studyareas.all()
        for i in sa:
            if not i.parent_id:
                res.update({i.name: [{'label': x.name, 'value': x.id} for x in i.deployment_set.all()]})
            else:
                parent_name = self.studyareas.get(id=i.parent_id).name
                res.update({f"{parent_name}_{i.name}": [{'label': x.name, 'value': x.id} for x in i.deployment_set.all()]})
        return res

    def find_and_create_deployment_journal_gap(self, year_list=[]):
        results = []
        if len(year_list) == 0:
            mnx = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(Max('working_end'), Min('working_start'))
            end_year = mnx['working_end__max'].year
            start_year = mnx['working_start__min'].year
            year_list = list(range(start_year, end_year+1))

        for year in year_list:
            deps = self.get_deployment_list(as_object=True)
            for sa in deps:
                items_d = []
                for d in sa['deployments']:
                    dep_id = d['deployment_id']
                    year_stats = []
                    for m in range(1, 13):
                        ret = d['object'].count_working_day(year, m)
                        working_day = ret[0]
                        year_stats += working_day
                    gaps = find_the_gap(year, year_stats)
                    for gap_range in gaps:
                        dj = DeploymentJournal(
                            project_id=self.id,
                            deployment_id=dep_id,
                            studyarea_id=d['object'].study_area_id,
                            working_start=gap_range[0],
                            working_end=gap_range[1],
                            is_effective=False,
                            is_gap=True)
                        #dj.save()
                        results.append(dj)
        return results

    def count_deployment_journal(self, year_list=[], studyarea_ids=[]):
        years = {}
        if len(year_list) == 0:
            mnx = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(Max('working_end'), Min('working_start'))
            end_year = mnx['working_end__max'].year
            start_year = mnx['working_start__min'].year
            year_list = list(range(start_year, end_year+1))

        for year in year_list:
            year_idx = str(year)
            years[year_idx] = []
            deps = self.get_deployment_list(as_object=True, studyarea_ids=studyarea_ids)
            for sa_idx, sa in enumerate(deps):
                items_d = []
                for d_idx, d in enumerate(sa['deployments']):
                    dep_id = d['deployment_id']
                    month_list = []
                    ratio_year = 0
                    year_species_images = d['object'].count_species_images(year)
                    year_stats = []
                    for m in range(1, 13):
                        days_in_month = monthrange(year, m)[1]
                        ret = d['object'].count_working_day(year, m)
                        working_day = ret[0]
                        month_cal = monthcalendar(year, m)
                        count_working_day = sum(working_day)
                        num_images = [0, 0]
                        if yd := year_species_images['species'].get(str(year)):
                            if md := yd.get(str(m)):
                                num_images[0] = md
                        if yd := year_species_images['all'].get(str(year)):
                            if md := yd.get(str(m)):
                                num_images[1] = md
                        data = [
                            year,
                            m,
                            d['name'],
                            count_working_day,
                            days_in_month,
                            month_cal,
                            working_day,
                            ret[1],
                        ]
                        ratio = count_working_day * 100.0 / days_in_month
                        ratio_year += ratio
                        ratio_sp_img = num_images[0] * 100.0/ num_images[1] if num_images[1] > 0 else 0
                        year_stats += working_day
                        month_list.append([ratio, json.dumps(data),  [ratio_sp_img, num_images[0], num_images[1]]])
                    #gaps = find_the_gap(year, year_stats)
                    # move to find_and_create_deployment_journal_gap
                    # move to find_deployment_journal_gaps, lively not cached, 220606
                    #rows = d['object'].get_deployment_journal_gaps(year)
                    # gaps = [{
                    #     'id': x.id,
                    #     'idx': x_idx,
                    #     'caused': x.gap_caused if x.gap_caused else '',
                    #     'label': '{} - {}'.format(
                    #         x.working_start.strftime('%m/%d'),
                    #         x.working_end.strftime('%m/%d'))} for x_idx, x in enumerate(rows)]
                    gaps = d['object'].find_deployment_journal_gaps(year)
                    items_d.append({
                        'name': d['name'],
                        'id': dep_id,
                        'd_idx': d_idx,
                        'items': month_list,
                        'ratio_year': ratio_year / 12.0,
                        'gaps': gaps,
                    })
                years[year_idx].append({
                    'name': sa['name'],
                    'items': items_d,
                    'sa_idx': sa_idx,
                })

        return years

    def count_stats(self):
        start_count = time.time()
        result = Image.objects.filter(project_id=self.id).aggregate(
            Max('datetime'), Min('datetime'))
        result2 = DeploymentJournal.objects.filter(project_id=self.id, is_effective=True).aggregate(
            Max('working_end'), Min('working_start'))

        # deploymeont journal
        if result2['working_end__max'] is not None and result2['working_start__min'] is not None:
            deps = self.get_deployment_list(as_object=True)
            end_year = result2['working_end__max'].year
            start_year = result2['working_start__min'].year
            year_list = list(range(start_year, end_year+1))
            data = self.count_deployment_journal(year_list)

            value = {
                'datetime__range': [result['datetime__min'].timestamp(), result['datetime__max'].timestamp()],
                'working__range': [result2['working_start__min'].timestamp(), result2['working_end__max'].timestamp()],
                'updated': time.time(),
                'elapsed': time.time() - start_count,
                'years': data,
            }
            return value
        else:
            return None

    def get_or_count_stats(self, force=False):
        key = f'project-{self.id}-stats'
        p = Path(f'cache-files/{key}.json')
        if force is False and p.exists():
            # try/except or with not working here, WHY!!
            f = p.open()
            return json.loads(f.read())
        else:
            if value := self.count_stats():
                self.write_stats(value)
                return value
            return None

    def write_stats(self, data):
        key = f'project-{self.id}-stats'
        f = open(f'cache-files/{key}.json', 'w')
        f.write(json.dumps(data))
        f.close()


class StudyArea(models.Model):
    name = models.CharField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='studyareas')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'<StudyArea {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


# Survey
'''The Survey level includes information on different surveys completed within the same
Project or Study Area. In some cases, a Project or Study Area will consist of more than one
type of Survey. In those cases, the Survey fields can be used to provide information about
each unique Survey. For example, if some aspect of the research or monitoring design
changed during the Project (e.g., the target species or method of data collection) then each
Survey is uniquely identified and the data fields are populated for each unique Survey. Ensure
that each Survey is linked to the appropriate Study Area Name where projects have multiple
Surveys and Study Areas. The Project, Study Area, and Survey may be the same in cases
where surveys were always completed in the same area following the same design. However,
oftentimes surveys with the same methodology, Study Area and Project are separated on a
yearly basis to facilitate annual data submission to WSI. The Survey data is recorded through
the WSI Submissions SharePoint website.'''


class Deployment(models.Model):
    CAMERA_STATUS_CHOICES = (
        ('1', 'Camera Functioning'),
        ('2', 'Unknown Failure'),
        ('3', 'Vandalism/Theft'),
        ('4', 'Memory Card/Film Failure'),
        ('5', 'Camera Hardware Failure'),
        ('6', 'Wildlife Damag'),
    )

    GEODETIC_DATUM_CHOICES = (
        ('TWD97', 'TWD97'),
        ('WGS84', 'WGS84'),
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    # cameraDeploymentBeginDateTime
    # cameraDeploymentEndDateTime
    longitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    altitude = models.SmallIntegerField(null=True, blank=True, db_index=True)
    # deploymentLocationID
    name = models.CharField(max_length=1000)
    # cameraStatus
    camera_status = models.CharField(max_length=4, default='1', choices=CAMERA_STATUS_CHOICES)
    study_area = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True)
    source_data = models.JSONField(default=dict, blank=True)

    geodetic_datum = models.CharField(max_length=10, default='WGS84', choices=GEODETIC_DATUM_CHOICES)
    county = models.CharField('縣市', max_length=1000, blank=True, null=True, db_index=True)
    protectedarea = models.CharField('國家公園/保護留區', max_length=1000, blank=True, null=True, db_index=True)
    landcover = models.CharField('土地覆蓋類型', max_length=1000, blank=True, null=True)
    vegetation = models.CharField('植被類型', max_length=1000, blank=True, null=True)
    verbatim_locality = models.CharField(max_length=1000, blank=True, null=True)
    # 是否已棄用
    deprecated = models.BooleanField(default=False, blank=True)
    # calculation_data = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f'<Deployment {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'altitude': self.altitude,
        }

    def count_working_day(self, year, month):
        '''計算相機工作時數
        根據 DeploymentJournal 記錄
        '''
        num_month = monthrange(year, month)[1]
        #month_start = make_aware(timezone_tw_to_utc(datetime(year, month, 1)))
        #month_end = make_aware(timezone_tw_to_utc(datetime(year, month, num_month)))
        ## deployment_journal 的 working_start, working_end timezone +8 的時間 (台灣時間)，不是 shift 過的，所以不用特別處理timezone
        month_start = make_aware(datetime(year, month, 1))
        month_end = make_aware(datetime(year, month, num_month))
        month_stat = [0] * num_month

        query = DeploymentJournal.objects.filter(
            is_effective=True,
            deployment_id=self.id,
            working_start__lte=month_end,
            working_end__gte=month_start).\
            filter(Q(is_gap__isnull=True) | Q(is_gap=False)).\
            order_by('working_start')
        #print(self.name, year, month, query.all())
        ret = []
        for i in query.all():
            # updated
            #print (i.working_start.toordinal(), i.working_end.toordinal(), dt1.toordinal(), dt2.toordinal())
            month_stat_part = [0] * num_month
            overlap_range = [max(i.working_start, month_start), min(i.working_end, month_end)]
            gap_days = (overlap_range[0]-month_start).days
            duration_days = (overlap_range[1]-overlap_range[0]).days+1
            #print(overlap_range, gap_days, duration_days)
            for index, stat in enumerate(month_stat):
                if index >= gap_days and index < gap_days + duration_days:
                    month_stat[index] = 1
                    month_stat_part[index] = 1

            ret.append([i.working_start.strftime('%Y-%m-%d'), i.working_end.strftime('%Y-%m-%d')])
            #print(month_stat, ret)
        return month_stat, ret

    # cache moved to cache-files
    # def get_species_images(self, year):
    #     key = f'SPIMG_{self.id}_{year}'
    #     if value:= cache.get(key):
    #         # print('cache', key)
    #         return json.loads(value)
    #     else:
    #         value = self.count_species_images(year)
    #         # print('count', value)
    #         cache.set(key, json.dumps(value), 8640000) # 100 d
    #         return value

    def count_species_images(self, year):
        '''計算該年有物種的照片數/全部照片數
        '''
        key = f'SPIMG_{self.id}_{year}'

        with connection.cursor() as cursor:
            q_all = f"SELECT count(distinct image_uuid), \
            DATE_part('year', datetime) as year, \
            DATE_part('month', datetime) as month \
            FROM taicat_image \
            WHERE deployment_id = {self.id} AND DATE_part('year', datetime) = {year} \
            GROUP BY year, DATE_part('month', datetime) \
            ORDER BY year, month;"

            cursor.execute(q_all)
            res = cursor.fetchall()

            by_year_month_all = {}
            for i in res:
                n = i[0]
                year = str(int(i[1]))
                month = str(int(i[2]))
                if year not in by_year_month_all:
                    by_year_month_all[year] = {}

                by_year_month_all[year][month] = n

            q_sp = f"SELECT count(distinct image_uuid), \
            DATE_part('year', datetime) as year, \
            DATE_part('month', datetime) as month \
            FROM taicat_image \
            WHERE deployment_id = {self.id} AND DATE_part('year', datetime) = {year} AND species !='' \
            GROUP BY year, DATE_part('month', datetime) \
            ORDER BY year, month;"
            cursor.execute(q_sp)
            res = cursor.fetchall()
            by_year_month_sp = {}
            for i in res:
                n = i[0]
                year = str(int(i[1]))
                month = str(int(i[2]))
                if year not in by_year_month_sp:
                    by_year_month_sp[year] = {}

                by_year_month_sp[year][month] = n

            return {
                'all': by_year_month_all,
                'species': by_year_month_sp
            }

    def find_deployment_journal_gaps(self, year):
        '''
        get gap in database and count by working_day

        returns: {
                   id: deployment_journal.id,
                   label: [start, end]
                 }
        '''
        year = int(year)
        gaps = []
        query = DeploymentJournal.objects.filter(
            is_gap=True,
            deployment_id=self.id,
            working_start__year__gte=year,
            working_end__year__lte=year)
        rows = query.all()

        for r in rows:
            gaps.append({
                'id': r.id,
                'caused': r.gap_caused,
                'range': [r.working_start.timestamp(), r.working_end.timestamp()],
                'label': '{} - {}'.format(
                    r.working_start.strftime('%m/%d'),
                    r.working_end.strftime('%m/%d'))
            })

        year_stats = []
        for m in range(1, 13):
            ret = self.count_working_day(year, m)
            year_stats += ret[0]

        year_gap = find_the_gap(year, year_stats)
        for i in year_gap:
            found = list(filter(lambda x: x['range'][0] == i[0] and x['range'][1] == i[1], gaps))
            if not found:
                gaps.append({
                    'range': i,
                    'label': '{}/{} - {}/{}'.format(
                        datetime.fromtimestamp(i[0]).month,
                        datetime.fromtimestamp(i[0]).day,
                        datetime.fromtimestamp(i[1]).month,
                        datetime.fromtimestamp(i[1]).day
                    )
                })
        return gaps

    def calculate(self, year, month, species, image_interval, event_interval, to_save=False):
        '''default
        POD: occasion (回合): 1 天, session (期間): 1 月
        APOA: occation: 1 小時
        '''
        working_days = self.count_working_day(year, month)[0]
        #print(self.id, year, month, species, working_days)
        sum_working_hours = sum(working_days) * 24
        image_interval_seconds = image_interval * 60
        event_interval_seconds = event_interval * 60
        days_in_month = monthrange(year, month)[1]

        # count image num
        day_start = timezone_tw_to_utc(datetime(year, month, 1))
        day_start = make_aware(day_start)
        day_end = day_start + timedelta(days=days_in_month) # ex: 12/1 - 12/31 => 11/30 16:00 => 12/31 16:00
        day_end = day_end
        #print(day_start, day_end)
        query_ym_sp = Image.objects.filter(
            deployment_id=self.id,
            #datetime__year=year,
            #datetime__month=month,
            datetime__range=[day_start, day_end],
            species=species
        ).order_by('datetime')
        # print(day_start, day_end)
        # by_species = query_ym.values('species').annotate(count=Count('species'))
        last_datetime = None
        image_count = 0 # OI3
        event_count = 0
        image_count_oi2 = 0
        image_count_oi1 = 0
        delta_count = 0
        delta_count_oi1 = 0
        exist_animals = []
        rows = list(query_ym_sp.values('id', 'datetime', 'animal_id').all())
        # OI1, OI3, event count
        for image in rows:
            image_dt = timezone_utc_to_tw(image['datetime'])
            # print(image['id'], image_dt)
            if last_datetime:
                delta = image_dt - last_datetime
                delta_seconds = (delta.days * 86400) + delta.seconds
                delta_count += delta_seconds # 累加
                delta_count_oi1 += delta_seconds # 累加
                # print (image.id, image.datetime, delta_seconds, delta_count)

                if image['animal_id']:
                    # OI1
                    # 考慮 animal_id, animal_id 跟上一個不同, image_count 加 1
                    if len(exist_animals) > 0:
                        if image['animal_id'] != exist_animals[-1]:
                            image_count_oi1 += 1
                        elif delta_count >= image_interval_seconds:
                            image_count_oi1 += 1
                            delta_count_oi1 = 0
                    else:
                        exist_animals.append(image['animal_id'])
                        image_count_oi1 += 1
                else:
                    # OI3
                    #print(image, image['id'], image_interval_seconds, delta_count)
                    if delta_count >= image_interval_seconds:
                        #print ('ocunt!!')
                        image_count += 1
                        delta_count = 0

                if delta_seconds >= event_interval_seconds:  # 相鄰照片
                    event_count += 1

            else:
                # 第一次事件, 直接加 1
                event_count = 1
                # 第一張照片, 直接加 1
                image_count = 1

                if image['animal_id']:
                    image_count_oi1 += 1

            last_datetime = image_dt

        # OI2
        last_datetime = None
        delta_count = 0
        for image in query_ym_sp.values('deployment', 'datetime', 'species').order_by().annotate(Count('id')):
            #print (year, month, rows)
            if last_datetime:
                delta = image_dt - last_datetime
                delta_seconds = (delta.days * 86400) + delta.seconds
                delta_count += delta_seconds # 累加
                # print (image.id, image.datetime, delta_seconds, delta_count)

                if delta_count >= image_interval_seconds:
                    image_count_oi2 += 1
                    delta_count = 0

            else:
                # 第一張照片, 直接加 1
                image_count_oi2 = 1

            last_datetime = image_dt

        by_day = query_ym_sp.values('datetime__day').annotate(count=Count('datetime__day')).order_by('datetime__day')
        by_hour = query_ym_sp.values('datetime__day', 'datetime__hour').annotate(count=Count('*')).order_by('datetime__day', 'datetime__hour')
        oi3 = (image_count * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
        oi1 = (image_count_oi1 * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
        oi2 = (image_count_oi2 * 1.0 / sum_working_hours) * 1000 if sum_working_hours > 0 else 'N/A'
        pod = by_day.count() * 1.0 / sum(working_days) if sum(working_days) > 0 else 'N/A'
        # month, day, hour
        # note: [[0, [0]*24]] * days_in_month => call by reference error (一個改全部變)
        #print (by_day, by_hour)
        mdh = [[0, [0 for h in range(24)]] for x in range(days_in_month)]
        for day in by_day:
            # print(day, mdh, day['datetime__day']-1, len(mdh))
            if len(mdh) > day['datetime__day'] - 1:
                mdh[day['datetime__day']-1][0] = 1
        for hour in by_hour:
            if len(mdh) > hour['datetime__day']-1:
                mdh[hour['datetime__day']-1][1][hour['datetime__hour']] = 1

        #print (i['species'], image_count, event_count, oi3, pod, by_day.count(), mdh)
        # print(year, month, species, working_days)
        result = [working_days, image_count, event_count, oi1, oi2, oi3, pod, mdh]
        if to_save:
            if c := Calculation.objects.filter(
                    deployment=self,
                    datetime_from=day_start,
                    datetime_to=day_end,
                    image_interval=image_interval,
                    event_interval=event_interval,
                    species=species).first():
                c.data = result
                c.save()
            else:
                c = Calculation(
                    deployment=self,
                    studyarea=self.study_area,
                    project=self.project,
                    datetime_from=day_start,
                    datetime_to=day_end,
                    species=species,
                    image_interval=image_interval,
                    event_interval=event_interval,
                    data=result
                )
                #print('createu')
                c.save()

        return result

    def get_calc_cache(self):
        if rows := caches['file'].get(f'calc-dep-{self.id}'):
            return rows
        return None

class Image(models.Model):
    '''if is_sequence, ex: 5 Images, set last 4 Images's is_sequence to True (wouldn't  count)'''
    PHOTO_TYPE_CHOICES = (
        ('start', 'Start'),
        ('end', 'End'),
        ('set-up', 'Set Up'),
        ('blank', 'Blank'),
        ('animal', 'Animal'),
        ('staff', 'Staff'),
        ('unknown', 'Unknown'),
        ('unidentifiable', 'Unidentifiable'),
        ('time-lapse', 'Timelapse'),
    )
    id = models.BigAutoField(primary_key=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True, related_name='images')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    # be careful, this field has no underline!
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    file_url = models.CharField(max_length=1000, null=True)
    filename = models.CharField(max_length=1000)  # first file if is_sequence
    # dateTimeCaptured
    datetime = models.DateTimeField(null=True, db_index=True)
    # photoType
    # photo_type = models.CharField(max_length=100, null=True, choices=PHOTO_TYPE_CHOICES)
    # photoTypeIdentifiedBy
    # count = models.PositiveSmallIntegerField(default=1, db_index=True)
    species = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    #taxon = models
    # sequence = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # imageid
    # sequence_definition = models.CharField(max_length=1000, default='', null=True, blank=True)
    annotation_seq = models.PositiveSmallIntegerField(default=0, null=True)
    life_stage = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    sex = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    antler = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    remarks = models.TextField(default='', null=True, blank=True, db_index=True)
    animal_id = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    # mongoDB的自填欄位
    remarks2 = models.JSONField(default=dict, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)
    annotation = models.JSONField(default=dict, blank=True, db_index=True)
    memo = models.TextField(default='', blank=True)
    image_hash = models.TextField(default='', blank=True)
    from_mongo = models.BooleanField(default=False, blank=True)
    # file_path = models.TextField(default='', blank=True)  # deprecated
    image_uuid = models.CharField(max_length=1000, default='', blank=True, null=True, db_index=True)
    has_storage = models.CharField('實體檔案(有無上傳)', max_length=2, default='Y', blank=True) # Y/N or 如果之後有其他種狀況, 如: 存在別的圖台?
    source_data = models.JSONField(default=dict, blank=True)
    # exif = models.JSONField(default=dict, blank=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True, db_index=True)
    specific_bucket = models.CharField(max_length=1000, default='', blank=True) # 跟預設不同的 bucket
    deployment_journal = models.ForeignKey('DeploymentJournal', on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的

    def get_associated_media(self, thumbnail='m'):
        if self.from_mongo:
            return f'https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{self.file_url}'
        else:
            bucket_name = settings.AWS_S3_BUCKET
            if self.specific_bucket:
                bucket_name = self.specific_bucket

            return f'https://{bucket_name}.s3.ap-northeast-1.amazonaws.com/{self.image_uuid}-{thumbnail}.jpg'

    @property
    def species_list(self):
        return [x['species'] for x in self.annotation if isinstance(x, dict) and x.get('species', '')]

    # Image.to_dict
    def to_dict(self):
        county_name = ''
        protectedarea_name_list = []
        protectedarea_name = ''
        if x := self.deployment.county:
            if obj := ParameterCode.objects.filter(parametername=x).first():
                county_name = obj.name

        if x := self.deployment.protectedarea:
            if ',' in x:
                name_list = x.split(',')
            else:
                name_list = [x]

            for i in name_list:
                if obj := ParameterCode.objects.filter(parametername=i).first():
                    protectedarea_name_list.append(obj.name)

            protectedarea_name = ', '.join(protectedarea_name_list)

        return {
            'id': self.id,
            'species': self.species,
            'filename': self.filename,
            'datetime': timezone_utc_to_tw(self.datetime).strftime('%Y-%m-%d %H:%M:%S') if self.datetime else '',
            'project__name': self.project.name if self.project else None,
            'studyarea__name': self.studyarea.name if self.studyarea_id else None,
            'deployment__name': self.deployment.name if self.deployment_id else None,
            'deployment__altitude': self.deployment.altitude or '',
            'deployment__county': county_name,
            'deployment__protectedarea': protectedarea_name,
            'media': self.get_associated_media(),
        }

    class Meta:
        ordering = ['-created']
        indexes = [GinIndex(fields=['annotation'])]


class DeletedImage(models.Model):
    '''if is_sequence, ex: 5 Images, set last 4 Images's is_sequence to True (wouldn't  count)'''
    PHOTO_TYPE_CHOICES = (
        ('start', 'Start'),
        ('end', 'End'),
        ('set-up', 'Set Up'),
        ('blank', 'Blank'),
        ('animal', 'Animal'),
        ('staff', 'Staff'),
        ('unknown', 'Unknown'),
        ('unidentifiable', 'Unidentifiable'),
        ('time-lapse', 'Timelapse'),
    )
    id = models.BigAutoField(primary_key=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    file_url = models.CharField(max_length=1000, null=True)
    filename = models.CharField(max_length=1000)  # first file if is_sequence
    datetime = models.DateTimeField(null=True, db_index=True)
    # photo_type = models.CharField(max_length=100, null=True, choices=PHOTO_TYPE_CHOICES)
    # count = models.PositiveSmallIntegerField(default=1, db_index=True)
    species = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    # sequence = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)  # imageid
    # sequence_definition = models.CharField(max_length=1000, default='', blank=True)
    annotation_seq = models.PositiveSmallIntegerField(default=0, null=True)
    life_stage = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    sex = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    antler = models.CharField(max_length=1000, default='', null=True, blank=True, db_index=True)
    remarks = models.TextField(default='', null=True, blank=True, db_index=True)
    animal_id = models.CharField(max_length=1000, null=True, default='', blank=True, db_index=True)
    remarks2 = models.JSONField(default=dict, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)
    annotation = models.JSONField(default=dict, blank=True, db_index=True)
    memo = models.TextField(default='', blank=True)
    image_hash = models.TextField(default='', blank=True)
    from_mongo = models.BooleanField(default=False, blank=True)
    image_uuid = models.CharField(max_length=1000, default='', blank=True, null=True, db_index=True)
    source_data = models.JSONField(default=dict, blank=True)
    # exif = models.JSONField(default=dict, blank=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True, db_index=True)
    has_storage = models.CharField('實體檔案(有無上傳)', max_length=2, default='Y', blank=True) # Y/N or 如果之後有其他種狀況, 如: 存在別的圖台?
    specific_bucket = models.CharField(max_length=1000, default='', blank=True) # 跟預設不同的 bucket
    deployment_journal = models.ForeignKey('DeploymentJournal', on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的

    @property
    def species_list(self):
        return [x['species'] for x in self.annotation if isinstance(x, dict) and x.get('species', '')]

    class Meta:
        ordering = ['created']


class Image_info(models.Model):
    '''
    手動加上 primary key id:
    ALTER TABLE taicat_image_info ADD COLUMN id SERIAL PRIMARY KEY;
    '''
    # image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True)
    id = models.BigAutoField(primary_key=True)
    image_uuid = models.CharField(max_length=1000, default='')
    source_data = models.JSONField(default=dict, blank=True)
    exif = models.JSONField(default=dict, blank=True)


class HomePageStat(models.Model):
    count = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    # type = models.CharField(max_length=10, null=True, blank=True)


class ProjectStat(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    num_sa = models.IntegerField(null=True, blank=True)
    num_deployment = models.IntegerField(null=True, blank=True)
    num_data = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)
    latest_date = models.DateTimeField(null=True, db_index=True)
    earliest_date = models.DateTimeField(null=True, db_index=True)


class ProjectSpecies(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=1000, db_index=True)
    count = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True)


class DeploymentJournal(models.Model):
    GAP_CHOICES = (
        '道路中斷 / 路況不佳無法回收',
        '相機遭竊',
        '相機遭刻意破壞',
        '樣點暫時撤除',
        '樣點永久撤除',
        '樣點尚未架設',
        '樣點剛架設尚未回收資料',
        '相機故障',
        '記憶卡故障',
        '記憶卡遺失',
        '電池沒電',
        '其他(自由填寫)',
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    working_start = models.DateTimeField(null=True, blank=True)
    working_end = models.DateTimeField(null=True, blank=True)
    working_unformat = models.CharField(max_length=1000, null=True, blank=True)
    is_effective = models.BooleanField('是否有效', default=True)
    is_gap = models.BooleanField('缺失', default=False)
    gap_caused = models.CharField('缺失原因', max_length=1000, null=True, blank=True)
    folder_name = models.CharField(max_length=1000, null=True, blank=True, default='')
    local_source_id = models.CharField(max_length=1000, null=True, blank=True, default='') # client local database (sqlite)'s folder id, 用來檢查是否上傳過
    created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(null=True, auto_now_add=True)
    upload_status = models.CharField(max_length=100, null=True, blank=True)# start-annotation/start-media/finished

    @property
    def display_range(self):
        return '{}/{}'.format(self.working_start.strftime('%Y-%m-%d'), self.working_end.strftime('%Y-%m-%d'))

# class ClientUploadLog(models.Model):
#     project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
#     deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
#     studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
#     deployment_journal = models.ForeignKey('DeploymentJournal', on_delete=models.SET_NULL, null=True, blank=True) # 知道是那次上傳的

class DeploymentStat(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    year = models.SmallIntegerField(null=True, blank=True)
    month = models.SmallIntegerField(null=True, blank=True)
    count_working_hour = models.SmallIntegerField(null=True, blank=True)
    session = models.CharField(max_length=50, null=True)


class ImageFolder(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    folder_name = models.CharField(max_length=1000, default='', blank=True)
    folder_last_updated = models.DateTimeField(null=True, db_index=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)


class GeoStat(models.Model):
    # deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    county = models.CharField(max_length=10, db_index=True)
    num_project = models.IntegerField(null=True, blank=True)
    num_deployment = models.IntegerField(null=True, blank=True)
    num_image = models.IntegerField(null=True, blank=True)
    num_working_hour = models.IntegerField(null=True, blank=True)
    identified = models.FloatField(null=True, blank=True)
    species = models.CharField(max_length=1000, default='', blank=True, null=True)
    studyarea = models.TextField(default='', blank=True, null=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)


class StudyAreaStat(models.Model):
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    # 用相機位置算出樣區中心點
    longitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    latitude = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, db_index=True, auto_now_add=True)


# taicat_deploymentstat count_working_hour

# 計畫總數
# 相機位置
# 總辨識進度
# 總相片數
# 相機總工時
# 出現物種


class ProjectMember(models.Model):
    ROLE_CHOICES = (
        #('system_admin', '系統管理員'),
        #('organization_admin', '計畫總管理人'),
        ('project_admin', '個別計畫承辦人'),
        ('uploader', '資料上傳者'),
        #('general', '一般使用者'),
    )
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    member = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=1000, choices=ROLE_CHOICES, null=True, blank=True)
    pmstudyarea =  models.ManyToManyField('StudyArea')


class ParameterCode(models.Model):
    TYPE_CHOICES = (
        ('study_area', '樣區'),
        ('county', '縣市'),
        ('protectedarea', '保護留區'),
        ('vegetation', '植被類型'),
        ('identity', '使用者身份'),
    )
    name = models.CharField('參數中文名稱',max_length=1000 ,null=True, blank=True)
    parametername = models.CharField('參數名稱',max_length=1000 ,null=True, blank=True)
    type = models.CharField('參數類型',max_length=1000 ,choices=TYPE_CHOICES, null=True, blank=True)
    pmajor = models.CharField('上階層名稱',max_length=1000 ,null=True, blank=True)
    description = models.CharField('參數描述',max_length=1000, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)


class Calculation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    studyarea = models.ForeignKey(StudyArea, on_delete=models.SET_NULL, null=True)
    deployment = models.ForeignKey(Deployment, on_delete=models.SET_NULL, null=True)
    #year = models.PositiveSmallIntegerField('year')
    #month = models.PositiveSmallIntegerField('month')
    datetime_from = models.DateTimeField(null=True, db_index=True)
    datetime_to = models.DateTimeField(null=True, db_index=True)
    species = models.CharField('species', max_length=1000, null=True, default='', blank=True, db_index=True)
    image_interval = models.PositiveSmallIntegerField('image interval')
    event_interval = models.PositiveSmallIntegerField('event interval')
    data = models.JSONField(default=dict, blank=True, null=True)

class DownloadLog(models.Model):
    
    user_role = models.CharField('使用者角色', max_length=1000, null=True, default='', blank=True)
    condition = models.CharField('篩選條件', max_length=1000, null=True, default='', blank=True)
    file_link = models.CharField('下載連結', max_length=1000, null=True, default='', blank=True)
