import os
from flask import Flask, render_template, redirect, url_for
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from auth import auth
from models import db, User

app = Flask(__name__, template_folder='UI')

app.secret_key = os.getenv('SECRET_KEY') or 'supersecretkey'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

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
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)


# No need for /logout route here — handled by auth.logout


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
