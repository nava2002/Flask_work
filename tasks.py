import os
import requests
from dotenv import load_dotenv

load_dotenv()

Domain = os.getenv("MAILGUN_DOMAIN")
api_key = os.getenv("MAILGUN_API_KEY")

def send_simple_message(to,subject,body):
    return requests.post(
  		f"https://api.mailgun.net/v3/{Domain}/messages",
  		auth=("api", api_key),
  		data={"from": f"Mailgun Sandbox <postmaster@{Domain}>",
			"to": to,
  			"subject": subject,
  			"text": body})
    
def send_user_registration_email(email,username):
    return send_simple_message(
        to=email,
        subject="Successfully signed up",
        body=f"Hi {username}, Welcom to the Stores REST API"
    )