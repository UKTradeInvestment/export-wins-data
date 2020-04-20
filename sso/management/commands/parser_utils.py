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


def format_user_state(user):
    # yes.. i know this will be slow
    win_count = user.wins.count()
    return f"\"{user.id}\",\"{user.email}\",\"{user.is_active}\",\"{user.sso_user_id}\",\"{user.last_login}\", \"{win_count}\""


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
