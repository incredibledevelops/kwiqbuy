from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, abort, after_this_request, send_from_directory,
    make_response
)
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ServerSelectionTimeoutError
from bson.objectid import ObjectId
from bson.errors import InvalidId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from functools import wraps
from config import Config
from mail_ext import mail
import email_service
import re
import uuid
import os

app = Flask(__name__)
app.config.from_object(Config)

# ------------------ Extensions ------------------
mail.init_app(app)


# ------------------ Global Jinja variables ------------------
@app.context_processor
def inject_globals():
    """Make these available in every template (incl. email templates)."""
    site_mode = get_site_mode()
    return {
        "now_year": datetime.now(timezone.utc).year,
        "app_name": "KwiqBuy",
        "site_mode": site_mode,
        "site_mode_label": SITE_MODES.get(site_mode, {}).get("label", "Coming Soon"),
    }


# ------------------ Site Mode Configuration ------------------
SITE_MODES = {
    "coming_soon": {
        "label": "Coming Soon",
        "template": "index.html",
        "description": "Pre-launch waitlist mode",
        "icon": "rocket",
        "color": "brand",
    },
    "under_construction": {
        "label": "Under Construction",
        "template": "under-construction.html",
        "description": "Site is being built",
        "icon": "hammer",
        "color": "amber",
    },
    "live": {
        "label": "Live",
        "template": "shop.html",
        "description": "Full e-commerce experience",
        "icon": "shopping-bag",
        "color": "emerald",
    },
}

DEFAULT_SITE_MODE = "coming_soon"


# ------------------ MongoDB ------------------
client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
db = client[app.config["MONGO_DB_NAME"]]

users_col    = db["users"]
waitlist_col = db["waitlist"]
vendors_col  = db["vendors"]
audit_col    = db["audit_logs"]
views_col    = db["page_views"]
settings_col = db["settings"]  # NEW: For site settings


# ------------------ Non-fatal bootstrap ------------------
def bootstrap_indexes():
    """Create indexes once at startup. Non-fatal if DB is down."""
    try:
        users_col.create_index("email", unique=True)
        waitlist_col.create_index("email", unique=True)
        vendors_col.create_index("owner_email", unique=True)
        views_col.create_index("session_id")
        views_col.create_index("timestamp")
        settings_col.create_index("key", unique=True)
        client.admin.command("ping")
        safe_uri = app.config["MONGO_URI"].split("@")[-1]
        print(f"✅ MongoDB connected → {safe_uri}")
    except ServerSelectionTimeoutError as e:
        print(f"\n⚠️  MongoDB unreachable at startup: {e}")
        print("   App will keep running — admin will show an offline overlay.\n")


bootstrap_indexes()


# ------------------ Seed default users ------------------
def seed_users():
    try:
        defaults = [
            {"email": "admin@kwiqbuy.com",   "password": "password123",
             "full_name": "Super Admin",     "role": "Admin"},
            {"email": "manager@kwiqbuy.com", "password": "password123",
             "full_name": "Jane Marketing",  "role": "Manager"},
        ]
        for d in defaults:
            if not users_col.find_one({"email": d["email"]}):
                users_col.insert_one({
                    "email": d["email"],
                    "password_hash": generate_password_hash(d["password"]),
                    "full_name": d["full_name"],
                    "role": d["role"],
                    "status": "Active",
                    "created_at": datetime.now(timezone.utc),
                })
    except ServerSelectionTimeoutError:
        print("⚠️  seed_users() skipped — MongoDB unreachable.")


seed_users()


# ------------------ Seed default settings ------------------
def seed_settings():
    try:
        if not settings_col.find_one({"key": "site_mode"}):
            settings_col.insert_one({
                "key": "site_mode",
                "value": DEFAULT_SITE_MODE,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": "system",
            })
    except ServerSelectionTimeoutError:
        print("⚠️  seed_settings() skipped — MongoDB unreachable.")


seed_settings()


# ------------------ Helpers ------------------
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def utcnow():
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def get_client_ip():
    return (
        request.headers.get("X-Forwarded-For", request.remote_addr or "0.0.0.0")
        .split(",")[0]
        .strip()
    )


def current_session_id():
    """Read the visitor's session cookie (set in before_request)."""
    return request.cookies.get("session_id") or "anon"


def get_site_mode():
    """Get the current site mode from database."""
    try:
        setting = settings_col.find_one({"key": "site_mode"})
        if setting:
            return setting.get("value", DEFAULT_SITE_MODE)
    except ServerSelectionTimeoutError:
        pass
    return DEFAULT_SITE_MODE


