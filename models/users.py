from models.get_dates import get_current_month_and_year
import os
from models.spreadsheets import SpreadSheet
from models import db
from sqlalchemy import func, JSON
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name = db.Column(db.String(50), nullable = False)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email_id = db.Column(db.String(100), unique=True, nullable=False)
    all_sheets = db.Column(JSON, default = dict)

    def __init__(self, first_name, last_name, user_name,password, email_id):
        self.first_name = first_name
        self.last_name = last_name
        self.email_id = email_id
        self.user_name = user_name
        self.password = generate_password_hash(password)  # Hash the password
        self.make_user_dir()
        self.get_current_sheet()

    def to_dict(self):
        return {
            'id' : self.id,
            'user_name' : self.user_name,
            'first_name' : self.first_name,
            'last_name' : self.last_name,
            'email_id' : self.email_id,
            'all_sheets' : self.all_sheets,
            'password' : self.password  # Add this line
        }
    
    #create new user
    def save(self):
        db.session.add(self)
        db.session.commit()

    #delete user
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    #update user
    def update(self):
        db.session.commit()

    #find user by id
    def get_by_id(id):
        return User.query.get(id)
    
    #find user by username
    def get_by_user_name(user_name):
        return User.query.filter_by(user_name = user_name).first()

    #get all users
    @staticmethod
    def get_all_users():
        return User.query.all()

    def get_current_sheet(self):
        #refresh dates before continuing
        self.get_todays_date()

        #current month sheet
        file_name = f'{self.month}_{self.year}'

        if os.path.exists(f'Sheets/{self.user_name}') == False:
            self.make_user_dir()

        if self.all_sheets is None:
            self.all_sheets = {}

        user = User.query.get(self.id)

        #check if current month sheet exist
        verify_sheet = os.path.exists(f'Sheets/{self.user_name}/{file_name}.xlsx')
        if not verify_sheet:
            #if sheet does not exist, create one
            print(os.getcwd())
            os.chdir(f'D:/Code/Transactions Mapper/Sheets/{self.user_name}')
            
            #creating a object of excel sheet using Spreadsheet class
            sheet = SpreadSheet(file_name, user)

            #this line creates a new spreadsheet as it doesnt exist in the user's dir
            sheet.create_sheet()

            os.chdir('../')
            os.chdir('../')

            #assigning newly created sheet to user's all_sheets
            self.all_sheets[file_name] = f'Sheets/{self.user_name}/{file_name}.xlsx'
            db.session.commit()

        
        if user is not None:
            user_all_sheets = user.all_sheets
            current_sheet = user_all_sheets.get(file_name)
            self.current_sheet_path = current_sheet
            self.current_sheet_name = file_name

            if current_sheet:
                # Check if the Excel file is blank and apply a template if it is
                sheet = SpreadSheet(self.current_sheet_name, user)
                if sheet.is_blank():
                    sheet.apply_template()
                return True
            else:
                return False
        else:
            return False

    def get_todays_date(self):
        today = get_current_month_and_year()
        self.day = today['Day']
        self.month = today['Month']
        self.year = today['Year']

    def make_user_dir(self):
        #Make Sheets Dir if it doesn't exist
        #and if it exist, pass
        os.makedirs('Sheets', exist_ok=True)
        
        #verify if the user's dir already exist in sheets dir
        path = f'Sheets/{self.user_name}'
        verify_users_sheet_dir = os.path.exists(path)
        print(f'{self.user_name} dir is {verify_users_sheet_dir = }')

        #if dir doesnt not exist then create one
        if verify_users_sheet_dir == False:
            os.chdir('Sheets')

            os.makedirs(f'{self.user_name}', exist_ok=True)
            print(f'{self.first_name} user dir created')
            os.chdir('../')
            return
        else:
            return
        
    def update_user_dir_name(self,prev_user_name, new_user_name):
        print('\n\nTrying to change user dir\n\n')
        if new_user_name == prev_user_name:
            return
        else:
            print('\n\nVerifying user dir\n\n')
            verify_user_dir = os.path.exists(f'Sheets/{prev_user_name}')
            print(f'{verify_user_dir = }')
            if verify_user_dir:
                print('\n\nChanging user dir\n\n')
                os.rename(f"Sheets/{prev_user_name}", f"Sheets/{new_user_name}")
                print("\n\nUser Dir's Name Changed Successfully\n\n")

                self.update_user_dir_in_allsheets(prev_user_name, new_user_name)
            else:
                return
            
    def update_user_dir_in_allsheets(self,prev_user_name, new_user_name):
        # "Sheets/omeher/March_2025.xlsx"

        for item in self.all_sheets:
            print(f'\n{self.all_sheets[item] = }')
            s = self.all_sheets[item]
            new_value = s.replace(prev_user_name, new_user_name)

            print(f'{new_value = }')

            User.query.filter_by(id=self.id).update(
                {User.all_sheets: func.json_set(
                    User.all_sheets, f'$.{item}', new_value)})


            db.session.commit()
            print(f'{self.all_sheets[item] = }\n')
            

        db.session.commit()
        print('\nAll Sheets Updated Successfully\n')

    def check_password(self, password):
        return check_password_hash(self.password, password)






