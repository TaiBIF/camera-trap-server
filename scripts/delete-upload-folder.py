from taicat.models import DeploymentJournal, Image
from base.models import UploadHistory, UploadNotification
from django.conf import settings

import boto3

DJ_ID = GIVE_ME_A_ID

dj = DeploymentJournal.objects.get(pk=DJ_ID)
'''
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
        object_key = f'{i.image_uuid}-{j}.jpg'
        response = s3_client.list_object_versions(Bucket=settings.AWS_S3_BUCKET, Prefix=object_key)
        versions = response.get('Versions', []) + response.get('DeleteMarkers', [])
        #print(versions)
        for version in versions:
            version_id = version['VersionId']
            print(f"Deleting {object_key} version {version_id}")
            #s3_client.delete_object(Bucket=bucket_name, Key=object_key, VersionId=version_id)
            #response = s3_client.delete_object(
            #    Bucket=settings.AWS_S3_BUCKET,
            #    Key=key
            #)
        #print(response)

    # too slow
    #if info := Image_info.objects.filter(image_uuid=i.uuid).first():
    #    info.delete()

    #i.delete()

'''
dj.delete()



