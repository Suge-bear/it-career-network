from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from models import Base, User, Training, CareerPath
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'secret'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup database
engine = create_engine("sqlite:///data.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

@app.route("/home")
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    user = db.query(User).filter_by(username=session["username"]).first()
    paths = db.query(CareerPath).all()
    user_training = {t.name: t.progress for t in user.training}

    def match_score(requirements):
        required_skills = requirements.split(",")
        total = len(required_skills)
        met = sum(1 for skill in required_skills if user_training.get(skill.strip(), 0) >= 70)
        return int((met / total) * 100) if total else 0

    path_data = [{
        "title": p.title,
        "match": match_score(p.requirements),
        "requirements": p.requirements
    } for p in paths]

    return render_template("home.html", user=user, path_data=path_data)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            return redirect(url_for("home"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]
        if db.query(User).filter_by(username=username).first():
            return "User exists"
        user = User(username=username, password=password, role=role)
        db.add(user)
        db.commit()
        session["username"] = username
        return redirect(url_for("home"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/path/<path_id>")
def path_detail(path_id):
    path = db.query(CareerPath).filter_by(id=path_id).first()
    return render_template("path_detail.html", path=path)

@app.route("/update_training", methods=["POST"])
def update_training():
    user = db.query(User).filter_by(username=session["username"]).first()
    course = Training(
        name=request.form["name"],
        progress=int(request.form["progress"]),
        user=user
    )
    db.add(course)
    db.commit()
    return redirect(url_for("home"))

@app.route("/profiles")
def profiles():
    users = db.query(User).all()
    return render_template("profiles.html", users=users)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        f = request.files["upload"]
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for("home"))
    return render_template("uploads.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "chats" not in session:
        session["chats"] = []
    if request.method == "POST":
        session["chats"].append({
            "to": request.form["to"],
            "message": request.form["message"]
        })
    return render_template("chat.html", chats=session["chats"])

@app.route("/jobs")
def jobs():
    if os.path.exists("example_jobs.txt"):
        with open("example_jobs.txt") as f:
            jobs = [line.strip() for line in f if "IT" in line or "Admin" in line]
    else:
        jobs = ["IT Help Desk at XYZ Corp", "SysAdmin at ACME", "Cloud Intern at Meta"]
    return render_template("jobs.html", jobs=jobs)

if __name__ == "__main__":
    app.run(debug=True)
