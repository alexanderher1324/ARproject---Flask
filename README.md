# ARproject Flask App 🚀

A Flask-based social media scheduler web app that allows users to:

✅ Register / Login with email and password confirmation
✅ Connect Instagram, TikTok or YouTube accounts
✅ Schedule posts for any platform
✅ View past posts
✅ Track post analytics and follower growth
✅ Upload videos to generate a thumbnail and custom preview clip (10/20/30 seconds)
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
   This installs the official `openai` library which the app uses for generating caption suggestions.
3. Copy `.env.example` to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```
   Set environment variables inside `.env` (the application loads this file automatically and will fall back to `.env.example` if needed):
   - `SECRET_KEY` – **required** secret key for Flask sessions. The app exits if this is not provided.
   - `DATABASE_URL` – (optional) SQLAlchemy connection string. Defaults to SQLite `app.db`.
   - `OPENAI_API_KEY` – (optional) enables automatic caption suggestions.
   - `INSTAGRAM_CLIENT_ID` and `INSTAGRAM_CLIENT_SECRET` – enable Instagram OAuth.
   - `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` – enable TikTok OAuth.
   - `YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET` – enable YouTube OAuth.
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

All timestamps stored in the database are saved in **UTC** for consistency
across deployments.

The dashboard and authentication pages are under the `UI` folder.

## Connecting social accounts

Open the **Connect Social Accounts** page from the dashboard and use the
provided buttons to authorize Instagram, TikTok or YouTube via OAuth. After you
approve access, the obtained tokens are stored automatically and the dashboard
will show the platforms as connected.

## Analytics

Use the **Analytics** tab on the dashboard to view engagement for your posts and
track follower counts over time. Choose the desired platform from the dropdown
menu to filter results.
