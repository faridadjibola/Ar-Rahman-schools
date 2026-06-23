# Ar-Rahman Schools Student Management System

A Django student management system for Ar-Rahman Schools. It manages school users, student records, attendance, grades/results, fees, dashboards, reports, and student self-service access.

The project uses Django templates with HTML, CSS, and JavaScript for the current interface. PostgreSQL is supported through `DATABASE_URL`, while local development can run with SQLite.

## Current Status

This project is ready for local development, testing, and demonstration.

It is not production-ready until the deployment checklist in this file is completed.

## Tech Stack

- Python 3.13
- Django 5.2
- PostgreSQL with `psycopg`
- SQLite for local development when `DATABASE_URL` is empty
- HTML, CSS, JavaScript
- WhiteNoise for static files
- Gunicorn for production WSGI serving

## Main Features

- Login/logout authentication
- Public student signup
- Role-based access for Admin, Teacher, and Student
- Student portal for checking results, attendance, fees, and records
- Dashboard with school summary data
- Student record management
- Attendance tracking
- Results and grade tracking
- Bulk CSV upload/download for results
- Fee records and payment status
- Reports page
- Django admin panel
- Edit/delete actions for student records, attendance, results, and fees

## Important URLs

```text
Login:       http://127.0.0.1:8000/accounts/login/
Signup:      http://127.0.0.1:8000/signup/student/
Dashboard:   http://127.0.0.1:8000/
My Portal:   http://127.0.0.1:8000/portal/student/
Admin panel: http://127.0.0.1:8000/admin/
Students:    http://127.0.0.1:8000/students/
Attendance:  http://127.0.0.1:8000/attendance/
Results:     http://127.0.0.1:8000/results/
Result CSV:  http://127.0.0.1:8000/results/export/
Fees:        http://127.0.0.1:8000/fees/
Reports:     http://127.0.0.1:8000/reports/
```

## Test Accounts

These accounts are for local development only.

```text
Admin username:   admin
Admin password:   admin12345

Student username: student1
Student password: student12345
```

Change these passwords before using the system with real data.

## Student Signup

Students can create their own Ar-Rahman Schools portal account from:

```text
http://127.0.0.1:8000/signup/student/
```

The signup form creates:

- A user account with the `Student` role.
- A linked student profile.
- Login access to the student portal.

Required signup details:

- Username
- First name
- Last name
- Password
- Admission number
- Class
- Guardian name
- Guardian phone

Optional signup details:

- Email
- Date of birth
- Address

After signup, the student is automatically logged in and sent to:

```text
http://127.0.0.1:8000/portal/student/
```

Student portal features:

- View personal student record.
- Check results and grades.
- Check attendance.
- Check fee records.
- View pass/fail and attendance summary counts.

Important: at least one school class must exist before students can sign up, because every student profile must be assigned to a class.

## Project Structure

```text
accounts/
  Custom user model with Admin, Teacher, and Student roles.

academics/
  School classes, subjects, teacher profiles, student profiles,
  attendance, grade results, fee payments, forms, views, and URLs.

sms_project/
  Django project settings, root URLs, ASGI, and WSGI config.

templates/
  Shared layout, login page, dashboard, records, forms, and reports.

static/
  CSS and JavaScript used by the Django templates.

requirements.txt
  Python dependencies.

.env.example
  Example environment variables for local or deployed setup.
```

## Local Setup

From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Environment Variables

Create a `.env` file in the project root.

```text
SECRET_KEY=change-me-before-deployment
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=
```

For local SQLite development, leave `DATABASE_URL` empty.

For PostgreSQL:

```text
DATABASE_URL=postgresql://sms_user:sms_password@localhost:5432/student_management
```

## PostgreSQL Setup

Create a PostgreSQL database and user, then set `DATABASE_URL` in `.env`.

Example:

```text
DATABASE_URL=postgresql://sms_user:sms_password@localhost:5432/student_management
```

