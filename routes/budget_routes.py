from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.budget_recurring import Budget, RecurringTransaction, db
from models.transactions import Transaction
from sqlalchemy import func
from datetime import datetime

budget_bp = Blueprint('budget', __name__)

@budget_bp.route('/budgets', methods=['GET', 'POST'])
@login_required
def manage_budgets():
    if request.method == 'POST':
        category = request.form.get('category')
        amount = request.form.get('amount')
        now = datetime.now()
        
        # Check if budget for this category and month already exists
        budget = Budget.query.filter_by(
            user_id=current_user.id, 
            category=category, 
            month=now.month, 
            year=now.year
        ).first()
        
        if budget:
            budget.amount = float(amount)
        else:
            budget = Budget(
                user_id=current_user.id,
                category=category,
                amount=float(amount),
                month=now.month,
                year=now.year
            )
            db.session.add(budget)
            
        db.session.commit()
        flash(f'Budget for {category} updated!', 'success')
        return redirect(url_for('budget.manage_budgets'))

    # GET request
    now = datetime.now()
    budgets = Budget.query.filter_by(user_id=current_user.id, month=now.month, year=now.year).all()
    
    # Get actual spending per category for this month
    spending_data = db.session.query(
        Transaction.category, func.sum(Transaction.amount)
    ).filter(
        Transaction.user_id == current_user.id,
        db.extract('month', Transaction.date) == now.month,
        db.extract('year', Transaction.date) == now.year
    ).group_by(Transaction.category).all()
    
    spending_dict = {s[0]: float(s[1]) for s in spending_data}
    
    budget_list = []
    for b in budgets:
        spent = spending_dict.get(b.category, 0)
        budget_list.append({
            'category': b.category,
            'budget_amount': b.amount,
            'spent_amount': spent,
            'remaining': b.amount - spent,
            'percent': min(100, (spent / b.amount * 100)) if b.amount > 0 else 0
        })
        
    return render_template('budgets.html', budgets=budget_list)

@budget_bp.route('/recurring', methods=['GET', 'POST'])
@login_required
def manage_recurring():
    if request.method == 'POST':
        title = request.form.get('title')
        amount = request.form.get('amount')
        category = request.form.get('category')
        sub_category = request.form.get('sub_category')
        payment_method = request.form.get('payment_method')
        day = request.form.get('day_of_month')
        
        recurring = RecurringTransaction(
            user_id=current_user.id,
            title=title,
            amount=float(amount),
            category=category,
            sub_category=sub_category,
            payment_method=payment_method,
            day_of_month=int(day)
        )
        db.session.add(recurring)
        db.session.commit()
        flash('Recurring transaction added!', 'success')
        return redirect(url_for('budget.manage_recurring'))
        
    recurring_txs = RecurringTransaction.query.filter_by(user_id=current_user.id).all()
    return render_template('recurring.html', recurring_transactions=recurring_txs)

@budget_bp.route('/recurring/delete/<int:id>', methods=['POST'])
@login_required
def delete_recurring(id):
    rtx = RecurringTransaction.query.get(id)
    if rtx and rtx.user_id == current_user.id:
        db.session.delete(rtx)
        db.session.commit()
        flash('Recurring transaction deleted.', 'success')
    return redirect(url_for('budget.manage_recurring'))
