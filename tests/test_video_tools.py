import os
import tempfile
from moviepy.video.VideoClip import ColorClip
import pytest
import sys
import os as _os
sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))

# Set required environment variables before importing the app
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

import BD

@pytest.fixture
def client():
    BD.app.config['TESTING'] = True
    BD.app.config['LOGIN_DISABLED'] = True
    BD.app.config['WTF_CSRF_ENABLED'] = False
    with BD.app.test_client() as client:
        yield client

def _create_sample_video(path):
    clip = ColorClip(size=(64, 64), color=(255, 0, 0), duration=1)
    clip.write_videofile(path, fps=24, codec='libx264', audio=False, logger=None)
    clip.close()


def test_video_tools_get(client):
    resp = client.get('/video_tools')
    assert resp.status_code == 200


def test_video_processing(client, tmp_path):
    video_path = tmp_path / 'vid.mp4'
    _create_sample_video(str(video_path))
    with open(video_path, 'rb') as f:
        data = {'video_file': (f, 'vid.mp4')}
        resp = client.post('/video_tools', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert b'20-second Clip' in resp.data
    files = os.listdir(os.path.join('static', 'uploads'))
    assert any(name.startswith('short_') for name in files)
    assert any(name.startswith('thumb_') for name in files)
