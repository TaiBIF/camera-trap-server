import pandas as pd
import os
import datetime
from pathlib import Path
from django.conf import settings
from taicat.models import ModifiedImage
from taicat.models import Contact
from taicat.utils import get_studyarea_member

modified_images = ModifiedImage.objects.all().values()
df = pd.DataFrame(list(modified_images))
print(df)

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

groups = df2.groupby(['project_id', 'studyarea_id'])
for (project_id, studyarea_id), group in groups:
    studyarea_memebers = get_studyarea_member(project_id, studyarea_id)
    email_list = [x.email for x in Contact.objects.filter(id__in=studyarea_memebers)]
    print(f'EMAIL LIST: {email_list}')
    save_root = Path(settings.MEDIA_ROOT, 'email-attachment')
    save_root.mkdir(parents=True, exist_ok=True)  # 檢查並創建目錄
    save_path = os.path.join(save_root, f'{project_id}_{studyarea_id}.csv')
    file_name = f'{project_id}_{studyarea_id}_{today}.csv'
    group.to_csv(file_name)
