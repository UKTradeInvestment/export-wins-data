# Generated by Django 2.2.10 on 2020-03-03 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wins', '0052_deletedwin'),
    ]

    operations = [
        migrations.AddField(
            model_name='win',
            name='match_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
