"""
mail_ext.py
-----------
Isolated Flask-Mail instance so `app.py` and `email_service.py`
can both import it without circular dependency headaches.
"""
from flask_mail import Mail

mail = Mail()