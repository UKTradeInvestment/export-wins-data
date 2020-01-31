import collections
import csv
import zipstream
from zipfile import ZIP_DEFLATED
from operator import attrgetter
import mimetypes

from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.core.exceptions import ValidationError
from django.db import connection, models
from django.db.models import F, Func
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.views.decorators.gzip import gzip_page

from rest_framework import permissions
from rest_framework.views import APIView

from alice.authenticators import IsDataTeamServer
from ..constants import BREAKDOWN_TYPES
from ..models import Advisor, Breakdown, CustomerResponse, Notification, Win
from ..serializers import CustomerResponseSerializer, WinSerializer
from users .models import User


class HasUnusablePassword(Func):
    function = 'LEFT'
    template = f'%(function)s(%(expressions)s, 1) != \'{UNUSABLE_PASSWORD_PREFIX}\''


class CSVView(APIView):
    """ Endpoint returning CSV of all Win data, with foreign keys flattened """

    permission_classes = (permissions.IsAdminUser,)
    # cache for speed
    win_fields = WinSerializer().fields
    customerresponse_fields = CustomerResponseSerializer().fields
    IGNORE_FIELDS = ['responded', 'sent', 'country_name', 'updated',
                     'complete', 'type', 'type_display',
                     'export_experience_display', 'location']
    _choices_cache = {}

    def __init__(self, **kwargs):
        # cache some stuff to make flat CSV. like prefetch but works easily
        # with .values()
        self.users_map = {u.id: u for u in User.objects.all()}
        prefetch_tables = [
            ('advisors', Advisor),
            ('breakdowns', Breakdown),
            ('confirmations', CustomerResponse),
            ('notifications', Notification),
        ]
        self.table_maps = {}
        for table, model in prefetch_tables:
            prefetch_map = collections.defaultdict(list)
            instances = model.objects.all()
            if table == 'notifications':
                instances = instances.filter(type='c').order_by('created')
            for instance in instances:
                prefetch_map[instance.win_id].append(instance)
            self.table_maps[table] = prefetch_map
        super().__init__(**kwargs)

    def _extract_breakdowns(self, win):
        """ Return list of 10 tuples, 5 for export, 5 for non-export """

        breakdowns = self.table_maps['breakdowns'][win['id']]
        retval = []
        for db_val, name in BREAKDOWN_TYPES:

            # get breakdowns of given type sorted by year
            type_breakdowns = [b for b in breakdowns if b.type == db_val]
            type_breakdowns = sorted(type_breakdowns, key=attrgetter('year'))

            # we currently solicit 5 years worth of breakdowns, but historic
            # data may have no input for some years
            for index in range(5):
                try:
                    breakdown = "{0}: £{1:,}".format(
                        type_breakdowns[index].year,
                        type_breakdowns[index].value,
                    )
                except IndexError:
                    breakdown = None

                retval.append((
                    "{0} breakdown {1}".format(name, index + 1),
                    breakdown,
                ))

        return retval

    def _confirmation(self, win):
        """ Add fields for confirmation """

        if win['id'] in self.table_maps['confirmations']:
            confirmation = self.table_maps['confirmations'][win['id']][0]
        else:
            confirmation = None

        values = [
            ('customer response recieved',
             self._val_to_str(bool(confirmation)))
        ]
        for field_name in self.customerresponse_fields:
            if field_name in ['win']:
                continue

            model_field = self._get_customerresponse_field(field_name)
            if confirmation:
                if model_field.choices:
                    display_fn = getattr(
                        confirmation, "get_{0}_display".format(field_name)
                    )
                    value = display_fn()
                else:
                    value = getattr(confirmation, field_name)
            else:
                value = ''

            model_field_name = model_field.verbose_name or model_field.name
            if model_field_name == 'created':
                csv_field_name = 'date response received'
                if value:
                    value = value.date()  # just want date
            else:
                csv_field_name = model_field_name

            values.append((csv_field_name, self._val_to_str(value)))
        return values

    def _get_model_field(self, model, name):
        return next(
            filter(lambda field: field.name == name, model._meta.fields)
        )

    @cached_property
    def _customer_response_fields_map(self):
        return {f.name: f for f in CustomerResponse._meta.fields}

    def _get_customerresponse_field(self, name):
        """ Get field specified in CustomerResponse model """
        return self._customer_response_fields_map[name]

    @cached_property
    def _win_fields_map(self):
        return {f.name: f for f in Win._meta.fields}

    def _get_win_field(self, name):
        """ Get field specified in Win model """
        return self._win_fields_map[name]

    def _val_to_str(self, val):
        if val is True:
            return 'Yes'
        elif val is False:
            return 'No'
        elif val is None:
            return ''
        else:
            return str(val)

    def _choices_dict(self, choices):
        """
        Memoizes result of conversion of a choices object to a dict.
        Cache is stored on the instance
        """
        key = id(choices)
        result = self._choices_cache.get(key)
        if not result:
            result = self._choices_cache[key] = dict(choices)
        return result

    def _get_win_data(self, win):
        """ Take Win dict, return ordered dict of {name -> value} """

        # want consistent ordering so CSVs are always same format
        win_data = collections.OrderedDict()

        # local fields
        for field_name in self.win_fields:
            if field_name in self.IGNORE_FIELDS:
                continue

            model_field = self._get_win_field(field_name)
            if field_name == 'user':
                value = str(self.users_map[win['user_id']])
            elif field_name == 'created':
                value = win[field_name].date()  # don't care about time
            elif field_name == 'cdms_reference':
                # numeric cdms reference numbers should be prefixed with
                # an apostrophe to make excel interpret them as text
                value = win[field_name]
                try:
                    int(value)
                except ValueError:
                    pass
                else:
                    if value.startswith('0'):
                        value = "'" + value
            else:
                value = win[field_name]
            # if it is a choicefield, do optimized lookup of the display value
            if model_field.choices and value:
                try:
                    choices = getattr(model_field.choices, 'superset', model_field.choices)
                    value = self._choices_dict(choices)[value]
                except KeyError as e:
                    if model_field.attname == 'hvc':
                        value = value
                    else:
                        raise e
            else:
                comma_fields = [
                    'total_expected_export_value',
                    'total_expected_non_export_value',
                    'total_expected_odi_value',
                ]
                if field_name in comma_fields:
                    value = "£{:,}".format(value)

            model_field_name = model_field.verbose_name or model_field.name
            win_data[model_field_name] = self._val_to_str(value)

        # remote fields
        win_data['contributing advisors/team'] = (
            ', '.join(map(str, self.table_maps['advisors'][win['id']]))
        )

        # get customer email sent & date
        notifications = self.table_maps['notifications'][win['id']]
        # old Wins do not have notifications
        email_sent = bool(notifications or win['complete'])
        win_data['customer email sent'] = self._val_to_str(email_sent)
        if notifications:
            win_data['customer email date'] = str(
                notifications[0].created.date())
        elif win['complete']:
            win_data['customer email date'] = '[manual]'
        else:
            win_data['customer email date'] = ''

        win_data.update(self._extract_breakdowns(win))
        win_data.update(self._confirmation(win))

        return win_data

    def _make_flat_wins_csv(self, deleted=False):
        """ Make CSV of all Wins, with non-local data flattened """

        if deleted:
            wins = Win.objects.inactive()
        else:
            wins = Win.objects.all()

        if deleted:
            # ignore users should show up in normal CSV
            wins = wins.exclude(
                user__email__in=settings.IGNORE_USERS
            )

        stringio = Echo()
        yield stringio.write(u'\ufeff').encode('utf-8')

        if wins.count():
            wins_iter = wins.values().iterator()
            win_datas = (self._get_win_data(win) for win in wins_iter)
            first = next(win_datas)
            csv_writer = csv.DictWriter(stringio, first.keys())
            header = dict(zip(csv_writer.fieldnames, csv_writer.fieldnames))
            yield csv_writer.writerow(header).encode('utf-8')
            yield csv_writer.writerow(first).encode('utf-8')
            for win_data in win_datas:
                yield csv_writer.writerow(win_data).encode('utf-8')

    def _make_user_csv(self):
        users = User.objects.all().values(
            'name',
            'email',
            joined=F('date_joined'),
            has_export_wins_access=HasUnusablePassword(F('password'))
        ).iterator()
        stringio = Echo()
        first = next(users)
        csv_writer = csv.DictWriter(stringio, first.keys())
        yield stringio.write(u'\ufeff').encode('utf-8')
        header = dict(zip(csv_writer.fieldnames, csv_writer.fieldnames))
        yield csv_writer.writerow(header).encode('utf-8')
        yield csv_writer.writerow(first).encode('utf-8')
        for user_dict in users:
            yield csv_writer.writerow(user_dict).encode('utf-8')

    def _make_plain_csv(self, table):
        """ Get CSV of table """

        cursor = connection.cursor()
        cursor.execute("select * from wins_{};".format(table))
        csv_writer = csv.writer(Echo())
        header = [i[0] for i in cursor.description]
        yield csv_writer.writerow(header).encode('utf-8')
        for row in cursor:
            yield csv_writer.writerow(row).encode('utf-8')

    def get(self, request, format=None):
        zf = zipstream.ZipFile(mode='w', compression=ZIP_DEFLATED)
        for table in ['customerresponse', 'notification', 'advisor']:
            csv_iter = self._make_plain_csv(table)
            zf.write_iter(table + 's.csv', csv_iter)

        full_csv_iter = self._make_flat_wins_csv()
        zf.write_iter('wins_complete.csv', full_csv_iter)

        full_csv_del_iter = self._make_flat_wins_csv(deleted=True)
        zf.write_iter('wins_deleted_complete.csv', full_csv_del_iter)

        user_csv_iter = self._make_user_csv()
        zf.write_iter('users.csv', user_csv_iter)

        response = StreamingHttpResponse(zf, content_type=mimetypes.types_map['.csv'])

        return response


