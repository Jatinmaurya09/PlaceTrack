import os
import csv
import smtplib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import (
    get_conn, get_auto_apply_settings, create_application,
    has_applied_to_job, count_applications_today,
    get_all_auto_apply_students
)
from companies import _skill_level_to_keywords

import config


# ---------- Load Jobs ----------
JOBS_PATH = "jobs.csv"


def load_jobs():
    """Load all jobs from CSV."""
    if not os.path.exists(JOBS_PATH):
        return []
    jobs = []
    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["required_skills_list"] = [
                s.strip().lower() for s in row["required_skills"].split(",")
            ]
            row["min_cgpa"] = float(row["min_cgpa"])
            row["max_backlogs"] = int(row["max_backlogs"])
            jobs.append(row)
    return jobs


# ---------- Matching Logic ----------
def calculate_match(student_skills, job):
    """Return (match_score, matched_skills, missing_skills)."""
    required = set(job["required_skills_list"])
    have = set(s.lower() for s in student_skills)

    matched = required & have
    missing = required - have

    if not required:
        return 0, [], []

    score = round((len(matched) / len(required)) * 100, 1)
    return score, sorted(matched), sorted(missing)


def find_matches_for_student(student, settings, pred, resume):
    """Return list of matching jobs for a student above threshold."""

    # Gather student skills from resume + form
    skills = set()
    if resume and resume["matched_skills"]:
        skills.update(s.strip().lower() for s in resume["matched_skills"].split(",") if s.strip())

    if pred:
        skills |= _skill_level_to_keywords(
            pred["dsa_level"] or "",
            pred["coding_practice"] or "",
            pred["internship_experience"] or "",
            pred["projects_completed"] or 0,
        )

    cgpa = pred["cgpa"] if pred else 0
    backlogs = pred["backlogs"] if pred else 0

    # Settings
    min_match = settings["min_match"] or config.DEFAULT_MIN_MATCH
    preferred_roles = (settings["preferred_roles"] or "").lower()
    preferred_locations = (settings["preferred_locations"] or "").lower()

    jobs = load_jobs()
    matches = []

    for job in jobs:
        # Check eligibility
        if cgpa < job["min_cgpa"]:
            continue
        if backlogs > job["max_backlogs"]:
            continue

        # Role/location filter
        if preferred_roles and preferred_roles != "any":
            role_match = any(r.strip() in job["role"].lower() for r in preferred_roles.split(","))
            if not role_match:
                continue

        if preferred_locations and preferred_locations != "any":
            loc_match = any(l.strip() in job["location"].lower() for l in preferred_locations.split(","))
            if not loc_match:
                continue

        # Match score
        score, matched, missing = calculate_match(skills, job)
        if score < min_match:
            continue

        # Already applied?
        if has_applied_to_job(student["id"], job["job_id"]):
            continue

        matches.append({
            "job": job,
            "score": score,
            "matched": matched,
            "missing": missing,
        })

    return matches


