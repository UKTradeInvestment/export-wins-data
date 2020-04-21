from os import path
import csv

from django.core.management.base import CommandError


class MigrationUser:

    @staticmethod
    def parse_csv_bool(text):
        return text.lower() in ["true"]

    def __init__(self, csv_row):
        self.id = csv_row['EW_ID']
        self.current_email = csv_row['EW_CURRENT_EMAIL']
        self.future_email = csv_row['EW_FUTURE_EMAIL']
        self.sso_user_id = csv_row['EW_SSO_UUID']
        self.current_active = MigrationUser.parse_csv_bool(csv_row['EW_CURRENT_ACTIVE'])
        self.future_active = MigrationUser.parse_csv_bool(csv_row['EW_FUTURE_ACTIVE'])

    def __str__(self):
        return f"{self.id} {self.current_email}->{self.future_email} {self.current_active}->{self.future_active}"


def get_obfuscated_email_address(user):
    if user.email.startswith("!!"):
        # this user has already been migrated... ignore it?
        return user.email

    return f"!!{user.id}_{user.email.lower()}"


def get_users_hashed_by_sso_id(migration_users, filter_sso_user_id):
    users_hashed_by_sso_id = {}
    users_with_sso_ids = list(filter(lambda u: u.sso_user_id, migration_users))
    for migrated_user in users_with_sso_ids:
        if filter_sso_user_id and migrated_user.sso_user_id != filter_sso_user_id:
            continue

        if migrated_user.sso_user_id not in users_hashed_by_sso_id:
            users_hashed_by_sso_id[migrated_user.sso_user_id] = []

        users_hashed_by_sso_id[migrated_user.sso_user_id].append(migrated_user)

    return users_hashed_by_sso_id


def format_user_state(user):
    # yes.. i know this will be slow
    win_count = user.wins.count()
    return f"{user.id},{user.email},{user.is_active},{user.sso_user_id or ''},{user.last_login or ''},{win_count}"


def parse_csv(filename):
    full_path = path.abspath(filename)

    if not path.exists(full_path):
        raise CommandError(f"{full_path} not found")

    parsed_users = []

    with open(full_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=",")
        for row in reader:
            migration_user = MigrationUser(row)
            parsed_users.append(migration_user)

    return parsed_users
