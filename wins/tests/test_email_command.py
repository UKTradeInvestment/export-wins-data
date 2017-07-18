from django.core.management import call_command
from django.test import TestCase

class CommandsTestCase(TestCase):
    def test_no_wins(self):
        " Test my custom command."

        args = []
        opts = {}
        call_command('email_blast', *args, **opts)
