from flask import Flask, request, jsonify, render_template_string, url_for
from database import db
from models import User, Resource, Policy
from abac import ABACEngine
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/abac_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def get_user_from_request():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return User.query.get(int(user_id))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    user = User(
        username=data['username'],
        subscription_level=data.get('subscription_level', 'basic'),
        account_status=data.get('account_status', 'active')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'user_id': user.id}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        return jsonify({'user_id': user.id}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/resources', methods=['POST'])
def create_resource():
    user = get_user_from_request()
    if not user or user.subscription_level != 'premium':
        return jsonify({'error': 'Premium required'}), 403
    
    data = request.get_json()
    hours = data['available_hours'].split('-')
    
    resource = Resource(
        name=data['name'],
        access_level=data['access_level'],
        available_hours_start=hours[0],
        available_hours_end=hours[1]
    )
    
    db.session.add(resource)
    db.session.commit()
    
    return jsonify({'resource_id': resource.id}), 201

@app.route('/resources', methods=['GET'])
def get_resources():
    user = get_user_from_request()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    resources = Resource.query.all()
    accessible = []
    
    for resource in resources:
        if ABACEngine.check_access(user, resource):
            accessible.append({
                'id': resource.id,
                'name': resource.name,
                'access_level': resource.access_level,
                'available_hours': f"{resource.available_hours_start}-{resource.available_hours_end}"
            })
    
    return jsonify({'resources': accessible}), 200

@app.route('/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    user = get_user_from_request()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    resource = Resource.query.get(resource_id)
    
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    
    if ABACEngine.check_access(user, resource):
        return jsonify({
            'id': resource.id,
            'name': resource.name,
            'access_level': resource.access_level,
            'available_hours': f"{resource.available_hours_start}-{resource.available_hours_end}"
        }), 200
    
    return jsonify({'error': 'Access denied'}), 403

@app.route('/policies', methods=['POST'])
def create_policy():
    user = get_user_from_request()
    if not user or user.subscription_level != 'premium':
        return jsonify({'error': 'Premium required'}), 403
    
    data = request.get_json()
    
    policy = Policy(
        attribute=data['attribute'],
        operator=data['operator'],
        value=data['value']
    )
    
    db.session.add(policy)
    db.session.commit()
    
    return jsonify({'policy_id': policy.id}), 201

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>ABAC API - Управление доступом</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <h1>ABAC API - Управление доступом</h1>
        
        <div class="section">
            <h3>1. Регистрация пользователя</h3>
            <div class="form-group">
                <label>Имя пользователя:</label>
                <input type="text" id="reg-username" placeholder="Введите username">
            </div>
            <div class="form-group">
                <label>Пароль:</label>
                <input type="password" id="reg-password" placeholder="Введите пароль">
            </div>
            <div class="form-group">
                <label>Уровень подписки:</label>
                <select id="reg-subscription">
                    <option value="basic">Basic</option>
                    <option value="premium">Premium</option>
                </select>
            </div>
            <div class="form-group">
                <label>Статус аккаунта:</label>
                <select id="reg-status">
                    <option value="active">Active</option>
                    <option value="frozen">Frozen</option>
                </select>
            </div>
            <button class="btn" onclick="registerUser()">Зарегистрировать</button>
            <div class="output" id="register-output"></div>
        </div>
        
        <div class="section">
            <h3>2. Вход в систему</h3>
            <div class="form-group">
                <label>Имя пользователя:</label>
                <input type="text" id="login-username" placeholder="Введите username">
            </div>
            <div class="form-group">
                <label>Пароль:</label>
                <input type="password" id="login-password" placeholder="Введите пароль">
            </div>
            <button class="btn" onclick="loginUser()">Войти</button>
            <div class="output" id="login-output"></div>
        </div>
        
        <div class="section">
            <h3>3. Создание ресурса (только для Premium)</h3>
            <div class="form-group">
                <label>Ваш user_id (из входа):</label>
                <input type="text" id="resource-user-id" placeholder="Введите user_id">
            </div>
            <div class="form-group">
                <label>Название ресурса:</label>
                <input type="text" id="resource-name" placeholder="Введите название курса">
            </div>
            <div class="form-group">
                <label>Уровень доступа:</label>
                <select id="resource-access">
                    <option value="basic">Basic</option>
                    <option value="premium">Premium</option>
                </select>
            </div>
            <div class="form-group">
                <label>Время доступа (ЧЧ:ММ-ЧЧ:ММ):</label>
                <input type="text" id="resource-hours" placeholder="09:00-18:00" value="09:00-18:00">
            </div>
            <button class="btn" onclick="createResource()">Создать ресурс</button>
            <div class="output" id="create-resource-output"></div>
        </div>
        
        <div class="section">
            <h3>4. Получение ресурсов</h3>
            <div class="form-group">
                <label>Ваш user_id:</label>
                <input type="text" id="get-user-id" placeholder="Введите user_id">
            </div>
            <button class="btn" onclick="getResources()">Получить ресурсы</button>
            <div class="output" id="get-resources-output"></div>
        </div>
        
        <div class="section">
            <h3>5. Получение конкретного ресурса</h3>
            <div class="form-group">
                <label>Ваш user_id:</label>
                <input type="text" id="get-one-user-id" placeholder="Введите user_id">
            </div>
            <div class="form-group">
                <label>ID ресурса:</label>
                <input type="text" id="resource-id" placeholder="Введите ID ресурса">
            </div>
            <button class="btn" onclick="getResource()">Получить ресурс</button>
            <div class="output" id="get-resource-output"></div>
        </div>
    </div>
    
<script>
async function registerUser() {
    const output = document.getElementById('register-output');
    output.textContent = 'Выполняю запрос...';
    output.className = 'output info';
    
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    const subscription = document.getElementById('reg-subscription').value;
    const status = document.getElementById('reg-status').value;
    
    if (!username || !password) {
        output.textContent = 'Ошибка: Заполните все поля';
        output.className = 'output error';
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: username,
                password: password,
                subscription_level: subscription,
                account_status: status
            })
        });
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.status === 201 && data.user_id) {
                output.textContent = `Вы успешно зарегистрировались! ID: ${data.user_id}, Имя: ${username}`;
                output.className = 'output success';
            } else {
                output.textContent = `Ошибка: ${data.error || 'Неизвестная ошибка'}`;
                output.className = 'output error';
            }
        } else {
            const text = await response.text();
            output.textContent = `Ошибка сервера: ${response.status} ${response.statusText}`;
            output.className = 'output error';
        }
        
    } catch (error) {
        output.textContent = 'Ошибка подключения к серверу';
        output.className = 'output error';
    }
}

