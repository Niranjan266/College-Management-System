"""
Django settings for college_management_system project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import dj_database_url
import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-dev-only-do-not-use-in-production',
)

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False on Vercel so a public deployment never leaks tracebacks and
# settings on an error page, and to True locally for development.
DEBUG = os.environ.get(
    'DEBUG', 'False' if os.environ.get('VERCEL') else 'True'
).lower() not in ('false', '0', 'no')

ALLOWED_HOSTS = ['*']  # Vercel terminates on its own domain; hosts are validated upstream

CSRF_TRUSTED_ORIGINS = [
    'https://lms.niranjand.in',
    'https://college-management-system-lovat.vercel.app',
    'https://*.vercel.app',
]

# Vercel proxies requests over HTTP internally, so Django must be told the
# original request was HTTPS or every POST will fail CSRF origin checks.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Application definition

INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # My Apps
    'main_app.apps.MainAppConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Third Part Middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # My Middleware
    'main_app.middleware.LoginCheckMiddleWare',
]

ROOT_URLCONF = 'college_management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['main_app/templates'], #My App Templates
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

WSGI_APPLICATION = 'college_management_system.wsgi.application'


# Database
# SQLite locally; Postgres in production. Vercel's filesystem is read-only, so
# a normal SQLite file cannot be used there.
#
# Vercel's storage integrations each inject a different variable name, so check
# all the common ones rather than DATABASE_URL alone:
#   Neon      -> DATABASE_URL, DATABASE_URL_UNPOOLED
#   Supabase  -> POSTGRES_URL, POSTGRES_URL_NON_POOLING
DATABASE_URL = (
    os.environ.get('DATABASE_URL')
    or os.environ.get('POSTGRES_URL')
    or os.environ.get('DATABASE_URL_UNPOOLED')
    or os.environ.get('POSTGRES_URL_NON_POOLING')
)

# True when running on Vercel with no real database attached. In that mode the
# app falls back to a throwaway SQLite file in /tmp (the only writable path),
# seeded from the demo fixture on cold start by wsgi.py. Good enough to browse
# the demo; writes vanish when the instance is recycled. Attaching a Postgres
# database under Vercel Storage flips this off automatically.
EPHEMERAL_DEMO_DB = bool(os.environ.get('VERCEL')) and not DATABASE_URL

if EPHEMERAL_DEMO_DB:
    DB_URL = 'sqlite:////tmp/db.sqlite3'
else:
    DB_URL = DATABASE_URL or f'sqlite:///{BASE_DIR / "db.sqlite3"}'

DATABASES = {
    'default': dj_database_url.parse(
        DB_URL,
        conn_max_age=600,
        conn_health_checks=True,  # serverless reuses instances; verify before use
        ssl_require=bool(DATABASE_URL),
    )
}

if EPHEMERAL_DEMO_DB:
    # Sessions must NOT live in the throwaway database: each serverless instance
    # gets its own /tmp, so a DB-backed session would log the user out as soon as
    # a request landed on a different instance. Signed cookies survive that.
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'


# Password validation

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

LANGUAGE_CODE = 'en-us'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# On Vercel the project directory is read-only. /tmp is the only writable path,
# so uploads land there to avoid 500s -- but they are WIPED between requests.
# For uploads that actually persist, move to S3/Cloudinary via django-storages.
if os.environ.get('VERCEL'):
    MEDIA_ROOT = '/tmp/media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'main_app.CustomUser'
AUTHENTICATION_BACKENDS = ['main_app.EmailBackend.EmailBackend']
TIME_ZONE = 'Asia/Kolkata'

# Session Configuration for Remember Me functionality
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds (default)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # This will be overridden by remember me
SESSION_SAVE_EVERY_REQUEST = True  # Save session on every request to extend expiry

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True

# Google reCAPTCHA on the login page. Both must be set for it to be enforced;
# leave them unset to disable the captcha (required for the public demo, since
# a site key only works on the domains it was registered for).
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
