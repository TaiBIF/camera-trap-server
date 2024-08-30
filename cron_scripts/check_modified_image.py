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

if df2.empty:
    print('NO modified images for this week.')
else: 
    groups = df2.groupby(['project_id', 'studyarea_id'])
    for (project_id, studyarea_id), group in groups:
        studyarea_memebers = get_studyarea_member(project_id, studyarea_id)
        email_list = [x.email for x in Contact.objects.filter(id__in=studyarea_memebers)]
        # print(f'EMAIL LIST: {email_list}')
        save_root = Path(settings.MEDIA_ROOT, 'email-attachment')
        save_root.mkdir(parents=True, exist_ok=True)  # 檢查並創建目錄
        save_path = os.path.join(save_root, f'{project_id}_{studyarea_id}.csv')
        project_name = group['project'].iloc[0]
        studyarea_name = group['studyarea'].iloc[0]
        group = group.drop(columns=['id', 'project_id', 'studyarea_id', 'image_id'])
        group = group.rename(columns={
            'last_updated': '最後更新日期',
            'datetime':'影像拍攝日期時間',
            'project':'計畫名稱',
            'studyarea':'樣區名稱',
            'deployment':'相機位置',
            'species':'物種',
            'life_stage':'年齡',
            'sex':'性別',
            'antler':'角況',
            'animal_id':'個體ID',
            'remarks':'備註',
            'modified_datetime':'修改後影像拍攝日期時間',
            'modified_project':'修改後計畫名稱',
            'modified_studyarea':'修改後樣區名稱',
            'modified_deployment':'修改後相機位置',
            'modified_species':'修改後物種',
            'modified_life_stage':'修改後年齡',
            'modified_sex':'修改後性別',
            'modified_antler':'修改後角況',
            'modified_animal_id':'修改後個體ID',
            'modified_remarks':'修改後備註',
        })
        group.to_csv(save_path)

        download_url = f'https://staging.camera-trap.tw/media/email-attachment/{project_id}_{studyarea_id}.csv'
        email_body = f'''
        您好：

        您所負責的樣區（計畫名稱：{project_name}, 樣區名稱：{studyarea_name}）中的影像資料在過去一週內有經過修改。為了方便您查閱詳細的修改內容，請點擊以下連結下載相關資料：

        [下載修改內容]({download_url})

        如有任何問題，請隨時聯繫我們團隊。

        臺灣自動相機資訊系統 團隊敬上
        '''
        send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, email_list)

        print(f'{project_id}_{studyarea_id}.csv was sent to {email_list}')