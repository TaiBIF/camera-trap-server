# Generated by Django 3.2.8 on 2021-10-23 08:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taicat', '0052_alter_image_datetime'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('type', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='image',
            name='annotation',
            field=models.JSONField(blank=True, db_index=True, default=dict),
        ),
        migrations.AlterField(
            model_name='image',
            name='created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='species',
            name='last_updated',
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='species',
            name='name',
            field=models.CharField(db_index=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='species',
            name='status',
            field=models.CharField(blank=True, db_index=True, default='', max_length=4, null=True),
        ),
        migrations.CreateModel(
            name='ProjectStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_sa', models.IntegerField(blank=True, null=True)),
                ('num_deployment', models.IntegerField(blank=True, null=True)),
                ('num_image', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(db_index=True, null=True)),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taicat.project')),
            ],
        ),
    ]