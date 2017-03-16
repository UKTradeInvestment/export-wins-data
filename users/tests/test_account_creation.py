from io import StringIO
from unittest import mock

from django.test import TestCase

from ..management.commands.account_creation import Command
from ..models import User


class AccountCreationTestCase(TestCase):

    def test_sanitise_email_spaced(self):
        email = "test.name@example.com"
        self.assertEqual(Command._sanitise_email(email + " "), email)
        self.assertEqual(Command._sanitise_email(" " + email + " "), email)
        self.assertEqual(Command._sanitise_email(email.upper()), email)
        self.assertEqual(Command._sanitise_email(email.capitalize()), email)

    def test_generate_password(self):
        for i in range(0, 20):
            password = Command()._generate_password()
            self.assertGreaterEqual(len(password), 7 * 4 + 3, password)

    def test_create_user(self):
        path = "users.management.commands.account_creation.Command.send"
        with mock.patch(path):
            email = "test.name@example.com"
            Command()._handle_user("Name", email, "password")
            self.assertEqual(User.objects.get(email=email).name, "Name")

    def test_create_interesting_user(self):
        path = "users.management.commands.account_creation.Command.send"
        with mock.patch(path):
            email = "test.name@example.com"
            Command()._handle_user("Ναμε", email, "password")
            self.assertEqual(User.objects.get(email=email).name, "Ναμε")

    def test_handle_single(self):
        path = "users.management.commands.account_creation.Command.send"
        with mock.patch(path):
            email = "test.name@example.com"
            Command()._handle_single("Name", email)
            self.assertEqual(User.objects.get(email=email).name, "Name")

    def test_handle_batch(self):
        path = "users.management.commands.account_creation.Command.send"
        with mock.patch(path):
            file_handle = StringIO(
                '"Test Name 0","test.name0@example.com"\n'
                '"Test Name 1","test.name1@example.com"\n'
            )
            Command()._handle_batch(file_handle)
            self.assertEqual(
                User.objects.get(email="test.name0@example.com").name,
                "Test Name 0"
            )
            self.assertEqual(
                User.objects.get(email="test.name1@example.com").name,
                "Test Name 1"
            )
            self.assertEqual(User.objects.all().count(), 2)
