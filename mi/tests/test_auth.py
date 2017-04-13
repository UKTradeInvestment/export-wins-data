from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from alice.tests.client import AliceClient
from mi.models import OverseasRegion, SectorTeam, HVCGroup
from users.factories import UserFactory
from wins.factories import HVCFactory


class MIPermissionTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        HVCFactory.create_batch(255, financial_year=16)

    def setUp(self):
        self.sector_teams_list = reverse("mi:sector_teams") + "?year=2016"
        self.regions_list = reverse("mi:overseas_regions") + "?year=2016"
        self.hvc_groups_list = reverse("mi:hvc_groups") + "?year=2016"

        self.alice_client = AliceClient()

        self.user = UserFactory.create()
        self.user.set_password("asdf")
        self.user.save()

    def _add_to_mi_group(self):
        mi_group = Group.objects.get(name="mi_group")
        mi_group.user_set.add(self.user)

    def _test_get_status(self, url, status, mi=False):
        if mi:
            self._add_to_mi_group()
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, status)

    # Sector Teams List
    def test_mi_st_not_allowed_without_group(self):
        self._test_get_status(self.sector_teams_list, 400)

    def test_mi_st_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.sector_teams_list, 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_not_allowed_no_login(self):
        self._test_get_status(self.sector_teams_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.sector_teams_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.sector_teams_list, 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_st_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.sector_teams_list, 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_st_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.sector_teams_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.sector_teams_list, 200, mi=True)

    # specific Sector Team
    def _get_first_sector_team_url(self):
        st = SectorTeam.objects.all()[0]
        st_url = reverse("mi:sector_team_detail", kwargs={"team_id": st.id}) + "?year=2016"
        return st_url

    def test_mi_st_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_sector_team_url(), 400)

    def test_mi_st_1_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_1_not_allowed_no_login(self):
        self._test_get_status(self._get_first_sector_team_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_1_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_st_1_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_st_1_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_st_1_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_sector_team_url(), 200, mi=True)

    # Overseas Regions List
    def test_mi_or_not_allowed_without_group(self):
        self._test_get_status(self.regions_list, 400)

    def test_mi_or_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.regions_list, 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_not_allowed_no_login(self):
        self._test_get_status(self.regions_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.regions_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.regions_list, 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_or_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.regions_list, 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_or_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.regions_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.regions_list, 200, mi=True)

    # specific Overseas Region
    def _get_first_region_url(self):
        region = OverseasRegion.objects.all()[0]
        region_url = reverse("mi:overseas_region_detail", kwargs={"region_id": region.id}) + "?year=2016"
        return region_url

    def test_mi_or_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_region_url(), 400)

    def test_mi_or_1_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_region_url(), 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_1_not_allowed_no_login(self):
        self._test_get_status(self._get_first_region_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self._get_first_region_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_1_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_region_url(), 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_or_1_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_region_url(), 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_or_1_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_region_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_or_1_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_region_url(), 200, mi=True)

    # HVC Groups List
    def test_mi_hg_not_allowed_without_group(self):
        self._test_get_status(self.hvc_groups_list, 400)

    def test_mi_hg_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.hvc_groups_list, 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_not_allowed_no_login(self):
        self._test_get_status(self.hvc_groups_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.hvc_groups_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.hvc_groups_list, 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_hg_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.hvc_groups_list, 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_hg_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.hvc_groups_list, 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self.hvc_groups_list, 200, mi=True)

    # specific HVC Group
    def _get_first_hvc_group_url(self):
        group = HVCGroup.objects.all()[0]
        group_url = reverse("mi:hvc_group_detail", kwargs={"group_id": group.id}) + "?year=2016"
        return group_url

    def test_mi_hg_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_hvc_group_url(), 400)

    def test_mi_hg_1_not_allowed_no_mi_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 400, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_not_allowed_no_login(self):
        self._test_get_status(self._get_first_hvc_group_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_not_allowed_no_mi_group(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 403, mi=False)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_not_allowed_ui_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 403, mi=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_not_allowed_admin_secret(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 403, mi=True)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_mi_hg_1_allowed(self):
        self.alice_client.login(username=self.user.email, password="asdf")
        self._test_get_status(self._get_first_hvc_group_url(), 200, mi=True)