def set_site_mode(mode):
    """Set the site mode in database."""
    if mode not in SITE_MODES:
        return False
    try:
        settings_col.update_one(
            {"key": "site_mode"},
            {
                "$set": {
                    "value": mode,
                    "updated_at": utcnow(),
                    "updated_by": session.get("user", {}).get("email", "unknown"),
                }
            },
            upsert=True,
        )
        return True
    except ServerSelectionTimeoutError:
        return False


def log_audit(action, target, actor=None):
    """Write an audit log entry. Safely ignores malformed actor IDs and DB downtime."""
    actor = actor or session.get("user")
    actor_id = None
    actor_role = "Anonymous"

    if actor:
        actor_role = actor.get("role", "Anonymous")
        raw_id = actor.get("id")
        if raw_id:
            try:
                actor_id = ObjectId(raw_id) if isinstance(raw_id, str) else raw_id
            except (InvalidId, TypeError):
                actor_id = None

    try:
        audit_col.insert_one({
            "timestamp": utcnow(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "event_action": action,
            "target_resource": target,
            "ip_address": get_client_ip(),
        })
    except ServerSelectionTimeoutError:
        pass


def db_online():
    """Return True if MongoDB responds to a ping within the timeout."""
    try:
        client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False


def get_public_counters():
    """
    Return (waitlist_count, vendor_count) for public-facing social proof.
    Falls back to (0, 0) if the DB is unreachable — never raises.
    """
    waitlist_count = 0
    vendor_count = 0
    try:
        waitlist_count = waitlist_col.count_documents({})
        # Count Pending + Approved as "secured early access" — Rejected don't count
        vendor_count = vendors_col.count_documents(
            {"status": {"$in": ["Pending", "Approved"]}}
        )
    except ServerSelectionTimeoutError:
        app.logger.warning("[COUNTERS] DB offline — using zero counters")
    return waitlist_count, vendor_count


# ------------------ Decorators ------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user or user.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def api_db_required(f):
    """
    Wrap JSON API routes (POST/PATCH/DELETE) ONLY.
    If MongoDB is unreachable, return JSON 503 with offline flag,
    so the JS fetch interceptor in base.html shows the overlay.

    ⚠️ Do NOT use on GET page routes — those should render normally
    so base.html loads and the overlay can appear client-side.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            app.logger.error(f"[DB_OFFLINE] {request.path}: {e}")
            return jsonify({
                "ok": False,
                "error": "Database offline. Please try again shortly.",
                "offline": True,
            }), 503
        return f(*args, **kwargs)
    return wrapper


@app.before_request
def ensure_session_id():
    """Give every visitor a long-lived session_id cookie for analytics."""
    if not request.cookies.get("session_id"):
        @after_this_request
        def set_cookie(response):
            response.set_cookie(
                "session_id",
                uuid.uuid4().hex,
                max_age=60 * 60 * 24 * 365,  # 1 year
                httponly=True,
                samesite="Lax",
            )
            return response


# ============================================================
#                     SEO ROUTES
# ============================================================

@app.route("/robots.txt")
def robots_txt():
    """Serve robots.txt for SEO."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "robots.txt",
        mimetype="text/plain"
    )


