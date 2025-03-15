import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
from dotenv import load_dotenv
import os

load_dotenv()

def send_email(to_address, subject, body, attachment):
    # Gmail SMTP Configuration
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    if not gmail_user or not gmail_password:
        raise ValueError("Gmail credentials not found in environment variables")

    # Create email message
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach file
    part = MIMEBase('application', 'octet-stream')
    attachment.seek(0)
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    
    part.add_header(
        'Content-Disposition',
        'attachment',
        filename=attachment.filename
    )
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
            logging.info(f"Email sent successfully to {to_address}")
            return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        raise e