async function loginUser() {
    const output = document.getElementById('login-output');
    output.textContent = 'Выполняю запрос...';
    output.className = 'output info';
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        output.textContent = 'Ошибка: Заполните все поля';
        output.className = 'output error';
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.status === 200 && data.user_id) {
                output.textContent = `Вход выполнен! Ваш ID: ${data.user_id}`;
                output.className = 'output success';
                
                document.getElementById('resource-user-id').value = data.user_id;
                document.getElementById('get-user-id').value = data.user_id;
                document.getElementById('get-one-user-id').value = data.user_id;
            } else {
                output.textContent = `Ошибка: ${data.error || 'Неверные учетные данные'}`;
                output.className = 'output error';
            }
        } else {
            const text = await response.text();
            output.textContent = `Ошибка сервера: ${response.status} ${response.statusText}`;
            output.className = 'output error';
        }
        
    } catch (error) {
        output.textContent = 'Ошибка подключения к серверу';
        output.className = 'output error';
    }
}

async function createResource() {
    const output = document.getElementById('create-resource-output');
    output.textContent = 'Выполняю запрос...';
    output.className = 'output info';
    
    const userId = document.getElementById('resource-user-id').value;
    const name = document.getElementById('resource-name').value;
    const access = document.getElementById('resource-access').value;
    const hours = document.getElementById('resource-hours').value;
    
    if (!userId || !name || !hours) {
        output.textContent = 'Ошибка: Заполните все поля';
        output.className = 'output error';
        return;
    }
    
    try {
        const response = await fetch('/resources', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            },
            body: JSON.stringify({
                name: name,
                access_level: access,
                available_hours: hours
            })
        });
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.status === 201 && data.resource_id) {
                output.textContent = `Ресурс создан! ID: ${data.resource_id}, Название: ${name}`;
                output.className = 'output success';
            } else {
                output.textContent = `Ошибка: ${data.error || 'Требуется премиум подписка'}`;
                output.className = 'output error';
            }
        } else {
            const text = await response.text();
            output.textContent = `Ошибка сервера: ${response.status} ${response.statusText}`;
            output.className = 'output error';
        }
        
    } catch (error) {
        output.textContent = 'Ошибка подключения к серверу';
        output.className = 'output error';
    }
}

