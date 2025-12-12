from flask import Flask, request, jsonify
from database import db
from models import User, Resource, Policy
from abac import ABACEngine

app = Flask(__name__)

# Простая конфигурация для PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/abac_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def get_user_from_request():
    """Получаем пользователя из заголовка user_id"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return User.query.get(int(user_id))

# POST /register
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

# POST /login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        return jsonify({'user_id': user.id}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

# POST /resources
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

# GET /resources
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
                'access_level': resource.access_level
            })
    
    return jsonify({'resources': accessible}), 200

# GET /resources/<id>
@app.route('/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    user = get_user_from_request()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    resource = Resource.query.get(resource_id)
    
    if ABACEngine.check_access(user, resource):
        return jsonify({
            'id': resource.id,
            'name': resource.name,
            'access_level': resource.access_level
        }), 200
    
    return jsonify({'error': 'Access denied'}), 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)