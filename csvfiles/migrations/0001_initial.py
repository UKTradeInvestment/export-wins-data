# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-06 15:01
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('s3_path', models.CharField(max_length=255, unique=True)),
                ('file_type', models.PositiveSmallIntegerField(choices=[
                 (1, 'Export Wins'), (2, 'FDI Investments Monthly'), (3, 'FDI Investments Daily')])),
                ('report_date', models.DateTimeField(auto_now_add=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(
                    encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]