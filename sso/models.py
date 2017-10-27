from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.db.models import QuerySet
from django.utils.timezone import now
from django_extensions.db.fields import CreationDateTimeField
from django.conf import settings


class ADFSUser(AbstractBaseUser):
    """ For SAML2 SSO """

    USERNAME_FIELD = "email"

    email = models.EmailField(unique=True)


class AuthorizationStateManager(models.Manager):

    def _delete_expired(self):
        self.get_queryset().expired().delete()

    def check_state(self, state):
        self._delete_expired()
        return self.get_queryset().valid().filter(state=state).exists()

    def get_next_url(self, state):
        state = self.get_queryset().valid().filter(state=state).last()
        if state:
            return state.next_url

        return None


class AuthorizationStateQuerySet(QuerySet):

    def _get_cutoff_datetime(self):
        """
        gets the cutoff time for state objects
        :return: now - ~1 hour
        """
        cutoff = settings.OAUTH2_STATE_TIMEOUT_SECONDS
        return now() - timedelta(seconds=cutoff)

    def _get_valid_filter(self):
        return dict(created__gte=self._get_cutoff_datetime())

    def valid(self):
        return self.filter(**self._get_valid_filter())

    def expired(self):
        return self.exclude(**self._get_valid_filter())


class AuthorizationState(models.Model):

    state = models.CharField(max_length=255, db_index=True)
    next_url = models.CharField(max_length=255, null=True)
    created = CreationDateTimeField('created', db_index=True)

    objects = AuthorizationStateManager.from_queryset(
        AuthorizationStateQuerySet)()
