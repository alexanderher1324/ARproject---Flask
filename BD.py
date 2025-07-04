import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from authlib.integrations.flask_client import OAuth
import openai
from moviepy.video.io.VideoFileClip import VideoFileClip
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError
import time
from auth import auth
from models import db, User, Post, FollowerTrend
from pathlib import Path
from dotenv import load_dotenv

# Load variables from `.env` if present. If not, fall back to `.env.example` so
# the sample app still runs with default values.
load_dotenv()
if not os.getenv("SECRET_KEY") and Path(".env.example").exists():
    load_dotenv(".env.example")

app = Flask(__name__, template_folder='UI')
# Removed redundant load_dotenv() call to avoid conflicts
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

oauth = OAuth(app)
oauth.register(
    name='instagram',
    client_id=os.getenv('INSTAGRAM_CLIENT_ID'),
    client_secret=os.getenv('INSTAGRAM_CLIENT_SECRET'),
    access_token_url='https://api.instagram.com/oauth/access_token',
    authorize_url='https://api.instagram.com/oauth/authorize',
    client_kwargs={'scope': 'user_profile,user_media'}
)

oauth.register(
    name='tiktok',
    client_id=os.getenv('TIKTOK_CLIENT_KEY'),
    client_secret=os.getenv('TIKTOK_CLIENT_SECRET'),
    access_token_url='https://open-api.tiktok.com/oauth/access_token',
    authorize_url='https://open-api.tiktok.com/platform/oauth/connect/',
    client_kwargs={'scope': 'user.info.basic,video.list'}
)

oauth.register(
    name='youtube',
    client_id=os.getenv('YOUTUBE_CLIENT_ID'),
    client_secret=os.getenv('YOUTUBE_CLIENT_SECRET'),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com',
    client_kwargs={'scope': 'https://www.googleapis.com/auth/youtube.readonly openid email',
                   'prompt': 'consent'},
    authorize_params={'access_type': 'offline'}
)

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
    youtube_connected = bool(current_user.youtube_access_token)
    return render_template('dashboard.html',
                           username=current_user.username,
                           instagram_connected=instagram_connected,
                           tiktok_connected=tiktok_connected,
                           youtube_connected=youtube_connected)

@app.route('/connect')
@login_required
def connect_accounts():
    return render_template('connect_accounts.html')

@app.route('/oauth/instagram')
@login_required
def oauth_instagram():
    redirect_uri = url_for('instagram_callback', _external=True)
    return oauth.instagram.authorize_redirect(redirect_uri)


@app.route('/oauth/instagram/callback')
@login_required
def instagram_callback():
    token = oauth.instagram.authorize_access_token()
    current_user.instagram_access_token = token.get('access_token')
    current_user.ig_user_id = token.get('user_id')
    db.session.commit()
    flash('Instagram connected!')
    return redirect(url_for('connect_accounts'))


@app.route('/oauth/tiktok')
@login_required
def oauth_tiktok():
    redirect_uri = url_for('tiktok_callback', _external=True)
    return oauth.tiktok.authorize_redirect(redirect_uri)


@app.route('/oauth/tiktok/callback')
@login_required
def tiktok_callback():
    token = oauth.tiktok.authorize_access_token()
    current_user.tiktok_access_token = token.get('access_token')
    current_user.tiktok_user_id = token.get('open_id')
    db.session.commit()
    flash('TikTok connected!')
    return redirect(url_for('dashboard'))


@app.route('/oauth/youtube')
@login_required
def oauth_youtube():
    redirect_uri = url_for('youtube_callback', _external=True)
    return oauth.youtube.authorize_redirect(redirect_uri)


@app.route('/oauth/youtube/callback')
@login_required
def youtube_callback():
    token = oauth.youtube.authorize_access_token()
    current_user.youtube_access_token = token.get('access_token')
    current_user.youtube_refresh_token = token.get('refresh_token')
    # fetch channel id
    resp = oauth.youtube.get('https://www.googleapis.com/youtube/v3/channels',
                             params={'part': 'id', 'mine': 'true'},
                             token=token)
    if resp.ok:
        data = resp.json()
        if data.get('items'):
            current_user.youtube_channel_id = data['items'][0]['id']
    db.session.commit()
    flash('YouTube connected!')
    return redirect(url_for('dashboard'))


