# College Management System — run & deploy

## Run locally

From the project root, with the venv active:

```
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The file is `manage.py` — not `manange.py`.

Open http://127.0.0.1:8000/ and log in with an **email address** (this project
uses a custom user model where email is the login field, not a username).

Create an admin account with:

```
python manage.py createsuperuser
```

Locally the app uses SQLite (`db.sqlite3`). That file is gitignored, so a fresh
clone starts with an empty database.

---

## Deploy to Vercel (lms.niranjand.in)

### 1. Create a Postgres database

**SQLite does not work on Vercel** — the filesystem is read-only, so every write
(login, add student, mark attendance) would fail. Create a free Postgres database
on [Neon](https://neon.tech) or [Supabase](https://supabase.com) and copy the
connection string.

### 2. Set environment variables in Vercel

Project → Settings → Environment Variables:

| Name | Value |
| --- | --- |
| `DATABASE_URL` | `postgres://user:pass@host/dbname` from Neon/Supabase |
| `SECRET_KEY` | A fresh 50+ character random string |
| `DEBUG` | `False` |
| `EMAIL_HOST_USER` | Gmail address used for password-reset mail |
| `EMAIL_HOST_PASSWORD` | Gmail **app password**, not the account password |

Generate a secret key with:

```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Run the migrations and load the demo data

Vercel does not run migrations for you. From your machine, once:

```
set DATABASE_URL=postgres://user:pass@host/dbname
python manage.py migrate
python manage.py loaddata demo_data
```

`demo_data` is `main_app/fixtures/demo_data.json` — the courses, subjects,
attendance records, results, feedback and notifications from the original local
SQLite database, plus these accounts:

| Role | Email | Password |
| --- | --- | --- |
| Superuser | lms@niranjand.in | admin |
| Admin (demo) | admin@admin.com | admin |
| Staff | staffone@staff.com | staffone |
| Student | studentone@student.com | studentone |
| Student | studenttwo@student.com | studenttwo |
| Student | studentthree@student.com | studentthree |
| Student | studentfour@student.com | studentfour |

The staff and student rows are shown on the login page and fill the form when
clicked. Re-running `loaddata demo_data` resets the demo back to this state.

> These are public credentials on a public site. Anyone can log in as admin and
> change or delete the data. Do not put anything real behind them.

### reCAPTCHA

The login page's captcha is disabled unless you set both `RECAPTCHA_SITE_KEY`
and `RECAPTCHA_SECRET_KEY`. It has to stay off for the demo: a Google site key
only works on the domains it was registered for, and the keys that used to be
hardcoded in `views.py` belong to the original author's deployment, so login
would fail on `lms.niranjand.in` with no way to recover.

### 4. Deploy

Import the GitHub repo in Vercel. It auto-detects Django from `manage.py`,
reads the entrypoint from `WSGI_APPLICATION`, and runs `collectstatic`
automatically because `STATIC_ROOT` is set. Then add `lms.niranjand.in` under
Project → Settings → Domains and point the DNS record at Vercel.

`CSRF_TRUSTED_ORIGINS` in `settings.py` already includes `lms.niranjand.in`.

### Known limitation: file uploads

Profile picture uploads write to `MEDIA_ROOT`, which on Vercel is `/tmp` and is
**wiped between requests**. Uploads will appear to succeed and then 404.

To fix properly, add `django-storages` with S3 or Cloudinary:

```
pip install django-storages[s3]
```

and set the `default` backend in the `STORAGES` setting in `settings.py`.
Until then, avoid relying on profile pictures in production.
