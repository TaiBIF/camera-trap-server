# Generated by Django 4.0.4 on 2023-02-20 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_alter_announcement_created_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='mod_date',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='更新時間'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='created',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True, verbose_name='建立時間'),
        ),
    ]
