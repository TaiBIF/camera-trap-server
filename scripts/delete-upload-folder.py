from taicat.models import DeploymentJournal, Image
from django.conf import settings

import boto3


DJ_ID = 26514

dj = DeploymentJournal.objects.get(pk=DJ_ID)
images = Image.objects.filter(deployment_journal_id=DJ_ID).all()

s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='ap-northeast-1'
)

print('images: ', len(images))
for i in images:
    print(i.image_uuid)
    for j in ['l', 'm', 'x', 'q']:
        response = s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=f"{i.image_uuid}-{j}.jpg"
        )
        print(response)

    # too slow
    #if info := Image_info.objects.filter(image_uuid=i.uuid).first():
    #    info.delete()

    i.delete()

dj.delete()
