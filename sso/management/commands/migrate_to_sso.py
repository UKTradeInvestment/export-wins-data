from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from sso.management.commands.parser_utils import parse_csv, format_user_state


def update_single_user(migration_user):
    user_model = get_user_model()

    try:
        user = user_model.objects.get(pk=migration_user.id)
        return user
    except user_model.DoesNotExist:
        return None


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
        # self.stdout.write(f"there are {len(migration_users)} in {filename}")
        future_active_users = list(filter(lambda x: x.future_active, migration_users))

        # self.stdout.write(f"{len(future_active_users)} will be active after migration")

        # Group the users by SSO id
        users_hashed_by_sso_id = {}
        for migrated_user in future_active_users:
            if migrated_user.sso_user_id not in users_hashed_by_sso_id:
                users_hashed_by_sso_id[migrated_user.sso_user_id] = []

            users_hashed_by_sso_id[migrated_user.sso_user_id].append(migrated_user)

        for key in users_hashed_by_sso_id:
            should_merge = len(users_hashed_by_sso_id[key]) > 1

            if should_merge:
                print(f"{key} {len(users_hashed_by_sso_id[key])} ")
                continue

            # Not merged just update the user
            updated_user = update_single_user(users_hashed_by_sso_id[key][0])

            if updated_user:
                self.stdout.write(format_user_state(updated_user))
            else:
                self.stdout.write(self.style.ERROR('not updated'))
