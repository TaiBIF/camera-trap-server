# Generated by Django 4.0.4 on 2022-05-05 06:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_uploadnotification'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uploadnotification',
            old_name='is_readed',
            new_name='is_read',
        ),
    ]