import os
import json
from unittest.mock import patch, Mock
import httpx
import openai
import pytest
import sys
import os as _os
sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))

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
    mock_resp.choices = [Mock(message=Mock(content='caption suggestions'))]
    with patch('BD.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_resp
        mock_openai.return_value = mock_client
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 200
    assert resp.get_json() == {'suggestions': 'caption suggestions'}
    mock_client.chat.completions.create.assert_called_once()

def test_suggest_captions_api_error(client):
    with patch('BD.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.APIError(
            'bad request', request=httpx.Request('POST', 'http://x'), body=None)
        mock_openai.return_value = mock_client
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 500
    assert 'bad request' in resp.get_json()['error']
    mock_client.chat.completions.create.assert_called_once()

def test_suggest_captions_timeout(client):
    with patch('BD.openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=httpx.Request('POST', 'http://x')
        )
        mock_openai.return_value = mock_client
        resp = client.post('/suggest_captions', json={'image': 'http://img.jpg'})
    assert resp.status_code == 500
    assert 'Network error' in resp.get_json()['error']
    assert mock_client.chat.completions.create.call_count == 3
