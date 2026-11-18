# SkillBridge – Student Skill Automation for Internship & Placement

A Flask + SQLite web application that helps students maintain a skill profile, compare their skills with internship/placement requirements, identify skill gaps, and track opportunities.

## Features
- Student registration, login, and logout
- Student profile management
- Add and remove technical/soft skills with proficiency levels
- Internship and placement opportunity listings
- Skill matching percentage and missing-skill analysis
- Application tracker with status updates
- Skill-gap learning roadmap
- Sample opportunities inserted automatically on first run

## Tech stack
Python, Flask, SQLite, HTML, CSS, Bootstrap, Werkzeug password hashing.

## Run locally

### 1. Install Python
Use Python 3.10 or later.

### 2. Open the project folder
```bash
cd skillbridge_project
```

### 3. Create and activate a virtual environment
Windows PowerShell:
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
```
Windows Command Prompt:
```cmd
.venv\\Scripts\\activate
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Start the application
```bash
python app.py
```
Open http://127.0.0.1:5000 in your browser. Register a student account to begin.

The SQLite database and sample opportunities are created automatically on first launch.

## GitHub upload

Create a new empty repository on GitHub, for example `student-skill-automation`.

Run these commands from the project folder:
```bash
git init
git add .
git commit -m "Initial commit: SkillBridge student skill automation"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/student-skill-automation.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your GitHub username.

## Important notes
- The sample opportunity links use `example.com`. Replace them with verified company application links before presenting this as a live opportunity portal.
- The matching score is a transparent baseline: exact skill-name matches divided by the number of required skills. It is not an AI prediction or a guarantee of selection.
- For deployment, set a strong `SECRET_KEY` environment variable and use a production WSGI server such as Gunicorn. Do not deploy with Flask debug mode enabled.
- The SQLite database is suitable for a local academic demo. For a multi-user production deployment, consider PostgreSQL and database migrations.
