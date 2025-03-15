from models.users import User, db
from services.user_services import UserService
import os
from flask import send_file, abort
import logging
import openpyxl
from openpyxl.styles import Alignment
from services.email_service import send_email  # Import the send_email function
import io

class TransactionServices:       

    @staticmethod
    def generate_file_content(month, year, user_id):
        try:
            if not user_id:
                logging.error("User ID is missing")
                return None, None, None
            
            logging.debug(f"Starting download for month: {month}, year: {year}, user_id: {user_id}")
            
            user = UserService.get_user_by_id(user_id)
            if not user:
                logging.error(f"No user found with id: {user_id}")
                return None, None, None
            
            file_name = f'{month}_{year}'
            file_path = f'Sheets/{user.user_name}/{file_name}.xlsx'

            if os.path.exists(file_path):
                logging.debug(f"XLSX file found: {file_path}")
                response = send_file(file_path, as_attachment=True)
                logging.debug(f"XLSX file sent: {file_path}")
                return file_path, response, file_name
            else:
                logging.error(f"XLSX file not found: {file_path}")
                abort(404, description="File not found")
        except Exception as e:
            logging.error(f"Error in generate_file_content: {e}")
            return None, None, None
    
    @staticmethod
    def send_file_via_email(file_path, user_id):
        try:
            user = UserService.get_user_by_id(user_id)
            if not user:
                logging.error(f"No user found with id: {user_id}")
                return

            email_address = user.email_id
            subject = f"{os.path.basename(file_path)} - Monthly Expense Report"
            body = "File attached, Monthly expense report."

            print('\n\nSending email to:', email_address)

            # Create BytesIO object from file
            with open(file_path, 'rb') as f:
                file_data = io.BytesIO(f.read())
                file_data.filename = os.path.basename(file_path)

            send_email(email_address, subject, body, file_data)
            logging.info(f"Email sent successfully to {email_address}")
        except Exception as e:
            logging.error(f"Failed to send email to {email_address}: {e}")
            

class ExcelService:

    @staticmethod
    def append_transaction_data(file_path, transaction_data):
        # Load the workbook and select the active sheet
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active

        # Determine the next "Sr No"
        next_sr_no = sheet.max_row - 2

        # Append the transaction data to the sheet
        new_row = [
            next_sr_no,
            transaction_data['date'],
            transaction_data['title'],
            float(transaction_data['amount']),
            transaction_data['category'],
            transaction_data['sub_category'],
            transaction_data['payment_method'],
        ]
        sheet.append(new_row)

        max_row = sheet.max_row
        headings = 7
        amount_column = 'D'  # Assuming "Amount" is in column D
        sheet.cell(row=3, column=headings + 1, value=f"=SUM({amount_column}4:{amount_column}{max_row})").alignment = Alignment(horizontal='center', vertical='center')

        # Center-align all cells in the new row
        for cell in sheet[sheet.max_row]:
            cell.alignment = Alignment(horizontal='center', vertical='center')
        # Save the workbook
        workbook.save(file_path)
        logging.debug("Transaction data appended to the Excel sheet")

