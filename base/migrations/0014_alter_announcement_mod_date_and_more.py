# Generated by Django 4.0.4 on 2023-02-22 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_announcement_mod_date_alter_announcement_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='mod_date',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='最後更新時間'),
        ),
        migrations.AlterField(
            model_name='uploadhistory',
            name='status',
            field=models.CharField(blank=True, choices=[('uploading', '上傳中'), ('finished', '已完成'), ('unfinished', '未完成'), ('image-text', '處理文字上傳')], max_length=10, null=True),
        ),
    ]
