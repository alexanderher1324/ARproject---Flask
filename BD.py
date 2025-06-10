import os
from flask import Flask, render_template, redirect, url_for, session, flash
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from auth import auth  # import blueprint
from models import db, User  # your models and db setup

app = Flask(__name__, template_folder='UI')

app.secret_key = os.getenv('SECRET_KEY') or 'supersecretkey'

# CSRF Protection
csrf = CSRFProtect(app)

# Register auth blueprint with /auth prefix
app.register_blueprint(auth, url_prefix='/auth')

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('auth.login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    # Just redirect to auth.logout to keep logic consistent
    return redirect(url_for('auth.logout'))


if __name__ == '__main__':
    app.run(debug=True)
