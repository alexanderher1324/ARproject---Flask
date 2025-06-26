import os
from datetime import datetime, UTC
import pytest
import sys
import os as _os
sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

import BD

@pytest.fixture
def client():
    BD.app.config['TESTING'] = True
    BD.app.config['WTF_CSRF_ENABLED'] = False
    with BD.app.app_context():
        BD.db.drop_all()
        BD.db.create_all()
        user = BD.User(username='u', email='u@example.com')
        user.set_password('pw')
        BD.db.session.add(user)
        BD.db.session.commit()
        user_id = user.id
        post = BD.Post(user_id=user_id, caption='post1', platform='instagram', likes=10, comments=5, shares=1, saves=2)
        BD.db.session.add(post)
        trend1 = BD.FollowerTrend(user_id=user.id, platform='instagram', followers=100,
                                  timestamp=datetime(2024, 1, 1, tzinfo=UTC))
        trend2 = BD.FollowerTrend(user_id=user.id, platform='instagram', followers=120,
                                  timestamp=datetime(2024, 1, 2, tzinfo=UTC))
        BD.db.session.add_all([trend1, trend2])
        BD.db.session.commit()
    with BD.app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
        yield client

def test_analytics_page(client):
    resp = client.get('/analytics?platform=instagram')
    assert resp.status_code == 200
    data = resp.get_data(as_text=True)
    assert 'post1' in data
    assert '120' in data
