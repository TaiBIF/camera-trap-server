import pandas as pd
import os
import datetime
from pathlib import Path
from django.conf import settings
from taicat.models import ModifiedImage
from taicat.models import Contact
from taicat.utils import get_studyarea_member
from django.core.mail import send_mail

modified_images = ModifiedImage.objects.all().values()
df = pd.DataFrame(list(modified_images))

modified_images = ModifiedImage.objects.all().values()
df = pd.DataFrame(list(modified_images))
# 確保 'last_updated' 欄位為 datetime 格式
df['last_updated'] = pd.to_datetime(df['last_updated'])

# 設定基準日期和範圍日期
today = datetime.datetime.now()
one_week_ago = today - datetime.timedelta(weeks=1)

# 選擇 'last_updated' 在一個禮拜前到今天之間的行
df2 = df[(df['last_updated'] >= one_week_ago) & (df['last_updated'] <= today)]
# print(df2)

email_subject = '[臺灣自動相機資訊系統] | 影像資料修改通知'

groups = df2.groupby(['project_id', 'studyarea_id'])
for (project_id, studyarea_id), group in groups:
    studyarea_memebers = get_studyarea_member(project_id, studyarea_id)
    email_list = [x.email for x in Contact.objects.filter(id__in=studyarea_memebers)]
    print(f'EMAIL LIST: {email_list}')
    save_root = Path(settings.MEDIA_ROOT, 'email-attachment')
    save_root.mkdir(parents=True, exist_ok=True)  # 檢查並創建目錄
    save_path = os.path.join(save_root, f'{project_id}_{studyarea_id}.csv')
    group.to_csv(save_path)

    download_url = f'https://staging.camera-trap.tw/media/email-attachment/{project_id}_{studyarea_id}.csv'
    email_body = f'''
    您好：

    您所負責的樣區（計畫名稱：{group['project']}, 樣區名稱：{group['studyarea']}）中的影像資料在過去一週內有經過修改。為了方便您查閱詳細的修改內容，請點擊以下連結下載相關資料：

    [下載修改內容]({download_url})

    如有任何問題，請隨時聯繫我們團隊。

    臺灣自動相機資訊系統 團隊敬上
    '''
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, email_list)