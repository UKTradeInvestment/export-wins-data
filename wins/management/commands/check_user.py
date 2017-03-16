from dateutil.relativedelta import relativedelta
from time import sleep

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from users.models import User

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--emails", type=str)
        parser.add_argument("--ids", type=str)


    def handle(self, *args, **options):
        """ Quick hack to check details of system users  """

        if options['ids']:
            user_ids = options['ids'].split(',')
            for user_id in user_ids:
                user = User.objects.get(id=user_id)
                print('id:', user_id, 'name:', user.name, 'email:', user.email, 'date added:', user.date_joined.strftime("%Y-%m-%d %H:%M:%S"))
        elif options['emails']:
            emails = options['emails'].split(',')
            for email in emails:
                try:
                    user = User.objects.get(email=email.lower())
                except User.DoesNotExist:
                    print(email, 'does not exist')
                else:
                    print('email:', user.email, 'date added:', user.date_joined.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            print('Please specify --emails or --ids as comma-seperated-list')