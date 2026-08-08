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

# Advisory lock id, so that if several serverless instances cold-start at once
# only one of them runs the migrations.
_BOOTSTRAP_LOCK_ID = 727212


def _needs_bootstrap():
    """Return (needs_migrate, needs_seed) for the configured database."""
    from django.db import connection

    needs_migrate = 'main_app_customuser' not in connection.introspection.table_names()
    if needs_migrate:
        return True, True

    from main_app.models import CustomUser
    return False, not CustomUser.objects.exists()


def _bootstrap_database():
    """Create the schema and load the demo data if the database is empty.

    Vercel never runs `migrate` for you, and on the ephemeral SQLite fallback
    /tmp starts empty on every new instance, so without this the first query
    fails with "relation main_app_customuser does not exist".

    Only ever runs against an empty database, so it cannot clobber real data.
    """
    if not os.environ.get('VERCEL'):
        return  # locally you run migrate yourself

    from django.db import connection
    from django.core.management import call_command

    needs_migrate, needs_seed = _needs_bootstrap()
    if not (needs_migrate or needs_seed):
        return

    use_lock = connection.vendor == 'postgresql'
    if use_lock:
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_lock(%s)', [_BOOTSTRAP_LOCK_ID])
    try:
        # Re-check: another instance may have finished while we waited.
        needs_migrate, needs_seed = _needs_bootstrap()
        if needs_migrate:
            print('Bootstrapping database: running migrations ...')
            call_command('migrate', verbosity=1, interactive=False)
        if needs_seed:
            print('Bootstrapping database: loading demo data ...')
            call_command('loaddata', 'demo_data', verbosity=1)
        if needs_migrate or needs_seed:
            print('Database bootstrap complete.')
    finally:
        if use_lock:
            with connection.cursor() as cur:
                cur.execute('SELECT pg_advisory_unlock(%s)', [_BOOTSTRAP_LOCK_ID])


try:
    _bootstrap_database()
except Exception as exc:  # never let bootstrapping take the whole app down
    print(f'WARNING: database bootstrap failed: {exc!r}')
