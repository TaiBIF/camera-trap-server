# Generated by Django 4.0.4 on 2023-04-18 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0029_deployment_calculation_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Calculation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField(verbose_name='year')),
                ('month', models.PositiveSmallIntegerField(verbose_name='month')),
                ('species', models.CharField(blank=True, db_index=True, default='', max_length=1000, null=True, verbose_name='species')),
                ('image_interval', models.PositiveSmallIntegerField(verbose_name='image interval')),
                ('event_inverval', models.PositiveSmallIntegerField(verbose_name='event interval')),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('deployment', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.deployment')),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
                ('studyarea', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.studyarea')),
            ],
        ),
    ]
