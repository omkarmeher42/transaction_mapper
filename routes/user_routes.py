from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from services.user_services import UserService
from models.users import db, User
from forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

user_bp = Blueprint("user", __name__, url_prefix='/user')

#create user
@user_bp.route('/create', methods = ['POST','GET'])
def create_user():
    if request.method == 'POST':
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if not data.get('first_name') or \
        not data.get('last_name') or \
        not data.get('user_name') or \
        not data.get('password') or \
        not data.get('email_id'):
            return jsonify({"error": "Missing fields"}), 400

        # Check for duplicate username or email
        if User.query.filter_by(user_name=data['user_name']).first() or User.query.filter_by(email_id=data['email_id']).first():
            return jsonify({"error": "Username or email already exists"}), 400

        user = UserService.create_user(first_name = data['first_name'],
                        last_name = data['last_name'],
                        user_name = data['user_name'],
                        password = data['password'],
                        email_id = data['email_id'])
            
        return jsonify(user.to_dict()), 200
    else:
        form = RegistrationForm()
        return render_template('register.html', form=form)

#get specific user
@user_bp.route('/<int:user_id>', methods = ['GET'])
def get_user(user_id):
    user = UserService.get_user_by_id(user_id)

    if user:
        return jsonify(user.to_dict())
    else:
        return jsonify({"message" : "User Not Found"}), 404
    
#show all users
@user_bp.route('/all', methods = ['GET'])
def show_users():
    users = UserService.get_all_users()

    return jsonify(
        [user.to_dict() for user in users]
    )

#update an user
@user_bp.route('/<int:user_id>', methods = ['PUT'])
def update_user(user_id):
    data = request.get_json()
    user =  UserService.get_user_by_id(user_id)
    prev_username = user.user_name

    if user:
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.user_name = data.get("user_name", user.user_name)
        user.email_id = data.get("email_id", user.email_id)
        
        # Only update password if one was provided and hash it
        if data.get("password"):
            user.password = generate_password_hash(data["password"])
        
        user.update()
        print('user updated')

        user.update_user_dir_name(prev_username, user.user_name)
        print('dir updated')

        return jsonify(user.to_dict())
    else:
        return jsonify({"error" : "User Not Found"}), 404
    
# Delete User
@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    success = UserService.delete_user(user_id)
    if not success:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted successfully"})

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))

@user_bp.route('/init_db')
def init_db():
    db.create_all()
    return "Database initialized!"

@user_bp.route('/details')
@login_required
def user_details():
    return render_template('user_details.html')

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check for duplicate username or email
        if User.query.filter_by(user_name=form.user_name.data).first() or User.query.filter_by(email_id=form.email_id.data).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('user_routes.register'))

        # Add user registration logic here
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_name=form.user_name.data,
            password=form.password.data,
            email_id=form.email_id.data
        )
        user.save()
        flash('Account created for {}!'.format(form.user_name.data), 'success')
        return redirect(url_for('user_routes.login'))
    return render_template('register.html', form=form)

@user_routes.route('/user/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_name=form.user_name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in as {}!'.format(form.user_name.data), 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html', form=form)

@user_routes.route('/users', methods=['GET'])
def get_users():
    users = User.get_all_users()
    return jsonify([user.to_dict() for user in users])