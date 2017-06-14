# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-10 23:10
from __future__ import unicode_literals

from django.db import migrations


def add_2016_hvc_countries(apps, schema_editor):
    Target = apps.get_model('mi', 'Target')
    FinancialYear = apps.get_model('mi', 'FinancialYear')
    Country = apps.get_model('mi', 'Country')
    hvc_2016 = [('E008', 'BH', 2016),
                ('E012', 'BR', 2016),
                ('E013', 'BR', 2016),
                ('E014', 'BR', 2016),
                ('E017', 'HU', 2016),
                ('E018', 'PL', 2016),
                ('E020', 'RO', 2016),
                ('E023', 'CN', 2016),
                ('E024', 'CN', 2016),
                ('E026', 'CN', 2016),
                ('E027', 'CN', 2016),
                ('E028', 'CN', 2016),
                ('E030', 'CN', 2016),
                ('E031', 'CN', 2016),
                ('E032', 'CN', 2016),
                ('E033', 'CN', 2016),
                ('E035', 'CN', 2016),
                ('E037', 'CN', 2016),
                ('E039', 'CN', 2016),
                ('E040', 'DK', 2016),
                ('E041', 'KE', 2016),
                ('E042', 'TZ', 2016),
                ('E044', 'FI', 2016),
                ('E045', 'FR', 2016),
                ('E047', 'FR', 2016),
                ('E050', 'DE', 2016),
                ('E051', 'DE', 2016),
                ('E053', 'DE', 2016),
                ('E054', 'DE', 2016),
                ('E056', 'GH', 2016),
                ('E058', 'HK', 2016),
                ('E060', 'HK', 2016),
                ('E061', 'HK', 2016),
                ('E063', 'IN', 2016),
                ('E064', 'IN', 2016),
                ('E065', 'IN', 2016),
                ('E067', 'IN', 2016),
                ('E068', 'IN', 2016),
                ('E070', 'IN', 2016),
                ('E071', 'IN', 2016),
                ('E072', 'IN', 2016),
                ('E073', 'IN', 2016),
                ('E074', 'IN', 2016),
                ('E075', 'IN', 2016),
                ('E076', 'IN', 2016),
                ('E077', 'IN', 2016),
                ('E078', 'ID', 2016),
                ('E079', 'ID', 2016),
                ('E081', 'IQ', 2016),
                ('E083', 'IT', 2016),
                ('E084', 'JP', 2016),
                ('E086', 'JP', 2016),
                ('E087', 'JP', 2016),
                ('E088', 'JP', 2016),
                ('E090', 'JP', 2016),
                ('E091', 'KZ', 2016),
                ('E092', 'KW', 2016),
                ('E094', 'BR', 2016),
                ('E095', 'BR', 2016),
                ('E099', 'MX', 2016),
                ('E103', 'MY', 2016),
                ('E105', 'IT', 2016),
                ('E106', 'ES', 2016),
                ('E107', 'MX', 2016),
                ('E111', 'AE', 2016),
                ('E112', 'SA', 2016),
                ('E114', 'DK', 2016),
                ('E116', 'SE', 2016),
                ('E117', 'NG', 2016),
                ('E118', 'US', 2016),
                ('E121', 'NO', 2016),
                ('E122', 'OM', 2016),
                ('E123', 'OM', 2016),
                ('E126', 'PH', 2016),
                ('E127', 'PT', 2016),
                ('E130', 'QA', 2016),
                ('E131', 'SA', 2016),
                ('E135', 'SA', 2016),
                ('E136', 'SA', 2016),
                ('E138', 'SA', 2016),
                ('E139', 'SG', 2016),
                ('E140', 'SG', 2016),
                ('E142', 'SG', 2016),
                ('E143', 'SG', 2016),
                ('E144', 'ZA', 2016),
                ('E145', 'ZA', 2016),
                ('E146', 'MY', 2016),
                ('E147', 'SG', 2016),
                ('E149', 'KR', 2016),
                ('E152', 'KR', 2016),
                ('E154', 'ZA', 2016),
                ('E155', 'ES', 2016),
                ('E156', 'ES', 2016),
                ('E158', 'SE', 2016),
                ('E160', 'SE', 2016),
                ('E163', 'TH', 2016),
                ('E166', 'TR', 2016),
                ('E168', 'TR', 2016),
                ('E171', 'UA', 2016),
                ('E173', 'AE', 2016),
                ('E174', 'AE', 2016),
                ('E175', 'AE', 2016),
                ('E176', 'AE', 2016),
                ('E178', 'AE', 2016),
                ('E179', 'AE', 2016),
                ('E180', 'AE', 2016),
                ('E181', 'AE', 2016),
                ('E182', 'US', 2016),
                ('E185', 'US', 2016),
                ('E187', 'US', 2016),
                ('E194', 'US', 2016),
                ('E209', 'TN', 2016),
                ('E211', 'KZ', 2016),
                ('E212', 'TW', 2016),
                ('E214', 'FR', 2016),
                ('E003', 'AU', 2016),
                ('E004', 'AU', 2016),
                ('E005', 'AU', 2016),
                ('E006', 'AU', 2016),
                ('E007', 'AZ', 2016),
                ('E010', 'BE', 2016),
                ('E015', 'CA', 2016),
                ('E019', 'PL', 2016),
                ('E022', 'CN', 2016),
                ('E029', 'CN', 2016),
                ('E038', 'CN', 2016),
                ('E043', 'KE', 2016),
                ('E046', 'FR', 2016),
                ('E055', 'DE', 2016),
                ('E062', 'IN', 2016),
                ('E066', 'IN', 2016),
                ('E069', 'IN', 2016),
                ('E085', 'JP', 2016),
                ('E089', 'JP', 2016),
                ('E093', 'KW', 2016),
                ('E098', 'CL', 2016),
                ('E100', 'CO', 2016),
                ('E102', 'MY', 2016),
                ('E109', 'MX', 2016),
                ('E115', 'DK', 2016),
                ('E119', 'NL', 2016),
                ('E132', 'SA', 2016),
                ('E133', 'SA', 2016),
                ('E141', 'SG', 2016),
                ('E150', 'KR', 2016),
                ('E151', 'KR', 2016),
                ('E161', 'CH', 2016),
                ('E162', 'TH', 2016),
                ('E167', 'TR', 2016),
                ('E170', 'UA', 2016),
                ('E183', 'US', 2016),
                ('E184', 'US', 2016),
                ('E188', 'US', 2016),
                ('E189', 'US', 2016),
                ('E190', 'US', 2016),
                ('E213', 'IR', 2016),
                ('E001', 'AU', 2016),
                ('E195', 'BS', 2016),
                ('E002', 'AU', 2016),
                ('E009', 'LT', 2016),
                ('E011', 'BE', 2016),
                ('E016', 'CA', 2016),
                ('E021', 'CL', 2016),
                ('E025', 'CN', 2016),
                ('E034', 'CN', 2016),
                ('E048', 'FR', 2016),
                ('E049', 'DE', 2016),
                ('E052', 'DE', 2016),
                ('E059', 'HK', 2016),
                ('E080', 'IQ', 2016),
                ('E082', 'IQ', 2016),
                ('E096', 'MX', 2016),
                ('E097', 'BR', 2016),
                ('E101', 'BR', 2016),
                ('E104', 'MY', 2016),
                ('E108', 'MX', 2016),
                ('E110', 'MX', 2016),
                ('E120', 'NO', 2016),
                ('E124', 'PH', 2016),
                ('E125', 'PH', 2016),
                ('E128', 'PT', 2016),
                ('E129', 'QA', 2016),
                ('E134', 'SA', 2016),
                ('E137', 'SA', 2016),
                ('E148', 'KR', 2016),
                ('E153', 'ZA', 2016),
                ('E157', 'SE', 2016),
                ('E159', 'SE', 2016),
                ('E164', 'TH', 2016),
                ('E165', 'TR', 2016),
                ('E169', 'TR', 2016),
                ('E172', 'AE', 2016),
                ('E177', 'AE', 2016),
                ('E186', 'US', 2016),
                ('E191', 'US', 2016),
                ('E192', 'US', 2016),
                ('E210', 'MN', 2016),
                ('E217', 'MA', 2016),
                ('E215', '', 2016)]
    financial_year = FinancialYear.objects.get(id=2016)
    for item in hvc_2016:
        hvc, country_code, fy = item
        # skip entries without country codes
        if country_code != '':
            country = Country.objects.get(country=country_code)
            if Target.objects.filter(campaign_id=hvc, financial_year=financial_year).exists():
                target = Target.objects.get(campaign_id=hvc, financial_year=financial_year)
                target.country.add(country)


class Migration(migrations.Migration):
    dependencies = [
        ('mi', '0036_auto_20170612_1438'),
    ]

    operations = [
        migrations.RunPython(add_2016_hvc_countries),
    ]