class Echo(object):
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


@method_decorator(gzip_page, name='dispatch')
class CompleteWinsCSVView(CSVView):

    permission_classes = (IsDataTeamServer,)

    def _make_flat_wins_csv(self, deleted=False):
        """ Make CSV of all Wins, with non-local data flattened """

        if deleted:
            wins = Win.objects.inactive()
        else:
            wins = Win.objects.all()

        if deleted:
            # ignore users should show up in normal CSV
            wins = wins.exclude(
                user__email__in=settings.IGNORE_USERS
            )

        wins = wins.values()

        for win in wins:
            yield self._get_win_data(win)

    def _make_flat_wins_csv_stream(self, win_data_generator):
        stringio = Echo()
        yield stringio.write(u'\ufeff')
        first = next(win_data_generator)
        csv_writer = csv.DictWriter(stringio, first.keys())
        header = dict(zip(first.keys(), first.keys()))
        yield csv_writer.writerow(header)
        yield csv_writer.writerow(first)

        for win_data in win_data_generator:
            yield csv_writer.writerow(win_data)

    def streaming_response(self, filename):
        resp = StreamingHttpResponse(
            self._make_flat_wins_csv_stream(self._make_flat_wins_csv()),
            content_type=mimetypes.types_map['.csv'],
        )
        resp['Content-Disposition'] = f'attachent; filename={filename}'
        return resp

    def get(self, request, format=None):
        return self.streaming_response(f'wins_complete_{now().isoformat()}.csv')


