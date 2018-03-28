import json

from django.core import mail
from django.urls import reverse
from django.test import TestCase, Client, override_settings

from ..factories import WinFactory
from ..models import Breakdown, Win
from ..notifications import generate_customer_email
from alice.tests.client import AliceClient
from users.factories import UserFactory


class AlicePermissionTestCase(TestCase):

    def setUp(self):

        self.client = Client()
        self.alice_client = AliceClient()

        self.user = UserFactory.create()
        self.user.set_password('asdf')
        self.user.save()

        self.superuser = UserFactory.create(is_superuser=True, email="a@b.c")

        self.wins_schema = reverse("drf:win-schema")
        self.wins_list = reverse("drf:win-list")
        self.wins_detail = reverse("drf:win-detail", kwargs={
            "pk": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        })

        self.customerresponses_schema = reverse("drf:customerresponse-schema")
        self.customerresponses_list = reverse("drf:customerresponse-list")
        self.customerresponses_detail = reverse("drf:customerresponse-detail", kwargs={
            "pk": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        })
        self.breakdowns_schema = reverse("drf:breakdown-schema")
        self.breakdowns_list = reverse("drf:breakdown-list")
        self.breakdowns_detail = reverse("drf:breakdown-detail", kwargs={
            "pk": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        })
        self.advisors_schema = reverse("drf:advisor-schema")
        self.advisors_list = reverse("drf:advisor-list")
        self.advisors_detail = reverse("drf:advisor-detail", kwargs={
            "pk": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        })

        self.win = WinFactory.create()

        self.WINS_POST_SAMPLE = {
          "user": self.user.id,
          "cdms_reference": "cdms reference",
          "company_name": "company name",
          "country": "AF",
          "created": "2016-05-17T12:44:48.021705Z",
          "customer_email_address": "no@way.ca",
          "customer_job_title": "customer job title",
          "customer_location": 3,
          "customer_name": "customer name",
          "date": "1979-06-01",
          "description": "asdlkjskdlfkjlsdjkl",
          "goods_vs_services": 1,
          "has_hvo_specialist_involvement": True,
          "hq_team": "other:1",
          "hvo_programme": "BSC-01",
          "is_e_exported": True,
          "is_line_manager_confirmed": True,
          "is_personally_confirmed": True,
          "is_prosperity_fund_related": True,
          "lead_officer_name": "lead officer name",
          "line_manager_name": "line manager name",
          "location": "Edinburgh, UK",
          "sector": 1,
          "team_type": "investment",
          "total_expected_export_value": 5,
          "total_expected_non_export_value": 5,
          "total_expected_odi_value": 5,
          "type": 1,
          "type_of_support_1": 1,
          "business_type": 1,
          "name_of_export": "name",
          "name_of_customer": "name",
        }

        self.CUSTOMER_RESPONSES_POST_SAMPLE = {
            "win": str(self.win.pk),
            "name": "bob",
            "improved_profile": "1",
            "gained_confidence": "1",
            "access_to_information": "1",
            "expected_portion_without_help": "1",
            "last_export": "1",
            "overcame_problem": "1",
            "developed_relationships": "1",
            "access_to_contacts": "1",
            "our_support": "1",
            "marketing_source": "1",
        }

        self.BREAKDOWNS_POST_SAMPLE = {
            "win": str(self.win.pk),
            "type": Breakdown.TYPE_EXPORT,
            "year": "1999",
            "value": "1",
        }

        self.ADVISORS_POST_SAMPLE = {
            "win": str(self.win.pk),
            "name": "bob",
            "team_type": "other",
            "hq_team": "team:1",
            "location": "france"
        }

    # GET Schema --------------------------------------------------------------


    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_schema_pass(self, url, keys):
        response = self.alice_client.get(url)
        content = json.loads(str(response.content, "utf-8"))
        self.assertEqual(response.status_code, 200)
        for key in keys:
            self.assertIn(key, content)

    def test_win_schema_pass(self):
        self._test_get_schema_pass(
            self.wins_schema,
            ['id', 'company_name', 'cdms_reference', 'cdms_reference'],
        )

    def test_customerresponse_schema_pass(self):
        self._test_get_schema_pass(
            self.customerresponses_schema,
            ['access_to_contacts', 'access_to_information'],
        )

    def test_breakdown_schema_pass(self):
        self._test_get_schema_pass(
            self.breakdowns_schema,
            ['win', 'type', 'year', 'value'],
        )

    def test_advisor_schema_pass(self):
        self._test_get_schema_pass(
            self.advisors_schema,
            ['name', 'team_type', 'hq_team', 'location'],
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_schema_fail_bad_client(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_win_schema_fail_bad_client(self):
        self._test_get_schema_fail_bad_client(self.wins_schema)

    def test_customerresponse_schema_fail_bad_client(self):
        self._test_get_schema_fail_bad_client(self.customerresponses_schema)

    def test_breakdown_schema_fail_bad_client(self):
        self._test_get_schema_fail_bad_client(self.breakdowns_schema)

    def test_advisor_schema_fail_bad_client(self):
        self._test_get_schema_fail_bad_client(self.advisors_schema)

    # GET List ----------------------------------------------------------------

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_list_pass(self, url):
        self._login()
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_wins_get_list_pass(self):
        self._test_get_list_pass(self.wins_list)

    def test_customerresponse_get_list_pass(self):
        self._test_get_list_pass(self.customerresponses_list)

    def test_breakdowns_get_list_pass(self):
        self._test_get_list_pass(self.breakdowns_list)

    def test_advisors_get_list_pass(self):
        self._test_get_list_pass(self.advisors_list)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_list_fail_no_auth(self, url):
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_wins_get_list_fail_no_auth(self):
        self._test_get_list_fail_no_auth(self.wins_list)

    def test_breakdowns_get_list_fail_no_auth(self):
        self._test_get_list_fail_no_auth(self.breakdowns_list)

    def test_advisors_get_list_fail_no_auth(self):
        self._test_get_list_fail_no_auth(self.advisors_list)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_list_fail_no_signature(self, url):
        self._login()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_wins_get_list_fail_no_signature(self):
        self._test_get_list_fail_no_signature(self.wins_list)

    def test_customerresponses_get_list_fail_no_signature(self):
        self._test_get_list_fail_no_signature(self.customerresponses_list)

    def test_breakdowns_get_list_fail_no_signature(self):
        self._test_get_list_fail_no_signature(self.breakdowns_list)

    def test_advisors_get_list_fail_no_signature(self):
        self._test_get_list_fail_no_signature(self.advisors_list)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_list_fail_bad_signature(self, url):
        auth = {
            "HTTP_X_SIGNATURE": "bad-signature",
        }
        self._login()
        response = self.alice_client.get(url, **auth)
        self.assertEqual(response.status_code, 400)

    def test_wins_get_list_fail_bad_signature(self):
        self._test_get_list_fail_bad_signature(self.wins_list)

    def test_customerresponses_get_list_fail_bad_signature(self):
        self._test_get_list_fail_bad_signature(self.customerresponses_list)

    def test_breakdowns_get_list_fail_bad_signature(self):
        self._test_get_list_fail_bad_signature(self.breakdowns_list)

    def test_advisors_get_list_fail_bad_signature(self):
        self._test_get_list_fail_bad_signature(self.advisors_list)

    # GET Detail --------------------------------------------------------------

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_detail_pass(self, url):
        self._login()
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_wins_get_detail_pass(self):
        self._test_get_detail_pass(self.wins_detail)

    def test_customerresponses_get_detail_pass(self):
        self._test_get_detail_pass(self.customerresponses_detail)

    def test_breakdowns_get_detail_pass(self):
        self._test_get_detail_pass(self.breakdowns_detail)

    def test_advisors_get_detail_pass(self):
        self._test_get_detail_pass(self.advisors_detail)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_detail_fail_no_auth(self, url):
        response = self.alice_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_wins_get_detail_fail_no_auth(self):
        self._test_get_detail_fail_no_auth(self.wins_detail)

    def test_breakdowns_get_detail_fail_no_auth(self):
        self._test_get_detail_fail_no_auth(self.breakdowns_detail)

    def test_advisors_get_detail_fail_no_auth(self):
        self._test_get_detail_pass(self.advisors_detail)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_detail_fail_no_signature(self, url):
        self._login()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_wins_get_detail_fail_no_signature(self):
        self._test_get_detail_fail_no_signature(self.wins_detail)

    def test_customerresponses_get_detail_fail_no_signature(self):
        self._test_get_detail_fail_no_signature(self.customerresponses_detail)

    def test_breakdowns_get_detail_fail_no_signature(self):
        self._test_get_detail_fail_no_signature(self.breakdowns_detail)

    def test_advisors_get_detail_fail_no_signature(self):
        self._test_get_detail_fail_no_signature(self.advisors_detail)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_get_detail_fail_bad_signature(self, url):
        auth = {
            "HTTP_X_SIGNATURE": "bad-signature",
        }
        self._login()
        response = self.alice_client.get(url, **auth)
        self.assertEqual(response.status_code, 400)

    def test_wins_get_detail_fail_bad_signature(self):
        self._test_get_detail_fail_bad_signature(self.wins_detail)

    def test_customerresponses_get_detail_fail_bad_signature(self):
        self._test_get_detail_fail_bad_signature(self.customerresponses_detail)

    def test_breakdowns_get_detail_fail_bad_signature(self):
        self._test_get_detail_fail_bad_signature(self.breakdowns_detail)

    def test_advisors_get_detail_fail_bad_signature(self):
        self._test_get_detail_pass(self.advisors_detail)

    # POST --------------------------------------------------------------------

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_pass(self, url, data):
        """ Test POSTing succeeds """

        self._login()
        response = self.alice_client.post(url, data)
        self.assertEqual(response.status_code, 201, response.content)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_patch_pass(self, url, data):
        """ Test PATCHing succeeds """

        self._login()
        response = self.alice_client.patch(
            url,
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)

    def test_wins_post_pass(self):
        self._test_post_pass(self.wins_list, self.WINS_POST_SAMPLE)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_wins_post_pass_complete_send_mail_no_officers(self):
        """ Test customer email & officer notifications sent as appropriate """

        self.win.delete(for_real=True)

        # if not complete, no mail (when you create a win, it is not complete)
        self._test_post_pass(self.wins_list, self.WINS_POST_SAMPLE)
        self.assertEquals(len(mail.outbox), 0)

        # if complete it should send customer mail, but not send any officer
        # mails, since no extra officer email addresses were added to the win
        win = Win.objects.all()[0]
        win_url = self.wins_list + str(win.id) + '/'
        json_data = json.dumps({'complete': True})
        self._test_patch_pass(win_url, json_data)

        win = Win.objects.all()[0]
        self.assertTrue(win.complete)
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue(
            mail.outbox[0].subject.startswith('Please confirm '),
        )
        self.assertIn(
            'delighted to hear of your recent',
            mail.outbox[0].body,
        )
        self.assertEqual(mail.outbox[0].to, ['no@way.ca'])

        # if re-submit the complete patch, no additional mail should be sent
        self._test_patch_pass(win_url, json_data)
        self.assertEquals(len(mail.outbox), 1)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_wins_post_pass_complete_send_mail_with_officers(self):
        """ Test customer email & officer notifications sent as appropriate """

        # if complete it should send customer mail, and send notifications
        # to additionally listed officers
        self.win.lead_officer_email_address = 'lead@email.address'
        self.win.other_official_email_address = 'other@email.address'
        self.win.save()
        win_url = self.wins_list + str(self.win.id) + '/'
        json_data = json.dumps({'complete': True})
        self._test_patch_pass(win_url, json_data)

        self.assertEquals(len(mail.outbox), 2)

        # customer email
        self.assertTrue(
            mail.outbox[0].subject.startswith('Please confirm '),
        )
        self.assertIn(
            'delighted to hear of your recent',
            mail.outbox[0].body,
        )
        self.assertEqual(mail.outbox[0].to, ['customer@email.address'])

        # email to both extra officers, but not Win creator
        self.assertTrue(
            mail.outbox[1].subject.startswith(
                'Thank you for submitting a new Win.'
            ),
        )
        self.assertIn(
            'an Export Win you recorded will shortly be forwarded',
            mail.outbox[1].body,
        )
        self.assertEqual(
            set(mail.outbox[1].to),
            set(['lead@email.address', 'other@email.address']),
        )

    def test_customerresponses_post_pass(self):
        self._test_post_pass(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_customerresponses_post_pass_send_confirmation(self):
        self.win.lead_officer_email_address = 'lead@example.com'
        self.win.save()
        self._test_post_pass(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
        )
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(
            mail.outbox[0].subject,
            'Customer response to Export Win',
        )
        self.assertIn(
            'has submitted a response to the Export Win you recorded in',
            mail.outbox[0].body,
        )
        self.assertEqual(
            set(mail.outbox[0].to),
            set([self.win.lead_officer_email_address, self.win.user.email]),
        )

    def test_breakdowns_post_pass(self):
        self._test_post_pass(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
        )

    def test_advisors_post_pass(self):
        self._test_post_pass(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_no_auth(self, url, data):
        response = self.alice_client.post(url, data)
        self.assertEqual(response.status_code, 403)

    def test_wins_post_fail_no_auth(self):
        self._test_post_fail_no_auth(self.wins_list, self.WINS_POST_SAMPLE)

    def test_breakdowns_post_fail_no_auth(self):
        self._test_post_fail_no_auth(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
        )

    def test_advisors_post_fail_no_auth(self):
        self._test_post_fail_no_auth(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_bad_auth(self, url, data):
        self.alice_client.login(username="not-a-user", password="asdf")
        response = self.alice_client.post(url, data)
        self.assertEqual(response.status_code, 403)

        self.alice_client.login(username=self.user.email, password="fail")
        response = self.alice_client.post(url, data)
        self.assertEqual(response.status_code, 403)

    def test_wins_post_fail_bad_auth(self):
        self._test_post_fail_bad_auth(
            self.wins_list,
            self.WINS_POST_SAMPLE,
        )

    def test_breakdowns_post_fail_bad_auth(self):
        self._test_post_fail_bad_auth(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
        )

    def test_advisors_post_fail_bad_auth(self):
        self._test_post_fail_bad_auth(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_no_signature(self, url, data):
        self._login()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)

    def test_wins_post_fail_no_signature(self):
        self._test_post_fail_no_signature(
            self.wins_list,
            self.WINS_POST_SAMPLE,
        )

    def test_customerresponses_post_fail_no_signature(self):
        self._test_post_fail_no_signature(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
        )

    def test_breakdowns_post_fail_no_signature(self):
        self._test_post_fail_no_signature(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
        )

    def test_advisors_post_fail_no_signature(self):
        self._test_post_fail_no_signature(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_bad_signature(self, url, data):
        auth = {
            "HTTP_X_SIGNATURE": "bad-signature"
        }
        self._login()
        response = self.alice_client.post(url, data, **auth)
        self.assertEqual(response.status_code, 400)

    def test_wins_post_fail_bad_signature(self):
        self._test_post_fail_bad_signature(
            self.wins_list,
            self.WINS_POST_SAMPLE,
        )

    def test_customerresponses_post_fail_bad_signature(self):
        self._test_post_fail_bad_signature(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
        )

    def test_breakdowns_post_fail_bad_signature(self):
        self._test_post_fail_bad_signature(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
        )

    def test_advisors_post_fail_bad_signature(self):
        self._test_post_fail_bad_signature(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_no_data(self, url, data, key):
        self._login()
        response = self.alice_client.post(url, {})
        self.assertEqual(response.status_code, 400)
        content = json.loads(str(response.content, "utf-8"))
        self.assertIn(key, content)
        self.assertEqual(content[key], ["This field is required."])

    def test_wins_post_fail_no_data(self):
        self._test_post_fail_no_data(
            self.wins_list,
            self.WINS_POST_SAMPLE,
            'customer_email_address',
        )

    def test_customerresponses_post_fail_no_data(self):
        self._test_post_fail_no_data(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
            'win',
        )

    def test_breakdowns_post_fail_no_data(self):
        self._test_post_fail_no_data(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
            'win',
        )

    def test_advisors_post_fail_no_data(self):
        self._test_post_fail_no_data(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
            'team_type',
        )

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def _test_post_fail_bad_data(self, url, data, key, error_msg):
        self._login()
        data[key] = 'not valid!'
        response = self.alice_client.post(url, data)
        self.assertEqual(response.status_code, 400)
        content = json.loads(str(response.content, "utf-8"))
        self.assertIn(key, content)
        self.assertEqual(content[key][0], error_msg)

    def test_wins_post_fail_bad_data(self):
        self._test_post_fail_bad_data(
            self.wins_list,
            self.WINS_POST_SAMPLE,
            'customer_email_address',
            'Enter a valid email address.',
        )

    def test_customerresponses_post_fail_bad_data(self):
        self._test_post_fail_bad_data(
            self.customerresponses_list,
            self.CUSTOMER_RESPONSES_POST_SAMPLE,
            'win',
            "'not valid!' is not a valid UUID.",
        )

    def test_breakdowns_post_fail_bad_data(self):
        self._test_post_fail_bad_data(
            self.breakdowns_list,
            self.BREAKDOWNS_POST_SAMPLE,
            'win',
            "'not valid!' is not a valid UUID.",
        )

    def test_advisors_post_fail_bad_data(self):
        self._test_post_fail_bad_data(
            self.advisors_list,
            self.ADVISORS_POST_SAMPLE,
            'team_type',
            '"not valid!" is not a valid choice.',
        )

    def _make_staff(self):
        self.user.is_staff = True
        self.user.save()

    def _login(self):
        self.alice_client.login(username=self.user.email, password="asdf")

    def _test_get_status(self, name, status, staff=False):
        if staff:
            self._make_staff()
        self._login()
        response = self.alice_client.get(reverse(name))
        self.assertEqual(response.status_code, status)

    def test_csv_not_allowed_without_sig_or_perm(self):
        self._test_get_status('csv', 400)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_not_allowed_without_perm(self):
        self._test_get_status('csv', 403)

    def test_csv_not_allowed_with_perm_without_sig(self):
        self._test_get_status('csv', 400, staff=True)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_csv_allowed_with_perm(self):
        self._test_get_status('csv', 200, staff=True)

    def test_admin_add_user_not_allowed_without_sig(self):
        self._test_get_status('admin-add-user', 400)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_admin_add_user_not_allowed_with_perm_with_ui_sig(self):
        self._test_get_status('admin-add-user', 403, staff=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_add_user_not_allowed_without_perm_with_admin_sig(self):
        self._test_get_status('admin-add-user', 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_add_user_allowed_with_perm_and_admin_sig(self):
        self._test_get_status('admin-add-user', 200, staff=True)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_add_user(self):
        self._make_staff()
        self._login()
        response = self.alice_client.post(
            reverse('admin-add-user'),
            {
                'name': 'Bilbo Vader',
                'email': 'bilbo.vader@example.com'
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(
            mail.outbox[0].subject,
            'Export Wins Login Credentials',
        )
        self.assertIn(
            'This email contains your login credentials',
            mail.outbox[0].body,
        )
        self.assertEqual(
            mail.outbox[0].to[0],
            'bilbo.vader@example.com',
        )

    def test_admin_new_password_not_allowed_without_sig(self):
        self._test_get_status('admin-new-password', 400)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_admin_new_password_not_allowed_with_perm_with_ui_sig(self):
        self._test_get_status('admin-new-password', 403, staff=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_new_password_not_allowed_without_perm_with_admin_sig(self):
        self._test_get_status('admin-new-password', 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_new_password_allowed_with_perm_and_admin_sig(self):
        self._test_get_status('admin-new-password', 200, staff=True)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_new_password(self):
        self._make_staff()
        self._login()
        UserFactory.create(email='bilbo.vader@example.com')
        response = self.alice_client.post(
            reverse('admin-new-password'),
            {'email': 'bilbo.vader@example.com'},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(
            mail.outbox[0].subject,
            'Export Wins Login Credentials',
        )
        self.assertIn(
            'This email contains your login credentials',
            mail.outbox[0].body,
        )
        self.assertEqual(
            mail.outbox[0].to[0],
            'bilbo.vader@example.com',
        )

    def test_admin_send_customer_email_not_allowed_without_sig(self):
        self._test_get_status('admin-send-customer-email', 400)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_admin_send_customer_email_not_allowed_with_perm_with_ui_sig(self):
        self._test_get_status('admin-send-customer-email', 403, staff=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_send_customer_email_not_allowed_without_perm_with_admin_sig(self):
        self._test_get_status('admin-send-customer-email', 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_send_customer_email_allowed_with_perm_and_admin_sig(self):
        self._test_get_status('admin-send-customer-email', 200, staff=True)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_send_customer_email(self):
        self._make_staff()
        self._login()
        win = WinFactory.create(
            customer_email_address='bilbo.vader@example.com'
        )
        response = self.alice_client.post(
            reverse('admin-send-customer-email'),
            {'win_id': str(win.id)},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEquals(len(mail.outbox), 2)
        self.assertIn(
            'helped with your success',
            mail.outbox[0].subject,
        )
        self.assertIn(
            'delighted to hear of your recent business',
            mail.outbox[0].body,
        )
        self.assertEqual(
            mail.outbox[0].to[0],
            'bilbo.vader@example.com',
        )

        self.assertIn(
            'hank you for submitting a new Win',
            mail.outbox[1].subject,
        )
        self.assertIn(
            'will shortly be forwarded to',
            mail.outbox[1].body,
        )
        self.assertEqual(
            mail.outbox[1].to[0],
            win.user.email,
        )

    def test_admin_change_customer_email_not_allowed_without_sig(self):
        self._test_get_status('admin-send-customer-email', 400)

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_admin_change_customer_email_not_allowed_with_perm_with_ui_sig(self):
        self._test_get_status('admin-change-customer-email', 403, staff=True)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_change_customer_email_not_allowed_without_perm_with_admin_sig(self):
        self._test_get_status('admin-change-customer-email', 403)

    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_change_customer_email_allowed_with_perm_and_admin_sig(self):
        self._test_get_status('admin-change-customer-email', 200, staff=True)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @override_settings(ADMIN_SECRET=AliceClient.SECRET)
    def test_admin_change_customer_email(self):
        self._make_staff()
        self._login()
        win = WinFactory.create(
            customer_email_address='bilbo.vader@example.com'
        )
        response = self.alice_client.post(
            reverse('admin-change-customer-email'),
            {
                'win_id': str(win.id),
                'email': 'new-email@example.com'
            },
        )
        self.assertEqual(response.status_code, 201)
        win = Win.objects.get(id=win.id)
        self.assertEqual(win.customer_email_address, 'new-email@example.com')
        self.assertEquals(len(mail.outbox), 2)
        self.assertIn(
            'helped with your success',
            mail.outbox[0].subject,
        )
        self.assertIn(
            'delighted to hear of your recent business',
            mail.outbox[0].body,
        )
        self.assertEqual(
            mail.outbox[0].to[0],
            'new-email@example.com',
        )

        self.assertIn(
            'hank you for submitting a new Win',
            mail.outbox[1].subject,
        )
        self.assertIn(
            'will shortly be forwarded to',
            mail.outbox[1].body,
        )
        self.assertEqual(
            mail.outbox[1].to[0],
            win.user.email,
        )


class EmailTestCase(TestCase):

    def test_email_line_length(self):
        """ Some email clients reject emails with lines > 1000 chars """

        url = 'https://www.exportwins.service.trade.gov.uk/wins/review/nunh0ijn0ijn90jniojonuj90u'
        win = WinFactory.create()
        email_dict = generate_customer_email(url, win)
        for line in email_dict['html_body'].split('\n'):
            self.assertTrue(len(line) < 1000, line)
