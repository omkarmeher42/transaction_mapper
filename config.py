import os
from dotenv import load_dotenv

# Load .env file if running locally
if not os.getenv('PYTHONANYWHERE_SITE'):
    load_dotenv()

# Note: For PythonAnywhere, set environment variables in the web app:
# 1. Go to Web tab
# 2. Scroll to "Environment variables"
# 3. Add GMAIL_USER and GMAIL_APP_PASSWORD variables
# 4. Click "Reload" to apply changes

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
