from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from sso.management.commands.parser_utils import parse_csv, format_user_state


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-c", "--commit_changes", action="store_true", help="commit any changes to the users file")
        parser.add_argument("users_file", type=str, help="path to a csv list of export wins users")

    def handle(self, *args, **options):
        commit_changes = options["commit_changes"]

        if commit_changes:
            self.stdout.write(self.style.WARNING("Commit changes is True"))

        filename = options["users_file"]

        migration_users = parse_csv(filename)

        user_model = get_user_model()

        for migration_user in migration_users:
            if not migration_user.future_active:
                user = user_model.objects.get(pk=migration_user.id)

                if commit_changes:
                    user.is_active = migration_user.future_active
                    user.sso_user_id = None
                    user.email = ">" + user.email
                    user.save()

                state = format_user_state(user)
                self.stdout.write(state)
