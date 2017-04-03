from __future__ import unicode_literals

from django.db import migrations, models


def add_financial_years(apps, schema_editor):
    FinancialYear = apps.get_model('mi', 'FinancialYear')
    FinancialYear(id=2016, description="2016-17").save()
    FinancialYear(id=2017, description="2017-18").save()

def update_2016_targets_fy(apps, schema_editor):
    Target = apps.get_model('mi', 'Target')
    hvcs = ['E100', 'E140', 'E133', 'E105', 'E026', 'E063', 'E172', 'E048', 'E032', 'E074', 'E016', 'E084', 'E040', 'E160', 'E013', 'E154', 'E108', 'E189', 'E041', 'E075', 'E062', 'E092', 'E009', 'E146', 'E083', 'E142', 'E165', 'E007', 'E175', 'E042', 'E088', 'E058', 'E191', 'E064', 'E089', 'E021', 'E033', 'E153', 'E045', 'E110', 'E117', 'E217', 'E168', 'E098', 'E035', 'E030', 'E151', 'E099', 'E188', 'E065', 'E051', 'E213', 'E145', 'E167', 'E171', 'E020', 'E118', 'E156', 'E211', 'E081', 'E152', 'E079', 'E037', 'E066', 'E162', 'E086', 'E022', 'E076', 'E129', 'E091', 'E128', 'E019', 'E060', 'E143', 'E053', 'E176', 'E034', 'E114', 'E194', 'E027', 'E082', 'E043', 'E210', 'E170', 'E001', 'E166', 'E209', 'E190', 'E029', 'E149', 'E080', 'E047', 'E052', 'E157', 'E158', 'E169', 'E077', 'E056', 'E161', 'E121', 'E101', 'E018', 'E012', 'E085', 'E102', 'E069', 'E127', 'E123', 'E025', 'E147', 'E122', 'E055', 'E215', 'E015', 'E115', 'E187', 'E179', 'E046', 'E131', 'E070', 'E137', 'E028', 'E178', 'E119', 'E054', 'E138', 'E039', 'E059', 'E139', 'E134', 'E031', 'E144', 'E094', 'E006', 'E126', 'E067', 'E124', 'E150', 'E050', 'E096', 'E071', 'E049', 'E116', 'E093', 'E107', 'E174', 'E112', 'E087', 'E005', 'E106', 'E097', 'E014', 'E184', 'E155', 'E011', 'E214', 'E023', 'E186', 'E182', 'E044', 'E095', 'E212', 'E024', 'E180', 'E159', 'E164', 'E078', 'E004', 'E073', 'E136', 'E103', 'E111', 'E141', 'E061', 'E008', 'E090', 'E109', 'E017', 'E163', 'E010', 'E130', 'E177', 'E183', 'E002', 'E120', 'E104', 'E132', 'E125', 'E068', 'E003', 'E181', 'E173', 'E148', 'E192', 'E185', 'E038', 'E072', 'E135', 'E195']
    for hvc in hvcs:
        Target(campaign_id=hvc, fin_year=2016).save()


class Migration(migrations.Migration):

    dependencies = [
        ('mi', '0028_auto_20170222_1202'),
    ]

    operations = [
        migrations.RunPython(add_financial_years),
        migrations.RunPython(update_2016_targets_fy),
    ]
