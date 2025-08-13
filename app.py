import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User, Training, CareerPath

# --------------------
# Config
# --------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "career.db")
CAREER_JSON = os.path.join(APP_DIR, "career_paths.json")
UPLOAD_FOLDER = os.path.join(APP_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")  # override in prod
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB uploads

# --------------------
# Database
# --------------------
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
db = DBSession()

# Seed career paths from JSON when DB empty
if not db.query(CareerPath).first():
    try:
        with open(CAREER_JSON, "r", encoding="utf-8") as f:
            entries = json.load(f)
        for e in entries:
            if not db.query(CareerPath).filter_by(id=e["id"]).first():
                db.add(CareerPath(id=e["id"], title=e["title"], requirements=e.get("requirements","")))
        db.commit()
        print("Seeded career paths.")
    except Exception as exc:
        print("Could not seed career paths:", exc)

# --------------------
# Helpers
# --------------------
def current_user():
    if "username" in session:
        return db.query(User).filter_by(username=session["username"]).first()
    return None

def calc_match_percent(user, career_requirements):
    """
    career_requirements: comma-separated string
    We consider a requirement 'met' if user has training with that exact name and progress >= 70.
    (You can tune matching logic later — fuzzy matching, synonyms, etc.)
    """
    if not career_requirements:
        return 0
    reqs = [r.strip() for r in career_requirements.split(",") if r.strip()]
    if not reqs:
        return 0
    user_training = {t.name: t.progress for t in user.training} if user else {}
    met = 0
    for r in reqs:
        # exact match first; fallback: case-insensitive
        prog = user_training.get(r, user_training.get(r.lower(), 0))
        if prog >= 70:
            met += 1
    return int((met / len(reqs)) * 100)

# --------------------
# Routes
# --------------------
@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()
        if not username or not password:
            flash("Username and password required.")
            return redirect(url_for("register"))
        if db.query(User).filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("register"))
        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, role=role)
        db.add(user)
        db.commit()
        session["username"] = username
        flash("Account created. Welcome!")
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return register()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            flash("Logged in.")
            return redirect(url_for("home"))
        flash("Invalid credentials.")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route("/home")
def home():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    paths = db.query(CareerPath).all()
    path_data = []
    for p in paths:
        match = calc_match_percent(user, p.requirements)
        path_data.append({
            "id": p.id,
            "title": p.title,
            "requirements": p.requirements,
            "match": match
        })
    return render_template("home.html", user=user, path_data=path_data)

@app.route("/add_training", methods=["POST"])
def add_training():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    try:
        progress = int(request.form.get("progress", "0"))
    except ValueError:
        progress = 0
    if not name:
        flash("Training name required.")
        return redirect(url_for("home"))
    t = Training(name=name, progress=max(0, min(100, progress)), user=user)
    db.add(t)
    db.commit()
    flash("Training added.")
    return redirect(url_for("home"))

@app.route("/profiles")
def profiles():
    users = db.query(User).all()
    return render_template("profiles.html", users=users)

@app.route("/profile/<username>")
def profile_detail(username):
    u = db.query(User).filter_by(username=username).first()
    if not u:
        flash("User not found.")
        return redirect(url_for("profiles"))
    # compute match for each path
    paths = db.query(CareerPath).all()
    path_matches = [{ "title": p.title, "match": calc_match_percent(u, p.requirements), "requirements": p.requirements } for p in paths]
    return render_template("profile_detail.html", user=u, path_matches=path_matches)

# Simple file upload (resumes/certs)
@app.route("/upload", methods=["GET", "POST"])
def upload():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part.")
            return redirect(url_for("upload"))
        f = request.files["file"]
        if f.filename == "":
            flash("No selected file.")
            return redirect(url_for("upload"))
        filename = secure_filename(f.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(save_path)
        flash("Uploaded.")
        return redirect(url_for("home"))
    return render_template("uploads.html")

# Simple example job feed
@app.route("/jobs")
def jobs():
    jobs_list = []
    example_path = os.path.join(APP_DIR, "example_jobs.txt")
    if os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as fh:
            jobs_list = [line.strip() for line in fh if line.strip()]
    return render_template("jobs.html", jobs=jobs_list)

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
