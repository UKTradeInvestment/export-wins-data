import uuid

from django.conf import settings
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import IsAdminServer
from users.management.commands import account_creation
from users.models import User
from wins.management.commands import generate_customer_emailses
from wins.models import Win


class AdminView(APIView):
    permission_classes = (IsAdminUser, IsAdminServer)

    def _invalid(self, msg):
        return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        return Response({}, status=status.HTTP_200_OK)


class BaseUserAdminView(AdminView):

    def _get_email(self, data):
        return data['email'].strip().lower()

    def _valid_email(self, email):
        if not email:
            return False
        if '@' not in email:
            return False
        if '.' not in email:
            return False
        return True

    def _get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return False

    def _set_and_send_password(self, user):
        command = account_creation.Command()
        password = command._generate_password()
        user.set_password(password)
        user.save()
        account_creation.Command.send(user.email, password)


class AddUserView(BaseUserAdminView):

    def _valid_name(self, name):
        if not name:
            return False
        return True

    def post(self, request):
        name = request.data['name'].strip()
        email = self._get_email(request.data)

        if not self._valid_name(name):
            return self._invalid('invalid name: {}'.format(name))

        if not self._valid_email(email):
            return self._invalid('invalid email: {}'.format(email))

        if self._get_user(email):
            return self._invalid(
                'user with email {} already exists'.format(email)
            )

        user = User.objects.create(name=name, email=email)
        self._set_and_send_password(user)

        return Response({}, status=status.HTTP_201_CREATED)


class NewPasswordView(BaseUserAdminView):

    def post(self, request):
        email = self._get_email(request.data)
        user = self._get_user(email)

        if not user:
            return self._invalid(
                'user with email {} does not exist'.format(
                    request.data['email']
                )
            )

        self._set_and_send_password(user)

        return Response({}, status=status.HTTP_201_CREATED)


class BaseCustomerEmailAdminView(AdminView):

    def _get_win(self, win_id):
        try:
            return Win.objects.get(id=win_id)
        except Win.DoesNotExist:
            return False

    def _valid_win_id(self, win_id):
        try:
            uuid.UUID(win_id)
            return True
        except ValueError:
            return False

    def _get_win_id(self, data):
        return data['win_id'].strip()

    def _send_customer_email_and_notify_officers(self, win):
        command = generate_customer_emailses.Command()
        command.send_win_customer_email(win)
        command.send_officer_email(win)


class SendCustomerEmailView(BaseCustomerEmailAdminView):

    def post(self, request):
        win_id = self._get_win_id(request.data)

        if not self._valid_win_id(win_id):
            return self._invalid('invalid Win ID: {}'.format(win_id))

        win = self._get_win(win_id)
        if not win:
            return self._invalid(
                'ID {} does not match any Wins'.format(
                    request.data['win_id']
                )
            )

        self._send_customer_email_and_notify_officers(win)

        return Response({}, status=status.HTTP_201_CREATED)


class SendAdminEmailView(BaseCustomerEmailAdminView):

    def post(self, request):
        win_id = self._get_win_id(request.data)

        if not self._valid_win_id(win_id):
            return self._invalid('invalid Win ID: {}'.format(win_id))

        win = self._get_win(win_id)
        if not win:
            return self._invalid(
                'ID {} does not match any Wins'.format(
                    request.data['win_id']
                )
            )

        command = generate_customer_emailses.Command()
        customer_email_dict = command.make_customer_email_dict(win)
        send_mail(
            customer_email_dict['subject'],
            customer_email_dict['body'],
            settings.SENDING_ADDRESS,
            [settings.FEEDBACK_ADDRESS],
        )

        return Response({}, status=status.HTTP_201_CREATED)


class ChangeCustomerEmailView(BaseUserAdminView, BaseCustomerEmailAdminView):

    def post(self, request):
        win_id = self._get_win_id(request.data)
        email = self._get_email(request.data)

        if not self._valid_win_id(win_id):
            return self._invalid('invalid Win ID: {}'.format(win_id))

        if not self._valid_email(email):
            return self._invalid('invalid email: {}'.format(email))

        win = self._get_win(win_id)
        if not win:
            return self._invalid(
                'win With ID {} does not exist'.format(
                    request.data['win_ID']
                )
            )

        if win.customer_email_address == email:
            return self._invalid(
                'The customer email is already {} for Win with ID {}'.format(
                    email,
                    request.data['win_id'],
                )
            )

        win.customer_email_address = email
        win.save()

        self._send_customer_email_and_notify_officers(win)

        return Response({}, status=status.HTTP_201_CREATED)


class SoftDeleteWinView(BaseCustomerEmailAdminView):

    def post(self, request):
        win_id = self._get_win_id(request.data)

        if not self._valid_win_id(win_id):
            return self._invalid('invalid Win ID: {}'.format(win_id))

        win = self._get_win(win_id)
        if not win:
            return self._invalid(
                'ID {} does not match any Wins'.format(
                    request.data['win_id']
                )
            )

        win.soft_delete()

        return Response({}, status=status.HTTP_201_CREATED)
