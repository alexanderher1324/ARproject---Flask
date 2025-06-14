import os
import json
from unittest.mock import patch, Mock
import requests
import pytest

# Set required environment variables before importing the app
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('OPENAI_API_KEY', 'testkey')

import BD

@pytest.fixture
def client():
    BD.app.config['TESTING'] = True
    BD.app.config['LOGIN_DISABLED'] = True
    BD.app.config['WTF_CSRF_ENABLED'] = False
    with BD.app.test_client() as client:
        yield client

def test_suggest_captions_success(client):
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.json.return_value = {
        'choices': [{
            'message': {'content': 'caption suggestions'}
        }]
    }
    with patch('BD.requests.post', return_value=mock_resp) as mock_post:
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 200
    assert resp.get_json() == {'suggestions': 'caption suggestions'}
    mock_post.assert_called_once()

def test_suggest_captions_api_error(client):
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError('bad request')
    with patch('BD.requests.post', return_value=mock_resp):
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 500
    assert 'bad request' in resp.get_json()['error']

def test_suggest_captions_timeout(client):
    with patch('BD.requests.post', side_effect=requests.exceptions.Timeout('timeout')):
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 500
    assert 'timeout' in resp.get_json()['error']
