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
        # Retrieve form values
        title = request.form.get('title')
        amount = request.form.get('amount')
        category = request.form.get('category')
        sub_category = request.form.get('sub_category')
        payment_method = request.form.get('payment_method')
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_obj = datetime.now().date()

        transaction_data = {
            'date': date_str,
            'title': title,
            'amount': amount,
            'category': category,
            'sub_category': sub_category,
            'payment_method': payment_method,
        }

        logging.debug(f"Received transaction data: {transaction_data}")

        # Save to Database (New Primary)
        try:
            from models.transactions import Transaction
            from models import db
            new_tx = Transaction(
                user_id=current_user.id,
                date=date_obj,
                title=title,
                amount=float(amount),
                category=category,
                sub_category=sub_category,
                payment_method=payment_method
            )
            db.session.add(new_tx)
            db.session.commit()
            logging.debug("Transaction saved to database successfully.")
        except Exception as e:
            logging.error(f"Error saving to database: {e}")
            flash('Error saving to database', 'danger')
            return redirect(url_for('transaction.map_transaction'))

        # Append to Excel (Secondary/Backup)
        try:
            current_user.get_current_sheet()
            ExcelService.append_transaction_data(current_user.current_sheet_path, transaction_data)
        except Exception as e:
            logging.error(f"Error appending to Excel: {e}")
            # We don't flash error here as DB was successful

        flash('Transaction recorded successfully', 'success')
        return redirect(url_for('transaction.map_transaction'))

    return render_template('transactions.html', action=url_for('transaction.map_transaction'))

@transaction_bp.route('/view_transactions', methods=['GET', 'POST'])
@login_required
def view_transactions():
    from models.transactions import Transaction
    from models import db
    
    # Get values from form or default to current month/year
    month_val = request.form.get('month')
    year_val = request.form.get('year')
    search_query = request.form.get('search_query', '')
    category_filter = request.form.get('category', '')
    sort_by = request.form.get('sort_by', 'date_desc')
    
    if not month_val or not year_val:
        now = datetime.now()
        month_val = now.strftime('%B')
        year_val = str(now.year)

    logging.debug(f"Viewing transactions: {month_val} {year_val}, Search: {search_query}, Category: {category_filter}, Sort: {sort_by}")

    # Query from DB
    try:
        # Convert month name to number
        month_num = datetime.strptime(month_val, '%B').month
        
        query = Transaction.query.filter_by(user_id=current_user.id)
        
        # Date Filter
        query = query.filter(db.extract('month', Transaction.date) == month_num)
        query = query.filter(db.extract('year', Transaction.date) == int(year_val))
        
        # Search Filter
        if search_query:
            query = query.filter(Transaction.title.ilike(f"%{search_query}%"))
            
        # Category Filter
        if category_filter:
            query = query.filter(Transaction.category == category_filter)
            
        # Sorting
        if sort_by == 'date_asc':
            query = query.order_by(Transaction.date.asc())
        elif sort_by == 'amount_asc':
            query = query.order_by(Transaction.amount.asc())
        elif sort_by == 'amount_desc':
            query = query.order_by(Transaction.amount.desc())
        else: # date_desc
            query = query.order_by(Transaction.date.desc())
        
        db_transactions = query.all()
        transactions = [tx.to_dict() for tx in db_transactions]
        
        logging.debug(f"Found {len(transactions)} transactions in DB")
    except Exception as e:
        logging.error(f"Error querying database: {e}")
        flash('Error retrieving transactions from database', 'error')
        transactions = []

    return render_template('view_transactions.html',
                           transactions=transactions,
                           request=request,
                           month_val=month_val,
                           year_val=year_val,
                           search_query=search_query,
                           category_filter=category_filter,
                           sort_by=sort_by)

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
                # Set proper filename with quotes to handle special characters
                response.headers['Content-Disposition'] = f'attachment; filename="{month}_{year}.xlsx"'
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

