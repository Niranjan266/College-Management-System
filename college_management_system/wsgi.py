"""
WSGI config for college_management_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_management_system.settings')

application = get_wsgi_application()


def _seed_ephemeral_demo_database():
    """Build the demo database in /tmp on cold start.

    Only runs on Vercel when no Postgres is attached. Vercel's filesystem is
    read-only apart from /tmp, and /tmp starts empty on every new serverless
    instance, so the schema and demo rows have to be recreated here rather than
    shipped in the bundle. Takes a couple of seconds, once per cold start.

    Attaching a database under Vercel Storage sets DATABASE_URL, which turns
    this off and makes the data durable instead.
    """
    from django.conf import settings

    if not getattr(settings, 'EPHEMERAL_DEMO_DB', False):
        return

    db_path = settings.DATABASES['default']['NAME']
    if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
        return

    from django.core.management import call_command

    print(f'Seeding ephemeral demo database at {db_path} ...')
    call_command('migrate', verbosity=0, interactive=False)
    call_command('loaddata', 'demo_data', verbosity=1)
    print('Demo database ready.')


try:
    _seed_ephemeral_demo_database()
except Exception as exc:  # never let seeding take the whole app down
    print(f'WARNING: could not seed demo database: {exc!r}')
