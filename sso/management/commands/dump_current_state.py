from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from sso.management.commands.parser_utils import parse_csv, format_user_state


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("users_file", type=str, help="path to a csv list of export wins users")

    def handle(self, *args, **options):

        filename = options["users_file"]

        migration_users = parse_csv(filename)

        user_model = get_user_model()

        for migration_user in sorted(migration_users, key=lambda u: u.future_email):
            if not migration_user.future_active:
                user = user_model.objects.get(pk=migration_user.id)
                state = format_user_state(user)
                self.stdout.write(state)
