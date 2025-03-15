from models.users import User,db

class UserService:

    @staticmethod
    def create_user(first_name, last_name, user_name, password, email_id):
        user = User(first_name=first_name,
                    last_name=last_name,
                    user_name= user_name,
                    password=password,
                    email_id=email_id)
        
        user.save()
        return user
    
    @staticmethod
    def update_user(user_id, user_name=None, password=None, email_id=None, 
                    first_name = None, last_name = None):
        user = User.query.get(user_id)
        if not user:
            return None
        
        if user_name:
            user.user_name = user_name
        if email_id:
            user.email_id = email_id
        if password:
            user.password = password
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        user.update()
        return user
    
    @staticmethod
    def delete_user(user_id):
        user = User.get_by_id(user_id)

        if user:
            user.delete()
            return True

        return False

    
    @staticmethod
    def get_user_by_id(user_id):
        return User.get_by_id(user_id)
    
    @staticmethod
    def get_user_by_username(user_name):
        return User.get_by_username(user_name)
    
    @staticmethod
    def get_all_users():
        return User.query.all()