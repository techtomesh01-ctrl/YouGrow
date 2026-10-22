import os
import secrets
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from policy import POINT_RULES, FORBIDDEN_REWARD_ACTIONS, validate_youtube_url

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "dev-only-change-me"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
PREMIUM_MEMBER_THRESHOLD = 1000
PREMIUM_MONTHLY_PRICE_INR = 99
ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", "").strip()
ADSENSE_SLOT_ID = os.environ.get("ADSENSE_SLOT_ID", "").strip()

def connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required. Configure PostgreSQL first.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, connect_timeout=8)

def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
      id BIGSERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
      display_name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
      points_balance INTEGER NOT NULL DEFAULT 0 CHECK (points_balance >= 0), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS channels (
      id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title TEXT NOT NULL, youtube_url TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
      approved BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(user_id, youtube_url)
    );
    CREATE TABLE IF NOT EXISTS point_ledger (
      id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      delta INTEGER NOT NULL CHECK (delta <> 0), action TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
      idempotency_key TEXT UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS reports (
      id BIGSERIAL PRIMARY KEY, reporter_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
      channel_id BIGINT REFERENCES channels(id) ON DELETE CASCADE, reason TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'open', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)

# Initialize tables lazily on the first request. CREATE TABLE IF NOT EXISTS is safe
# across multiple Gunicorn workers and keeps a fresh Render database bootable.
_db_initialized = False

@app.before_request
def ensure_database_initialized():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

@app.context_processor
def monetization_context():
    # Count registered accounts from PostgreSQL; Premium stays unavailable until
    # the threshold is reached. This does not enable payment collection by itself.
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM users")
                member_count = int(cur.fetchone()["total"])
    except Exception:
        member_count = 0
    return {
        "member_count": member_count,
        "premium_threshold": PREMIUM_MEMBER_THRESHOLD,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE_INR,
        "premium_unlocked": member_count >= PREMIUM_MEMBER_THRESHOLD,
        "adsense_ready": bool(ADSENSE_CLIENT_ID and ADSENSE_SLOT_ID),
        "adsense_client_id": ADSENSE_CLIENT_ID,
        "adsense_slot_id": ADSENSE_SLOT_ID,
    }

def csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token
app.jinja_env.globals["csrf_token"] = csrf_token

@app.before_request
def protect_post():
    if request.method == "POST":
        sent, expected = request.form.get("_csrf", ""), session.get("_csrf", "")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "Invalid form token. Refresh and try again.")

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,email,display_name,role,points_balance FROM users WHERE id=%s", (uid,))
            return cur.fetchone()

def award_points(user_id, action, idempotency_key):
    """Award only whitelisted in-app task points, atomically and once per key."""
    if action in FORBIDDEN_REWARD_ACTIONS or action not in POINT_RULES:
        raise ValueError("This action cannot earn points.")
    amount = POINT_RULES[action]
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO point_ledger(user_id,delta,action,note,idempotency_key) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(idempotency_key) DO NOTHING RETURNING id",
                        (user_id, amount, action, "Permitted in-app task", idempotency_key))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE users SET points_balance=points_balance+%s WHERE id=%s", (amount, user_id))
                return True
    return False

@app.get("/health")
def health():
    if not DATABASE_URL:
        return {"ok": True, "app": "YouGrow", "database_configured": False, "registered_members": 0, "premium_unlocked": False, "premium_threshold": PREMIUM_MEMBER_THRESHOLD}, 503
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            member_count = int(cur.fetchone()["total"])
    return {"ok": True, "app": "YouGrow", "database_configured": True, "registered_members": member_count, "premium_unlocked": member_count >= PREMIUM_MEMBER_THRESHOLD, "premium_threshold": PREMIUM_MEMBER_THRESHOLD}

