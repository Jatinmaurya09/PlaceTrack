import os
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session)
from werkzeug.utils import secure_filename
import joblib
import pandas as pd
import pdfplumber
from database import (
    init_db, get_or_create_student, save_prediction, save_resume,
    get_student_by_roll, get_predictions, get_resumes,
    get_all_students, get_admin_stats,
    get_auto_apply_settings, save_auto_apply_settings,
    get_applications, get_application_stats,
    get_application_by_token, update_application_status,
)
from auto_apply import run_auto_apply_for_student, run_auto_apply_all
from companies import match_companies, get_role_types, get_locations
from scheduler import start_scheduler

# ---------- Flask App ----------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key-2025")
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs("uploads", exist_ok=True)

# ---------- Load Model ----------
MODEL_PATH = "model/placement_model.pkl"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found at {MODEL_PATH}. Pehle `python train_model.py` chalao."
    )

bundle = joblib.load(MODEL_PATH)
pipeline = bundle["pipeline"]
FEATURES = bundle["features"]

# ---------- ATS Keywords ----------
SKILL_KEYWORDS = [
    "python", "java", "c++", "c", "sql", "html", "css", "javascript", "react",
    "flask", "django", "node", "machine learning", "deep learning", "pandas",
    "numpy", "scikit", "tensorflow", "pytorch", "git", "github", "docker",
    "aws", "azure", "linux", "data structures", "algorithms", "dsa", "oop",
    "rest api", "communication", "teamwork", "problem solving", "leadership",
    "mongodb", "mysql", "postgresql", "tableau", "power bi", "excel",
]
ALLOWED_EXT = {"pdf"}


def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------- Validation ----------
def validate(data):
    errors = []

    def num(k, lo, hi):
        try:
            v = float(data.get(k))
            if v < lo or v > hi:
                errors.append(f"{k} must be between {lo} and {hi}")
        except (TypeError, ValueError):
            errors.append(f"{k} must be a number")

    num("age", 18, 30)
    num("cgpa", 0, 10)
    num("tenth_percentage", 0, 100)
    num("twelfth_percentage", 0, 100)
    num("backlogs", 0, 10)
    num("attendance_percentage", 0, 100)
    num("projects_completed", 0, 10)
    num("mock_interviews", 0, 20)

    for f in ["name", "roll_no", "department", "gender", "branch",
              "internship_experience", "dsa_level", "coding_practice",
              "aptitude_level", "communication_level"]:
        if not str(data.get(f, "")).strip():
            errors.append(f"{f} is required")
    return errors


# ---------- Auth Decorators ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or not user.get("is_admin"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return wrapper


# ---------- Template Globals ----------
@app.context_processor
def inject_globals():
    return {
        "session_user": session.get("user"),
        "current_date": datetime.now().strftime("%b %d, %Y"),
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def root():
    if session.get("user"):
        if session["user"].get("is_admin"):
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))


