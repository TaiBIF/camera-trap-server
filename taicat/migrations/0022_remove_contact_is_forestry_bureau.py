# Generated by Django 3.2.2 on 2021-07-19 05:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0021_auto_20210719_0511'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='is_forestry_bureau',
        ),
    ]