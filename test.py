import smtplib
from email.message import EmailMessage

def send_test_email():
    msg = EmailMessage()
    msg.set_content("This is a test email")
    msg["Subject"] = "Test Email"
    msg["From"] = "test@example.com"
    msg["To"] = "recipient@example.com"
    
    with smtplib.SMTP('127.0.0.1', 1025) as server:
        server.send_message(msg)
        print("Test email sent!")

if __name__ == "__main__":
    send_test_email()