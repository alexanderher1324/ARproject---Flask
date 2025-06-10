import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from auth import auth
from models import db, User, Post

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


@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_post():
    if request.method == 'POST':
        caption = request.form.get('caption')
        image_url = request.form.get('image_url')
        time_str = request.form.get('scheduled_time')
        try:
            scheduled_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M')
        except (TypeError, ValueError):
            flash('Invalid date/time format.')
            return redirect(url_for('schedule_post'))

        new_post = Post(user_id=current_user.id,
                        caption=caption,
                        image_url=image_url,
                        scheduled_time=scheduled_time)
        db.session.add(new_post)
        db.session.commit()
        flash('Post scheduled successfully!')
        return redirect(url_for('dashboard'))

    return render_template('schedule_post.html')


@app.route('/posts')
@login_required
def view_past_posts():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.scheduled_time.desc()).all()
    return render_template('past_posts.html', posts=posts)


# No need for /logout route here — handled by auth.logout


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
