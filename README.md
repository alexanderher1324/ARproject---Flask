# ARproject Flask App 🚀

A Flask-based social media scheduler web app that allows users to:

✅ Register / Login  
✅ Connect their Instagram account  
✅ Schedule Instagram posts  
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

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install Flask Flask-WTF Flask-Login Flask-SQLAlchemy
   ```
3. (Optional) set environment variables:
   - `SECRET_KEY` – secret key for Flask sessions.
   - `DATABASE_URL` – SQLAlchemy connection string. Defaults to SQLite `app.db`.
4. Run the development server:
   ```bash
   python BD.py
   ```
5. Open your browser at `http://localhost:5000`.

The dashboard and authentication pages are under the `UI` folder.
