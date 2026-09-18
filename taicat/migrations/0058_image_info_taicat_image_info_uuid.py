from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction; building it
    # concurrently avoids locking writes on the ~24M-row table during deploy.
    atomic = False

    dependencies = [
        ('taicat', '0057_image_taicat_image_journal_filename'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='image_info',
            index=models.Index(fields=['image_uuid'], name='taicat_image_info_uuid'),
        ),
    ]
