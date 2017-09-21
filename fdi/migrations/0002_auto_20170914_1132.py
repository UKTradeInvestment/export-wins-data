# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-14 11:32
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('fdi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyLegacyLoad',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('row_index', models.PositiveSmallIntegerField()),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
            ],
        ),
        migrations.AlterField(
            model_name='investmentlegacyload',
            name='data',
            field=django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterUniqueTogether(
            name='investmentlegacyload',
            unique_together=set([('filename', 'row_index')]),
        ),
        migrations.AlterUniqueTogether(
            name='companylegacyload',
            unique_together=set([('filename', 'row_index')]),
        ),
    ]