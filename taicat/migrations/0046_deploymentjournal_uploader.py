# Generated by Django 4.0.4 on 2024-08-23 00:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0045_alter_image_is_duplicated'),
    ]

    operations = [
        migrations.AddField(
            model_name='deploymentjournal',
            name='uploader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.contact'),
        ),
    ]
