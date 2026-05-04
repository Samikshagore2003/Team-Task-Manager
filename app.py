from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ================= CONFIG =================

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret123')

# 🔥 IMPORTANT: Render DB support
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ================= MODELS =================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    created_by = db.Column(db.Integer)


class ProjectMember(db.Model):
    __tablename__ = "project_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
    role = db.Column(db.String(20), default='member')


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='To Do')
    project_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    assigned_to = db.Column(db.Integer)
    due_date = db.Column(db.String(20))


# ================= AUTO CREATE TABLES =================

with app.app_context():
    print("🔥 Creating tables...")
    db.create_all()


# ================= PAGES =================

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


# ================= AUTH =================

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'User already exists'}), 400

        user = User(
            name=data['name'],
            email=data['email'],
            password=generate_password_hash(data['password'])
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'Signup successful'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        user = User.query.filter_by(email=data['email']).first()

        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401

        token = create_access_token(identity=str(user.id))

        return jsonify({'token': token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================= PROJECT =================

@app.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    project = Project(name=data['name'], created_by=user_id)
    db.session.add(project)
    db.session.commit()

    db.session.add(ProjectMember(user_id=user_id, project_id=project.id, role='admin'))
    db.session.commit()

    return jsonify({'message': 'Project created'})


@app.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    user_id = int(get_jwt_identity())

    memberships = ProjectMember.query.filter_by(user_id=user_id).all()

    result = []
    for m in memberships:
        project = Project.query.get(m.project_id)
        if project:
            result.append({'id': project.id, 'name': project.name})

    return jsonify(result)


# ================= RUN =================

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)