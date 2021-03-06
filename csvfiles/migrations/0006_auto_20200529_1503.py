# Generated by Django 2.2.10 on 2020-05-29 15:03

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('csvfiles', '0005_auto_20180117_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Export Wins'), (2, 'FDI Investments Monthly'), (3, 'FDI Investments Daily'), (4, 'Service Deliveries Monthly'), (5, 'Service Deliveries Daily'), (6, 'Contacts for Regions'), (7, 'Contacts for Sectors'), (8, 'Companies for Regions'), (9, 'Companies for Sectors'), (10, 'Kantar Report Monthly'), (11, "Marketing Companies' Contacts by Country Tiers Daily"), (12, "Marketing Companies' Contacts by Country Tiers Monthly")]),
        ),
        migrations.AlterField(
            model_name='file',
            name='metadata',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
    ]
