import os
from datetime import datetime
import pytest
import sys
import os as _os
sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

import BD

@pytest.fixture
def client(tmp_path):
    BD.app.config['TESTING'] = True
    BD.app.config['WTF_CSRF_ENABLED'] = False
    with BD.app.app_context():
        BD.db.drop_all()
        BD.db.create_all()
        user = BD.User(username='u', email='u@example.com', instagram_access_token='tok')
        user.set_password('pw')
        BD.db.session.add(user)
        BD.db.session.commit()
        user_id = user.id
    with BD.app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
        yield client


def test_multiple_files_allowed(client, tmp_path):
    f1 = tmp_path / 'a.jpg'
    f2 = tmp_path / 'b.jpg'
    f1.write_text('x')
    f2.write_text('y')
    data = {
        'caption': 'cap',
        'scheduled_date': '2025-01-01',
        'scheduled_time': '00:00',
        'platforms': 'instagram',
        'image_file': [
            (open(f1, 'rb'), 'a.jpg'),
            (open(f2, 'rb'), 'b.jpg'),
        ]
    }
    resp = client.post('/schedule', data=data, content_type='multipart/form-data')
    assert resp.status_code == 302
    with BD.app.app_context():
        assert BD.Post.query.count() == 2
