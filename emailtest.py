import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASS")
recipient_email = "ma1303507@gmail.com"  # change to your real address

msg = MIMEText("Test email from Python SMTP!")
msg["Subject"] = "Test Email"
msg["From"] = sender_email
msg["To"] = recipient_email

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    print("✅ Email sent!")
except Exception as e:
    print("❌ Failed to send:", str(e))
