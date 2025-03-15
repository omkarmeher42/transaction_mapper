from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.transaction_services import TransactionServices, ExcelService  # Import ExcelService
import logging
import io
from datetime import datetime
import os  # Add this import at the top with other imports
import pandas as pd

transaction_bp = Blueprint('transaction', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@transaction_bp.route('/map_transaction', methods=['GET', 'POST'])
@login_required
def map_transaction():
    if request.method == 'POST':
        # Trigger the function to get the current file
        current_user.get_current_sheet()

        # Generate the current date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Retrieve form values
        transaction_data = {
            'date': current_date,
            'title': request.form.get('title'),
            'amount': request.form.get('amount'),
            'category': request.form.get('category'),
            'sub_category': request.form.get('sub_category'),
            'payment_method': request.form.get('payment_method'),
        }

        logging.debug(f"Received transaction data: {transaction_data}")

        # Append the values to the respective columns in the Excel sheet
        ExcelService.append_transaction_data(current_user.current_sheet_path, transaction_data)

        flash('Transaction data mapped successfully', 'success')
        return redirect(url_for('transaction.map_transaction'))

    return render_template('transactions.html', action=url_for('transaction.map_transaction'))

@transaction_bp.route('/view_transactions', methods=['GET', 'POST'])
@login_required
def view_transactions():
    transactions = []
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        logging.debug(f"Form data received - Month: {month}, Year: {year}")
        logging.debug(f"User's all_sheets: {current_user.all_sheets}")
        
        if not month or not year:
            flash('Please select both month and year', 'error')
            return redirect(url_for('transaction.view_transactions'))

        # Construct the file key (e.g., "March_2025")
        file_key = f"{month}_{year}"
        logging.debug(f"Constructed file key: {file_key}")
        
        file_path = current_user.all_sheets.get(file_key)
        logging.debug(f"Retrieved file path: {file_path}")
        
        if not file_path:
            flash('File not found', 'error')
            logging.error(f"No file found for key: {file_key}")
        else:
            try:
                logging.debug(f"Attempting to read file from: {file_path}")
                df = pd.read_excel(file_path, skiprows=2)
                
                logging.debug(f"Original Excel columns: {df.columns.tolist()}")
                
                # Map the actual Excel columns to our expected names
                column_mapping = {
                    'Sr No': 'sr_no',
                    'Date': 'date',
                    'Transaction Title': 'title', 
                    'Amount': 'amount',
                    'Category': 'category',
                    'Sub Category': 'sub_category',
                    'Payment Method': 'payment_method'
                }
                
                # Rename only the columns that exist
                existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
                df = df.rename(columns=existing_columns)
                
                # Remove rows with all NaN values
                df = df.dropna(how='all')
                
                # Fill NaN values with empty strings
                df = df.fillna('')
                
                # Convert to dict with only the columns we want to show
                transactions = []
                for _, row in df.iterrows():
                    transaction = {
                        'title': row.get('title', '') or row.get('Transaction Title', ''),
                        'amount': row.get('amount', ''),
                        'category': row.get('category', ''),
                        'sub_category': row.get('sub_category', '') or row.get('Sub Category', ''),
                        'payment_method': row.get('payment_method', ''),
                        'date': row.get('date', '')
                    }
                    transactions.append(transaction)
                
                logging.debug(f"Found {len(transactions)} transactions")
                logging.debug(f"Sample transaction: {transactions[0] if transactions else None}")
                
            except Exception as e:
                flash('Error reading file', 'error')
                logging.error(f"Error reading file: {str(e)}")
                logging.exception("Full traceback:")

    return render_template('view_transactions.html', 
                         transactions=transactions,
                         request=request)  # Pass request object to template

@transaction_bp.route('/download', methods=['GET', 'POST'])
@login_required
def download():
    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')
        user_id = request.form.get('user_id') or current_user.id
        action = request.form.get('action')

        logging.debug(f"Received download request: month={month}, year={year}, user_id={user_id}, action={action}")

        if not month or not year or not user_id:
            logging.error("Missing form parameters")
            return "Missing form parameters", 400

        # Generate the file content
        file_path, file_response, file_name = TransactionServices.generate_file_content(month, year, user_id)
        
        if file_path is None:
            return "Error generating file", 500

        if action == 'send_to_email':
            try:
                # Send the file via email using the file path
                TransactionServices.send_file_via_email(file_path, user_id)
                return "File sent to email", 200
            except Exception as e:
                logging.error(f"Failed to send email: {e}")
                return "Failed to send file to email", 500
        elif action == 'download':
            try:
                response = file_response
                response.headers['Content-Disposition'] = f'attachment; filename="{file_name}.xlsx"'
                logging.debug(f'Content-Disposition: {response.headers["Content-Disposition"]}')
                return response
            except Exception as e:
                logging.error(f"Failed to download file: {e}")
                return "Failed to download file", 500

    return render_template('download.html')

@transaction_bp.route('/handle_submit', methods=['POST'])
def handle_submit():
    month = request.form.get("month")
    year = request.form.get("year")
    action = request.form.get("action")

    if action == "download":
        return redirect(url_for('transaction.download_file', month=month, year=year))
    elif action == "send_to_email":
        return redirect(url_for('transaction.send_to_email', month=month, year=year))
    
    return "Invalid Action", 400
