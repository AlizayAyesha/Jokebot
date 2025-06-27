# otp_sender.py
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("MAILER_SEND_API_KEY")
SENDER_EMAIL = os.getenv("MAILER_SEND_SENDER")

def send_otp_email(email, code):
    if not API_KEY or not SENDER_EMAIL:
        print("❌ Error: MAILER_SEND_API_KEY or MAILER_SEND_SENDER not set in .env file")
        return False

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "from": {
            "email": SENDER_EMAIL,
            "name": "JokeBot"
        },
        "to": [{"email": email}],
        "subject": "🔐 Your OTP Code",
        "text": f"Your OTP is: {code}"
    }

    try:
        res = requests.post("https://api.mailersend.com/v1/email", headers=headers, json=data)
        if res.status_code == 202:
            print(f"✅ OTP sent successfully to {email}")
            return True
        else:
            print(f"❌ Error sending OTP to {email}: Status={res.status_code}, Response={res.text}")
            try:
                error_details = res.json()
                print("Error Details:", error_details)
            except:
                print("No JSON response available.")
            return False
    except Exception as e:
        print(f"❌ Exception while sending OTP to {email}: {str(e)}")
        return False