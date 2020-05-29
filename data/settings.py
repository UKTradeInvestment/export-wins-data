import json
import logging
import os
import shutil
import sys
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
import dj_database_url
from dotenv import find_dotenv, load_dotenv

from core.types import HawkScope

load_dotenv(find_dotenv(), verbose=True)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_ROOT)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.getenv("DEBUG", False))

STAGING = bool(os.getenv("STAGING", False))

TEST_RUNNER = os.getenv('TEST_RUNNER', 'django.test.runner.DiscoverRunner')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# As app is running behind a host-based router supplied by Heroku or other
# PaaS, we can open ALLOWED_HOSTS
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # misc 3rd party
    "django_extensions",
    "raven.contrib.django.raven_compat",
    "trackstats",

    # local apps
    "core.apps.CoreConfig",
    "mi.apps.MiConfig",
    "wins.apps.WinsConfig",
    "users.apps.UsersConfig",
    "sso.apps.SsoConfig",
    "fixturedb.apps.FixtureDBConfig",
    "fdi.apps.InvestmentConfig",
    "activity_stream.apps.ActivityStreamConfig",
    "datasets.apps.DatasetConfig",
    "csvfiles",

    # drf
    "rest_framework",
    "rest_framework.authtoken",
]

MIDDLEWARE = [
    'core.middleware.HttpsSecurityMiddleware',
    'alice.middleware.SignatureRejectionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sso.middleware.saml2.SSOAuthenticationMiddleware',
    'sso.middleware.permission_denied.Metadata403',
    'sso.middleware.oauth2.OAuth2IntrospectToken',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggerMiddleware',
]

ROOT_URLCONF = 'data.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'data.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
# https://devcenter.heroku.com/articles/getting-started-with-python#provision-a-database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:////{0}'.format(os.path.join(BASE_DIR, 'db.sqlite3'))
    )
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_URL = '/static/'

# User stuffs
AUTH_USER_MODEL = "users.User"
LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/"

# Application authorisation
# used in signature middleware to determine if API request is signed by a
# server with shared secret, and if so which one.
UI_SECRET = os.getenv("UI_SECRET")
ADMIN_SECRET = os.getenv("ADMIN_SECRET")
MI_SECRET = os.getenv("MI_SECRET")
DATA_SECRET = os.getenv("DATA_SECRET")
assert len(set([UI_SECRET, ADMIN_SECRET, MI_SECRET, DATA_SECRET])) == 4, "secrets must be different"

# DataHub API
DH_TOKEN_URL = os.getenv("DH_TOKEN_URL")
DH_METADATA_URL = os.getenv("DH_METADATA_URL")
DH_INVEST_URL = os.getenv("DH_INVEST_URL")
DH_CLIENT_ID = os.getenv("DH_CLIENT_ID")
DH_CLIENT_SECRET = os.getenv("DH_CLIENT_SECRET")

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "alice.authentication.NoCSRFSessionAuthentication",
    )
}

# Mail stuffs
FEEDBACK_ADDRESS = os.getenv("FEEDBACK_ADDRESS")
SENDING_ADDRESS = os.getenv("SENDING_ADDRESS")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = bool(os.getenv("EMAIL_USE_TLS"))
EMAIL_USE_SSL = bool(os.getenv("EMAIL_USE_SSL"))
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT")) if os.getenv(
    "EMAIL_TIMEOUT") else None
EMAIL_SSL_KEYFILE = os.getenv("EMAIL_SSL_KEYFILE")
EMAIL_SSL_CERTFILE = os.getenv("EMAIL_SSL_CERTFILE")
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

# ABC OAuth2 settings

# one of 'saml2' or 'oauth2', defaults to saml2
SSO_PREFER_AUTH = os.getenv('SSO_PREFER_AUTH', 'oauth2')

OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH2_TOKEN_FETCH_URL = os.getenv("OAUTH2_TOKEN_FETCH_URL")
OAUTH2_USER_PROFILE_URL = os.getenv("OAUTH2_USER_PROFILE_URL")
OAUTH2_AUTH_URL = os.getenv("OAUTH2_AUTH_URL")
OAUTH2_STATE_TIMEOUT_SECONDS = int(
    os.getenv('OAUTH2_STATE_TIMEOUT_SECONDS', '3600'))
OAUTH2_INTROSPECT_TOKEN = os.getenv("OAUTH2_INTROSPECT_TOKEN")
OAUTH2_INTROSPECT_URL = os.getenv("OAUTH2_INTROSPECT_URL")
OAUTH2_INTROSPECT_INTERVAL = int(
    os.getenv("OAUTH2_INTROSPECT_INTERVAL", '600'))

# Amazon S3 settings for CSV
AWS_KEY_CSV_READ_ONLY_ACCESS = os.getenv("AWS_KEY_CSV_READ_ONLY_ACCESS")
AWS_SECRET_CSV_READ_ONLY_ACCESS = os.getenv("AWS_SECRET_CSV_READ_ONLY_ACCESS")
AWS_REGION_CSV = os.getenv("AWS_REGION_CSV")
AWS_BUCKET_CSV = os.getenv("AWS_BUCKET_CSV", "csv.exportwins.dev")
AWS_KEY_CSV_UPLOAD_ACCESS = os.getenv(
    'AWS_KEY_CSV_UPLOAD_ACCESS')
AWS_SECRET_CSV_UPLOAD_ACCESS = os.getenv(
    'AWS_SECRET_CSV_UPLOAD_ACCESS')

BASEDIR = os.path.dirname(os.path.abspath(__file__))

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", 'True') == 'True'

# deleted wins from these users will not show up in deleted wins CSV
IGNORE_USERS = [
    'adam.malinowski@digital.bis.gov.uk',
    'daniel.quinn@digital.bis.gov.uk',
    'mateusz.lapsa-malawski@digital.bis.gov.uk',
    'paul.mccomb@ukti.gsi.gov.uk',
    'rob.sommerville@digital.bis.gov.uk',
    'christine.leaver@ukti.gsi.gov.uk',
    'gino.golluccio@ukti.gsi.gov.uk',
    'adrian.woodcock@digital.trade.gov.uk',
    'graham.veal@digital.trade.gov.uk',
    'sekhar.panja@digital.trade.gov.uk',
    'darren.mccormac@digital.trade.gov.uk',
    'emma.jackson@digital.trade.gov.uk',
]

# allow access to API in browser for dev
API_DEBUG = bool(os.getenv("API_DEBUG", False))

# Sentry
RAVEN_CONFIG = {
    "dsn": os.getenv("SENTRY_DSN"),
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    # 'release': raven.fetch_git_sha(os.path.dirname(__file__)),
}

if DEBUG:
    logger_level = 'DEBUG'
    handler_level = 'DEBUG'
    handler_options = {}
    django_request_logger_level = 'WARNING'
else:
    logger_level = 'INFO'
    handler_level = 'INFO'
    handler_options = {'stream': sys.stdout}
    django_request_logger_level = 'DEBUG'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            **{
                'level': handler_level,
                'class': 'logging.StreamHandler',
            },
            **handler_options
        },
        'json': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': django_request_logger_level,
            'propagate': True,
        },
        'core.middleware': {
            'handlers': ['json'],
            'level': logger_level,
            'propagate': True,
        },
        '': {
            'handlers': ['console'],
            'level': logger_level,
            'propagate': False,
        },
    }
}

# only show critical log message when running tests
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    logging.disable(logging.CRITICAL)

FIXTURE_DIRS = (
    '/fdi/fixtures/',
)

# django countries only uses ISO countries. Wikipedia says, "XK is a
# 'user assigned' ISO 3166 code not designated by the standard, but used by
# the European Commission, Switzerland, the Deutsche Bundesbank..."
# adding Global (XG) to deal with global HVCs
COUNTRIES_OVERRIDE = {
    'XK': 'Kosovo',
    'XG': 'Global',
    'FK': 'Falkland Islands',
    'CZ': 'Czech Republic',
}