# ---------- Email Template ----------
def build_email_html(student_name, job, score, matched, missing, token):
    yes_link = f"{config.BASE_URL}/auto_apply/respond/{token}?action=yes"
    no_link = f"{config.BASE_URL}/auto_apply/respond/{token}?action=no"

    matched_html = "".join(
        f'<span style="display:inline-block;background:#dcfce7;color:#16a34a;'
        f'padding:4px 10px;border-radius:6px;font-size:12px;margin:2px;">{s}</span>'
        for s in matched
    ) or "None"

    missing_html = "".join(
        f'<span style="display:inline-block;background:#fee2e2;color:#dc2626;'
        f'padding:4px 10px;border-radius:6px;font-size:12px;margin:2px;">{s}</span>'
        for s in missing
    ) or "None 🎉"

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
      <div style="max-width:600px;margin:0 auto;padding:24px;">
        <div style="background:#fff;border-radius:14px;padding:32px;box-shadow:0 4px 18px rgba(0,0,0,.06);">

          <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
            <div style="width:40px;height:40px;background:#2563eb;color:#fff;border-radius:10px;
                        display:inline-block;text-align:center;line-height:40px;font-weight:700;">PT</div>
            <span style="font-size:20px;font-weight:700;color:#0f172a;">PlaceTrack</span>
          </div>

          <h2 style="color:#0f172a;font-size:20px;margin:0 0 8px;">Hi {student_name},</h2>
          <p style="color:#64748b;font-size:14px;margin:0 0 24px;">
            We found a demo opportunity matching your profile.
          </p>

          <div style="border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div>
                <div style="font-size:18px;font-weight:700;color:#0f172a;">{job['company']}</div>
                <div style="color:#64748b;font-size:14px;margin-top:4px;">{job['role']}</div>
                <div style="color:#94a3b8;font-size:12px;margin-top:2px;">{job['location']} · {job['package']}</div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;">Match Score</div>
                <div style="font-size:28px;font-weight:800;color:#2563eb;">{score}%</div>
              </div>
            </div>
          </div>

          <div style="margin-bottom:20px;">
            <div style="font-size:13px;font-weight:600;color:#0f172a;margin-bottom:6px;">✅ Matched Skills</div>
            <div>{matched_html}</div>
          </div>

          <div style="margin-bottom:24px;">
            <div style="font-size:13px;font-weight:600;color:#0f172a;margin-bottom:6px;">⚠ Missing Skills</div>
            <div>{missing_html}</div>
          </div>

          <div style="border-top:1px solid #e2e8f0;padding-top:20px;margin-bottom:20px;">
            <div style="font-size:15px;font-weight:700;color:#0f172a;margin-bottom:14px;">
              Would you like to continue with this application?
            </div>

            <a href="{yes_link}"
               style="display:inline-block;background:#2563eb;color:#fff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:600;margin-right:8px;">
              YES, APPLY
            </a>

            <a href="{no_link}"
               style="display:inline-block;background:#f1f5f9;color:#0f172a;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:600;border:1px solid #e2e8f0;">
              NO, SKIP
            </a>
          </div>

          <p style="color:#94a3b8;font-size:12px;margin:0;">
            Nothing will be submitted until you click Yes.
          </p>

        </div>

        <p style="color:#94a3b8;font-size:11px;text-align:center;margin-top:16px;">
          Demo opportunity — verify details on the employer's official careers page.
        </p>
      </div>
    </body>
    </html>
    """


# ---------- Send Email ----------
def send_email(to_email, subject, html_body):
    """Send HTML email via Gmail SMTP. Returns (success, error_msg)."""
    if not config.SENDER_EMAIL or "your_email" in config.SENDER_EMAIL:
        return False, "SMTP not configured. Edit config.py first."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"PlaceTrack Alerts <{config.SENDER_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.send_message(msg)

        return True, None
    except Exception as e:
        return False, str(e)


# ---------- Run Auto Apply for One Student ----------
def run_auto_apply_for_student(student):
    """Run automation for one student. Returns (sent_count, errors)."""

    settings = get_auto_apply_settings(student["id"])
    if not settings or not settings["enabled"]:
        return 0, ["Auto-apply disabled"]

    if not settings["notification_email"]:
        return 0, ["No notification email set"]

    # Daily limit
    today_count = count_applications_today(student["id"])
    max_per_day = settings["max_per_day"] or 5
    if today_count >= max_per_day:
        return 0, [f"Daily limit reached ({max_per_day})"]

    # Get latest prediction + resume
    from database import get_predictions, get_resumes
    preds = get_predictions(student["id"])
    resumes = get_resumes(student["id"])
    pred = preds[0] if preds else None
    resume = resumes[0] if resumes else None

    if not pred:
        return 0, ["No prediction found"]

    # Find matches
    matches = find_matches_for_student(student, settings, pred, resume)

    if not matches:
        return 0, ["No new matches"]

    sent = 0
    errors = []
    remaining = max_per_day - today_count

    for m in matches[:remaining]:
        job = m["job"]
        score = m["score"]

        # Create application record with token
        token = secrets.token_urlsafe(24)
        app_id = create_application(
            student_id=student["id"],
            job_id=job["job_id"],
            company=job["company"],
            role=job["role"],
            location=job["location"],
            package=job["package"],
            match_score=score,
            matched_skills=",".join(m["matched"]),
            missing_skills=",".join(m["missing"]),
            token=token,
        )

        # Send email
        subject = f"New {score}% Job Match — {job['company']}"
        html = build_email_html(
            student["name"], job, score, m["matched"], m["missing"], token
        )
        ok, err = send_email(settings["notification_email"], subject, html)

        if ok:
            sent += 1
        else:
            errors.append(f"{job['company']}: {err}")

    return sent, errors


# ---------- Run for All Students ----------
def run_auto_apply_all():
    """Run automation for all students who enabled it."""
    students = get_all_auto_apply_students()
    total_sent = 0
    log = []

    for s in students:
        sent, errs = run_auto_apply_for_student(s)
        total_sent += sent
        if sent:
            log.append(f"✓ {s['name']} ({s['roll_no']}): {sent} email(s) sent")
        for e in errs:
            log.append(f"✗ {s['name']}: {e}")

    return total_sent, log
# ---------- Auto Apply ----------

def get_auto_apply_settings(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM auto_apply_settings WHERE student_id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    return row


def save_auto_apply_settings(student_id, data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM auto_apply_settings WHERE student_id=?", (student_id,))
    existing = c.fetchone()

    if existing:
        c.execute("""UPDATE auto_apply_settings SET
            enabled=?, notification_email=?, min_match=?, preferred_roles=?,
            preferred_locations=?, max_per_day=?, email_required=?,
            updated_at=CURRENT_TIMESTAMP
            WHERE student_id=?""",
            (data["enabled"], data["notification_email"], data["min_match"],
             data["preferred_roles"], data["preferred_locations"],
             data["max_per_day"], data["email_required"], student_id))
    else:
        c.execute("""INSERT INTO auto_apply_settings
            (student_id, enabled, notification_email, min_match,
             preferred_roles, preferred_locations, max_per_day, email_required)
            VALUES (?,?,?,?,?,?,?,?)""",
            (student_id, data["enabled"], data["notification_email"],
             data["min_match"], data["preferred_roles"],
             data["preferred_locations"], data["max_per_day"],
             data["email_required"]))

    conn.commit()
    conn.close()


def get_all_auto_apply_students():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT s.* FROM students s
                 JOIN auto_apply_settings a ON a.student_id = s.id
                 WHERE a.enabled = 1""")
    rows = c.fetchall()
    conn.close()
    return rows


