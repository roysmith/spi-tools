"""
Django settings for tools_app project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from configparser import ConfigParser
import os
from pathlib import Path
import re
import sys
import datetime
import tools_app.git
from uuid import uuid4

# True if running unit tests
TESTING = 'manage.py' in sys.argv[0]


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
LOG_DIR = os.path.join(os.environ.get('HOME'), 'logs/django')
PROFILE_DIR = LOG_DIR

# This is horribly ugly; we need to not call git.get_info() here during
# testing becasue otherwise it gets called before test_git can patch it.
VERSION_ID = 'TESTING VERSION_ID' if TESTING else tools_app.git.get_info()

SERVER_START_TIME_UTC = datetime.datetime.utcnow()


# Intuit our toolforge tool name from the file system path.
m = re.match(r'.*/(?P<tool_name>[^/]*)/www/python/src', BASE_DIR)
TOOL_NAME = m.group('tool_name') if m else 'unknown'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = TOOL_NAME.lower().endswith('-dev')

ALLOWED_HOSTS = [
    '127.0.0.1',
    'tools.wmflabs.org',
    'spi-tools.toolforge.org',
    'spi-tools-dev.toolforge.org',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cat_checker',
    'search',
    'spi',
    'api',
    'pageutils',
    'wiki_interface',
    'tools_app.apps.ToolsAppConfig',
    'social_django',
    'debug_toolbar',
]

MIDDLEWARE = [
    'log_request_id.middleware.RequestIDMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django_tools.middlewares.ThreadLocal.ThreadLocalMiddleware',
    'tools_app.middleware.RequestAugmentationMiddleware',
    'tools_app.middleware.LoggingMiddleware',
]


# WARNING: some keys may not be usable on non-redis backends.  See
# https://docs.djangoproject.com/en/2.2/topics/cache/#cache-key-transformation

# This configuration uses a short timeout and invalidates every cache
# entry on every server restart.
REDIS_CACHE = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://tools-redis.svc.eqiad.wmflabs:6379/0',
        'TIMEOUT': 300,
        'KEY_PREFIX': str(uuid4()),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
DUMMY_CACHE = {
     'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }

CACHES = {
    'default': DUMMY_CACHE if TESTING else REDIS_CACHE,
    'dummy': DUMMY_CACHE,
    }

DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
DJANGO_REDIS_LOGGER = 'tools_app.redis'


ROOT_URLCONF = 'tools_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'tools_app.context_preprocessors.debug',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'tools_app.jinja2.environment',
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'social_core.backends.mediawiki.MediaWiki',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_MEDIAWIKI_KEY = os.environ.get('MEDIAWIKI_KEY')
SOCIAL_AUTH_MEDIAWIKI_SECRET = os.environ.get('MEDIAWIKI_SECRET')
SOCIAL_AUTH_MEDIAWIKI_URL = 'https://meta.wikimedia.org/w/index.php'
SOCIAL_AUTH_MEDIAWIKI_CALLBACK = 'https://%s.toolforge.org/oauth/complete/mediawiki/' % TOOL_NAME

# This seems to be needed when using social-auth-app-django > 3.1.0
# See https://github.com/python-social-auth/social-app-django/issues/256
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['groups']

# For use with mwclient library
MEDIAWIKI_SITE_NAME = 'example.com' if TESTING else 'en.wikipedia.org'
MEDIAWIKI_USER_AGENT = f'{TOOL_NAME} (toolforge)'

# It would be neater to use django.urls.reverse() here, but that's
# apparently not available when this is executed.
LOGIN_URL = '/oauth/login/mediawiki'

# Given that social-auth does ?next= processing, it's not clear this
# does anything in our setup.
LOGIN_REDIRECT_URL = 'home'

WSGI_APPLICATION = 'tools_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files setup.  For more information, see:
#   https://wikitech.wikimedia.org/wiki/Portal:Toolforge/Tool_Accounts
#   https://docs.djangoproject.com/en/2.2/howto/static-files
STATIC_URL = f'//tools-static.wmflabs.org/{TOOL_NAME}/'
STATIC_ROOT = f'{WWW_DIR}/static/'

# Unused?
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o711

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda x: False,
    }

os.environ['PYTHONASYNCIODEBUG'] = '1' if DEBUG else '0'

LOG_NAME = 'django-test.log' if TESTING else 'django.log'
LOG_LEVEL = 'INFO' if 'dev' in TOOL_NAME else 'INFO'
LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"


ELASTICSEARCH_CONFIG_FILE = Path.home() / '.elasticsearch.ini'
if ELASTICSEARCH_CONFIG_FILE.exists():
    ELASTICSEARCH_CONFIG = ConfigParser()
    ELASTICSEARCH_CONFIG.read(ELASTICSEARCH_CONFIG_FILE)
    ELASTICSEARCH = {
        'user': ELASTICSEARCH_CONFIG.get('elasticsearch', 'user'),
        'password': ELASTICSEARCH_CONFIG.get('elasticsearch', 'password'),
        'server': 'elasticsearch.svc.tools.eqiad1.wikimedia.cloud:80',
        'index': 'spi-tools-dev-es-index',
    }
else:
    ELASTICSEARCH = {}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, LOG_NAME),
            'when': 'D',
            'backupCount': 7,
            'utc': True,
            'filters': ['request_id'],
            'formatter': 'file_formatter',
        },
        # Hack to get real-time logging, as a work-around to T256426 and T256482,
        # but disable in testing due to https://code.djangoproject.com/ticket/29186
        'bastion': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        } if TESTING else {
            'level': 'DEBUG',
            'class': 'logging.handlers.SocketHandler',
            'host': 'tools-sgebastion-11',
            'port': 23001,
        },
    },
    'filters': {
        'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        }
    },
    'formatters': {
        'file_formatter': {
            'format': '%(asctime)s [%(request_id)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'spi': {
            'handlers': ['file', 'bastion'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'wiki_interface': {
            'handlers': ['file', 'bastion'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tools_app': {
            'handlers': ['file', 'bastion'],
            'level': 'INFO',
            'propagate': True,
        },
        'urllib3': {
            'handlers': ['file', 'bastion'],
            'level': 'ERROR',
            'propagate': True,
        },
        'asyncio': {
            'handlers': ['file', 'bastion'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