@method_decorator(gzip_page, name='dispatch')
class CurrentFinancialYearWins(CompleteWinsCSVView):

    permission_classes = (permissions.IsAdminUser,)
    end_date = None

    def _make_flat_wins_csv(self, **kwargs):
        """
        Make CSV of all completed Wins till now for this financial year, with non-local data flattened
        remove all rows where:
        1. total expected export value = 0 and total non export value = 0 and total odi value = 0
        2. date created = today (not necessary if this task runs before end of the day for next day download)
        3. customer email sent is False / No
        4. Customer response received is not from this financial year
        Note that this view removes win, notification and customer response entries
        that might have been made inactive in duecourse
        """
        with connection.cursor() as cursor:
            if self.end_date:
                cursor.execute(
                    "SELECT id FROM wins_completed_wins_fy where created <= %s", (self.end_date,))
            else:
                cursor.execute("SELECT id FROM wins_completed_wins_fy")
            ids = cursor.fetchall()

        wins = Win.objects.filter(id__in=[id[0] for id in ids]).values()

        for win in wins:
            yield self._get_win_data(win)

    def get(self, request, format=None):
        end_str = request.GET.get("end", None)
        if end_str:
            try:
                self.end_date = models.DateField().to_python(end_str)
            except ValidationError:
                self.end_date = None

        return self.streaming_response(f'wins_current_fy_{now().isoformat()}.csv')
