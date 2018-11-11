"""
Django settings for website project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import json

# open config.json
with open('config.json', 'r') as f:
    config = json.load(f)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config['SECRET_KEY']

# SocialLogin: Google
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config['API_KEY']['GOOGLE_KEY']
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config['API_KEY']['GOOGLE_SECRET']
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['videosr.koreacentral.cloudapp.azure.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'videosr',
    'login',
    'dashboard',
    'payment',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'website.urls'

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
                'social_django.context_processors.backends', 
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'website.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config['DATABASE']['NAME'],
        'USER': config['DATABASE']['USER'],
        'PASSWORD': config['DATABASE']['PASSWORD'],
        'HOST': 'localhost',
        'PORT': '',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2', # Google
    'django.contrib.auth.backends.ModelBackend', # Django 기본 유저모델
]

# social login url settings
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# The URL where requests are redirected for login
# especially when using the login_required() decorator.
LOGIN_URL='login:index'
# The URL where requests are redirected after login 
# when the contrib.auth.login view gets no next parameter.
LOGIN_REDIRECT_URL='dashboard:index'
# The URL where requests are redirected after a user logs out 
# using LogoutView (if the view doesn’t get a next_page argument).
LOGOUT_REDIRECT_URL='login:index'

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'ko'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static', '')

# this directory for staticfiles which is independent from all apps.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles', '')
]

# URL prefix for each media file
MEDIA_URL = '/media/'
# Directory path to save uploaded file
MEDIA_ROOT = os.path.join(BASE_DIR, 'media', '')

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': { 
        'verbose': { 
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s", 
            'datefmt' : "%d/%b/%Y %H:%M:%S" 
        }, 
        'simple': { 
            'format': '%(levelname)s %(message)s' 
        }, 
    },

    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'log','debug.log'),     
            'formatter': 'verbose',
            'maxBytes':1024*1024*10, 
            'backupCount':5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },

        'django.request': { 
            'handlers':['file'], 
            'propagate': False, 
            'level':'INFO', 
        }, 
        
        'videosr': { 
            'handlers': ['file'], 
            'level': 'DEBUG', 
        }, 
    }
}

