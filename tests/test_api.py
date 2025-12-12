import pytest
import json
import os
from app import app
from database import db
from models import User

@pytest.fixture
def client():
    # Используем тестовую БД
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/test_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Создаем таблицы
            db.create_all()
            yield client
            # Очищаем после тестов
            db.drop_all()

def test_register(client):
    """Тест регистрации пользователя"""
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass123',
        'subscription_level': 'premium'
    })
    assert response.status_code == 201
    assert 'user_id' in json.loads(response.data)

def test_login(client):
    """Тест аутентификации"""
    # Сначала регистрируем
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    
    # Логинимся
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user_id' in data

def test_create_resource_premium_only(client):
    """Тест что только premium может создавать ресурсы"""
    # Создаем basic пользователя
    client.post('/register', json={
        'username': 'basicuser',
        'password': 'pass123',
        'subscription_level': 'basic'
    })
    
    # Логинимся как basic
    login_resp = client.post('/login', json={
        'username': 'basicuser',
        'password': 'pass123'
    })
    basic_user_id = json.loads(login_resp.data)['user_id']
    
    # Пытаемся создать ресурс как basic - должно быть ошибка
    response = client.post('/resources',
        headers={'X-User-ID': str(basic_user_id)},
        json={'name': 'Test Resource', 'access_level': 'basic', 'available_hours': '09:00-18:00'}
    )
    assert response.status_code == 403
    assert 'Premium required' in json.loads(response.data)['error']