Then run:

```powershell
python manage.py migrate
```

## Role Permissions

Admin:
- Can access Django admin.
- Can create, view, edit, and delete student records.
- Can manage attendance.
- Can manage results and grades.
- Can manage fee records.
- Can view reports and dashboard data.

Teacher:
- Can view students connected to assigned subject classes.
- Can manage attendance for allowed classes.
- Can manage results for assigned subjects.
- Cannot manage fee records.
- Cannot create or delete student profiles.

Student:
- Can view their own student profile.
- Can view their own attendance.
- Can view their own results.
- Can view their own fee records.
- Can sign up through the public student signup page.
- Cannot edit or delete records.

## Recommended Data Setup Order

Use `http://127.0.0.1:8000/admin/` for the first setup.

1. Create school classes.
2. Create subjects and assign them to classes.
3. Create users.
4. Set each user's role: Admin, Teacher, or Student.
5. Create teacher profiles for teacher users.
6. Assign subjects to teacher profiles.
7. Create student profiles for student users.
8. Add attendance, results, and fee records.

Important: create the `User` first, then create the matching `StudentProfile` or `TeacherProfile`.

## Bulk Result Upload and Download

Admins and teachers can upload and download results in CSV format from the Results page.

Go to:

```text
http://127.0.0.1:8000/results/
```

Available actions:

- `Download Template`: downloads a blank CSV structure with example data.
- `Download Results`: exports the visible results to CSV.
- `Upload CSV`: imports grades from a CSV file.

Upload CSV columns:

```text
admission_no,subject_code,term,score,remarks
```

Example:

```csv
admission_no,subject_code,term,score,remarks
ADM001,MATH101,Term 1,88,Good progress
```

Import rules:

- `admission_no` must match an existing student profile.
- `subject_code` must match an existing subject.
- `term` is required.
- `score` must be a number from 0 to 100.
- `remarks` is optional.
- If a result already exists for the same student, subject, and term, it is updated.
- If no matching result exists, a new one is created.
- If any row has an error, no rows from that upload are imported.

Teacher limitation:

- Teachers can only import or export results for their assigned subjects/classes.
- Students cannot upload or download bulk result files.

## Common Commands

Run the development server:

```powershell
python manage.py runserver
```

Create migrations after model changes:

```powershell
python manage.py makemigrations
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an admin user:

```powershell
python manage.py createsuperuser
```

Check the project for errors:

```powershell
python manage.py check
```

Collect static files for production:

```powershell
python manage.py collectstatic
```

## Deployment Checklist

Before production deployment:

- Change all test account passwords.
- Set a strong `SECRET_KEY`.
- Set `DEBUG=False`.
- Set `ALLOWED_HOSTS` to the real domain or server host.
- Configure PostgreSQL using `DATABASE_URL`.
- Run `python manage.py migrate`.
- Run `python manage.py collectstatic`.
- Create a real superuser.
- Use HTTPS.
- Configure backups for PostgreSQL.
- Do not commit `.env` or `db.sqlite3`.

Example production environment:

```text
SECRET_KEY=<strong-production-secret>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Example production commands:

```powershell
python manage.py migrate
python manage.py collectstatic
gunicorn sms_project.wsgi
```

## Known Limitations

- No React frontend is included yet.
- No password reset flow is configured yet.
- No student/teacher self-registration flow is configured yet.
- Reports are basic summaries, not exportable PDFs or Excel files yet.
- Production email settings are not configured yet.
- Deployment platform files are not included yet.

## Suggested Next Improvements

- Add search and filters to students, attendance, results, and fees.
- Add CSV or Excel export for reports.
- Add printable student report cards.
- Add parent/guardian login.
- Add password reset by email.
- Add audit logs for record changes.
- Add automated tests for permissions and forms.
- Add deployment files for Render, Railway, Fly.io, or VPS hosting.
#   A r - R a h m a n - s c h o o l s  
 