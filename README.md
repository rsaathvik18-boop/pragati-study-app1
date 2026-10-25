# PRAGATI — Read Test Improve (Python Cloud App)
Created by Saathvik Ryali

This is an improved Flask web application starter with password-based accounts (NO OTP), server-side database storage, a responsive student dashboard, notes, tasks, syllabus topic tracking, a sample quiz, test score history, progress reports, optional AI study coach, admin overview, and installable PWA metadata.

## Features
- Email + password sign-up/sign-in. Passwords are stored as secure password hashes; no OTP is used.
- SQL database via Flask-SQLAlchemy. Local default is SQLite; set `DATABASE_URL` to PostgreSQL in hosted deployment for shared cloud persistence.
- Per-account notes, tasks, topic tracking, test results, profile and progress.
- Responsive layout, mobile navigation, app manifest and home-screen install support.
- Optional OpenAI-powered Study Coach. AI is not enabled until the owner configures an API key.
- Admin summary for the account whose email matches `ADMIN_EMAIL` at registration time.

## Run locally (Windows)
1. Install Python 3.11+ from https://www.python.org/downloads/ (tick **Add Python to PATH**).
2. Extract the ZIP and open Command Prompt inside the `PRAGATI_Cloud_App` folder.
3. Run:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

4. Open http://127.0.0.1:5000

For local use, a `pragati.db` SQLite file is created in the Flask instance folder. Do not delete it if you want to keep local records.

## Deploy online with Render + PostgreSQL
1. Create a GitHub account and a new repository, e.g. `pragati-study-app`.
2. Upload the contents of this project folder to the repository (files at repository root: `app.py`, `requirements.txt`, `render.yaml`, `Procfile`, `templates/`, `static/`).
3. Sign in to Render and create a Blueprint from that repository. Review the services and database described in `render.yaml`, then deploy. If Render asks for a plan, choose one that supports the database and web service; pricing/free availability can change.
4. Set `ADMIN_EMAIL` to the email you will use to create your account. Register that account after deployment; admin status is assigned when the account is created.
5. For the AI Study Coach, optionally add `OPENAI_API_KEY` as a secret environment variable in Render. Do not put API keys in the code or commit them to GitHub. AI usage can incur provider charges.
6. Open the public `https://...onrender.com` address given by Render. Send that link to friends on WhatsApp.

### If deploying without the Blueprint
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Environment variables: `SECRET_KEY` (long random secret), `COOKIE_SECURE=true`, `DATABASE_URL` (PostgreSQL connection string), `ADMIN_EMAIL` (your email), optional `OPENAI_API_KEY`, optional `OPENAI_MODEL=gpt-4.1-mini`.

## WhatsApp sharing message
PRAGATI — Read Test Improve 📚
I made a study app for notes, tasks, syllabus tracking, practice tests and progress.
Open it here: [PASTE YOUR DEPLOYED LINK]
Created by Saathvik Ryali

## Important limitations / production checklist
- This is a working starter, not a security-audited production product. Before a broad public launch, add rate limiting, CSRF protection for browser forms, email verification/password reset, privacy policy/terms, account deletion/export workflow, monitoring, backups, and security review.
- No OTP or SMS verification is implemented, as requested. Email/password authentication means users should choose unique strong passwords.
- AI is optional and disabled until an API key is configured. Never commit the key to GitHub; store it as a secret in hosting settings. AI calls may cost money and should be subject to usage limits before public release.
- The built-in sample quiz is only a demo. The syllabus topic tracker lets students add their own topics; its contents are not a complete or officially verified CBSE/JEE/NEET/university syllabus. Verify against the current official syllabus.
- PWA install support requires HTTPS and a compatible browser. Core account features require internet; private pages and API responses are intentionally not cached offline.
- Set `ADMIN_EMAIL` before creating the admin account. If that account already exists, set its admin flag through a controlled database migration/admin procedure rather than recreating accounts.
- Cloud storage works only when deployed with a persistent PostgreSQL database. Do not use ephemeral local SQLite for a public multi-user deployment.
