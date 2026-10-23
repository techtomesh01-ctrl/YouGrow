# YouGrow — Hindi + English Creator Discovery (Starter)

Separate project scaffold. This does **not** modify CINEMA WORLD and is **not deployed**.

## Included
- Flask web app with PostgreSQL schema/bootstrap
- Registration/login with password hashing and CSRF tokens
- Public creator/channel directory (users choose to open YouTube themselves)
- Points ledger restricted to permitted in-app tasks; no rewards for YouTube subscriptions, views, likes, comments, or shares
- Admin moderation screen (requires `ADMIN_EMAIL` and admin account setup)
- Native Kotlin Android starter UI (not a WebView), with Home / Discover / Tasks / Profile navigation
- Basic tests and Render blueprint

## Run locally
1. Python 3.11+
2. `python -m venv .venv`
3. Activate the venv, then `pip install -r requirements.txt`
4. Set `DATABASE_URL` to a PostgreSQL connection string, `SECRET_KEY` to a long random secret, and `ADMIN_EMAIL` to the admin email.
5. Run `flask --app app init-db`
6. Run `flask --app app run`

For production, use HTTPS and a managed PostgreSQL database. Never commit secrets.

## Important limitations
- This is a starter scaffold, not a production-certified service.
- Admin user promotion is a manual database operation (see `docs/admin-setup.sql`).
- Referral rewards are intentionally not automated in this starter.
- Do not offer points, money, prizes, or reciprocal tasks for YouTube engagement. Users may discover channels, but YouTube engagement remains voluntary and unrewarded.
- Native Android UI currently uses starter/demo content. Shared registration/login, approved live creator listings, moderation and points require a secure backend API connection before production use.
- GitHub Actions is configured to build a debug APK when Android files change; verify the workflow run and download its artifact from the Actions page.
- No production deployment or live URL has been created or verified by this package.