@app.route('/suggest_captions', methods=['POST'])
@login_required
def suggest_captions():
    data = request.get_json() or {}
    image = data.get('image')
    if not image:
        return jsonify({'error': 'No image provided'}), 400

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({'error': 'OPENAI_API_KEY not configured'}), 500

    client = openai.OpenAI(api_key=api_key, max_retries=0)
    attempts = 3
    for attempt in range(attempts):
        try:
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Suggest three short captions and trending hashtags for this image.'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {'url': image}
                            }
                        ]
                    }
                ],
                max_tokens=200
            )
            suggestions = response.choices[0].message.content
            return jsonify({'suggestions': suggestions})
        except (APIConnectionError, APITimeoutError) as e:
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            return jsonify({'error': f'Network error: {e}'}), 500
        except RateLimitError:
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
                continue
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        except APIError as e:
            return jsonify({'error': f'OpenAI API error: {e}'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_post():
    if request.method == 'POST':
        caption = request.form.get('caption')
        image_url = request.form.get('image_url')
        uploaded_files = [f for f in request.files.getlist('image_file') if f and f.filename]
        image_urls = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                extension = uploaded_file.filename.rsplit('.', 1)[-1].lower()
                if extension in ALLOWED_EXTENSIONS or extension in ALLOWED_VIDEO_EXTENSIONS:
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(uploaded_file.filename)}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    uploaded_file.save(file_path)
                    image_urls.append(url_for('static', filename=f'uploads/{filename}'))
                else:
                    flash('Unsupported file type.')
                    return redirect(url_for('schedule_post'))
        elif image_url:
            image_urls.append(image_url)
        if not image_urls:
            image_urls.append(None)
        date_str = request.form.get('scheduled_date')
        time_str = request.form.get('scheduled_time')
        platforms = request.form.getlist('platforms')
        try:
            scheduled_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        except (TypeError, ValueError):
            flash('Invalid date/time format.')
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
            if platform == 'youtube' and not current_user.youtube_access_token:
                flash('Please connect your YouTube account first.')
                return redirect(url_for('connect_accounts'))

            for url in image_urls:
                new_post = Post(user_id=current_user.id,
                                caption=caption,
                                image_url=url,
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


@app.route('/analytics')
@login_required
def analytics():
    platform = request.args.get('platform', 'instagram')
    posts = Post.query.filter_by(user_id=current_user.id, platform=platform).all()
    follower_data = FollowerTrend.query.filter_by(user_id=current_user.id, platform=platform).order_by(FollowerTrend.timestamp).all()
    top_posts = sorted(posts, key=lambda p: (p.likes or 0) + (p.comments or 0) + (p.shares or 0) + (p.saves or 0), reverse=True)[:3]
    return render_template('analytics.html', posts=posts, follower_data=follower_data,
                           platform=platform, top_posts=top_posts)


@app.route('/video_tools', methods=['GET', 'POST'])
@login_required
def video_tools():
    short_video_url = None
    thumbnail_url = None
    clip_length = 20
    if request.method == 'POST':
        video_file = request.files.get('video_file')
        clip_start = float(request.form.get('clip_start', 0))
        clip_length = int(request.form.get('clip_length', 20))
        thumb_time = float(request.form.get('thumbnail_time', 1))
        if clip_length not in (10, 20, 30):
            clip_length = 20
        if video_file and video_file.filename:
            ext = video_file.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_VIDEO_EXTENSIONS:
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(video_file.filename)}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                video_file.save(file_path)
                clip = VideoFileClip(file_path)
                duration = clip.duration
                start = max(0, min(clip_start, duration))
                end = min(start + clip_length, duration)
                short_clip = clip.subclipped(start, end)
                short_name = f"short_{filename}"
                short_path = os.path.join(app.config['UPLOAD_FOLDER'], short_name)
                short_clip.write_videofile(short_path, codec='libx264', audio_codec='aac', logger=None)
                thumb_name = f"thumb_{os.path.splitext(filename)[0]}.jpg"
                thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_name)
                clip.save_frame(thumb_path, t=min(thumb_time, duration))
                clip.close()
                short_clip.close()
                short_video_url = url_for('static', filename=f'uploads/{short_name}')
                thumbnail_url = url_for('static', filename=f'uploads/{thumb_name}')
            else:
                flash('Unsupported video type.')
                return redirect(url_for('video_tools'))
        else:
            flash('No video uploaded.')
            return redirect(url_for('video_tools'))
    return render_template('video_tools.html', short_video_url=short_video_url,
                           thumbnail_url=thumbnail_url, clip_length=clip_length)


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
