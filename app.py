import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "skillbridge.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        branch TEXT DEFAULT '',
        year TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        level TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        kind TEXT NOT NULL,
        description TEXT,
        required_skills TEXT NOT NULL,
        location TEXT DEFAULT 'Remote',
        apply_url TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        opportunity_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Interested',
        applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, opportunity_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    if count == 0:
        samples = [
            ("Python Developer Intern", "TechNova", "Internship", "Build Python applications and APIs.", "python,sql,git", "Remote", "https://example.com"),
            ("Frontend Developer Intern", "PixelWorks", "Internship", "Develop responsive web interfaces.", "html,css,javascript,git", "Hyderabad", "https://example.com"),
            ("Data Analyst Trainee", "DataSpring", "Placement", "Analyze datasets and create reports.", "python,sql,excel", "Bengaluru", "https://example.com"),
            ("Java Software Engineer", "CodeCraft", "Placement", "Work on Java-based enterprise applications.", "java,dsa,sql,git", "Pune", "https://example.com"),
            ("Full Stack Intern", "LaunchPad", "Internship", "Work across frontend and backend technologies.", "html,css,javascript,python,sql", "Remote", "https://example.com")
        ]
        db.executemany("""INSERT INTO opportunities
            (title,company,kind,description,required_skills,location,apply_url)
            VALUES (?,?,?,?,?,?,?)""", samples)
    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

def normalized_skills(user_id):
    rows = get_db().execute("SELECT * FROM skills WHERE user_id=?", (user_id,)).fetchall()
    return rows

def match_details(opportunity, skills):
    owned = {s["name"].strip().lower() for s in skills}
    required = [x.strip().lower() for x in opportunity["required_skills"].split(",") if x.strip()]
    matched = [x for x in required if x in owned]
    missing = [x for x in required if x not in owned]
    score = round((len(matched) / len(required)) * 100) if required else 0
    return score, matched, missing

@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        if not name or not email or len(password) < 6:
            flash("Enter all required details. Password must contain at least 6 characters.", "danger")
            return render_template("register.html")
        try:
            db = get_db()
            db.execute("INSERT INTO users(name,email,password,branch,year) VALUES(?,?,?,?,?)",
                       (name, email, generate_password_hash(password), branch, year))
            db.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    skills = normalized_skills(user["id"])
    opportunities = get_db().execute("SELECT * FROM opportunities ORDER BY id DESC").fetchall()
    matches = []
    for opp in opportunities:
        score, matched, missing = match_details(opp, skills)
        matches.append({"opportunity": opp, "score": score, "matched": matched, "missing": missing})
    matches.sort(key=lambda x: x["score"], reverse=True)
    app_count = get_db().execute("SELECT COUNT(*) FROM applications WHERE user_id=?", (user["id"],)).fetchone()[0]
    readiness = round(sum(1 for s in skills if s["level"] in ("Intermediate", "Advanced")) / max(len(skills), 1) * 100)
    return render_template("dashboard.html", user=user, skills=skills, matches=matches[:3],
                           app_count=app_count, readiness=readiness)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        get_db().execute("UPDATE users SET name=?, branch=?, year=? WHERE id=?",
                         (request.form.get("name", "").strip(), request.form.get("branch", "").strip(),
                          request.form.get("year", "").strip(), user["id"]))
        get_db().commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

@app.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    user = current_user()
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "Technical")
        level = request.form.get("level", "Beginner")
        if name:
            existing = db.execute("SELECT id FROM skills WHERE user_id=? AND lower(name)=lower(?)",
                                  (user["id"], name)).fetchone()
            if existing:
                flash("That skill is already in your profile.", "warning")
            else:
                db.execute("INSERT INTO skills(user_id,name,category,level) VALUES(?,?,?,?)",
                           (user["id"], name, category, level))
                db.commit()
                flash("Skill added successfully.", "success")
        return redirect(url_for("skills"))
    rows = db.execute("SELECT * FROM skills WHERE user_id=? ORDER BY category,name", (user["id"],)).fetchall()
    return render_template("skills.html", skills=rows)

@app.route("/skills/delete/<int:skill_id>", methods=["POST"])
@login_required
def delete_skill(skill_id):
    get_db().execute("DELETE FROM skills WHERE id=? AND user_id=?", (skill_id, session["user_id"]))
    get_db().commit()
    flash("Skill removed.", "info")
    return redirect(url_for("skills"))

@app.route("/opportunities")
@login_required
def opportunities():
    user_skills = normalized_skills(session["user_id"])
    rows = get_db().execute("SELECT * FROM opportunities ORDER BY id DESC").fetchall()
    items = []
    for opp in rows:
        score, matched, missing = match_details(opp, user_skills)
        items.append({"opportunity": opp, "score": score, "matched": matched, "missing": missing})
    items.sort(key=lambda x: x["score"], reverse=True)
    return render_template("opportunities.html", items=items)

@app.route("/apply/<int:opportunity_id>", methods=["POST"])
@login_required
def apply(opportunity_id):
    db = get_db()
    exists = db.execute("SELECT id FROM opportunities WHERE id=?", (opportunity_id,)).fetchone()
    if not exists:
        flash("Opportunity not found.", "danger")
        return redirect(url_for("opportunities"))
    try:
        db.execute("INSERT INTO applications(user_id,opportunity_id,status) VALUES(?,?,?)",
                   (session["user_id"], opportunity_id, "Interested"))
        db.commit()
        flash("Opportunity added to your application tracker.", "success")
    except sqlite3.IntegrityError:
        flash("This opportunity is already in your tracker.", "warning")
    return redirect(url_for("applications"))

@app.route("/applications")
@login_required
def applications():
    rows = get_db().execute("""SELECT a.id,a.status,a.applied_on,o.title,o.company,o.kind,o.location
        FROM applications a JOIN opportunities o ON a.opportunity_id=o.id
        WHERE a.user_id=? ORDER BY a.applied_on DESC""", (session["user_id"],)).fetchall()
    return render_template("applications.html", applications=rows)

@app.route("/applications/update/<int:application_id>", methods=["POST"])
@login_required
def update_application(application_id):
    status = request.form.get("status")
    allowed = ["Interested", "Applied", "Assessment", "Interview", "Selected", "Rejected"]
    if status in allowed:
        get_db().execute("UPDATE applications SET status=? WHERE id=? AND user_id=?",
                         (status, application_id, session["user_id"]))
        get_db().commit()
        flash("Application status updated.", "success")
    return redirect(url_for("applications"))

@app.route("/roadmap")
@login_required
def roadmap():
    skills = normalized_skills(session["user_id"])
    opps = get_db().execute("SELECT * FROM opportunities").fetchall()
    missing = {}
    for opp in opps:
        _, _, gaps = match_details(opp, skills)
        for skill in gaps:
            missing[skill] = missing.get(skill, 0) + 1
    recommendations = sorted(missing.items(), key=lambda x: x[1], reverse=True)
    return render_template("roadmap.html", recommendations=recommendations)

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
