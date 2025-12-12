import pytest
import json
from app import app
from database import db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/test_db'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_register(client):
    response = client.post('/register', json={
        'username': 'test',
        'password': 'pass',
        'subscription_level': 'premium'
    })
    assert response.status_code == 201

def test_login(client):
    client.post('/register', json={
        'username': 'test',
        'password': 'pass'
    })
    
    response = client.post('/login', json={
        'username': 'test',
        'password': 'pass'
    })
    assert response.status_code == 200
    assert 'access_token' in json.loads(response.data)
    