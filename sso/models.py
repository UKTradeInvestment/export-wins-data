from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class ADFSUser(AbstractBaseUser):
    """ For SAML2 SSO """

    USERNAME_FIELD = "email"

    email = models.EmailField(unique=True)
