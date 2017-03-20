# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-30 12:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0012_auto_20160630_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerresponse',
            name='has_explicit_export_plans',
            field=models.BooleanField(verbose_name='Beyond this win, do you have specific plans to export in the next 12 months?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='overcame_problem',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you overcome a problem in the country (eg legal, regulatory, commercial)?'),
        ),
    ]