@app.get("/")
def index():
    user = current_user()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT c.id,c.title,c.youtube_url,c.category,c.description,u.display_name FROM channels c JOIN users u ON u.id=c.user_id WHERE c.approved=TRUE ORDER BY c.created_at DESC LIMIT 100")
            channels = cur.fetchall()
    return render_template("index.html", user=user, channels=channels)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        name = request.form.get("display_name","").strip()[:80]
        password = request.form.get("password","")
        if not email or "@" not in email or not name or len(password) < 6:
            flash("Enter a valid email, name and password with at least 6 characters.")
            return render_template("register.html")
        if request.form.get("agree_terms") != "yes":
            flash("Please agree to the Terms and Privacy Policy to create your account.")
            return render_template("register.html")
        try:
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users(email,password_hash,display_name) VALUES(%s,%s,%s) RETURNING id", (email, generate_password_hash(password), name))
                    uid = cur.fetchone()["id"]
            session.clear()
            session["user_id"] = uid
            return redirect(url_for("dashboard"))
        except psycopg2.errors.UniqueViolation:
            flash("This email is already registered.")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id,password_hash FROM users WHERE email=%s", (email,))
                row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user_id"] = row["id"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.")
    return render_template("login.html")

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,title,youtube_url,category,approved,created_at FROM channels WHERE user_id=%s ORDER BY id DESC", (user["id"],))
            channels = cur.fetchall()
            cur.execute("SELECT delta,action,note,created_at FROM point_ledger WHERE user_id=%s ORDER BY id DESC LIMIT 50", (user["id"],))
            ledger = cur.fetchall()
    return render_template("dashboard.html", user=user, channels=channels, ledger=ledger)

@app.route("/channels/add", methods=["GET","POST"])
@login_required
def add_channel():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title","").strip()[:120]
        url = request.form.get("youtube_url","").strip()
        category = request.form.get("category","").strip()[:40]
        description = request.form.get("description","").strip()[:1000]
        if not title or not validate_youtube_url(url) or not category:
            flash("Add a title, category and valid HTTPS YouTube URL.")
            return render_template("add_channel.html")
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO channels(user_id,title,youtube_url,category,description) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id,youtube_url) DO NOTHING", (user["id"],title,url,category,description))
        flash("Channel submitted for admin review. No points are awarded for YouTube engagement.")
        return redirect(url_for("dashboard"))
    return render_template("add_channel.html")

@app.post("/report/<int:channel_id>")
@login_required
def report_channel(channel_id):
    reason = request.form.get("reason","").strip()[:500]
    if not reason:
        flash("Please explain the report.")
    else:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO reports(reporter_id,channel_id,reason) SELECT %s,id,%s FROM channels WHERE id=%s AND approved=TRUE", (session["user_id"],reason,channel_id))
        flash("Report submitted for review.")
    return redirect(url_for("index"))

@app.get("/admin")
@login_required
def admin():
    user = current_user()
    if not user or user["role"] != "admin":
        abort(403)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT c.id,c.title,c.youtube_url,c.category,c.created_at,u.email FROM channels c JOIN users u ON u.id=c.user_id WHERE c.approved=FALSE ORDER BY c.id")
            pending = cur.fetchall()
            cur.execute("SELECT id,reason,status,created_at FROM reports WHERE status='open' ORDER BY id")
            reports = cur.fetchall()
    return render_template("admin.html", user=user, pending=pending, reports=reports)

@app.post("/admin/channel/<int:channel_id>/approve")
@login_required
def approve_channel(channel_id):
    user = current_user()
    if not user or user["role"] != "admin":
        abort(403)
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE channels SET approved=TRUE WHERE id=%s", (channel_id,))
    flash("Channel approved.")
    return redirect(url_for("admin"))

@app.cli.command("init-db")
def init_db_command():
    init_db()
    print("YouGrow PostgreSQL tables created.")

@app.cli.command("make-admin")
def make_admin_command():
    """Promote an existing account whose email matches ADMIN_EMAIL."""
    if not ADMIN_EMAIL:
        raise SystemExit("Set ADMIN_EMAIL before running make-admin.")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET role='admin' WHERE email=%s RETURNING id", (ADMIN_EMAIL,))
            row = cur.fetchone()
            if not row:
                raise SystemExit("Register the ADMIN_EMAIL account first, then rerun make-admin.")
    print("Admin role assigned.")
