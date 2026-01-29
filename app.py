from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from forms import RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models.users import User, db
from models.transactions import Transaction
from models.budget_recurring import Budget, RecurringTransaction
from routes.user_routes import user_bp, user_routes
from routes.transaction_routes import transaction_bp
import logging

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session Configuration for Persistence
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days in seconds
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript from accessing session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
    
    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # This line creates the database tables

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.transaction_routes import transaction_bp
    from routes.budget_routes import budget_bp
    from routes.quick_routes import quick_bp

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(user_routes)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(quick_bp)

    # Home Tab
    @app.route('/', methods=['GET'])
    def home():
        return render_template('homepage.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        from models.transactions import Transaction
        from services.transaction_services import TransactionServices
        from datetime import datetime
        from sqlalchemy import func
        
        # Process recurring transactions (with error handling)
        try:
            TransactionServices.process_recurring_transactions(current_user.id)
        except AttributeError:
            # Method not available yet, skip recurring transaction processing
            logging.warning("process_recurring_transactions method not available")
        except Exception as e:
            logging.error(f"Error processing recurring transactions: {e}")
        
        now = datetime.now()
        month_num = now.month
        year_num = now.year
        
        # Calculate summary statistics for the current month
        try:
            # Total spending
            total_spent = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == current_user.id,
                db.extract('month', Transaction.date) == month_num,
                db.extract('year', Transaction.date) == year_num
            ).scalar() or 0
            
            # Category breakdown (for charts)
            category_data = db.session.query(
                Transaction.category, func.sum(Transaction.amount)
            ).filter(
                Transaction.user_id == current_user.id,
                db.extract('month', Transaction.date) == month_num,
                db.extract('year', Transaction.date) == year_num
            ).group_by(Transaction.category).all()
            
            category_labels = [c[0] for c in category_data]
            category_values = [float(c[1]) for c in category_data]
            
            # Recent transactions
            recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
            
            # Find top spending category
            top_category = "None"
            if category_data:
                top_category = max(category_data, key=lambda x: x[1])[0]
            
            # Get advanced analytics
            analytics = TransactionServices.get_analytics_data(current_user.id)
            
            summary = {
                'total_spent': total_spent,
                'top_category': top_category,
                'category_labels': category_labels,
                'category_values': category_values,
                'recent_transactions': [tx.to_dict() for tx in recent_transactions],
                'analytics': analytics
            }
        except Exception as e:
            print(f"Error gathering summary data: {e}")
            summary = {
                'total_spent': 0,
                'top_category': "None",
                'category_labels': [],
                'category_values': [],
                'recent_transactions': [],
                'analytics': {}
            }
            
        return render_template('dashboard.html', user=current_user, summary=summary)

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