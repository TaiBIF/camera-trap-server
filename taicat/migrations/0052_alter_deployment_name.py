# Generated by Django 4.2 on 2024-12-13 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0051_deploymentjournal_action_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployment',
            name='name',
            field=models.CharField(db_index=True, max_length=1000),
        ),
    ]
