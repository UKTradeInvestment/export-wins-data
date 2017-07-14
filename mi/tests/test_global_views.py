from django.core.management import call_command
from django.urls import reverse
from freezegun import freeze_time

from fixturedb.factories.win import create_win_factory
from mi.tests.base_test_case import MiApiViewsWithWinsBaseTestCase, MiApiViewsBaseTestCase


@freeze_time(MiApiViewsBaseTestCase.frozen_date_17)
class GlobalWinsViewTestCase(MiApiViewsWithWinsBaseTestCase):
    """ Tests to test global win aggregate view `GlobalWinsView` """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('create_missing_hvcs', verbose=False)

    def setUp(self):
        super().setUp()
        self._win_factory_function = create_win_factory(
            self.user, sector_choices=self.TEAM_1_SECTORS)
        self.view_base_url = self.cen_campaign_url

    cen_campaign_url = reverse('mi:global_wins')
