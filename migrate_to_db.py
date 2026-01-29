import os
import pandas as pd
from app import create_app
from models.users import User, db
from models.transactions import Transaction
from datetime import datetime

def migrate_data():
    app = create_app()
    with app.app_context():
        # Ensure tables are created
        db.create_all()
        
        users = User.query.all()
        print(f"Found {len(users)} users.")
        
        for user in users:
            print(f"Processing user: {user.user_name}")
            user_dir = os.path.join('Sheets', user.user_name)
            
            if not os.path.exists(user_dir):
                print(f"No sheets directory for user {user.user_name}")
                continue
                
            for file_name in os.listdir(user_dir):
                if file_name.endswith('.xlsx'):
                    file_path = os.path.join(user_dir, file_name)
                    print(f"  Reading file: {file_name}")
                    
                    try:
                        # Skip the first two rows (Title and merged Total Amount header)
                        df = pd.read_excel(file_path, skiprows=2)
                        
                        # Map columns
                        column_mapping = {
                            'Sr No': 'sr_no',
                            'Date': 'date',
                            'Transaction Title': 'title',
                            'Amount': 'amount',
                            'Category': 'category',
                            'Sub Category': 'sub_category',
                            'Payment Method': 'payment_method'
                        }
                        
                        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
                        df = df.rename(columns=existing_columns)
                        
                        # Drop fully empty rows
                        df = df.dropna(subset=['title', 'amount'], how='all')
                        
                        for _, row in df.iterrows():
                            # Skip if title or amount is empty (could be the SUM row or empty space)
                            if pd.isna(row.get('title')) or pd.isna(row.get('amount')):
                                continue
                                
                            try:
                                # Parse date safely
                                date_val = row.get('date')
                                if isinstance(date_val, str):
                                    date_obj = datetime.strptime(date_val, '%Y-%m-%d').date()
                                elif hasattr(date_val, 'date'):
                                    date_obj = date_val.date()
                                else:
                                    date_obj = datetime.utcnow().date()
                                    
                                # Check if transaction already exists (optional, but good for idempotency)
                                # For simplicity, we'll just add them. 
                                # A better check would be (user_id, date, title, amount)
                                
                                transaction = Transaction(
                                    user_id=user.id,
                                    date=date_obj,
                                    title=str(row.get('title', '')),
                                    amount=float(row.get('amount', 0)),
                                    category=str(row.get('category', 'Other')),
                                    sub_category=str(row.get('sub_category', '')),
                                    payment_method=str(row.get('payment_method', ''))
                                )
                                db.session.add(transaction)
                            except Exception as e:
                                print(f"    Error processing row: {e}")
                                
                        db.session.commit()
                        print(f"  Completed migration for {file_name}")
                        
                    except Exception as e:
                        print(f"  Error reading {file_name}: {e}")
                        db.session.rollback()

if __name__ == "__main__":
    migrate_data()
