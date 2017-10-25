import json
import os
import textwrap

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intword
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models.aggregates import Sum
from django.utils import timezone

from users.models import User

from ...models import Win, CustomerResponse


class Command(BaseCommand):
    """ Emails stats of Wins and Users to date (optional JSON) """

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output the statistics in JSON format."
        )
        parser.add_argument(
            "--show-all",
            action="store_true",
            help="Don't exclude staff users."
        )

    def handle(self, *args, **options):

        wins = Win.objects.all()
        confirmations = CustomerResponse.objects.all()
        users = User.objects.all()
        one_week_ago = timezone.now() - relativedelta(weeks=1)

        stats = {
            "wins": {
                "total": wins.count(),
                "total-export-funds": wins.aggregate(
                    total=Sum("total_expected_export_value"))["total"],
                "total-non-export-funds": wins.aggregate(
                    total=Sum("total_expected_non_export_value"))["total"],
                "confirmed": confirmations.count(),
                "total-confirmed-export-funds": wins.filter(confirmation__isnull=False).aggregate(
                    total=Sum("total_expected_export_value"))["total"],
                "total-confirmed-non-export-funds": wins.filter(confirmation__isnull=False).aggregate(
                    total=Sum("total_expected_non_export_value"))["total"],

            },
            "users": {
                "total-active": users.filter(
                    last_login__gt=one_week_ago).count(),
                "total-creating-wins": users.exclude(
                    wins__isnull=True).distinct().count(),
                "total": users.count(),
            }
        }

        if options["json"]:
            return self._handle_json(stats)

        stats_txt = self._generate_txt(stats)
        send_to_addresses = os.getenv("STATS_EMAILS").split(',')

        send_mail(
            "Export Wins statistics",
            stats_txt,
            settings.SENDING_ADDRESS,
            send_to_addresses,
        )

    def _generate_txt(self, stats):
        wins = stats["wins"]
        users = stats["users"]
        stats_txt = """
            Export Wins input by officers:

            Total wins generated: {}
            Total expected export value: {}
            Total expected non-export value: {}


            -----


            Export wins customers have responded to:

            Total wins responded to: {}
            Total expected export value: {}
            Total expected non export value: {}


            -----


            Users (officers):

            Total logged in last week: {}
            Total who have submitted wins: {}
            Total who have been issued password: {}

            """.format(
            wins["total"],
            "£{}".format(intword(wins["total-export-funds"])),
            "£{}".format(intword(wins["total-non-export-funds"])),
            wins["confirmed"],
            "£{}".format(intword(wins["total-confirmed-export-funds"])),
            "£{}".format(
                intword(wins["total-confirmed-non-export-funds"])),
            users["total-active"],
            users["total-creating-wins"],
            users["total"]
        )
        return textwrap.dedent(stats_txt)

    @staticmethod
    def _handle_json(stats):
        return json.dumps(stats, separators={",", ":"})
