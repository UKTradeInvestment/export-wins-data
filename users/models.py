from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    name = models.CharField(max_length=128)
    email = models.EmailField(unique=True)

    is_staff = models.BooleanField(
        "Staff status",
        default=False,
        help_text="Designates whether the user can log into the admin site."
    )
    is_active = models.BooleanField(
        "Active",
        default=True,
        help_text="Designates whether this user can log into the primary site."
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = UserManager()

    def __init__(self, *args, **kwargs):
        AbstractBaseUser.__init__(self, *args, **kwargs)
        PermissionsMixin.__init__(self, *args, **kwargs)

    def __str__(self):
        return "{0} <{1}>".format(self.name, self.email)

    def get_short_name(self):
        return self.name

    def get_username(self):
        return self.email


class LoginFailure(models.Model):

    email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return "{} at {}".format(self.email, self.created)
