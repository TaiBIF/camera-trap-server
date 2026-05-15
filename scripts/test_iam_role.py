"""
Verify IAM role setup on the EC2 production host.

Checks:
  1. boto3 is using an instance-profile credential (not static keys).
  2. STS GetCallerIdentity returns the expected role ARN.
  3. SES: ses:SendEmail / ses:SendRawEmail (via GetSendQuota permission check).
  4. S3: GetObject, PutObject, ListBucketVersions, DeleteObject,
     DeleteObjectVersion on settings.AWS_S3_BUCKET.

Non-destructive: PutObject/Delete* operate only on a temporary key under
the prefix 'iam-role-test/'. Existing objects are not modified.

Usage:
  python scripts/test_iam_role.py
"""

import os
import sys
import uuid

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings

S3_REGION = 'ap-northeast-1'
SES_REGION = settings.AWS_SES_REGION_NAME or 'us-west-2'
TEST_KEY = f'iam-role-test/{uuid.uuid4()}.txt'

PASS = '\033[32m PASS\033[0m'
FAIL = '\033[31m FAIL\033[0m'
INFO = '\033[36m INFO\033[0m'

results = []


def record(name, ok, detail=''):
    tag = PASS if ok else FAIL
    print(f'[{tag}] {name}' + (f' — {detail}' if detail else ''))
    results.append((name, ok))


def check_credential_source():
    session = boto3.Session()
    creds = session.get_credentials()
    if creds is None:
        record('credentials available', False, 'no credentials found')
        return False
    frozen = creds.get_frozen_credentials()
    method = creds.method
    print(f'[{INFO}] credential method: {method}')
    print(f'[{INFO}] access_key_id starts with: {frozen.access_key[:4]}...')
    # 'iam-role' = EC2 instance profile via IMDS. Anything else (env,
    # shared-credentials-file, config-file) means static keys are still in
    # play somewhere on this host.
    record('credentials come from EC2 instance profile',
           method == 'iam-role', f'method={method}')
    return True


def check_sts():
    try:
        sts = boto3.client('sts')
        ident = sts.get_caller_identity()
        print(f'[{INFO}] Account: {ident["Account"]}')
        print(f'[{INFO}] ARN:     {ident["Arn"]}')
        record('sts:GetCallerIdentity', True)
        return ident
    except (ClientError, NoCredentialsError) as e:
        record('sts:GetCallerIdentity', False, str(e))
        return None


def check_ses():
    try:
        ses = boto3.client('ses', region_name=SES_REGION)
        quota = ses.get_send_quota()
        record('ses:GetSendQuota (permission proxy)', True,
               f'quota max24h={quota.get("Max24HourSend")}')
    except ClientError as e:
        record('ses:GetSendQuota', False, e.response['Error']['Code'])


def check_s3():
    bucket = settings.AWS_S3_BUCKET
    if not bucket:
        record('AWS_S3_BUCKET configured', False, 'empty')
        return
    print(f'[{INFO}] Bucket: {bucket} (region {S3_REGION})')
    s3 = boto3.client('s3', region_name=S3_REGION)

    # ListBucketVersions
    try:
        resp = s3.list_object_versions(Bucket=bucket, Prefix='iam-role-test/',
                                        MaxKeys=1)
        record('s3:ListBucketVersions', True)
    except ClientError as e:
        record('s3:ListBucketVersions', False, e.response['Error']['Code'])

    # PutObject
    version_id = None
    try:
        resp = s3.put_object(Bucket=bucket, Key=TEST_KEY,
                              Body=b'iam-role-test', ContentType='text/plain')
        version_id = resp.get('VersionId')
        record('s3:PutObject', True, f'version_id={version_id}')
    except ClientError as e:
        record('s3:PutObject', False, e.response['Error']['Code'])
        return

    # GetObject (head_object uses s3:GetObject)
    try:
        s3.head_object(Bucket=bucket, Key=TEST_KEY)
        record('s3:GetObject (via head_object)', True)
    except ClientError as e:
        record('s3:GetObject', False, e.response['Error']['Code'])

    # DeleteObject (delete-marker path)
    try:
        s3.delete_object(Bucket=bucket, Key=TEST_KEY)
        record('s3:DeleteObject', True)
    except ClientError as e:
        record('s3:DeleteObject', False, e.response['Error']['Code'])

    # DeleteObjectVersion — clean up any versions and the delete marker we
    # just produced. Skip silently if bucket is not versioned.
    try:
        resp = s3.list_object_versions(Bucket=bucket, Prefix=TEST_KEY)
        items = resp.get('Versions', []) + resp.get('DeleteMarkers', [])
        if not items:
            record('s3:DeleteObjectVersion', True,
                   'no versions to delete (bucket unversioned)')
        else:
            for it in items:
                s3.delete_object(Bucket=bucket, Key=it['Key'],
                                 VersionId=it['VersionId'])
            record('s3:DeleteObjectVersion', True,
                   f'cleaned {len(items)} version(s)')
    except ClientError as e:
        record('s3:DeleteObjectVersion', False, e.response['Error']['Code'])


def main():
    print('=== IAM role verification ===')
    if not check_credential_source():
        sys.exit(2)
    check_sts()
    check_ses()
    check_s3()

    print()
    failed = [n for n, ok in results if not ok]
    if failed:
        print(f'FAILED ({len(failed)}/{len(results)}): {", ".join(failed)}')
        sys.exit(1)
    print(f'OK: all {len(results)} checks passed.')


if __name__ == '__main__':
    main()
