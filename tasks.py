import os
import requests
from dotenv import load_dotenv
import jinja2

load_dotenv()

template_loader = jinja2.FileSystemLoader("templates")
template_env = jinja2.Environment(loader=template_loader)

def render_template(template_filename,**context):
    return template_env.get_template(template_filename).render(**context)

Domain = os.getenv("MAILGUN_DOMAIN")
api_key = os.getenv("MAILGUN_API_KEY")

def send_simple_message(to,subject,body,html):
    return requests.post(
  		f"https://api.mailgun.net/v3/{Domain}/messages",
  		auth=("api", api_key),
  		data={"from": f"Mailgun Sandbox <postmaster@{Domain}>",
			"to": to,
  			"subject": subject,
  			"text": body,
            "html":html
        })
    
def send_user_registration_email(email,username):
    return send_simple_message(
        to=email,
        subject="Successfully signed up",
        body=f"Hi {username}, Welcom to the Stores REST API",
        html=render_template("email/action.html", username=username)
    )