import argparse
import bz2
import csv
import os
import random
import time

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.template.loader import render_to_string

from ...models import User


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        BaseCommand.__init__(self, *args, **kwargs)
        self.words = self._get_words()

        self.do_mail = True
        self.ignore_existing = True
        self.resend = False

    def add_arguments(self, parser):

        parser.add_argument("--name", type=str)

        parser.add_argument("--email", type=str)

        parser.add_argument(
            "--resend",
            action="store_true",
            help="If a given email address exists, reset the password. "
                 "Otherwise raise an exception."
        )

        parser.add_argument(
            "--from-file",
            type=argparse.FileType('r'),
            help='The path to a CSV file in the following format: '
                 '"name","email".  This option is exclusive to use of --name '
                 'and --email.'
        )

        parser.add_argument(
            "--print",
            action="store_true",
            help="Create user and password, but just print it don't send."
        )

    def handle(self, *args, **options):
        """ Handle command line flags, and then do the business """

        if not (options["name"] and options["email"]):
            if not options["from_file"]:
                raise CommandError(
                    "Either --from-file or a combination of --name and "
                    "--email are required"
                )

        if options["print"]:
            self.do_mail = False

        if options["resend"]:
            self.resend = True

        if options["from_file"]:
            return self._handle_batch(options["from_file"])

        return self._handle_single(options["name"], options["email"])

    def _handle_batch(self, file_handle):
        for row in csv.reader(file_handle):
            if row:
                self._handle_user(
                    row[0].strip(),
                    self._sanitise_email(row[1]),
                    self._generate_password()
                )

    def _handle_single(self, name, email):
        self._handle_user(
            name.strip(),
            self._sanitise_email(email),
            self._generate_password()
        )

    @staticmethod
    def _sanitise_email(address):
        address = address.strip().lower()
        validate_email(address)
        return address

    @staticmethod
    def send(email, password):
        subject = "Export Wins Login Credentials"
        body = render_to_string(
            "users/email/password-issued.email",
            {
                "email": email,
                "password": password,
                "feedback_address": settings.FEEDBACK_ADDRESS,
            },
        )

        send_mail(
            subject,
            body,
            settings.SENDING_ADDRESS,
            (email,),
        )

        time.sleep(1)

    def _generate_password(self):
        """ Make a password from selection of random words """

        separator = random.choice(("-", ",", ".", "_"))
        return "{}{}{}{}{}{}{}".format(
            random.choice(self.words), separator,
            random.choice(self.words), separator,
            random.choice(self.words), separator,
            random.choice(self.words),
        )

    @staticmethod
    def _get_words():
        """ Get words for use in password from a pre-filtered file """

        path = os.path.join(settings.BASE_DIR, "users", "words.bz2")
        with bz2.open(path) as f:
            return [str(w.strip(), "utf-8") for w in f.readlines()]

    def _handle_user(self, name, email, password):
        """ Get or create the user, set password and either send or print """

        user, user_exists = self._get_or_create_user(name, email)

        if user_exists:
            if self.resend:
                print("Resending", user)
            elif self.ignore_existing:
                print(
                    "Ignoring",
                    user,
                    '-',
                    user.email,
                    '-',
                    'date added:', user.date_joined.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
                return
            else:
                raise Exception("user already exists")

        user.set_password(password)
        user.save()

        if self.do_mail:
            self.stdout.write("Sending mail to {}".format(name))
            self.send(email, password)
        else:
            self.stdout.write(
                "\nThe credentials for {} are: \n"
                "  Email:    {}\n"
                "  Password: {}\n\n".format(name, email, password)
            )

    def _get_or_create_user(self, name, email):
        try:
            user = User.objects.get(email=email)
            return (user, True)
        except User.DoesNotExist:
            # always want to create a new user if none exists
            user = User.objects.create(name=name, email=email)
            return (user, False)
