import asyncio
import logging
import smtplib
from email import message_from_bytes
from aiosmtpd.controller import Controller
from dotenv import load_dotenv
import os

load_dotenv()

class CustomHandler:
    async def handle_EHLO(self, server, session, envelope, hostname):
        session.host_name = hostname
        return '250 OK'

    async def handle_MAIL(self, server, session, envelope, address, mail_options=None):
        envelope.mail_from = address
        return '250 OK'

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options=None):
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        logging.info(f'Mail from: {envelope.mail_from}')
        logging.info(f'Mail to: {envelope.rcpt_tos}')
        
        try:
            # Create message from received data
            msg = message_from_bytes(envelope.content)
            
            # Gmail SMTP settings
            gmail_smtp = "smtp.gmail.com"
            gmail_port = 587
            gmail_user = os.getenv('GMAIL_USER')
            gmail_password = os.getenv('GMAIL_APP_PASSWORD')
            
            if not gmail_user or not gmail_password:
                raise ValueError("Gmail credentials not found in environment variables")
            
            # Forward via Gmail SMTP
            with smtplib.SMTP(gmail_smtp, gmail_port) as server:
                server.starttls()
                server.login(gmail_user, gmail_password)
                server.send_message(msg)
                logging.info(f'Email forwarded to {envelope.rcpt_tos}')
            
            return '250 Message accepted and forwarded'
        except Exception as e:
            logging.error(f'Failed to forward email: {str(e)}')
            return '550 Failed to forward message'
        
    async def handle_RSET(self, server, session, envelope):
        envelope = session.envelope = server.envelope_class()
        return '250 OK'
        
    async def handle_NOOP(self, server, session, envelope):
        return '250 OK'
        
    async def handle_QUIT(self, server, session, envelope):
        return '221 Bye'

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = CustomHandler()
    controller = Controller(
        handler, 
        hostname='127.0.0.1',
        port=1025
    )
    
    controller.start()
    logging.info(f'SMTP server running on {controller.hostname}:{controller.port}')
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info('Shutting down server')
        controller.stop()

if __name__ == "__main__":
    asyncio.run(main())