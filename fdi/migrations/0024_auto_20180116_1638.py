# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-16 16:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fdi', '0023_auto_20171201_1324'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestmentUKRegion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RemoveField(
            model_name='investments',
            name='uk_region',
        ),
        migrations.AddField(
            model_name='investmentukregion',
            name='investment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fdi.Investments'),
        ),
        migrations.AddField(
            model_name='investmentukregion',
            name='uk_region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fdi.UKRegion'),
        ),
        migrations.RemoveField(
            model_name='investments',
            name='approved_good_value',
        ),
        migrations.RemoveField(
            model_name='investments',
            name='approved_high_value',
        ),
        migrations.AddField(
            model_name='investments',
            name='uk_regions',
            field=models.ManyToManyField(through='fdi.InvestmentUKRegion', to='fdi.UKRegion'),
        ),
        migrations.AddField(
            model_name='investments',
            name='status',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
