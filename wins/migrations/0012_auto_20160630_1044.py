# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-30 10:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0011_auto_20160628_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerresponse',
            name='access_to_contacts',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you gain access to contacts not otherwise accessible?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='access_to_information',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you gain access to information or improved understanding of the country?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='developed_relationships',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you develop and/or nurture critical relationships?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='expected_portion_without_help',
            field=models.PositiveIntegerField(choices=[(1, 'Would not have achieved any export value without your support'), (2, 'Would have achieved 1% – 20% of the export value without your support'), (3, 'Would have achieved 21% - 40% of the export value without your support'), (4, 'Would have achieved 41% - 60% of the export value without your support'), (5, 'Would have achieved 61% - 80% of the export value without your support'), (6, 'Would have achieved 80% of the export value without your support'), (7, 'Would have achieved all of the export value without your support, the value would have been similar')], verbose_name='What proportion of the total expected export value above would you have achieved without our support?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='gained_confidence',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you gain the confidence to explore or expand in the country?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='has_explicit_export_plans',
            field=models.BooleanField(verbose_name='Beyond this event, do you have specific plans to export in the next 12 months?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='improved_profile',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you improve your profile or credibility in the country?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='involved_state_enterprise',
            field=models.BooleanField(verbose_name='Did the win involve a foreign government or state-owned enterprise (e.g. as a customer, an intermediary or facilitator)?'),
        ),
        migrations.AlterField(
            model_name='customerresponse',
            name='overcame_problem',
            field=models.PositiveIntegerField(choices=[(0, 'N/A'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], verbose_name='Did you overcome a problem in the country (eg legal, regulatory, commercial)'),
        ),
    ]