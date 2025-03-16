from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from forms import RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models.users import User, db
from routes.user_routes import user_bp, user_routes
from routes.transaction_routes import transaction_bp

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # This line creates the database tables

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(user_routes)
    app.register_blueprint(transaction_bp)

    # Home Tab
    @app.route('/', methods=['GET'])
    def home():
        return render_template('homepage.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_name = request.form['username']
            password = request.form['password']
            user = User.get_by_user_name(user_name)
            
            print(f"Login attempt: {user_name}")  # Debug statement
            if user:
                print(f"User found: {user.user_name}")  # Debug statement
                if user.check_password(password):
                    print("Password check passed")  # Debug statement
                    login_user(user)
                    flash('Login successful', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    print("Password check failed")  # Debug statement
            else:
                print("User not found")  # Debug statement
            
            flash('Invalid username or password', 'danger')
        
        return render_template('login.html')

    @app.route('/login_status')
    def login_status():
        logged_in = current_user.is_authenticated
        return jsonify(logged_in=logged_in)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)