def has_applied_to_job(student_id, job_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM applications WHERE student_id=? AND job_id=?",
              (student_id, job_id))
    row = c.fetchone()
    conn.close()
    return row is not None


def count_applications_today(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) AS cnt FROM applications
                 WHERE student_id=? AND date(created_at) = date('now')""",
              (student_id,))
    row = c.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def create_application(student_id, job_id, company, role, location, package,
                       match_score, matched_skills, missing_skills, token):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO applications
        (student_id, job_id, company, role, location, package,
         match_score, matched_skills, missing_skills, token, status)
        VALUES (?,?,?,?,?,?,?,?,?,?, 'pending')""",
        (student_id, job_id, company, role, location, package,
         match_score, matched_skills, missing_skills, token))
    conn.commit()
    app_id = c.lastrowid
    conn.close()
    return app_id


def get_application_by_token(token):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE token=?", (token,))
    row = c.fetchone()
    conn.close()
    return row


def update_application_status(token, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""UPDATE applications
                 SET status=?, responded_at=CURRENT_TIMESTAMP
                 WHERE token=?""",
              (status, token))
    conn.commit()
    conn.close()


def get_applications(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT * FROM applications
                 WHERE student_id=?
                 ORDER BY created_at DESC""",
              (student_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_application_stats(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
        SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) AS skipped,
        SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending
        FROM applications WHERE student_id=?""", (student_id,))
    row = c.fetchone()
    conn.close()
    return {
        "total": row["total"] or 0,
        "approved": row["approved"] or 0,
        "skipped": row["skipped"] or 0,
        "pending": row["pending"] or 0,
    }