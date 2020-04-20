import datetime
import pytz

from wins.models import Win

utc = pytz.UTC

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from sso.management.commands.parser_utils import parse_csv, format_user_state, MigrationUser


class BadFutureEmailException(BaseException):
    pass


class BadFutureSSOIdException(BaseException):
    pass


def update_single_user(migration_user):
    user_model = get_user_model()

    try:
        user = user_model.objects.get(pk=migration_user.id)
        return user
    except user_model.DoesNotExist:
        return None


def merge_users(migration_users: MigrationUser):
    user_model = get_user_model()
    target_email = migration_users[0].future_email
    target_sso_id = migration_users[0].sso_user_id

    # both future emails need to be the same or we cant easily handle this
    for single_user in migration_users:
        if target_email != single_user.future_email:
            raise BadFutureEmailException(f"target emails do not match {target_email}")

        if target_sso_id != single_user.sso_user_id:
            raise BadFutureSSOIdException(f"target SSO ids do not match {target_sso_id}")

    users = []
    # Check that we can find users for each id - any exceptions just bounce to the caller..
    for single_user in migration_users:
        user = user_model.objects.get(pk=single_user.id)
        users.append(user)

    # we are merging down to the user with the most recent login
    min_date = utc.localize(datetime.datetime(datetime.MINYEAR, 1, 1))
    ordered_users = sorted(users, reverse=True, key=lambda u: u.last_login or min_date)
    # so the target user is the first in the list
    target_user = ordered_users[0]

    target_user.email = target_email
    target_user.sso_user_id = target_sso_id

    for other_user in users[:1]:
        other_user.email = ">" + other_user.email
        other_user.sso_user_id = None
        other_user.is_active = False

        # Move wins to target user
        other_user_wins = other_user.wins.all()


    return ordered_users


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-c", "--commit_changes", action="store_true", help="commit any changes to the users file")
        parser.add_argument("users_file", type=str, help="path to a csv list of export wins users")
        parser.add_argument("-f", "--filter_sso_id", help="only run against a specific SSO_USER_ID")

    def handle(self, *args, **options):
        commit_changes = options["commit_changes"]
        filter_sso_user_id = options['filter_sso_id']

        if commit_changes:
            self.stdout.write(self.style.WARNING("Commit changes is True"))

        filename = options["users_file"]

        migration_users = parse_csv(filename)

        # Group the users by SSO id
        users_hashed_by_sso_id = {}
        for migrated_user in migration_users:

            if filter_sso_user_id and migrated_user.sso_user_id != filter_sso_user_id:
                continue

            if migrated_user.sso_user_id not in users_hashed_by_sso_id:
                users_hashed_by_sso_id[migrated_user.sso_user_id] = []

            users_hashed_by_sso_id[migrated_user.sso_user_id].append(migrated_user)

        for key in users_hashed_by_sso_id:
            should_merge = len(users_hashed_by_sso_id[key]) > 1

            if should_merge:
                try:
                    target_users = merge_users(users_hashed_by_sso_id[key])
                    for target_user in target_users:
                        self.stdout.write(format_user_state(target_user))
                except BadFutureEmailException as e:
                    self.stdout.write(self.style.ERROR(f"can't handle future emails {e}"))
                continue

            continue
            # Not merged just update the user
            single_user = users_hashed_by_sso_id[key][0]
            updated_user = update_single_user(users_hashed_by_sso_id[key][0])

            if updated_user:
                self.stdout.write(format_user_state(updated_user))
            else:
                self.stdout.write(
                    self.style.ERROR(f' {single_user.id} {single_user.current_email} not found in database'))
