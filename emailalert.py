# email_alert.py
import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def alert_system(product, link, price):
    email_id = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    if not email_id or not email_pass:
        print("Email credentials not set")
        return

    msg = EmailMessage()
    msg['Subject'] = f'Price Drop Alert: {product} now at ₹{price}'
    msg['From'] = email_id
    msg['To'] = email_id
    msg.set_content(f'''
    Great news! The price has dropped!
    
    Product: {product}
    Current Price: ₹{price}
    Link: {link}
    
    Happy shopping!
    ''')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_id, email_pass)
            smtp.send_message(msg)
        print("Alert sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
