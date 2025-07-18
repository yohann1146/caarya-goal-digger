import jwt
import os
import smtplib
import requests
from bs4 import BeautifulSoup
import json

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))

def create_access_token(id: int):
    access_token = jwt.encode({"sub": id}, SECRET_KEY, algorithm=ALGORITHM)
    return access_token

def send_verification(email: str, token: str):
    msg = EmailMessage()
    msg["Subject"] = "Verify your email - Goal Digger"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    verification_link = f"http://localhost:8000/verify-email?email={email}&token={token}"
    msg.set_content(
        f"Hi,\n\nPlease verify your email by clicking the link below:\n{verification_link}\n\n"
        "If you did not register, please ignore this message.\n\nThanks for using Goal Digger!"
    )
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")

def send_reset_password(email: str):
    msg = EmailMessage()
    msg["Subject"] = "Password Reset Request - Goal Digger"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    reset_link = f"http://localhost:8000/reset-password?email={email}"
    msg.set_content(
        f"Hi,\n\nWe just received a request to reset your password.\nPlease visit the following link to reset your password:\n{reset_link}\n\n"
        "If you did not create this request, please secure your account immediately.\n\nThanks for using Goal Digger!"
    )
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print(f"Reset password email sent to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")

def get_top_movers():
    def fetch_data(url):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        html = BeautifulSoup(response.text, 'html.parser')

        data = []
        table = html.find('table')
        if not table:
            return data

        rows = table.find_all('tr')[1:11]
        for r in rows:
            cols = r.find_all('td')
            if len(cols) >= 5:
                name = cols[1].text.strip()
                change = cols[5].text.strip()
                data.append({
                    "name": name,
                    "change": change
                })

        return data

    gainers_url = "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=10"
    losers_url = "https://finance.yahoo.com/markets/stocks/losers/?start=0&count=10"

    top_gainers = fetch_data(gainers_url)
    top_losers = fetch_data(losers_url)

    return top_gainers, top_losers