@app.route("/sitemap.xml")
def sitemap_xml():
    """Serve sitemap.xml for SEO."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "sitemap.xml",
        mimetype="application/xml"
    )


# ============================================================
#                     PUBLIC ROUTES
# ============================================================

@app.route("/")
def home():
    """
    Main entry point. Routes based on site mode:
    - coming_soon: Waitlist landing page
    - under_construction: Construction page
    - live: Full e-commerce shop
    """
    mode = get_site_mode()
    
    # Track page view (best-effort)
    try:
        views_col.insert_one({
            "page_path": "/",
            "site_mode": mode,
            "session_id": current_session_id(),
            "time_on_page": 0,
            "bounced": False,
            "timestamp": utcnow(),
        })
    except ServerSelectionTimeoutError:
        pass

    # Public counters for social proof
    waitlist_count, vendor_count = get_public_counters()

    if mode == "live":
        return render_template(
            "shop.html",
            waitlist_count=waitlist_count,
            vendor_count=vendor_count,
        )
    elif mode == "under_construction":
        return render_template(
            "under-construction.html",
            waitlist_count=waitlist_count,
            vendor_count=vendor_count,
        )
    else:
        return render_template(
            "index.html",
            waitlist_count=waitlist_count,
            vendor_count=vendor_count,
        )


@app.route("/vendor-register", methods=["GET", "POST"])
def vendor_register():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        owner_name     = (data.get("owner_name") or "").strip()
        owner_email    = (data.get("owner_email") or "").strip().lower()
        store_name     = (data.get("store_name") or "").strip()
        store_category = (data.get("store_category") or "").strip()

        if not all([owner_name, owner_email, store_name, store_category]):
            return jsonify({"ok": False, "error": "All fields are required."}), 400
        if not EMAIL_RE.match(owner_email):
            return jsonify({"ok": False, "error": "Invalid email address."}), 400

        try:
            if vendors_col.find_one({"owner_email": owner_email}):
                return jsonify({
                    "ok": False, "error": "This email is already registered."
                }), 409

            vendors_col.insert_one({
                "owner_name": owner_name,
                "owner_email": owner_email,
                "store_name": store_name,
                "store_category": store_category,
                "status": "Pending",
                "applied_at": utcnow(),
            })
        except ServerSelectionTimeoutError:
            return jsonify({
                "ok": False,
                "error": "Our servers are temporarily unavailable. Please try again in a moment.",
                "offline": True,
            }), 503

        log_audit("VENDOR_APPLY", f"Store: {store_name}")

        # 📧 Notify admin + vendor
        email_service.send_vendor_registration_emails(
            owner_name=owner_name,
            owner_email=owner_email,
            store_name=store_name,
            store_category=store_category,
            admin_email=app.config["ADMIN_EMAIL"],
            base_url=app.config["APP_BASE_URL"],
        )

        return jsonify({"ok": True, "message": "Application received!"})

    # GET — fetch counters for the form page
    waitlist_count, vendor_count = get_public_counters()

    return render_template(
        "vendor-register.html",
        waitlist_count=waitlist_count,
        vendor_count=vendor_count,
    )


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or request.form
    email  = (data.get("email") or "").strip().lower()
    source = (data.get("source") or "Direct").strip()

    if not email or not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Please enter a valid email address."}), 400

    try:
        if waitlist_col.find_one({"email": email}):
            return jsonify({
                "ok": False, "error": "You are already on the waitlist."
            }), 409

        waitlist_col.insert_one({
            "email": email,
            "source": source,
            "subscribed_at": utcnow(),
        })
    except ServerSelectionTimeoutError:
        return jsonify({
            "ok": False,
            "error": "Our servers are temporarily unavailable. Please try again in a moment.",
            "offline": True,
        }), 503

    log_audit("WAITLIST_JOIN", f"Email: {email}")

    # 📧 Notify admin + subscriber
    email_service.send_waitlist_emails(
        user_email=email,
        source=source,
        admin_email=app.config["ADMIN_EMAIL"],
        base_url=app.config["APP_BASE_URL"],
    )

    return jsonify({"ok": True, "message": "You're on the list!"})


# ============================================================
#                     AUTHENTICATION
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("user"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        email    = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        try:
            user = users_col.find_one({"email": email})
        except ServerSelectionTimeoutError:
            return jsonify({
                "ok": False,
                "error": "Database offline. Please try again in a moment.",
                "offline": True,
            }), 503

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"ok": False, "error": "Invalid email or password."}), 401
        if user.get("status") != "Active":
            return jsonify({"ok": False, "error": "Account is suspended."}), 403

        session["user"] = {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        }
        log_audit("USER_LOGIN", "System Portal", actor=session["user"])
        return jsonify({"ok": True, "redirect": url_for("admin_dashboard")})

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    if session.get("user"):
        log_audit("USER_LOGOUT", "System Portal")
    session.clear()
    return redirect(url_for("admin_login"))


# ============================================================
#                     HEALTH CHECK
# ============================================================

@app.route("/admin/health")
def health():
    """Lightweight JSON ping for the admin overlay to poll."""
    if db_online():
        return jsonify({"online": True}), 200
    return jsonify({"online": False}), 503


# ============================================================
#                     ADMIN PAGE ROUTES (render always)
# ============================================================

@app.route("/admin/")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "total_waitlist":  0,
        "total_vendors":   0,
        "pending_vendors": 0,
        "total_users":     0,
        "today_traffic":   0,
    }
    try:
        start_of_day = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        stats = {
            "total_waitlist":  waitlist_col.count_documents({}),
            "total_vendors":   vendors_col.count_documents({}),
            "pending_vendors": vendors_col.count_documents({"status": "Pending"}),
            "total_users":     users_col.count_documents({}),
            "today_traffic":   views_col.count_documents({"timestamp": {"$gte": start_of_day}}),
        }
    except ServerSelectionTimeoutError:
        app.logger.warning("[DASHBOARD] DB offline — rendering with empty stats")
    return render_template("admin/index.html", stats=stats, page_name="dashboard")


@app.route("/admin/waitlist")
@login_required
def admin_waitlist():
    items = []
    page = 1
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = 20
        cursor = (
            waitlist_col.find()
            .sort("subscribed_at", DESCENDING)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        items = [{
            "id": str(w["_id"]),
            "email": w["email"],
            "source": w.get("source", "Direct"),
            "subscribed_at": w["subscribed_at"].strftime("%b %d, %Y"),
        } for w in cursor]
    except ServerSelectionTimeoutError:
        app.logger.warning("[WAITLIST] DB offline — rendering empty list")
    return render_template(
        "admin/waitlist.html",
        waitlist=items, page=page, page_name="waitlist",
    )


@app.route("/admin/vendors")
@login_required
def admin_vendors():
    items = []
    try:
        vendors = list(vendors_col.find().sort("applied_at", DESCENDING))
        items = [{
            "id": str(v["_id"]),
            "owner_name": v["owner_name"],
            "owner_email": v["owner_email"],
            "store_name": v["store_name"],
            "store_category": v["store_category"],
            "status": v.get("status", "Pending"),
            "applied_at": v["applied_at"].strftime("%b %d, %Y"),
        } for v in vendors]
    except ServerSelectionTimeoutError:
        app.logger.warning("[VENDORS] DB offline — rendering empty list")
    return render_template("admin/vendors.html", vendors=items, page_name="vendors")


@app.route("/admin/insights")
@login_required
def admin_insights():
    total, unique, avg_time, bounce_rate, top_pages = 0, 0, 0, 0, []
    try:
        total = views_col.count_documents({})
        unique = len(views_col.distinct("session_id"))

        avg_agg = list(views_col.aggregate([
            {"$group": {"_id": None, "avg": {"$avg": "$time_on_page"}}}
        ]))
        avg_time = round(avg_agg[0]["avg"], 1) if avg_agg and avg_agg[0]["avg"] else 0

        bounced = views_col.count_documents({"bounced": True})
        bounce_rate = round((bounced / total * 100), 1) if total else 0

        pipeline = [
            {"$group": {
                "_id": "$page_path",
                "views": {"$sum": 1},
                "uniques": {"$addToSet": "$session_id"},
                "bounced": {"$sum": {"$cond": ["$bounced", 1, 0]}},
            }},
            {"$sort": {"views": -1}},
            {"$limit": 10},
        ]
        for p in views_col.aggregate(pipeline):
            u = len(p["uniques"])
            br = round((p["bounced"] / p["views"] * 100), 1) if p["views"] else 0
            top_pages.append({
                "path": p["_id"],
                "views": p["views"],
                "uniques": u,
                "bounce_rate": br,
            })
    except ServerSelectionTimeoutError:
        app.logger.warning("[INSIGHTS] DB offline — rendering empty stats")
    return render_template(
        "admin/insights.html",
        total=total, unique=unique, avg_time=avg_time,
        bounce_rate=bounce_rate, top_pages=top_pages, page_name="insights",
    )


@app.route("/admin/users")
@login_required
def admin_users():
    items = []
    try:
        users = list(users_col.find().sort("created_at", DESCENDING))
        items = [{
            "id": str(u["_id"]),
            "full_name": u["full_name"],
            "email": u["email"],
            "role": u["role"],
            "status": u.get("status", "Active"),
        } for u in users]
    except ServerSelectionTimeoutError:
        app.logger.warning("[USERS] DB offline — rendering empty list")
    return render_template("admin/users.html", users=items, page_name="users")


@app.route("/admin/audit-logs")
@login_required
@role_required("Admin")
def admin_audit():
    logs = []
    page = 1
    search = request.args.get("q", "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = 50
        query = {}
        if search:
            query = {"$or": [
                {"event_action":    {"$regex": search, "$options": "i"}},
                {"target_resource": {"$regex": search, "$options": "i"}},
                {"actor_role":      {"$regex": search, "$options": "i"}},
            ]}
        cursor = (
            audit_col.find(query)
            .sort("timestamp", DESCENDING)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        logs = [{
            "timestamp":       l["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "actor_role":      l.get("actor_role", "System"),
            "event_action":    l.get("event_action", ""),
            "target_resource": l.get("target_resource", ""),
            "ip_address":      l.get("ip_address", ""),
        } for l in cursor]
    except ServerSelectionTimeoutError:
        app.logger.warning("[AUDIT] DB offline — rendering empty list")
    return render_template(
        "admin/audit-logs.html",
        logs=logs, page=page, search=search, page_name="audit",
    )


@app.route("/admin/settings")
@login_required
@role_required("Admin")
def admin_settings():
    """Site settings page — control site mode."""
    current_mode = get_site_mode()
    return render_template(
        "admin/settings.html",
        current_mode=current_mode,
        site_modes=SITE_MODES,
        page_name="settings",
    )


# ============================================================
#                     ADMIN API ROUTES (need DB)
# ============================================================

@app.route("/admin/api/site-mode", methods=["POST"])
@login_required
@role_required("Admin")
@api_db_required
def api_set_site_mode():
    """API endpoint to change site mode."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "").strip()

    if mode not in SITE_MODES:
        return jsonify({
            "ok": False,
            "error": f"Invalid mode. Must be one of: {', '.join(SITE_MODES.keys())}"
        }), 400

    if set_site_mode(mode):
        log_audit("SITE_MODE_CHANGE", f"Mode: {mode}")
        return jsonify({
            "ok": True,
            "mode": mode,
            "label": SITE_MODES[mode]["label"],
            "message": f"Site mode changed to {SITE_MODES[mode]['label']}"
        })
    return jsonify({
        "ok": False,
        "error": "Failed to update site mode. Database may be offline."
    }), 503


