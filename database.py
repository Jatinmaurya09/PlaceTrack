import sqlite3

DB_PATH = "placement.db"


# ============================================================
# CONNECTION
# ============================================================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# INIT DB
# ============================================================

def init_db():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ---------- Students ----------
    c.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ---------- Predictions ----------
    c.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        age INTEGER, gender TEXT, branch TEXT,
        cgpa REAL, tenth_percentage REAL, twelfth_percentage REAL,
        backlogs INTEGER, attendance_percentage REAL,
        internship_experience TEXT, dsa_level TEXT,
        coding_practice TEXT, projects_completed INTEGER,
        aptitude_level TEXT, communication_level TEXT,
        mock_interviews INTEGER,
        prediction TEXT, probability REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    # ---------- Resumes ----------
    c.execute("""CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        filename TEXT,
        ats_score REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    # ---------- Auto Apply Settings ----------
    c.execute("""CREATE TABLE IF NOT EXISTS auto_apply_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE,
        enabled INTEGER DEFAULT 0,
        notification_email TEXT,
        min_match INTEGER DEFAULT 70,
        preferred_roles TEXT,
        preferred_locations TEXT,
        max_per_day INTEGER DEFAULT 5,
        email_required INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    # ---------- Applications ----------
    c.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        job_id TEXT,
        company TEXT,
        role TEXT,
        location TEXT,
        package TEXT,
        match_score REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        status TEXT DEFAULT 'pending',
        token TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        responded_at TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    conn.commit()
    conn.close()


# ============================================================
# STUDENTS
# ============================================================

def get_or_create_student(name, roll_no, department):
    """Return student id; create if not exists; update name/dept if exists."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM students WHERE roll_no=?", (roll_no,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE students SET name=?, department=? WHERE id=?",
                  (name, department, row["id"]))
        conn.commit()
        sid = row["id"]
    else:
        c.execute("INSERT INTO students (name, roll_no, department) VALUES (?,?,?)",
                  (name, roll_no, department))
        conn.commit()
        sid = c.lastrowid
    conn.close()
    return sid


def get_student_by_roll(roll_no):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
    row = c.fetchone()
    conn.close()
    return row


def get_all_students():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT s.*,
          (SELECT prediction FROM predictions p WHERE p.student_id=s.id ORDER BY created_at DESC LIMIT 1) AS latest_prediction,
          (SELECT probability FROM predictions p WHERE p.student_id=s.id ORDER BY created_at DESC LIMIT 1) AS latest_probability,
          (SELECT ats_score FROM resumes r WHERE r.student_id=s.id ORDER BY uploaded_at DESC LIMIT 1) AS latest_ats
        FROM students s ORDER BY s.created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


# ============================================================
# PREDICTIONS
# ============================================================

def save_prediction(sid, data, prediction, probability):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO predictions
        (student_id, age, gender, branch, cgpa, tenth_percentage, twelfth_percentage,
         backlogs, attendance_percentage, internship_experience, dsa_level,
         coding_practice, projects_completed, aptitude_level, communication_level,
         mock_interviews, prediction, probability)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (sid, data["age"], data["gender"], data["branch"], data["cgpa"],
         data["tenth_percentage"], data["twelfth_percentage"], data["backlogs"],
         data["attendance_percentage"], data["internship_experience"], data["dsa_level"],
         data["coding_practice"], data["projects_completed"], data["aptitude_level"],
         data["communication_level"], data["mock_interviews"], prediction, probability))
    conn.commit()
    conn.close()


def get_predictions(sid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM predictions WHERE student_id=? ORDER BY created_at DESC", (sid,))
    rows = c.fetchall()
    conn.close()
    return rows


# ============================================================
# RESUMES
# ============================================================

def save_resume(sid, filename, score, matched, missing):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO resumes (student_id, filename, ats_score, matched_skills, missing_skills)
                 VALUES (?,?,?,?,?)""",
              (sid, filename, score, ",".join(matched), ",".join(missing)))
    conn.commit()
    conn.close()


def get_resumes(sid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM resumes WHERE student_id=? ORDER BY uploaded_at DESC", (sid,))
    rows = c.fetchall()
    conn.close()
    return rows


# ============================================================
# ADMIN STATS
# ============================================================

def get_admin_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) AS total FROM students")
    total = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) AS placed FROM predictions WHERE prediction='Placed'")
    placed = c.fetchone()["placed"]
    c.execute("SELECT COUNT(*) AS not_placed FROM predictions WHERE prediction='Not Placed'")
    not_placed = c.fetchone()["not_placed"]
    c.execute("SELECT AVG(cgpa) AS avg_cgpa FROM predictions")
    avg_cgpa = c.fetchone()["avg_cgpa"] or 0
    conn.close()
    return {"total": total, "placed": placed, "not_placed": not_placed,
            "avg_cgpa": round(avg_cgpa, 2)}


# ============================================================
# AUTO APPLY SETTINGS
# ============================================================

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


# ============================================================
# APPLICATIONS
# ============================================================

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


# ============================================================
# AUTO-INIT WHEN RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    init_db()
    print("Database initialized:", DB_PATH)