# Generated by Django 4.0.4 on 2022-04-27 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='has_storage',
            field=models.CharField(blank=True, default='Y', max_length=2, verbose_name='實體檔案(有無上傳)'),
        ),
    ]