@app.route("/admin/api/waitlist/<wid>", methods=["DELETE"])
@login_required
@api_db_required
def delete_waitlist(wid):
    try:
        oid = ObjectId(wid)
    except (InvalidId, TypeError):
        return jsonify({"ok": False, "error": "Invalid ID"}), 400

    result = waitlist_col.delete_one({"_id": oid})
    if result.deleted_count:
        log_audit("WAITLIST_REMOVE", f"ID: {wid}")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Not found"}), 404


@app.route("/admin/api/vendors/<vid>", methods=["PATCH", "DELETE"])
@login_required
@api_db_required
def update_vendor(vid):
    try:
        oid = ObjectId(vid)
    except (InvalidId, TypeError):
        return jsonify({"ok": False, "error": "Invalid ID"}), 400

    if request.method == "DELETE":
        result = vendors_col.delete_one({"_id": oid})
        if result.deleted_count:
            log_audit("VENDOR_DELETE", f"ID: {vid}")
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ["Approved", "Rejected", "Pending"]:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    # Fetch vendor BEFORE update so we have owner info for the email
    vendor = vendors_col.find_one({"_id": oid})
    if not vendor:
        return jsonify({"ok": False, "error": "Not found"}), 404

    vendors_col.update_one({"_id": oid}, {"$set": {"status": status}})
    log_audit(f"VENDOR_{status.upper()}", f"ID: {vid}")

    # 📧 Only notify on final decisions (Approved / Rejected)
    if status in ["Approved", "Rejected"]:
        email_service.send_vendor_status_email(
            owner_email=vendor["owner_email"],
            owner_name=vendor["owner_name"],
            store_name=vendor["store_name"],
            status=status,
            base_url=app.config["APP_BASE_URL"],
        )

    return jsonify({"ok": True, "status": status})


