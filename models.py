from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, UTC

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    instagram_access_token = db.Column(db.String(500))
    ig_user_id = db.Column(db.String(100))
    tiktok_access_token = db.Column(db.String(500))
    tiktok_user_id = db.Column(db.String(100))
    youtube_access_token = db.Column(db.String(500))
    youtube_refresh_token = db.Column(db.String(500))
    youtube_channel_id = db.Column(db.String(100))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    caption = db.Column(db.String(2200))
    image_url = db.Column(db.String(500))
    scheduled_time = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    posted = db.Column(db.Boolean, default=False)
    platform = db.Column(db.String(50), default='instagram', nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    saves = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref='posts')


class FollowerTrend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    followers = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    user = db.relationship('User', backref='follower_trends')
