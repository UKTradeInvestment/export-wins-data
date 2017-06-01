import random

from django.core.management.base import BaseCommand, CommandError

from faker import Factory as FakeFactory

from users.models import User
from wins.models import HVC
from ...factories.win import create_win_factory

fake = FakeFactory.create('en_GB')

class Command(BaseCommand):
    help = 'Creates dummy wins in the database'

    def add_arguments(self, parser):
        parser.add_argument('num_wins', type=int)

    def handle(self, *args, **options):
        win_factory = create_win_factory(User.objects.last())
        hvc_choices = HVC.objects.all().values_list('campaign_id', flat=True).distinct()
        for i in range(options['num_wins']):
            w = win_factory(random.choice(hvc_choices), confirm=True)
            self.stdout.write(self.style.SUCCESS('Created Win {id}'.format(id=w.id)))