@app.route("/admin/api/users", methods=["POST"])
@login_required
@role_required("Admin")
@api_db_required
def create_user():
    data = request.get_json(silent=True) or {}
    email     = (data.get("email") or "").strip().lower()
    password  = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role      = data.get("role") or "Manager"

    if not all([email, password, full_name]):
        return jsonify({"ok": False, "error": "All fields required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    if role not in ["Admin", "Manager"]:
        return jsonify({"ok": False, "error": "Invalid role"}), 400
    if users_col.find_one({"email": email}):
        return jsonify({"ok": False, "error": "Email already exists"}), 409

    users_col.insert_one({
        "email": email,
        "password_hash": generate_password_hash(password),
        "full_name": full_name,
        "role": role,
        "status": "Active",
        "created_at": utcnow(),
    })
    log_audit("USER_CREATE", f"Email: {email} ({role})")

    # 📧 Notify admin + send credentials to new user
    email_service.send_user_creation_emails(
        admin_email=app.config["ADMIN_EMAIL"],
        new_user_email=email,
        new_user_name=full_name,
        new_user_role=role,
        plain_password=password,   # safe: admin just typed it
        base_url=app.config["APP_BASE_URL"],
    )

    return jsonify({"ok": True})


@app.route("/admin/api/users/<uid>", methods=["PATCH", "DELETE"])
@login_required
@api_db_required
def modify_user(uid):
    try:
        oid = ObjectId(uid)
    except (InvalidId, TypeError):
        return jsonify({"ok": False, "error": "Invalid ID"}), 400

    target = users_col.find_one({"_id": oid})
    if not target:
        return jsonify({"ok": False, "error": "Not found"}), 404

    current = session["user"]

    # RBAC: Manager cannot modify Admins
    if current["role"] == "Manager" and target["role"] == "Admin":
        log_audit("ACCESS_DENIED", f"Attempted to modify Admin: {target['email']}")
        return jsonify({
            "ok": False,
            "error": "Permission denied. Managers cannot modify Admins."
        }), 403

    if request.method == "DELETE":
        if str(target["_id"]) == current["id"]:
            return jsonify({"ok": False, "error": "You cannot delete yourself."}), 400
        users_col.delete_one({"_id": oid})
        log_audit("USER_DELETE", f"Email: {target['email']}")
        return jsonify({"ok": True})

    # PATCH: update role/status — Admin only
    if current["role"] != "Admin":
        return jsonify({"ok": False, "error": "Only Admins can edit users."}), 403

    data = request.get_json(silent=True) or {}
    update = {}
    if data.get("role") in ["Admin", "Manager"]:
        update["role"] = data["role"]
    if data.get("status") in ["Active", "Suspended"]:
        update["status"] = data["status"]

    if update:
        users_col.update_one({"_id": oid}, {"$set": update})
        log_audit("USER_UPDATE", f"Email: {target['email']} → {update}")
    return jsonify({"ok": True})


# ============================================================
#                     TRACKING (AJAX)
# ============================================================

@app.route("/api/track", methods=["POST"])
def track():
    # Accept both JSON and form data (sendBeacon may not set JSON content-type)
    data = request.get_json(silent=True)
    if not data:
        try:
            data = request.form.to_dict() if request.form else {}
        except Exception:
            data = {}

    try:
        time_on_page = int(data.get("time_on_page", 0))
    except (TypeError, ValueError):
        time_on_page = 0

    try:
        views_col.insert_one({
            "page_path":    data.get("page_path", "/"),
            "session_id":   current_session_id(),
            "time_on_page": time_on_page,
            "bounced":      bool(data.get("bounced", False)),
            "timestamp":    utcnow(),
        })
    except ServerSelectionTimeoutError:
        # Tracking is best-effort; never error out
        return jsonify({"ok": False, "offline": True}), 202

    return jsonify({"ok": True})


# ============================================================
#                     GLOBAL ERROR HANDLERS
# ============================================================

@app.errorhandler(ServerSelectionTimeoutError)
def handle_db_timeout(e):
    """Safety net for any unhandled Mongo timeout."""
    app.logger.error(f"[DB_TIMEOUT] {request.path}: {e}")

    if request.path.startswith("/admin/api/"):
        return jsonify({
            "ok": False,
            "error": "Database offline. Please try again shortly.",
            "offline": True,
        }), 503

    # For any other admin page — render the page with empty data
    # so base.html loads and the overlay shows client-side.
    return redirect(request.path)


@app.errorhandler(403)
def forbidden(e):
    return (
        "<div style='font-family:sans-serif;padding:3rem;text-align:center'>"
        "<h1 style='font-size:3rem;margin:0'>403</h1>"
        "<p style='color:#64748b'>Forbidden — you don't have permission to view this page.</p>"
        "<a href='/admin/dashboard' style='color:#4f46e5;font-weight:600'>Back to Dashboard</a>"
        "</div>",
        403,
    )


@app.errorhandler(404)
def not_found(e):
    return (
        "<div style='font-family:sans-serif;padding:3rem;text-align:center'>"
        "<h1 style='font-size:3rem;margin:0'>404</h1>"
        "<p style='color:#64748b'>Page not found.</p>"
        "<a href='/' style='color:#4f46e5;font-weight:600'>Back to Home</a>"
        "</div>",
        404,
    )


@app.errorhandler(500)
def internal_error(e):
    """Last-resort handler."""
    if request.path.startswith("/admin/api/"):
        return jsonify({
            "ok": False,
            "error": "Internal server error.",
            "offline": True,
        }), 500
    return ("<h1>500 — Internal Server Error</h1>", 500)


# ============================================================
#                     ENTRY POINT
# ============================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)