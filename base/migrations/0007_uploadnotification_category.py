# Generated by Django 4.0.4 on 2022-05-23 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_rename_is_readed_uploadnotification_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadnotification',
            name='category',
            field=models.CharField(blank=True, default='upload', max_length=100, null=True),
        ),
    ]
