import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from auth import auth
from models import db, User, Post
from dotenv import load_dotenv

load_dotenv(".env.example")  # Load environment variables from .env file

app = Flask(__name__, template_folder='UI')
# Removed redundant load_dotenv() call to avoid conflicts
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable not set")
app.config['SECRET_KEY'] = SECRET_KEY

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
    instagram_connected = bool(current_user.instagram_access_token)
    tiktok_connected = bool(current_user.tiktok_access_token)
    return render_template('dashboard.html',
                           username=current_user.username,
                           instagram_connected=instagram_connected,
                           tiktok_connected=tiktok_connected)

@app.route('/connect', methods=['GET', 'POST'])
@login_required
def connect_accounts():
    if request.method == 'POST':
        current_user.instagram_access_token = request.form.get('instagram_token')
        current_user.ig_user_id = request.form.get('instagram_user_id')
        current_user.tiktok_access_token = request.form.get('tiktok_token')
        current_user.tiktok_user_id = request.form.get('tiktok_user_id')
        db.session.commit()
        flash('Accounts connected!')
        return redirect(url_for('dashboard'))

    return render_template('connect_accounts.html',
                           instagram_token=current_user.instagram_access_token,
                           instagram_user_id=current_user.ig_user_id,
                           tiktok_token=current_user.tiktok_access_token,
                           tiktok_user_id=current_user.tiktok_user_id)


@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_post():
    if request.method == 'POST':
        caption = request.form.get('caption')
        image_url = request.form.get('image_url')
        uploaded_file = request.files.get('image_file')
        date_str = request.form.get('scheduled_date')
        time_str = request.form.get('scheduled_time')
        platforms = request.form.getlist('platforms')
        try:
            scheduled_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        except (TypeError, ValueError):
            flash('Invalid date/time format.')
            return redirect(url_for('schedule_post'))
        
        if uploaded_file and uploaded_file.filename:
            extension = uploaded_file.filename.rsplit('.', 1)[-1].lower()
            if extension in ALLOWED_EXTENSIONS:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(uploaded_file.filename)}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(file_path)
                image_url = url_for('static', filename=f'uploads/{filename}')
            else:
                flash('Unsupported file type.')
                return redirect(url_for('schedule_post'))

        if not platforms:
            flash('Please select at least one platform.')
            return redirect(url_for('schedule_post'))

        for platform in platforms:
            if platform == 'instagram' and not current_user.instagram_access_token:
                flash('Please connect your Instagram account first.')
                return redirect(url_for('connect_accounts'))
            if platform == 'tiktok' and not current_user.tiktok_access_token:
                flash('Please connect your TikTok account first.')
                return redirect(url_for('connect_accounts'))

            new_post = Post(user_id=current_user.id,
                            caption=caption,
                            image_url=image_url,
                            scheduled_time=scheduled_time,
                            platform=platform)
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
