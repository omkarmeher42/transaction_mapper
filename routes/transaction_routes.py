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
    transaction_day = request.form.get('transaction_day', '')
    search_query = request.form.get('search_query', '')
    category_filter = request.form.get('category', '')
    sort_by = request.form.get('sort_by', 'date_desc')
    
    if not month_val or not year_val:
        now = datetime.now()
        month_val = now.strftime('%B')
        year_val = str(now.year)

    logging.debug(f"Viewing transactions: {month_val} {year_val}, Day: {transaction_day}, Search: {search_query}, Category: {category_filter}, Sort: {sort_by}")

    # Query from DB
    try:
        query = Transaction.query.filter_by(user_id=current_user.id)
        
        # Date Filter - if specific day is selected, use it
        if transaction_day:
            try:
                day = int(transaction_day)
                month_num = datetime.strptime(month_val, '%B').month
                query = query.filter(db.extract('day', Transaction.date) == day)
                query = query.filter(db.extract('month', Transaction.date) == month_num)
                query = query.filter(db.extract('year', Transaction.date) == int(year_val))
            except (ValueError, AttributeError):
                # If day is invalid, fall back to month/year filter
                month_num = datetime.strptime(month_val, '%B').month
                query = query.filter(db.extract('month', Transaction.date) == month_num)
                query = query.filter(db.extract('year', Transaction.date) == int(year_val))
        else:
            # Convert month name to number
            month_num = datetime.strptime(month_val, '%B').month
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
                           transaction_day=transaction_day,
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
    from models.budget_recurring import Budget
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
    insights = {}

    try:
        # Convert month name to number
        month_num = datetime.strptime(month_val, '%B').month
        current_year = int(year_val)
        
        # Get current month transactions
        query = Transaction.query.filter_by(user_id=current_user.id)
        query = query.filter(db.extract('month', Transaction.date) == month_num)
        query = query.filter(db.extract('year', Transaction.date) == current_year)
        
        db_transactions = query.all()
        
        for tx in db_transactions:
            category = tx.category or 'Other'
            spendings_data[category] = spendings_data.get(category, 0) + tx.amount
            total_spendings += tx.amount
            
        logging.debug(f"Calculated spendings for {month_val} {year_val}: {spendings_data}")
        
        # Calculate additional metrics for the dashboard
        top_category = max(spendings_data.items(), key=lambda x: x[1])[0] if spendings_data else None
        transaction_count = len(db_transactions)
        daily_average = round(total_spendings / 30, 2) if total_spendings > 0 else 0
        
        # ===== INSIGHTS CALCULATION =====
        
        # 1. Top 3 and Bottom 3 categories
        sorted_categories = sorted(spendings_data.items(), key=lambda x: x[1], reverse=True)
        insights['top_3_categories'] = sorted_categories[:3] if len(sorted_categories) > 0 else []
        insights['bottom_3_categories'] = sorted_categories[-3:] if len(sorted_categories) > 3 else []
        
        # 2. Previous month comparison
        prev_month_num = month_num - 1 if month_num > 1 else 12
        prev_year = current_year if month_num > 1 else current_year - 1
        
        prev_query = Transaction.query.filter_by(user_id=current_user.id)
        prev_query = prev_query.filter(db.extract('month', Transaction.date) == prev_month_num)
        prev_query = prev_query.filter(db.extract('year', Transaction.date) == prev_year)
        prev_transactions = prev_query.all()
        
        prev_total = sum(tx.amount for tx in prev_transactions) if prev_transactions else 0
        
        if prev_total > 0:
            spending_change = total_spendings - prev_total
            spending_change_percent = round((spending_change / prev_total) * 100, 1)
            insights['prev_month_spending'] = round(prev_total, 2)
            insights['spending_change'] = round(spending_change, 2)
            insights['spending_change_percent'] = spending_change_percent
            insights['spending_trend'] = 'up' if spending_change > 0 else 'down'
        else:
            insights['prev_month_spending'] = 0
            insights['spending_change'] = total_spendings
            insights['spending_change_percent'] = 0
            insights['spending_trend'] = 'stable'
        
        # 3. Category changes (which categories increased/decreased compared to previous month)
        prev_spendings_data = {}
        for tx in prev_transactions:
            category = tx.category or 'Other'
            prev_spendings_data[category] = prev_spendings_data.get(category, 0) + tx.amount
        
        category_changes = []
        for category, current_amount in spendings_data.items():
            prev_amount = prev_spendings_data.get(category, 0)
            if prev_amount > 0:
                change = round(current_amount - prev_amount, 2)
                change_percent = round((change / prev_amount) * 100, 1)
                category_changes.append({
                    'category': category,
                    'current': current_amount,
                    'previous': prev_amount,
                    'change': change,
                    'change_percent': change_percent,
                    'trend': 'up' if change > 0 else 'down'
                })
        
        # Sort by change amount
        insights['category_changes'] = sorted(category_changes, key=lambda x: abs(x['change']), reverse=True)[:5]
        
        # 4. Budget analysis
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        budget_alerts = []
        total_budget = 0
        
        for budget in budgets:
            if budget.category in spendings_data:
                spent = spendings_data[budget.category]
                budget_limit = budget.amount
                total_budget += budget_limit
                
                if spent > budget_limit:
                    overspend = round(spent - budget_limit, 2)
                    overspend_percent = round((overspend / budget_limit) * 100, 1)
                    budget_alerts.append({
                        'category': budget.category,
                        'limit': budget_limit,
                        'spent': spent,
                        'overspend': overspend,
                        'overspend_percent': overspend_percent,
                        'status': 'alert'
                    })
        
        insights['budget_alerts'] = budget_alerts
        insights['total_budget'] = round(total_budget, 2)
        insights['budget_utilization'] = round((total_spendings / total_budget * 100), 1) if total_budget > 0 else 0
        
        # 5. Daily spending pattern (average per day, high day, low day)
        daily_spending = {}
        for tx in db_transactions:
            day = tx.date.day
            daily_spending[day] = daily_spending.get(day, 0) + tx.amount
        
        if daily_spending:
            max_day = max(daily_spending.items(), key=lambda x: x[1])
            min_day = min(daily_spending.items(), key=lambda x: x[1])
            insights['highest_spending_day'] = (max_day[0], round(max_day[1], 2))
            insights['lowest_spending_day'] = (min_day[0], round(min_day[1], 2))
        
        # 6. Recommendations based on patterns
        recommendations = []
        if insights['spending_trend'] == 'up' and insights['spending_change_percent'] > 10:
            recommendations.append({
                'type': 'warning',
                'text': f"Your spending increased by {insights['spending_change_percent']}% compared to last month. Consider reviewing your expenses."
            })
        
        if budget_alerts:
            recommendations.append({
                'type': 'alert',
                'text': f"You've exceeded budget in {len(budget_alerts)} category(ies). Review your spending limits."
            })
        
        if sorted_categories and sorted_categories[0][1] > total_spendings * 0.7:
            recommendations.append({
                'type': 'info',
                'text': f"Your top category ({sorted_categories[0][0]}) accounts for {round(sorted_categories[0][1]/total_spendings*100, 1)}% of spending. This is concentrated."
            })
        
        if daily_average > 0 and insights.get('highest_spending_day'):
            high_day_spending = insights['highest_spending_day'][1]
            if high_day_spending > daily_average * 3:
                recommendations.append({
                    'type': 'info',
                    'text': f"Day {insights['highest_spending_day'][0]} had unusually high spending (₹{high_day_spending}). Check for bulk purchases."
                })
        
        insights['recommendations'] = recommendations

    except Exception as e:
        logging.error(f"Error calculating spendings: {e}")
        flash('Error calculating spendings', 'error')
        top_category = None
        transaction_count = 0
        daily_average = 0
        insights = {}

    return render_template('spendings.html',
                           spendings_data=spendings_data,
                           total_spendings=total_spendings,
                           top_category=top_category,
                           transaction_count=transaction_count,
                           daily_average=daily_average,
                           insights=insights,
                           request=request,
                           user=current_user)
