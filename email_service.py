"""
email_service.py
----------------
Central email dispatcher for KwiqBuy.

All send_* functions build an HTML body from a Jinja template and
send it via Flask-Mail. Sends happen on a background thread so the
HTTP response isn't blocked by SMTP latency.
"""
from threading import Thread
from flask import render_template, current_app
from flask_mail import Message
from mail_ext import mail


# ---------- Low-level dispatch ----------
def _send_async(app, msg):
    """Send mail on a background thread using app context."""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(
                f"[MAIL] Sent '{msg.subject}' → {msg.recipients}"
            )
        except Exception as e:
            current_app.logger.error(
                f"[MAIL] FAILED '{msg.subject}' → {msg.recipients}: {e}"
            )


def _send(subject, recipients, html_body):
    """Queue an email for async delivery."""
    app = current_app._get_current_object()
    msg = Message(subject=subject, recipients=recipients, html=html_body)
    Thread(target=_send_async, args=(app, msg), daemon=True).start()


# ---------- Waitlist ----------
def send_waitlist_emails(user_email, source, admin_email, base_url):
    # Admin notification
    _send(
        subject=f"🎉 New Waitlist Signup — {user_email}",
        recipients=[admin_email],
        html_body=render_template(
            "emails/waitlist_admin.html",
            user_email=user_email,
            source=source,
            base_url=base_url,
        ),
    )
    # User confirmation
    _send(
        subject="You're on the KwiqBuy waitlist! 🚀",
        recipients=[user_email],
        html_body=render_template(
            "emails/waitlist_user.html",
            user_email=user_email,
            base_url=base_url,
        ),
    )


# ---------- Vendor registration ----------
def send_vendor_registration_emails(
    owner_name, owner_email, store_name, store_category, admin_email, base_url
):
    # Admin notification
    _send(
        subject=f"🏪 New Vendor Application — {store_name}",
        recipients=[admin_email],
        html_body=render_template(
            "emails/vendor_admin.html",
            owner_name=owner_name,
            owner_email=owner_email,
            store_name=store_name,
            store_category=store_category,
            base_url=base_url,
        ),
    )
    # Vendor confirmation
    _send(
        subject=f"Welcome to KwiqBuy — {store_name} application received ✅",
        recipients=[owner_email],
        html_body=render_template(
            "emails/vendor_user.html",
            owner_name=owner_name,
            store_name=store_name,
            store_category=store_category,
            base_url=base_url,
        ),
    )


# ---------- Vendor status change ----------
def send_vendor_status_email(owner_email, owner_name, store_name, status, base_url):
    if status == "Approved":
        subject = f"🎉 Your KwiqBuy storefront '{store_name}' is APPROVED!"
        template = "emails/vendor_approved.html"
    elif status == "Rejected":
        subject = f"Update on your KwiqBuy application — {store_name}"
        template = "emails/vendor_rejected.html"
    else:
        return  # only notify on final decisions

    _send(
        subject=subject,
        recipients=[owner_email],
        html_body=render_template(
            template,
            owner_name=owner_name,
            store_name=store_name,
            base_url=base_url,
        ),
    )


from datetime import datetime

def _send(subject, recipients, html_body):
    """Queue an email for async delivery."""
    app = current_app._get_current_object()
    msg = Message(subject=subject, recipients=recipients, html=html_body)
    Thread(target=_send_async, args=(app, msg), daemon=True).start()


# ---------- System user creation ----------
def send_user_creation_emails(
    admin_email, new_user_email, new_user_name, new_user_role,
    plain_password, base_url,
):
    # Notify admin
    _send(
        subject=f"🔐 New System User Created — {new_user_name} ({new_user_role})",
        recipients=[admin_email],
        html_body=render_template(
            "emails/user_created_admin.html",
            new_user_name=new_user_name,
            new_user_email=new_user_email,
            new_user_role=new_user_role,
            base_url=base_url,
        ),
    )
    # Send credentials to the new user
    _send(
        subject="Your KwiqBuy Admin Account Credentials",
        recipients=[new_user_email],
        html_body=render_template(
            "emails/user_created_credentials.html",
            new_user_name=new_user_name,
            new_user_email=new_user_email,
            new_user_role=new_user_role,
            plain_password=plain_password,
            base_url=base_url,
        ),
    )