# ---------- Login ----------
@app.route("/login", methods=["GET"])
def login_page():
    if session.get("user"):
        return redirect(url_for("root"))
    return render_template("login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    role = data.get("role", "student")

    # Admin — no password (as agreed)
    if role == "admin":
        session["user"] = {
            "name": "Admin",
            "roll_no": "ADMIN",
            "department": "Administration",
            "role": "Administrator",
            "is_admin": True,
        }
        return jsonify({"success": True, "redirect": "/admin"})

    # Student — check roll_no in DB
    roll_no = (data.get("roll_no") or "").strip().upper()
    if not roll_no:
        return jsonify({"error": "Roll number required"}), 400

    student = get_student_by_roll(roll_no)
    if not student:
        return jsonify({
            "error": "Roll number not registered. Please fill the prediction form first.",
            "redirect": "/predictor",
        }), 404

    session["user"] = {
        "name": student["name"],
        "roll_no": student["roll_no"],
        "department": student["department"],
        "role": "Student",
        "is_admin": False,
    }
    return jsonify({"success": True, "redirect": "/dashboard"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ---------- Predictor (public) ----------
@app.route("/predictor")
def predictor_page():
    return render_template("predictor.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(force=True)
        errs = validate(data)
        if errs:
            return jsonify({"error": "; ".join(errs)}), 400

        sid = get_or_create_student(
            data["name"], data["roll_no"], data["department"]
        )

        # Model input (gender excluded — fairness)
        model_input = {f: data[f] for f in FEATURES}
        df = pd.DataFrame([model_input])
        for col in ["age", "cgpa", "tenth_percentage", "twelfth_percentage",
                    "backlogs", "attendance_percentage",
                    "projects_completed", "mock_interviews"]:
            df[col] = pd.to_numeric(df[col])

        pred = pipeline.predict(df)[0]

        proba = None
        if hasattr(pipeline, "predict_proba"):
            classes = list(pipeline.classes_)
            probs = pipeline.predict_proba(df)[0]
            if "Placed" in classes:
                proba = float(probs[classes.index("Placed")])

        save_prediction(sid, data, pred, proba)

        # Auto-login student after first prediction
        student = get_student_by_roll(data["roll_no"])
        session["user"] = {
            "name": student["name"],
            "roll_no": student["roll_no"],
            "department": student["department"],
            "role": "Student",
            "is_admin": False,
        }

        return jsonify({
            "prediction": pred,
            "probability": round(proba, 4) if proba is not None else None,
            "roll_no": data["roll_no"],
            "redirect": "/dashboard",
            "message": "This is a model-based estimate, not a guarantee.",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Student Dashboard ----------
@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    student = get_student_by_roll(user["roll_no"])
    if not student:
        session.clear()
        return redirect(url_for("predictor_page"))

    preds = get_predictions(student["id"])
    resumes = get_resumes(student["id"])
    latest = preds[0] if preds else None
    latest_ats = resumes[0] if resumes else None

    return render_template(
        "dashboard.html",
        student=student,
        predictions=preds,
        resumes=resumes,
        latest=latest,
        latest_ats=latest_ats,
        active="dashboard",
        viewing_as_admin=False,
    )

# ---------- ATS Page ----------
@app.route("/ats")
@login_required
def ats_page():
    user = session["user"]
    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    student = get_student_by_roll(user["roll_no"])
    if not student:
        session.clear()
        return redirect(url_for("predictor_page"))

    resumes = get_resumes(student["id"])
    return render_template(
        "ats.html",
        student=student,
        resumes=resumes,
        active="ats",
    )


@app.route("/upload_resume/<roll_no>", methods=["POST"])
@login_required
def upload_resume(roll_no):
    student = get_student_by_roll(roll_no)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["resume"]
    if f.filename == "" or not allowed_file(f.filename):
        return jsonify({"error": "Only PDF files allowed"}), 400

    filename = secure_filename(f"{roll_no}_{f.filename}")
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(path)

    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                text += (p.extract_text() or "") + "\n"
    except Exception as e:
        return jsonify({"error": f"PDF read error: {e}"}), 500

    text_lower = text.lower()
    matched = [k for k in SKILL_KEYWORDS if k in text_lower]
    missing = [k for k in SKILL_KEYWORDS if k not in text_lower]
    score = round(len(matched) / len(SKILL_KEYWORDS) * 100, 2)

    save_resume(student["id"], filename, score, matched, missing)

    return jsonify({
        "ats_score": score,
        "matched_skills": matched,
        "missing_skills": missing[:10],
        "filename": filename,
    })


# ---------- Admin ----------
@app.route("/admin")
@admin_required
def admin_dashboard():
    students = get_all_students()
    stats = get_admin_stats()
    return render_template(
        "admin.html",
        students=students,
        stats=stats,
        active="admin",
    )


@app.route("/student/<roll_no>")
@login_required
def student_detail(roll_no):
    user = session["user"]
    if not user.get("is_admin") and user["roll_no"] != roll_no:
        return redirect(url_for("dashboard"))

    student = get_student_by_roll(roll_no)
    if not student:
        return "Student not found", 404

    preds = get_predictions(student["id"])
    resumes = get_resumes(student["id"])
    latest = preds[0] if preds else None
    latest_ats = resumes[0] if resumes else None

    return render_template(
        "dashboard.html",
        student=student,
        predictions=preds,
        resumes=resumes,
        latest=latest,
        latest_ats=latest_ats,
        active="dashboard",
        viewing_as_admin=user.get("is_admin", False),
    )
# ---------- Company Matches ----------
@app.route("/companies")
@login_required
def companies_page():
    user = session["user"]
    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    student = get_student_by_roll(user["roll_no"])
    if not student:
        session.clear()
        return redirect(url_for("predictor_page"))

    preds = get_predictions(student["id"])
    resumes = get_resumes(student["id"])

    latest = preds[0] if preds else None
    latest_resume = resumes[0] if resumes else None

    resume_skills = []
    if latest_resume and latest_resume["matched_skills"]:
        resume_skills = latest_resume["matched_skills"].split(",")

    cgpa = latest["cgpa"] if latest else 0
    backlogs = latest["backlogs"] if latest else 0
    dsa_level = latest["dsa_level"] if latest else ""
    coding_practice = latest["coding_practice"] if latest else ""
    internship = latest["internship_experience"] if latest else ""
    projects = latest["projects_completed"] if latest else 0

    # Filters from query string
    role_filter = request.args.get("role", "All Roles")
    location_filter = request.args.get("location", "All locations")
    min_match = int(request.args.get("min_match", 0))

    matches = match_companies(
        student_skills=resume_skills,
        cgpa=cgpa,
        backlogs=backlogs,
        dsa_level=dsa_level,
        coding_practice=coding_practice,
        internship=internship,
        projects=projects,
        role_filter=role_filter,
        location_filter=location_filter,
        min_match=min_match,
    )

    # Best match for display
    best_match = matches[0]["final_score"] if matches else 0

    return render_template(
        "companies.html",
        student=student,
        matches=matches,
        latest=latest,
        latest_resume=latest_resume,
        resume_skill_count=len(resume_skills),
        role_filter=role_filter,
        location_filter=location_filter,
        min_match=min_match,
        best_match=best_match,
        role_types=get_role_types(),
        locations=get_locations(),
        active="companies",
    )
# ---------- Auto Apply Settings ----------
@app.route("/auto-apply")
@login_required
def auto_apply_page():
    user = session["user"]
    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    student = get_student_by_roll(user["roll_no"])
    if not student:
        session.clear()
        return redirect(url_for("predictor_page"))

    settings = get_auto_apply_settings(student["id"])
    stats = get_application_stats(student["id"])

    return render_template(
        "auto_apply.html",
        student=student,
        settings=settings,
        stats=stats,
        active="auto_apply",
    )


@app.route("/auto-apply/save", methods=["POST"])
@login_required
def auto_apply_save():
    user = session["user"]
    if user.get("is_admin"):
        return jsonify({"error": "Only students can change settings"}), 403

    student = get_student_by_roll(user["roll_no"])
    data = request.get_json(force=True)

    settings_data = {
        "enabled": 1 if data.get("enabled") else 0,
        "notification_email": (data.get("notification_email") or "").strip(),
        "min_match": int(data.get("min_match") or 70),
        "preferred_roles": (data.get("preferred_roles") or "").strip(),
        "preferred_locations": (data.get("preferred_locations") or "").strip(),
        "max_per_day": int(data.get("max_per_day") or 5),
        "email_required": 1 if data.get("email_required", True) else 0,
    }

    if settings_data["enabled"] and not settings_data["notification_email"]:
        return jsonify({"error": "Email required to enable auto-apply"}), 400

    save_auto_apply_settings(student["id"], settings_data)
    return jsonify({"success": True, "message": "Settings saved"})


@app.route("/auto-apply/run-now", methods=["POST"])
@login_required
def auto_apply_run_now():
    user = session["user"]
    if user.get("is_admin"):
        return jsonify({"error": "Only students"}), 403

    student = get_student_by_roll(user["roll_no"])
    sent, errors = run_auto_apply_for_student(student)

    return jsonify({
        "sent": sent,
        "errors": errors,
        "message": f"{sent} email(s) sent" if sent else "No new matches to send",
    })


# ---------- Email Response (YES / NO) ----------
@app.route("/auto_apply/respond/<token>")
def auto_apply_respond(token):
    action = request.args.get("action", "").lower()

    app_row = get_application_by_token(token)
    if not app_row:
        return render_template(
            "response.html",
            status="error",
            message="Invalid or expired link.",
            application=None,
        )

    if app_row["status"] != "pending":
        return render_template(
            "response.html",
            status="info",
            message=f"You already responded: {app_row['status'].upper()}",
            application=app_row,
        )

    if action == "yes":
        update_application_status(token, "approved")
        return render_template(
            "response.html",
            status="success",
            message="Application submitted successfully! 🎉",
            application=app_row,
        )
    elif action == "no":
        update_application_status(token, "skipped")
        return render_template(
            "response.html",
            status="info",
            message="Application skipped.",
            application=app_row,
        )
    else:
        return render_template(
            "response.html",
            status="error",
            message="Invalid action.",
            application=app_row,
        )


# ---------- Applications History ----------
@app.route("/applications")
@login_required
def applications_page():
    user = session["user"]
    if user.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    student = get_student_by_roll(user["roll_no"])
    if not student:
        session.clear()
        return redirect(url_for("predictor_page"))

    apps = get_applications(student["id"])
    stats = get_application_stats(student["id"])

    return render_template(
        "applications.html",
        student=student,
        applications=apps,
        stats=stats,
        active="applications",
    )

# ---------- Init ----------
init_db()

# Start scheduler in production
if not app.debug:
    start_scheduler()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)