import pytest
import json
from app import app
from database import db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/abac_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.query(User).delete()
            db.session.commit()

def test_register(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass123',
        'subscription_level': 'basic',
        'account_status': 'active'
    })
    assert response.status_code == 201
    assert 'user_id' in json.loads(response.data)

def test_login(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'user_id' in json.loads(response.data)

def test_create_resource_premium_only(client):
    # Регистрируем basic пользователя
    response = client.post('/register', json={
        'username': 'basicuser',
        'password': 'pass123',
        'subscription_level': 'basic'
    })
    user_id = json.loads(response.data)['user_id']
    
    # Пробуем создать ресурс с basic подпиской
    response = client.post('/resources', 
        headers={'X-User-ID': str(user_id)},
        json={
            'name': 'Test Course',
            'access_level': 'basic',
            'available_hours': '09:00-18:00'
        }
    )
    assert response.status_code == 403

def test_get_resources_auth_required(client):
    response = client.get('/resources')
    assert response.status_code == 401