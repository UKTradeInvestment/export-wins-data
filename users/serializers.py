from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.timezone import now

from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from .models import User, LoginFailure


class LoggingAuthTokenSerializer(AuthTokenSerializer):
    """ As DRF AuthTokenSerializer, but prevent login after many failures """

    WINDOW = 5  # Minutes of wait time before we allow attempts again
    STRIKES = 3  # Number of failed logins before we complain

    def validate(self, attrs):
        """ Get authenticated user or raise exception """

        email = attrs.get("username")
        window_start = datetime.utcnow() - relativedelta(minutes=self.WINDOW)

        failures = LoginFailure.objects.filter(
            email=email, created__gt=window_start).count()

        if failures >= self.STRIKES:
            raise serializers.ValidationError(
                "Too many failed logins.  Please wait at least {} minutes and "
                "try again.".format(self.WINDOW)
            )

        try:
            attrs = AuthTokenSerializer.validate(self, attrs)
            User.objects.filter(pk=attrs["user"].pk).update(last_login=now())
            return attrs
        except Exception as e:
            LoginFailure.objects.create(email=email)
            raise e


class LoggedInUserSerializer(serializers.ModelSerializer):

    name = SerializerMethodField()
    permitted_applications = SerializerMethodField()

    def get_name(self, obj):
        return getattr(obj, 'name', obj.email)

    def get_permitted_applications(self, obj):
        request = self.context['request']
        return request.session.get('_abc_permitted_applications', {})

    class Meta:
        model = User
        fields = ('email', 'last_login', 'name', 'permitted_applications')
