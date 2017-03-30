import csv
import datetime
import io
import tempfile
import zipfile

from django.core.urlresolvers import reverse
from django.test import override_settings, TestCase

from ..serializers import WinSerializer
from ..factories import (
    AdvisorFactory,
    BreakdownFactory,
    CustomerResponseFactory,
    NotificationFactory,
    WIN_TYPES_DICT,
    WinFactory,
)
from alice.tests.client import AliceClient
from users.factories import UserFactory
from wins.views.flat_csv import CSVView


class TestFlatCSV(TestCase):

    def setUp(self):
        user = UserFactory(name='Johnny Fakeman', email="jfakeman@example.com")
        win1 = WinFactory(
            user=user,
            id='6e18a056-1a25-46ce-a4bb-0553a912706f',
            export_experience=1,)
        BreakdownFactory(
            win=win1,
            year=2016,
            value=10000,
            type=WIN_TYPES_DICT['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2018,
            value=20000,
            type=WIN_TYPES_DICT['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2020,
            value=2000000,
            type=WIN_TYPES_DICT['Export'],
        )
        BreakdownFactory(
            win=win1,
            year=2017,
            value=300000,
            type=WIN_TYPES_DICT['Non-export'],
        )
        AdvisorFactory(win=win1)
        AdvisorFactory(
            win=win1,
            name='Bobby Beedle',
            team_type='post',
            hq_team="post:Albania - Tirana"
        )
        CustomerResponseFactory(win=win1)
        NotificationFactory(win=win1)
        self.win1 = win1

        # another win with no non-local data
        win2 = WinFactory(
            user=user,
            id='6e18a056-1a25-46ce-a4bb-0553a912706d',
            created=win1.created + datetime.timedelta(days=1),
            audit='changes'
        )
        self.win2 = win2

        self.url = reverse('csv')

    @override_settings(UI_SECRET=AliceClient.SECRET)
    def test_request(self):
        client = AliceClient()
        user = UserFactory.create(is_superuser=True, email='a@b.c')
        user.set_password('asdf')
        user.is_staff = True
        user.save()
        client.login(username=user.email, password='asdf')
        resp = client.get(self.url)
        zf = zipfile.ZipFile(io.BytesIO(resp.content), 'r')
        csv_path = zf.extract('wins_complete.csv', tempfile.mkdtemp())
        with open(csv_path, 'r') as csv_fh:
            csv_str = csv_fh.read()[1:]  # exclude BOM
        win_dict = list(csv.DictReader(csv_str.split('\n')))[0]
        self._assert_about_win_dict(win_dict)

    def test_direct_call(self):
        csv_str = CSVView()._make_flat_wins_csv()[1:]  # exclude BOM
        win_dict = list(csv.DictReader(csv_str.split('\n')))[0]
        self._assert_about_win_dict(win_dict)

    def _choice_to_str(self, obj, fieldname):
        """ Convert display of a choice to equivalent as expected in CSV """

        if not getattr(obj, fieldname):
            return ''
        disp = getattr(obj, 'get_{}_display'.format(fieldname))()
        if ',' in disp:
            return '"{}"'.format(disp)
        return disp

    def test_expected_output(self):
        actual_lines = CSVView()._make_flat_wins_csv().split('\n')
        expected_lines = '''\ufeffid,user,Organisation or company name,CDMS Reference,Contact name,Job title,Contact email,HQ location,What kind of business deal was this win?,Summarise the support provided to help achieve this win,Overseas customer,What goods or services are being exported?,Date business won [MM/YY],country,Type of win,total expected export value,total expected non export value,Does the expected export value relate to,sector,Prosperity Fund,"HVC code, if applicable","HVO Programme, if applicable",An HVO specialist was involved,E-exporting programme,type of support 1,type of support 2,type of support 3,associated programme 1,associated programme 2,associated programme 3,I confirm that this information is complete and accurate,My line manager has confirmed the decision to record this win,Lead officer name,Lead officer email address,Secondary email address,Line manager,team type,"HQ team, Region or Post",export experience,created,audit,contributing advisors/team,customer email sent,customer email date,Export breakdown 1,Export breakdown 2,Export breakdown 3,Export breakdown 4,Export breakdown 5,Non-export breakdown 1,Non-export breakdown 2,Non-export breakdown 3,Non-export breakdown 4,Non-export breakdown 5,customer response recieved,date response received,Your name,Please confirm these details are correct,Other comments or changes to the export details,Securing the win overall?,Gaining access to contacts?,Getting information or improved understanding of the country?,Improving your profile or credibility in the country?,Having confidence to explore or expand in the country?,Developing or nurturing critical relationships?,"Overcoming a problem in the country (eg legal, regulatory, commercial)?",The win involved a foreign government or state-owned enterprise (eg as an intermediary or facilitator),Our support was a prerequisite to generate this export value,Our support helped you achieve this win more quickly,What value do you estimate you would have achieved without our support?,When did your company last export goods or services?,"If you hadn't achieved this win, your company might have stopped exporting","Apart from this win, you already have specific plans to export in the next 12 months",It enabled you to expand into a new market,It enabled you to increase exports as a proportion of your turnover,It enabled you to maintain or expand in an existing market,Would you be willing for DIT / Exporting is GREAT to feature your success in marketing materials?\r
6e18a056-1a25-46ce-a4bb-0553a912706f,Johnny Fakeman <jfakeman@example.com>,company name,cdms reference,customer name,customer job title,customer@email.address,East Midlands,,description,,,2016-05-25,Canada,Export,"£100,000","£2,300",Goods,{sector1},Yes,{hvc1},AER-01: Global Aerospace,Yes,Yes,Market entry advice and support – DIT/FCO in UK,,,,,,Yes,Yes,lead officer name,,,line manager name,Trade (TD or ST),TD - Events - Financial & Professional Business Services,Has never exported before,{created1},,"Name: Billy Bragg, Team DSO - TD - Events - Financial & Professional Business Services, Name: Bobby Beedle, Team Overseas Post - Albania - Tirana",Yes,{sent},"2016: £10,000","2018: £20,000","2020: £2,000,000",,,"2017: £300,000",,,,,Yes,{response_date},Cakes,{agree},Good work,1,2,3,4,5,1,2,Yes,No,Yes,More than 80%,"Apart from this win, we have exported in the last 12 months",No,Yes,No,Yes,No,No\r
6e18a056-1a25-46ce-a4bb-0553a912706d,Johnny Fakeman <jfakeman@example.com>,company name,cdms reference,customer name,customer job title,customer@email.address,East Midlands,,description,,,2016-05-25,Canada,Export,"£100,000","£2,300",Goods,{sector2},Yes,{hvc2},AER-01: Global Aerospace,Yes,Yes,Market entry advice and support – DIT/FCO in UK,,,,,,Yes,Yes,lead officer name,,,line manager name,Trade (TD or ST),TD - Events - Financial & Professional Business Services,,{created2},changes,,No,,,,,,,,,,,,No,,,,,,,,,,,,,,,,,,,,,,\r'''\
            .format(
                created1=self.win1.created.date(),
                created2=self.win2.created.date(),
                sent=self.win1.notifications.filter(type='c')[0].created.date(),
                response_date=self.win1.confirmation.created.date(),
                sector1=self._choice_to_str(self.win1, 'sector'),
                sector2=self._choice_to_str(self.win2, 'sector'),
                hvc1=self._choice_to_str(self.win1, 'hvc'),
                hvc2=self._choice_to_str(self.win2, 'hvc'),
                agree=CSVView()._val_to_str(self.win1.confirmation.agree_with_win),
            ).split('\n')

        # note these aren't really col-based since just split by comma
        for actual_line, expected_line in zip(actual_lines, expected_lines):
            zipped_cols = zip(actual_line.split(','), expected_line.split(','))
            for actual_col, expected_col in zipped_cols:
                self.assertEqual(actual_col, expected_col)

    def _assert_about_win_dict(self, win_dict):
        for field_name in WinSerializer().fields:
            if field_name in CSVView.IGNORE_FIELDS:
                continue

            field = CSVView()._get_win_field(field_name)
            csv_name = field.verbose_name or field.name
            try:
                comma_fields = [
                    'total_expected_export_value',
                    'total_expected_non_export_value',
                ]
                value = getattr(self.win1, field_name)
                if field_name in comma_fields:
                    value = "£{:,}".format(value)
                self.assertEquals(
                    win_dict[csv_name],
                    CSVView()._val_to_str(value),
                )
            except AssertionError as exc:
                try:
                    display_fn = getattr(
                        self.win1, "get_{0}_display".format(field_name)
                    )
                    self.assertEquals(
                        win_dict[csv_name],
                        CSVView()._val_to_str(display_fn()),
                    )
                except (AttributeError, AssertionError):
                    if field_name == 'date':
                        self.assertEquals(
                            win_dict[csv_name],
                            str(getattr(self.win1, field_name))[:10],
                        )
                    elif field_name == 'created':
                        self.assertEquals(
                            win_dict[csv_name],
                            str(getattr(self.win1, field_name))[:10],
                        )
                    else:
                        raise Exception(exc)