# Hawk Authentication
HAWK_RECEIVER_NONCE_EXPIRY_SECONDS = 60
HAWK_RECEIVER_CREDENTIALS = {}


def _add_hawk_credentials(id_env_name, key_env_name, scopes):
    id_ = os.getenv(id_env_name, default=None)

    if not id_:
        return

    if id_ in HAWK_RECEIVER_CREDENTIALS:
        raise ImproperlyConfigured(
            'Duplicate Hawk access key IDs detected. All access key IDs should be unique.',
        )

    HAWK_RECEIVER_CREDENTIALS[id_] = {
        'key': os.getenv(key_env_name),
        'scopes': scopes,
    }


_add_hawk_credentials(
    'DATA_HUB_ACCESS_KEY_ID',
    'DATA_HUB_SECRET_ACCESS_KEY',
    (HawkScope.data_hub, ),
)

_add_hawk_credentials(
    'ACTIVITY_STREAM_ACCESS_KEY_ID',
    'ACTIVITY_STREAM_SECRET_ACCESS_KEY',
    (HawkScope.activity_stream, ),
)

_add_hawk_credentials(
    'DATA_FLOW_API_ACCESS_KEY_ID',
    'DATA_FLOW_API_SECRET_ACCESS_KEY',
    (HawkScope.data_flow_api, ),
)

_add_hawk_credentials(
    'HAWK_ACCESS_KEY_ID',
    'HAWK_SECRET_ACCESS_KEY',
    (HawkScope.data_flow_api, HawkScope.activity_stream, ),
)

HAWK_IP_WHITELIST = os.getenv('HAWK_IP_WHITELIST', default='')
HAWK_NONCE_EXPIRY_SECONDS = 60


def get_redis_instance():
    """
    Helper to switch redis instance with enviroment varible.
    We need this because export-wins-data is runing in cluster mode 
    to help switch with minimum down time we use enviroment varibles.
    """
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])
    if len(vcap_services['redis']) == 1:
        return vcap_services['redis'][0]['credentials']

    REDIS_SERVICE_NAME = os.getenv('REDIS_SERVICE_NAME')
    if not REDIS_SERVICE_NAME:
        raise ImproperlyConfigured('REDIS_SERVICE_NAME must be set if there are multiple instances of redis.')
    redis_service = [r for r in vcap_services['redis'] if r['name'] == REDIS_SERVICE_NAME][0]
    return redis_service['credentials']


redis_credentials = get_redis_instance()


redis_uri = redis_credentials['uri']


def _build_redis_url(base_url, db_number=0, **query_args):
    encoded_query_args = urlencode(query_args)
    return f'{base_url}/{db_number}?{encoded_query_args}'


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': _build_redis_url(redis_uri, 0),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'export-wins-data',
    },
}

IMPORT_MATCH_ID_TO_WIN_BATCH_SIZE = int(os.getenv('IMPORT_MATCH_ID_TO_WIN_BATCH_SIZE', 500))

COMPANY_MATCHING_SERVICE_BASE_URL = os.getenv('COMPANY_MATCHING_SERVICE_BASE_URL', default=None)
COMPANY_MATCHING_HAWK_ID = os.getenv('COMPANY_MATCHING_HAWK_ID', default=None)
COMPANY_MATCHING_HAWK_KEY = os.getenv('COMPANY_MATCHING_HAWK_KEY', default=None)


is_rediss = redis_uri.startswith('rediss://')
url_args = {'ssl_cert_reqs': 'CERT_REQUIRED'} if is_rediss else {}
celery_redis_url = _build_redis_url(redis_uri, 1, **url_args)
CELERY_RESULT_BACKEND = celery_redis_url
CELERY_BROKER_URL = celery_redis_url
