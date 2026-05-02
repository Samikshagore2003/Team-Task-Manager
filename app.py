from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os

print("DB PATH:", os.getcwd())

app = Flask(__name__)

# CONFIG
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
db = SQLAlchemy(app)
jwt = JWTManager(app)

#  MODELS 

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer)

class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
    role = db.Column(db.String(20), default='member')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='To Do')
    project_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    due_date = db.Column(db.String(20))


#  PAGES 

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup-page')
def signup_page():
    return render_template('signup.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/projects-page')
def projects_page():
    return render_template('project.html')


#  AUTH 

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password'])
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Signup successful'})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({'token': token})


#  PROJECT 

@app.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'message': 'Project name required'}), 400

    # CREATE PROJECT
    project = Project(name=data['name'], created_by=user_id)
    db.session.add(project)
    db.session.commit()

    #  CREATOR = ADMIN
    db.session.add(ProjectMember(
        user_id=user_id,
        project_id=project.id,
        role='admin'
    ))
    db.session.commit()

    return jsonify({'message': 'Project created successfully'}), 201
@app.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    user_id = int(get_jwt_identity())

    memberships = ProjectMember.query.filter_by(user_id=user_id).all()

    result = []
    for m in memberships:
        project = Project.query.get(m.project_id)
        result.append({'id': project.id, 'name': project.name})

    return jsonify(result)


#  MEMBERS 

@app.route('/add-member', methods=['POST'])
@jwt_required()
def add_member():
    data = request.get_json()
    user_id = int(get_jwt_identity())

    # admin check
    admin = ProjectMember.query.filter_by(
        user_id=user_id,
        project_id=data['project_id'],
        role='admin'
    ).first()

    if not admin:
        return jsonify({'message': 'Only admin allowed'}), 403

    user = User.query.filter_by(email=data['email']).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if ProjectMember.query.filter_by(user_id=user.id, project_id=data['project_id']).first():
        return jsonify({'message': 'Already added'}), 400

    db.session.add(ProjectMember(user_id=user.id, project_id=data['project_id']))
    db.session.commit()

    return jsonify({'message': 'Member added'})


@app.route('/remove-member', methods=['POST'])
@jwt_required()
def remove_member():
    data = request.get_json()

    member = ProjectMember.query.filter_by(
        user_id=data['user_id'],
        project_id=data['project_id']
    ).first()

    if not member:
        return jsonify({'message': 'Not found'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Removed'})


@app.route('/members/<int:project_id>')
@jwt_required()
def get_members(project_id):
    members = ProjectMember.query.filter_by(project_id=project_id).all()

    result = []
    for m in members:
        user = User.query.get(m.user_id)
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': m.role
        })

    return jsonify(result)


#  TASK 

@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    data = request.get_json()
    user_id = int(get_jwt_identity())

    title = data.get('title')
    description = data.get('description')
    project_id = data.get('project_id')
    assigned_to = data.get('assigned_to')
    due_date = data.get('due_date')

    #  VALIDATION 
    if not title or not project_id:
        return jsonify({'message': 'Title and project_id required'}), 400

    #  ADMIN CHECK 
    admin = ProjectMember.query.filter_by(
        user_id=user_id,
        project_id=project_id,
        role='admin'
    ).first()

    if not admin:
        return jsonify({'message': 'Only admin can create/assign tasks'}), 403

    #  ASSIGNED USER CHECK 
    if assigned_to:
        assigned_to = int(assigned_to)

        member = ProjectMember.query.filter_by(
            user_id=assigned_to,
            project_id=project_id
        ).first()

        if not member:
            return jsonify({'message': 'User is not part of this project'}), 400

    #  CREATE TASK 
    new_task = Task(
        title=title,
        description=description,
        project_id=project_id,
        user_id=user_id,            # creator
        assigned_to=assigned_to,    # assigned user
        due_date=due_date,
        status='To Do'
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/tasks/<int:project_id>')
@jwt_required()
def get_tasks(project_id):
    user_id = int(get_jwt_identity())

    #  check role
    member = ProjectMember.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()

    tasks = Task.query.filter_by(project_id=project_id).all()

    result = []

    for t in tasks:

        #  ADMIN → sab dekhe
        if member and member.role == 'admin':
            pass

        #  MEMBER → sirf assigned
        else:
            if t.assigned_to != user_id:
                continue

        user = User.query.get(t.assigned_to) if t.assigned_to else None

        result.append({
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'assigned_name': user.name if user else None,
            'due_date': t.due_date
        })

    return jsonify(result)

@app.route('/tasks/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):

    task = Task.query.get(id)

    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'message': 'No data provided'}), 400

    status = data.get('status')

    #  Validate status
    if status not in ['To Do', 'In Progress', 'Done']:
        return jsonify({'message': 'Invalid status'}), 400

    task.status = status
    db.session.commit()

    return jsonify({'message': 'Task updated successfully'}), 200


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    task = Task.query.get(task_id)

    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Deleted'})


#  RUN 

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)