@transaction_bp.route('/update_transaction', methods=['POST'])
@login_required
def update_transaction():
    from models.transactions import Transaction
    from models import db
    try:
        transaction_id = request.form.get('transaction_id')
        title = request.form.get('title')
        amount = request.form.get('amount')
        category = request.form.get('category')
        sub_category = request.form.get('sub_category')
        payment_method = request.form.get('payment_method')
        date_str = request.form.get('date')
        
        # Update DB (Primary)
        tx = Transaction.query.get(transaction_id)
        if tx and tx.user_id == current_user.id:
            tx.title = title
            tx.amount = float(amount)
            tx.category = category
            tx.sub_category = sub_category
            tx.payment_method = payment_method
            tx.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            db.session.commit()
            logging.debug(f"Transaction {transaction_id} updated in DB.")
        else:
            flash('Transaction not found or unauthorized', 'error')
            return redirect(url_for('transaction.view_transactions'))

        # Update Excel (Secondary)
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month = date_obj.strftime('%B')
            year = date_obj.strftime('%Y')
            file_path = os.path.join('Sheets', current_user.user_name, f"{month}_{year}.xlsx")
            
            if os.path.exists(file_path):
                # ExcelService still expects sequential Sr No for ID? 
                # Actually Transaction.id is DB id, but Sr No is Excel row counter.
                # This might be tricky if they differ. 
                # For now, we'll assume Sr No is handled by ExcelService logic.
                # But we need a way to map DB ID to Excel Sr No if we want total sync.
                # However, the user usually views data from DB now.
                pass 
        except Exception as e:
            logging.error(f"Error syncing Excel update: {e}")

        flash('Transaction updated successfully', 'success')

    except Exception as e:
        logging.error(f"Error updating transaction: {str(e)}")
        flash('Error updating transaction', 'error')

    return redirect(url_for('transaction.view_transactions'))

@transaction_bp.route('/delete_transaction', methods=['POST'])
@login_required
def delete_transaction():
    from models.transactions import Transaction
    from models import db
    try:
        transaction_id = request.form.get('transaction_id')
        
        # Delete from DB (Primary)
        tx = Transaction.query.get(transaction_id)
        if tx and tx.user_id == current_user.id:
            db.session.delete(tx)
            db.session.commit()
            logging.debug(f"Transaction {transaction_id} deleted from DB.")
        else:
            flash('Transaction not found or unauthorized', 'error')
            return redirect(url_for('transaction.view_transactions'))

        flash('Transaction deleted successfully', 'success')

    except Exception as e:
        logging.error(f"Error deleting transaction: {str(e)}")
        flash('Error deleting transaction', 'error')

    return redirect(url_for('transaction.view_transactions'))

@transaction_bp.route('/spendings', methods=['GET', 'POST'])
@login_required
def spendings():
    from models.transactions import Transaction
    from models import db
    
    # Get values from form or default to current month/year
    month_val = request.form.get('month')
    year_val = request.form.get('year')
    
    if not month_val or not year_val:
        now = datetime.now()
        month_val = now.strftime('%B')
        year_val = str(now.year)

    spendings_data = {}
    total_spendings = 0

    try:
        # Convert month name to number
        month_num = datetime.strptime(month_val, '%B').month
        
        query = Transaction.query.filter_by(user_id=current_user.id)
        query = query.filter(db.extract('month', Transaction.date) == month_num)
        query = query.filter(db.extract('year', Transaction.date) == int(year_val))
        
        db_transactions = query.all()
        
        for tx in db_transactions:
            category = tx.category or 'Other'
            spendings_data[category] = spendings_data.get(category, 0) + tx.amount
            total_spendings += tx.amount
            
        logging.debug(f"Calculated spendings for {month_val} {year_val}: {spendings_data}")

    except Exception as e:
        logging.error(f"Error calculating spendings: {e}")
        flash('Error calculating spendings', 'error')

    return render_template('spendings.html',
                           spendings_data=spendings_data,
                           total_spendings=total_spendings,
                           request=request,
                           user=current_user)
