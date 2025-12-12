import pytest
import json
import os
from app import app
from database import db
from models import User

@pytest.fixture
def client():
    # Используем ТУ ЖЕ САМУЮ БД что и в основном приложении!
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/abac_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Создаем таблицы
            db.create_all()
            yield client
            # Очищаем таблицы после тестов (но не удаляем БД)
            db.session.query(User).delete()
            db.session.commit()

def test_register(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpass123',
        'subscription_level': 'premium'
    })
    assert response.status_code == 201

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