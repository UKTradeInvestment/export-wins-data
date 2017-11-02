from optparse import OptionParser

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from alice.tests.client import AliceClient
from mi.models import OverseasRegion, SectorTeam, HVCGroup
from sso.tests import BaseSSOTestCase
from wins.factories import HVCFactory

from users.models import User


class MIPermissionTestCase(BaseSSOTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        HVCFactory.create_batch(255, financial_year=16)

    def setUp(self):
        from django.core.management import call_command
        call_command('create_missing_hvcs', verbose=False)

        self.sector_teams_list = reverse("mi:sector_teams") + "?year=2016"
        self.regions_list = reverse("mi:overseas_regions") + "?year=2016"
        self.hvc_groups_list = reverse("mi:hvc_groups") + "?year=2016"

    def _test_get_status(self, url, status, mi=False, secret=None):
        if secret == 'mi':
            self._get_status_mi_secret(url, status, perm=mi)
        elif secret == 'admin':
            self._get_status_admin_secret(url, status, perm=mi)
        elif secret == 'ui':
            self._get_status_ui_secret(url, status, perm=mi)
        else:
            self._get_status_no_secret(url, status, perm=mi)

    # Sector Teams List
    def test_mi_st_not_allowed_without_group(self):
        self._test_get_status(self.sector_teams_list, 400)

    def test_mi_st_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self.sector_teams_list, 400, mi=True)

    def test_mi_st_not_allowed_no_login(self):
        self._test_get_status(self.sector_teams_list,
                              403, mi=True, secret='mi')

    def test_mi_st_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.sector_teams_list,
                              403, mi=True, secret='mi')

    def test_mi_st_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(self.sector_teams_list,
                              403, mi=False, secret='mi')

    def test_mi_st_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(self.sector_teams_list,
                              403, mi=True, secret='ui')

    def test_mi_st_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(self.sector_teams_list,
                              403, mi=True, secret='admin')

    def test_mi_st_allowed(self):
        self._login()
        self._test_get_status(self.sector_teams_list,
                              200, mi=True, secret='mi')

    # specific Sector Team
    def _get_first_sector_team_url(self):
        st = SectorTeam.objects.all()[0]
        st_url = reverse("mi:sector_team_detail", kwargs={
                         "team_id": st.id}) + "?year=2016"
        return st_url

    def test_mi_st_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_sector_team_url(), 400)

    def test_mi_st_1_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self._get_first_sector_team_url(), 400, mi=True)

    def test_mi_st_1_not_allowed_no_login(self):
        self._test_get_status(
            self._get_first_sector_team_url(), 403, mi=True, secret='mi')

    def test_mi_st_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(
            self._get_first_sector_team_url(), 403, mi=True, secret='mi')

    def test_mi_st_1_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(
            self._get_first_sector_team_url(), 403, mi=False, secret='mi')

    def test_mi_st_1_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(
            self._get_first_sector_team_url(), 403, mi=True, secret='ui')

    def test_mi_st_1_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(
            self._get_first_sector_team_url(), 403, mi=True, secret='admin')

    def test_mi_st_1_allowed(self):
        self._login()
        self._test_get_status(
            self._get_first_sector_team_url(), 200, mi=True, secret='mi')

    # Overseas Regions List
    def test_mi_or_not_allowed_without_group(self):
        self._test_get_status(self.regions_list, 400)

    def test_mi_or_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self.regions_list, 400, mi=True)

    def test_mi_or_not_allowed_no_login(self):
        self._test_get_status(self.regions_list, 403, mi=True, secret='mi')

    def test_mi_or_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.regions_list, 403, mi=True, secret='mi')

    def test_mi_or_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(self.regions_list, 403, mi=False, secret='mi')

    def test_mi_or_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(self.regions_list, 403, mi=True, secret='ui')

    def test_mi_or_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(self.regions_list, 403, mi=True, secret='admin')

    def test_mi_or_allowed(self):
        self._login()
        self._test_get_status(self.regions_list, 200, mi=True, secret='mi')

    # specific Overseas Region
    def _get_first_region_url(self):
        region = OverseasRegion.objects.all()[0]
        region_url = reverse("mi:overseas_region_detail", kwargs={
                             "region_id": region.id}) + "?year=2016"
        return region_url

    def test_mi_or_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_region_url(), 400)

    def test_mi_or_1_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self._get_first_region_url(), 400, mi=True)

    def test_mi_or_1_not_allowed_no_login(self):
        self._test_get_status(self._get_first_region_url(),
                              403, mi=True, secret='mi')

    def test_mi_or_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self._get_first_region_url(),
                              403, mi=True, secret='mi')

    def test_mi_or_1_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(self._get_first_region_url(),
                              403, mi=False, secret='mi')

    def test_mi_or_1_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(self._get_first_region_url(),
                              403, mi=True, secret='ui')

    def test_mi_or_1_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(self._get_first_region_url(),
                              403, mi=True, secret='admin')

    def test_mi_or_1_allowed(self):
        self._login()
        self._test_get_status(self._get_first_region_url(),
                              200, mi=True, secret='mi')

    # HVC Groups List
    def test_mi_hg_not_allowed_without_group(self):
        self._test_get_status(self.hvc_groups_list, 400)

    def test_mi_hg_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self.hvc_groups_list, 400, mi=True)

    def test_mi_hg_not_allowed_no_login(self):
        self._test_get_status(self.hvc_groups_list, 403, mi=True, secret='mi')

    def test_mi_hg_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(self.hvc_groups_list, 403, mi=True, secret='mi')

    def test_mi_hg_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(self.hvc_groups_list, 403, mi=False, secret='mi')

    def test_mi_hg_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(self.hvc_groups_list, 403, mi=True, secret='ui')

    def test_mi_hg_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(self.hvc_groups_list, 403,
                              mi=True, secret='admin')

    def test_mi_hg_allowed(self):
        self._login()
        self._test_get_status(self.hvc_groups_list, 200, mi=True, secret='mi')

    # specific HVC Group
    def _get_first_hvc_group_url(self):
        group = HVCGroup.objects.all()[0]
        group_url = reverse("mi:hvc_group_detail", kwargs={
                            "group_id": group.id}) + "?year=2016"
        return group_url

    def test_mi_hg_1_not_allowed_without_group(self):
        self._test_get_status(self._get_first_hvc_group_url(), 400)

    def test_mi_hg_1_not_allowed_no_mi_secret(self):
        self._login()
        self._test_get_status(self._get_first_hvc_group_url(), 400, mi=True)

    def test_mi_hg_1_not_allowed_no_login(self):
        self._test_get_status(
            self._get_first_hvc_group_url(), 403, mi=True, secret='mi')

    def test_mi_hg_1_not_allowed_bad_login(self):
        self.alice_client.login(username="no-email", password="asdf")
        self._test_get_status(
            self._get_first_hvc_group_url(), 403, mi=True, secret='mi')

    def test_mi_hg_1_not_allowed_no_mi_group(self):
        self._login()
        self._test_get_status(
            self._get_first_hvc_group_url(), 403, mi=False, secret='mi')

    def test_mi_hg_1_not_allowed_ui_secret(self):
        self._login()
        self._test_get_status(
            self._get_first_hvc_group_url(), 403, mi=True, secret='ui')

    def test_mi_hg_1_not_allowed_admin_secret(self):
        self._login()
        self._test_get_status(self._get_first_hvc_group_url(),
                              403, mi=True, secret='admin')

    def test_mi_hg_1_allowed(self):
        self._login()
        self._test_get_status(
            self._get_first_hvc_group_url(), 200, mi=True, secret='mi')


class CSVUploadPermissionTestCase(TestCase):
    def setUp(self):
        self.alice_client = AliceClient()

    def _login(self, is_staff=False):
        normal_user = User.objects.create_user(
            name='dummy', password="dummy", email='dummy@dummy.com', is_staff=is_staff)
        self.alice_client.force_login(
            normal_user, 'django.contrib.auth.backends.ModelBackend')

    def _admin_login(self):
        admin_user = User.objects.create_superuser(
            name='admin', password="dummy", email='admin@dummy.com')
        self.alice_client.force_login(
            admin_user, 'django.contrib.auth.backends.ModelBackend')

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_allowed_admin_secret(self):
        self._admin_login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 201)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret(self):
        self._admin_login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret(self):
        self._admin_login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_admin_secret_but_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_admin_secret_but_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 201)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret_non_staff_normal_user(self):
        self._login()
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(MI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_mi_secret_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_upload_not_allowed_ui_secret_staff_normal_user(self):
        self._login(is_staff=True)
        upload_url = reverse("mi:csv_upload")
        response = self.alice_client.post(
            upload_url, data={'path': 'dummy path'})
        self.assertEqual(response.status_code, 403)
