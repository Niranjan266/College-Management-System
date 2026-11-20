# College ERP — College Management System

**One system for a college department, with separate logins for the head of department, teaching staff and students.**

[Live demo](https://lms.niranjand.in) · [Case study on niranjand.in](https://www.niranjand.in/projects/college-erp)

![The head of department's dashboard: totals, a staff/student chart and attendance per subject](docs/screenshots/admin-home.png)

## What it is

A college department usually keeps attendance, marks, leave requests and library loans across paper registers, spreadsheets and messages, with no single view and no control over who sees what. This app puts all of it in one place.

There are three kinds of account. The **head of department (HOD)** sets up courses, subjects, sessions, staff and students and approves leave. **Staff** take attendance, enter results and run the small library. **Students** see their own attendance, results, books and notices, and apply for leave. Each person sees and changes only what their role allows.

## Features

**Head of department**
- Dashboard with totals and charts (staff vs students, attendance per subject)
- Add, edit and remove staff, students, courses, subjects and academic sessions
- View attendance by subject and session
- Approve or reject staff and student leave requests
- Read and reply to feedback from staff and students
- Send notices to individual staff members or students

**Staff**
- Dashboard with their students, attendance taken, leave applied and subjects
- Take attendance for a subject and session, and update it later
- Add and edit results (test and exam marks per subject)
- Library: add books, issue books to students (due back in 14 days), view issued books
- Apply for leave, send feedback, read notices

**Students**
- Dashboard with attendance percentage and subject-wise attendance charts
- View attendance, results and library books
- Apply for leave, send feedback, read notices

**Everyone**
- Sign in with an email address, "Remember me" for 30 days, password reset by email
- Optional Google reCAPTCHA on the login page
- Light and dark theme toggle
- Demo accounts listed on the login page that fill the form when clicked

## Screenshots

| | |
|---|---|
| ![Staff dashboard with attendance vs leave and subject-wise attendance](docs/screenshots/staff-home.png) | ![Student dashboard with attendance percentages and charts](docs/screenshots/student-home.png) |
| Staff dashboard | Student dashboard |

![Login page with the clickable demo accounts](docs/screenshots/login.png)

## How it works

A server-rendered Django app: one Django app (`main_app`) with a view module per role, Django templates styled with Bootstrap/AdminLTE, and Chart.js for the dashboards.

```text
 Browser ──► Django (WSGI: gunicorn locally/Procfile, or Vercel)
               │
               ├─ LoginCheckMiddleWare ── which module does the requested view live in?
               │       hod_views      → HOD only
               │       staff_views    → staff only
               │       student_views  → students only
               │       anything else  → signed-out visitors go to the login page
               │
               ├─ hod_views.py / staff_views.py / student_views.py / views.py (login, logout)
               │
               ├─ Database: PostgreSQL (DATABASE_URL / POSTGRES_URL …) ─or─ SQLite
               ├─ Static:   WhiteNoise (compressed)
               └─ Email:    Gmail SMTP for password resets
```

### One account table, three roles

- A **custom user model** (`CustomUser`) logs in with an email address instead of a username, through a custom authentication backend (`EmailBackend`), and carries a `user_type` of HOD, Staff or Student.
- When an account is created, a `post_save` **signal creates the matching profile row** (`Admin`, `Staff` or `Student`) automatically, so a user always has the profile its role needs.
- **Role checks happen in one place.** `LoginCheckMiddleWare` looks at the Python module of the view being requested and sends anyone outside their area back to their own home page: students can't reach HOD or staff views, staff can't reach HOD or student views, and signed-out visitors are sent to the login page (except for the login and password-reset views).
- **Each page reads from the signed-in person's own profile.** Student views load the `Student` record for `request.user` and filter attendance, results, leave and notices by it; staff pages list only the subjects assigned to that staff member.

### Workflows

- **Leave** is saved as pending; the HOD marks it approved or rejected, and the applicant sees the status.
- **Notices** from the HOD are saved to the recipient's notification list, and the app also sends a browser push notification through Firebase Cloud Messaging to the token stored on their account.
- **Attendance** is one `Attendance` row per subject, session and date, with an `AttendanceReport` row (present/absent) per student, which is what the dashboard charts aggregate.
- **Results** store test and exam marks per student and subject; staff edit them through a class-based view (`EditResultView`).

### Built for serverless hosting

The live demo runs on Vercel, which has a read-only filesystem and no step that runs migrations. The app handles that itself:

- **The database sets itself up on first start.** On a cold start, `wsgi.py` checks whether the tables exist. Only if the database is empty does it run migrations and load the demo fixture, and on PostgreSQL it holds an **advisory lock** while doing so, so two instances starting together can't both do it. It never touches a database that already has data, and a failure is logged rather than taking the app down.
- **It still opens with no database attached.** If no database URL is set on Vercel, it falls back to a throwaway SQLite file in `/tmp` seeded from the demo fixture, and switches sessions to signed cookies so a user isn't logged out when a request lands on a different instance.
- **Any common database variable works.** Settings check `DATABASE_URL`, `POSTGRES_URL`, `DATABASE_URL_UNPOOLED` and `POSTGRES_URL_NON_POOLING` (the names Neon and Supabase integrations inject), require SSL for hosted Postgres, and turn on connection health checks because serverless instances reuse connections.
- **Safe defaults in production.** `DEBUG` defaults to off on Vercel, cookies are `Secure` when `DEBUG` is off, and the proxy's HTTPS header is trusted so CSRF origin checks pass behind Vercel.

### Known limitations

- **Uploads don't persist on Vercel.** Profile pictures go to `/tmp/media` there, which is wiped between requests. Persistent uploads need `django-storages` with S3 or Cloudinary.
- **Public demo data.** The demo accounts are public on a public site; anyone can change or delete the demo data. `python manage.py loaddata demo_data` resets it.
- **Tests and per-view checks.** There are no automated tests yet, and access control depends on which module a view lives in. The plan is an explicit role check on every view, a test for each role's access, and tighter form protection on the staff pages.

## Tech stack

| Area | Technology |
|---|---|
| Back end | Python, Django 6.1, Pillow, requests |
| Database | PostgreSQL via psycopg 3 and `dj-database-url` (production), SQLite (local) |
| Front end | Django templates, Bootstrap / AdminLTE, Chart.js, Font Awesome |
| Notifications | Firebase Cloud Messaging (browser push), Gmail SMTP (password reset) |
| Static files | WhiteNoise |
| Hosting | Vercel (live demo), gunicorn via `Procfile` |

## Getting started

**Prerequisites:** Python 3.13 (see `.python-version`) and Git.

```bash
git clone https://github.com/Niranjan266/College-Management-System.git
cd College-Management-System

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata demo_data     # optional: demo courses, subjects, attendance, results and accounts
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with an **email address**. Locally the app uses SQLite (`db.sqlite3`). To create your own admin account instead of using the demo data:

```bash
python manage.py createsuperuser
```

### Demo accounts

Loaded by `loaddata demo_data` (`main_app/fixtures/demo_data.json`) and listed on the login page:

| Role | Email | Password |
|---|---|---|
| Admin (HOD) | `admin@admin.com` | `admin` |
| Staff | `staffone@staff.com` | `staffone` |
| Student | `studentone@student.com` | `studentone` |
| Student | `studenttwo@student.com` | `studenttwo` |
| Student | `studentthree@student.com` | `studentthree` |
| Student | `studentfour@student.com` | `studentfour` |

These are public demo credentials. Don't put real data behind them.

### Environment variables

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key (a long random string in production) |
| `DEBUG` | Defaults to `True` locally and `False` on Vercel |
| `DATABASE_URL` (or `POSTGRES_URL`, `DATABASE_URL_UNPOOLED`, `POSTGRES_URL_NON_POOLING`) | PostgreSQL connection string; SQLite is used when none is set |
| `DB_SSL_REQUIRE` | Set to `0` if your Postgres provider doesn't want `sslmode=require` |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail address and app password for password-reset email |
| `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` | Turn on reCAPTCHA at login (both must be set; leave unset for the public demo, since a site key only works on the domains it was registered for) |

Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Deploying to Vercel

1. Create a PostgreSQL database (for example on Neon or Supabase). SQLite can't be written on Vercel.
2. In the Vercel project settings, set `DATABASE_URL`, `SECRET_KEY`, `DEBUG=False`, and the email variables.
3. Import the repository in Vercel. It detects Django from `manage.py`, reads the entrypoint from `WSGI_APPLICATION`, and runs `collectstatic` because `STATIC_ROOT` is set.
4. On the first request the app migrates the empty database and loads the demo data by itself. To do it manually instead:

   ```bash
   set DATABASE_URL=postgres://user:pass@host/dbname
   python manage.py migrate
   python manage.py loaddata demo_data
   ```

5. Add your domain under Project → Settings → Domains, and add it to `CSRF_TRUSTED_ORIGINS` in `settings.py` (`lms.niranjand.in` is already there).

## Project structure

```text
College-Management-System/
├── college_management_system/
│   ├── settings.py        # database selection, serverless fallbacks, email, reCAPTCHA
│   ├── urls.py            # admin, auth (password reset) and main_app routes
│   └── wsgi.py            # WSGI app + first-start database bootstrap with advisory lock
├── main_app/
│   ├── models.py          # CustomUser, role profiles, courses, subjects, attendance, results, leave, feedback, notices, library
│   ├── middleware.py      # role-based routing (LoginCheckMiddleWare)
│   ├── EmailBackend.py    # sign in by email
│   ├── views.py           # login, logout, Firebase messaging service worker
│   ├── hod_views.py       # head of department pages
│   ├── staff_views.py     # staff pages, attendance, results, library
│   ├── student_views.py   # student pages
│   ├── EditResultView.py  # class-based view for editing results
│   ├── forms.py
│   ├── fixtures/demo_data.json
│   ├── templates/         # hod_template/, staff_template/, student_template/, main_app/, registration/
│   └── static/            # AdminLTE, Chart.js, styles, images
├── Showcase/              # screenshots
├── requirements.txt
├── Procfile               # gunicorn entry point
├── HOW_TO_RUN.md          # run and deploy notes
└── LICENSE
```

## License

Released under the Apache License 2.0 — see [LICENSE](LICENSE).

This project builds on [Ansarimajid/College-ERP](https://github.com/Ansarimajid/College-ERP).

## Author

Built by Niranjan D — [niranjand.in](https://www.niranjand.in) · [GitHub](https://github.com/Niranjan266) · [LinkedIn](https://www.linkedin.com/in/niranjan266)
