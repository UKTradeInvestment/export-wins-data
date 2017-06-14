from django.core.management import BaseCommand

from fixturedb.utils.hvc import get_all_hvcs_referenced_by_targets
from wins.models import HVC


class Command(BaseCommand):
    help = 'Creates dummy wins in the database'

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', type=bool,
                            required=False, default=False)
        parser.add_argument('--verbose', type=bool,
                            required=False, default=True)

    def handle(self, *args, **options):
        to_create = get_all_hvcs_referenced_by_targets()
        to_create_models = [HVC(campaign_id=data.campaign_id,
                                financial_year=data.financial_year,
                                name=data.campaign_id + str(data.financial_year))
                            for data in to_create]

        if options['dryrun']:
            for i in to_create_models:
                self.stdout.write(self.style.WARNING(
                    'Would create HVC {name}'.format(name=i.name)))
        else:
            created = HVC.objects.bulk_create(to_create_models)
            if options['verbose']:
                for i in created:
                    self.stdout.write(self.style.SUCCESS(
                        'Created HVC {name}'.format(name=i.name)))
