# Generated by Django 3.1.7 on 2021-03-05 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='note',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='region',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]