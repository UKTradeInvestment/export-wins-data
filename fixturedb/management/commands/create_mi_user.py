from django.contrib.auth.models import Group
from django.db import transaction

from users.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Creates dummy wins in the database'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email']
        pw = User.objects.make_random_password()
        u = User.objects.create_user(
            email, password=pw)
        self.stdout.write(
            self.style.SUCCESS(
                'User {username} created with password: {pw}'.format(
                    username=u.email, pw=pw)
            )
        )
        g = Group.objects.get(name='mi_group')
        u.groups.add(g)
        u.save()
        self.stdout.write(
            self.style.SUCCESS(
                'User {username} added to {group}'.format(
                    username=u.email, group=g.name)
            )
        )
