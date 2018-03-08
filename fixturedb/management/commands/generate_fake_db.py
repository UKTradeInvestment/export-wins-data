from typing import List
import random

from django.core.management.base import BaseCommand, CommandError
from factory.fuzzy import FuzzyChoice

from faker import Factory as FakeFactory

from users.models import User
from wins.constants import TEAMS, HQ_TEAM_REGION_OR_POST
from wins.factories import AdvisorFactory
from wins.models import HVC, Win
from ...factories.win import create_win_factory

fake = FakeFactory.create('en_GB')


def bool_to_tick(val):
    return '✔' if val else '✘'


class Command(BaseCommand):
    help = 'Creates dummy wins in the database'
    user = User.objects.last()
    hvc_choices = FuzzyChoice(HVC.objects.all().values_list('campaign_id', flat=True).distinct())
    team_type_choices = FuzzyChoice(dict(TEAMS).keys())
    hq_team_choices = FuzzyChoice(dict(HQ_TEAM_REGION_OR_POST).keys())

    def add_arguments(self, parser):
        parser.add_argument(
            'num_wins',
            type=int,
            nargs=2,
            help='number of hvc wins. first arg is confirmed, second is unconfirmed', default=[1, 1]
        )
        parser.add_argument('--non_hvc', type=int, nargs=2, default=[0, 0], help="number of non_hvc wins to create")
        parser.add_argument('-a', '--add-advisors', type=bool, default=False,
                            help="add some additional advisors (random)")

    def make_win(self, win_factory, has_customer_response, agree_with_win, is_hvc):
        w = win_factory(
            self.hvc_choices.fuzz() if is_hvc else None,
            confirm=has_customer_response,
            team_type=self.team_type_choices.fuzz()
        )
        if has_customer_response and w.confirmation.agree_with_win != agree_with_win:
            w.confirmation.agree_with_win = agree_with_win
            w.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {"non-" if not is_hvc else ""}HVC Win {w.id}. Confirmed={bool_to_tick(w.confirmed)}. '
                f'Team={w.hq_team} '
            )
        )
        return w

    def handle(self, *args, **options):
        win_factory = create_win_factory(User.objects.last())
        wins = []

        wins.extend(self.handle_hvc(options, win_factory))
        wins.extend(self.handle_non_hvc(options, win_factory))
        self.handle_advisors(options, wins)

    def handle_advisors(self, options, wins: List[Win]):
        if options['add_advisors']:
            for w in wins:
                for a in range(random.randint(1, 3)):
                    AdvisorFactory(
                        win_id=w.id,
                        name=fake.name(),
                        team_type=self.team_type_choices.fuzz(),
                        hq_team=self.hq_team_choices.fuzz()
                    )

    def handle_non_hvc(self, options, win_factory):
        wins = []
        confirmed, unconfirmed = options['non_hvc']
        for i in range(confirmed):
            wins.append(self.make_win(
                win_factory,
                has_customer_response=True,
                agree_with_win=True,
                is_hvc=False
            ))
        for i in range(unconfirmed):
            wins.append(self.make_win(
                win_factory,
                has_customer_response=True,
                agree_with_win=False,
                is_hvc=False
            ))
        return wins

    def handle_hvc(self, options, win_factory):
        wins = []
        confirmed, unconfirmed = options['num_wins']
        for i in range(confirmed):
            w = self.make_win(win_factory, has_customer_response=True, agree_with_win=True, is_hvc=True)
            wins.append(w)
        for i in range(unconfirmed):
            w = self.make_win(win_factory, has_customer_response=False, agree_with_win=False, is_hvc=True)
            wins.append(w)
        return wins
