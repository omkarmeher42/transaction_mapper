from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.budget_recurring import QuickCard, db
from models.transactions import Transaction
from datetime import datetime

quick_bp = Blueprint('quick', __name__)

@quick_bp.route('/quick_map', methods=['GET', 'POST'])
@login_required
def quick_map():
    if request.method == 'POST':
        # Logging a transaction from a quick card or creating a new card
        action = request.form.get('action')
        
        if action == 'log':
            card_id = request.form.get('card_id')
            card = QuickCard.query.get(card_id)
            if card and card.user_id == current_user.id:
                new_tx = Transaction(
                    user_id=current_user.id,
                    date=datetime.now().date(),
                    title=card.title,
                    amount=card.amount,
                    category=card.category,
                    sub_category=card.sub_category,
                    payment_method=card.payment_method
                )
                db.session.add(new_tx)
                db.session.commit()
                flash(f'Transaction "{card.title}" logged successfully!', 'success')
            return redirect(url_for('quick.quick_map'))
            
        elif action == 'create':
            title = request.form.get('title')
            amount = request.form.get('amount')
            category = request.form.get('category')
            sub_category = request.form.get('sub_category')
            payment_method = request.form.get('payment_method')
            
            new_card = QuickCard(
                user_id=current_user.id,
                title=title,
                amount=float(amount),
                category=category,
                sub_category=sub_category,
                payment_method=payment_method
            )
            db.session.add(new_card)
            db.session.commit()
            flash('Quick card created!', 'success')
            return redirect(url_for('quick.quick_map'))
        
        elif action == 'update':
            card_id = request.form.get('card_id')
            card = QuickCard.query.get(card_id)
            if card and card.user_id == current_user.id:
                card.title = request.form.get('title')
                card.amount = float(request.form.get('amount'))
                card.category = request.form.get('category')
                card.payment_method = request.form.get('payment_method')
                db.session.commit()
                flash('Quick card updated!', 'success')
            return redirect(url_for('quick.quick_map'))

    # GET request
    cards = QuickCard.query.filter_by(user_id=current_user.id).all()
    return render_template('quick_map.html', quick_cards=cards)

@quick_bp.route('/quick_map/delete/<int:id>', methods=['POST'])
@login_required
def delete_card(id):
    card = QuickCard.query.get(id)
    if card and card.user_id == current_user.id:
        db.session.delete(card)
        db.session.commit()
        flash('Quick card deleted.', 'success')
    return redirect(url_for('quick.quick_map'))