async function getResources() {
    const output = document.getElementById('get-resources-output');
    output.textContent = 'Загружаю ресурсы...';
    output.className = 'output info';
    
    const userId = document.getElementById('get-user-id').value;
    
    if (!userId) {
        output.textContent = 'Ошибка: Введите user_id';
        output.className = 'output error';
        return;
    }
    
    try {
        const response = await fetch('/resources', {
            method: 'GET',
            headers: {'X-User-ID': userId}
        });
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.status === 200) {
                if (data.resources && data.resources.length > 0) {
                    let result = `Найдено ресурсов: ${data.resources.length}\n\n`;
                    data.resources.forEach(resource => {
                        result += `ID: ${resource.id}, Название: ${resource.name}\n`;
                    });
                    output.textContent = result;
                    output.className = 'output success';
                } else {
                    output.textContent = 'Ресурсов не найдено';
                    output.className = 'output info';
                }
            } else {
                output.textContent = `Ошибка: ${data.error || 'Требуется аутентификация'}`;
                output.className = 'output error';
            }
        } else {
            const text = await response.text();
            output.textContent = `Ошибка сервера: ${response.status} ${response.statusText}`;
            output.className = 'output error';
        }
        
    } catch (error) {
        output.textContent = 'Ошибка подключения к серверу';
        output.className = 'output error';
    }
}

async function getResource() {
    const output = document.getElementById('get-resource-output');
    output.textContent = 'Загружаю ресурс...';
    output.className = 'output info';
    
    const userId = document.getElementById('get-one-user-id').value;
    const resourceId = document.getElementById('resource-id').value;
    
    if (!userId || !resourceId) {
        output.textContent = 'Ошибка: Заполните все поля';
        output.className = 'output error';
        return;
    }
    
    try {
        const response = await fetch('/resources/' + resourceId, {
            method: 'GET',
            headers: {'X-User-ID': userId}
        });
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.status === 200) {
                output.textContent = `Ресурс найден! ID: ${data.id}, Название: ${data.name}`;
                output.className = 'output success';
            } else if (response.status === 404) {
                output.textContent = 'Ресурс не найден';
                output.className = 'output error';
            } else if (response.status === 403) {
                output.textContent = 'Доступ запрещен';
                output.className = 'output error';
            } else {
                output.textContent = `Ошибка: ${data.error || 'Неизвестная ошибка'}`;
                output.className = 'output error';
            }
        } else {
            const text = await response.text();
            output.textContent = `Ошибка сервера: ${response.status} ${response.statusText}`;
            output.className = 'output error';
        }
        
    } catch (error) {
        output.textContent = 'Ошибка подключения к серверу';
        output.className = 'output error';
    }
}
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)