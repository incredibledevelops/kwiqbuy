# test_mail.py
from flask import Flask
from flask_mail import Mail, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="KwiqBuy Test Email",
        recipients=[app.config["ADMIN_EMAIL"]],
        html="<h1>✅ Gmail SMTP works!</h1>"
    )
    mail.send(msg)
    print("Sent!")