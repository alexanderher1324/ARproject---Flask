# ARproject Flask App 🚀

A Flask-based social media scheduler web app that allows users to:

✅ Register / Login with email and password confirmation
✅ Connect Instagram or TikTok accounts
✅ Schedule posts for either platform
✅ View past posts
✅ Secure CSRF-protected login/logout flow
✅ Background scheduler for automated posting

---

## Project Structure

- `BD.py`: Application entry point configuring Flask, database, CSRF, and the auth blueprint.
- `auth.py`: Handles registration, login, and logout routes using a Flask blueprint.
- `models.py`: SQLAlchemy models including the `User` model for storing credentials.
- `UI/`: HTML templates rendered by Flask.
- `static/`: Static assets such as stylesheets.

## Usage

1. Create and activate a Python 3 virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```
   Set environment variables inside `.env` (the application loads this file automatically and will fall back to `.env.example` if needed):
   - `SECRET_KEY` – **required** secret key for Flask sessions. The app exits if this is not provided.
   - `DATABASE_URL` – (optional) SQLAlchemy connection string. Defaults to SQLite `app.db`.
4. Run the development server:
   ```bash
   python BD.py
   ```
5. Open your browser at `http://localhost:5000`.

### Updating the database schema

If you add fields to models in `models.py` after the initial `app.db` has been
created, the existing SQLite database will not automatically pick up the new
columns. In that case delete `app.db` and let the application recreate it at
startup:

```bash
rm app.db
python BD.py  # creates a fresh database with the new columns
```

For production setups you would normally use a migration tool such as
[Flask-Migrate](https://flask-migrate.readthedocs.io/) instead of deleting the
database.

The dashboard and authentication pages are under the `UI` folder.

## Connecting social accounts without OAuth

If OAuth authentication fails or cannot be used, the app still allows you to
link Instagram and TikTok accounts by manually entering access tokens. Navigate
to **Connect Social Accounts** from the dashboard. The form lets you paste the
access token and user ID for each platform:

```
<form method="POST" action="{{ url_for('connect_accounts') }}">
    <label for="instagram_token">Instagram Access Token</label>
    <input type="text" id="instagram_token" name="instagram_token" placeholder="Paste your Instagram token" />

    <label for="instagram_user_id">Instagram User ID</label>
    <input type="text" id="instagram_user_id" name="instagram_user_id" placeholder="Your Instagram user ID" />

    <label for="tiktok_token">TikTok Access Token</label>
    <input type="text" id="tiktok_token" name="tiktok_token" placeholder="Paste your TikTok token" />

    <label for="tiktok_user_id">TikTok User ID</label>
    <input type="text" id="tiktok_user_id" name="tiktok_user_id" placeholder="Your TikTok user ID" />
```

Select a platform from the drop-down to see tips on generating tokens from the
respective developer portals. After saving, the tokens are stored in the
database and your accounts will be treated as connected.
