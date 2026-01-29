# Transaction Mapper Web App

Transaction Mapper is a robust Flask-based web application designed to simplify personal financial tracking. It allows users to securely log expenses, categorize transactions, and visualize spending habits through a modern, responsive interface.

## 🚀 Key Features

### 🌟 Core Functionality
- **User Authentication**: Secure registration and login system protected by Flask-Login.
- **Transaction Logging**: detailed entry form for transactions including title, amount, category, sub-category, and payment method.
- **Excel Integration**: Automatically organizes transactions into month-wise Excel files (`.xlsx`) for easy data portability.
- **Dynamic Spendings View**: Interactive visual breakdown of your spending by category and month.
- **Download & Email**: One-click download of monthly reports or direct email delivery.

### 🎨 Modern UI/UX
- **Quick Transaction Map**: Create "Quick Cards" for your most frequent expenses (e.g., daily coffee, bus fare) to log them with a single tap.
- **Responsive Design**: Fully optimized for all devices, featuring a custom mobile hamburger menu and adaptive layouts.
- **Theme Support**: Seamlessly switch between **Light** and **Dark** modes with persistent user preference.
- **Smart Notifications**: Non-intrusive, auto-dismissing toast notifications for user feedback.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite (SQLAlchemy)
- **Data Analysis**: Pandas, Openpyxl
- **Frontend**: HTML5, CSS3 (Vanilla + Glassmorphism), JavaScript
- **Security**: Werkzeug Security (Password Hashing)
- **Email**: SMTP integration

## 📂 Project Structure

```text
transaction_mapper/
├── app.py              # Application entry point & configuration
├── forms.py            # Flask-WTF forms definitions
├── models/             # Database models (User, etc.)
├── routes/             # Blueprint-based route controllers
├── services/           # Business logic (Excel, Email)
├── static/             # CSS (dashboard.css, notifications.css) & JS
├── templates/          # Jinja2 HTML templates
├── Sheets/             # User-specific Excel transaction files
└── instance/           # Local SQLite database
```

## ⚙️ Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd transaction_mapper
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Create a `.env` file in the root directory for email functionality (optional):
```env
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

### Running the App
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

## 📝 Usage Guide

1. **Dashboard**: Get an at-a-glance view of your total spending and top categories.
2. **Map Transaction**: Log a new expense manually.
3. **Quick Map**: Set up one-tap cards for recurring expenses like "Commute" or "Coffee".
4. **View Transactions**: Filter, search, edit, or delete past entries.
5. **Budgets**: Set monthly limits for specific categories and track progress.
6. **Download**: Export your financial data to Excel.

---
*Created for efficient and elegant financial tracking.*
