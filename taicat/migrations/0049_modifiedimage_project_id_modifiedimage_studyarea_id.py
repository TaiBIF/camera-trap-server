# Generated by Django 4.0.4 on 2024-07-26 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0048_rename_modified_remark_modifiedimage_modified_remarks_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='modifiedimage',
            name='project_id',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='modifiedimage',
            name='studyarea_id',
            field=models.IntegerField(default=1),
        ),
    ]