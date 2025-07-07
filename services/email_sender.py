import base64
import smtplib
import pickle
from email.message import EmailMessage
from google.auth.transport.requests import Request
from config import FROM_EMAIL

def send_email_oauth2(recipient, subject, body, attachments=None):
    try:
        with open("token.pkl", "rb") as token_file:
            creds = pickle.load(token_file)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open("token.pkl", "wb") as token_file:
                pickle.dump(creds, token_file)

        access_token = creds.token
        auth_string = f"user={FROM_EMAIL}\x01auth=Bearer {access_token}\x01\x01"
        auth_bytes = base64.b64encode(auth_string.encode("utf-8"))

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = recipient
        msg.set_content(body)

        if attachments:
            for filename, file_bytes in attachments:
                msg.add_attachment(file_bytes, maintype='application', subtype='octet-stream', filename=filename)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.docmd("AUTH", "XOAUTH2 " + auth_bytes.decode())
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Email sending error:", e)
        return False
