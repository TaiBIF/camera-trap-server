# templatetags/tag_library.py
# https://stackoverflow.com/a/15820445/644070

from datetime import timedelta,datetime
import re

from django import template
from django.utils.safestring import mark_safe
from django.db.models import Q
from taicat.models import Organization, ProjectMember, Contact
from base.models import UploadNotification,Announcement
from django.conf import settings


register = template.Library()


@register.filter()
def to_int(value):
    return int(value)


@register.simple_tag()
def get_env():
    return settings.ENV

@register.filter
def get_value_in_qs(queryset, key):
    return queryset.values_list(key, flat=True)


# https://stackoverflow.com/questions/46247729/django-mark-as-read-notifications
@register.filter
def has_unread_notif(contact_id):
    notifications = UploadNotification.objects.filter(contact_id=contact_id, is_read=False)
    if notifications.exists():
        return True
    return False


status_map = {
    'uploading': '上傳中',
    'finished': '已完成',
    'unfinished': '未完成'
}

@register.filter
def get_notif(contact_id):
    return 
    notifications = UploadNotification.objects.filter(contact_id=contact_id).order_by('-created')[:20]
    results = ""
    for n in notifications:
        # 上傳狀態通知
        if n.category == 'upload': 
            created_8 = n.created + timedelta(hours=8)
            dj = n.upload_history.deployment_journal
            try:
                results += f"""
                    <li>
                    <div class="date">{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
                    <p>「{dj.project.name} > {dj.studyarea.name} > {dj.deployment.name} > {dj.folder_name}」上傳狀態為：<strong>{status_map[n.upload_history.status]}</strong></p>
                    </li>
                """
                # f"""
                # <div class="notification-item">
                # <div class="notification-item-content">
                #     <div class='notification-item-date'>{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
                #     <div class="notification-item-message"> 
                #         「{dj.project.name} > {dj.studyarea.name} > {dj.deployment.name} > {dj.folder_name}」上傳狀態為：<strong>{status_map[n.upload_history.status]}</strong>
                #     </div>
                # </div>
                # </div>
                # """


            except Exception as e:
                print("notifications bug == ",e)
                continue
        # 資料缺失通知
        elif n.category == 'gap': 
            created_8 = n.created + timedelta(hours=8)
            results += f"""
                    <li>
                    <div class="date">{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
                    <p>「{n.project.name}」有缺失資料，請至管考介面填寫缺失原因</p>
                    </li>
                    """
            # f"""
            # <div class="notification-item">
            # <div class="notification-item-content">
            #     <div class='notification-item-date'>{created_8.strftime('%Y-%m-%d %H:%M:%S')}</div>
            #     <div class="notification-item-message"> 
            #         「{n.project.name}」有缺失資料，請至管考介面填寫缺失原因
            #     </div>
            # </div>
            # </div>
            # """
    if not results:
        results = f"""
                    <li>
                    <div class="date"></div>
                    <p>暫無通知</p>
                    </li>
                    """
        # results = """
        # <div class="notification-item">
        # <div class="notification-item-content">
        #     <div class="notification-item-message"> 
        #     暫無通知
        #     </div>
        # </div>
        # </div>
        # """
    return mark_safe(results)


# 確認是否有權限取得單機版檔案
@register.filter()
def if_desktop(user_id):

    # 任何計畫下成員
    # 計畫總管理人
    # 系統管理員

    # projects = list(Organization.objects.get(name='林務局').projects.all().values_list('id',flat=True))
    if ProjectMember.objects.filter(member_id=user_id).exists():
        return True
    elif Contact.objects.filter(Q(id=user_id, is_organization_admin=True)|Q(id=user_id, is_system_admin=True)).exists():
        return True
    else:
        return False


# 確認是否有權限設定
@register.filter()
def if_permission(user_id):
    # 系統管理員
    if Contact.objects.filter(id=user_id, is_system_admin=True).exists():
        return True
    else:
        return False

@register.filter
def announcement_content (contact_id):
    title = None
    try:
        title = Announcement.objects.latest('created').title
        # expire_time = int(notifications.mod_date.strftime('%s')) + 7776000
    except:
        pass
    return title


@register.filter
def announcement_expire_time (contact_id):
    expire_time = None
    try:
        notifications = Announcement.objects.latest('created')
        expire_time = str(int(notifications.last_updated.strftime('%s')) + 7776000)
    except:
        pass

    return expire_time

@register.filter(name='check_is_login')
def check_is_login(session_list):
    '''for hide template session.is_login
    '''
    for k, v in session_list.items():
        if k == 'is_login' and v == True:
            return True
    return False
