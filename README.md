# 🎓 PlaceTrack — Student Placement Prediction System

An end-to-end ML-powered web application that predicts student placement outcomes, analyzes resumes with ATS scoring, matches jobs, and automates the job application workflow via email.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange)
![License](https://img.shields.io/badge/License-Educational-lightgrey)

---

## 📌 Overview

**PlaceTrack** is a full-stack placement preparation platform built for college students and placement officers. It combines:

- **Machine Learning** for placement prediction
- **Resume Analysis** with ATS scoring
- **Job Matching** based on skills
- **Auto Apply** with email YES/NO approval
- **Multi-user Dashboards** for students and admins

This is an **educational ML project** — predictions are not guarantees of real placement.

---

## ✨ Features

### 🎯 For Students
- **Placement Prediction** — ML model predicts Placed/Not Placed with probability
- **Student Dashboard** — Stats, history chart, personalized insights
- **Resume ATS Analyzer** — Upload PDF → keyword matching → ATS score + matched/missing skills
- **Company Matches** — 15 companies ranked by skill match + eligibility (CGPA, backlogs)
- **Auto Apply** — Enable automation → get email notifications for matches above threshold
- **Email Approval Flow** — Click YES (apply) or NO (skip) directly from email
- **Application History** — Track all job matches and their statuses

### 🎛️ For Admin (Placement Officer)
- **Admin Dashboard** — Combined view of all students
- **Charts** — Placed vs Not Placed (pie), Department-wise (bar)
- **All Students Table** — Predictions, ATS scores, application status
- **Top Performers** — List of students with high placement probability

### 🧠 ML & Automation
- **3 Models Compared:** Logistic Regression, Decision Tree, Random Forest
- **Best Model Selected:** Logistic Regression (~86% accuracy)
- **Fairness:** Gender is collected but **excluded from ML features**
- **Background Scheduler:** Runs every 5 minutes for auto-apply
- **Real Email:** Gmail SMTP integration with HTML email templates

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask (Python 3.11) |
| **ML** | scikit-learn, pandas, numpy, joblib |
| **Database** | SQLite (5 tables) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Jinja2 |
| **Charts** | Chart.js |
| **PDF Parsing** | pdfplumber |
| **Email** | Gmail SMTP (smtplib) |
| **Scheduler** | Python threading |
| **Hosting** | Render.com (Gunicorn) |

---

## 📁 Project Structure

```
student-placement-prediction/
│
├── app.py                     # Flask main app (18 routes)
├── database.py                # SQLite operations (5 tables)
├── train_model.py             # ML training script
├── auto_apply.py              # Email automation engine
├── companies.py               # Company matching logic
├── scheduler.py               # Background scheduler
├── config.py                  # Email credentials (env vars)
├── requirements.txt
├── Procfile                   # Render deployment
├── jobs.csv                   # 12 job listings
├── placement.db               # SQLite database (auto-created)
│
├── dataset/
│   └── student_placement.csv  # Auto-generated (800 rows)
│
├── model/
│   └── placement_model.pkl    # Trained ML pipeline
│
├── templates/
│   ├── login.html
│   ├── predictor.html
│   ├── dashboard.html
│   ├── ats.html
│   ├── companies.html
│   ├── auto_apply.html
│   ├── applications.html
│   ├── response.html
│   └── admin.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── uploads/                   # Uploaded resume PDFs
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- pip
- (Optional) Gmail account for email features

### Step 1: Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/placetrack.git
cd placetrack
```

### Step 2: Create virtual environment
**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Train the ML model
```bash
python train_model.py
```
This will:
- Auto-generate a demo dataset (`dataset/student_placement.csv`) if missing
- Train 3 models and pick the best
- Save the pipeline to `model/placement_model.pkl`

### Step 5: Configure email (optional)
Edit `config.py` and add your Gmail App Password:
```python
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_16_char_app_password"
```

> **How to generate App Password:**
> 1. Enable 2-Step Verification: https://myaccount.google.com/security
> 2. Generate App Password: https://myaccount.google.com/apppasswords
> 3. Copy the 16-character code into `config.py`

### Step 6: Run the application
```bash
python app.py
```

Open in browser:
- **Main:** http://127.0.0.1:5000
- **Admin:** http://127.0.0.1:5000/admin
- **Predictor:** http://127.0.0.1:5000/predictor

---

## 🎬 Usage Guide

### For Students
1. Go to `/predictor` → fill 18-field form → **Generate Prediction**
2. Auto-login → view `/dashboard` with stats + history
3. Upload resume at `/ats` → get ATS score
4. Check `/companies` → see matched companies with filters
5. Enable `/auto-apply` → set email + threshold
6. Check email → click **YES, APPLY** or **NO, SKIP**
7. Track everything in `/applications`

### For Admin
1. Go to `/login` → click **Administrator** tab
2. View `/admin` → see all students, charts, stats

### Demo Login
- **Roll Number:** `21CS001` (after filling predictor form)
- **Admin:** Click "Administrator" tab → Continue

---

## 🧠 ML Model Details

### Dataset
- **Rows:** 800 (auto-generated demo)
- **Columns:** 16 (15 features + target)
- **Target:** `placement_status` (Placed / Not Placed)

### Features Used (14 after excluding gender)
```
age, branch, cgpa, tenth_percentage, twelfth_percentage,
backlogs, attendance_percentage, internship_experience,
dsa_level, coding_practice, projects_completed,
aptitude_level, communication_level, mock_interviews
```

### Preprocessing Pipeline
```python
ColumnTransformer([
    ("num", StandardScaler(), [numeric features]),
    ("cat", OneHotEncoder(handle_unknown="ignore"), [categorical features])
])
```

### Model Comparison Results

| Model | Accuracy |
|---|---|
| **Logistic Regression** | **~86%** ✅ |
| Random Forest | ~82% |
| Decision Tree | ~78% |

**Best model saved:** `model/placement_model.pkl`

---

## 🔌 API Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Redirect based on session |
| `/login` | GET | Login page |
| `/api/login` | POST | Login API (student roll_no / admin) |
| `/logout` | GET | Clear session |
| `/predictor` | GET | Prediction form |
| `/predict` | POST | ML prediction |
| `/dashboard` | GET | Student dashboard |
| `/ats` | GET | ATS analyzer page |
| `/upload_resume/<roll_no>` | POST | Resume upload + scoring |
| `/companies` | GET | Company matches (with filters) |
| `/auto-apply` | GET | Auto apply settings |
| `/auto-apply/save` | POST | Save auto apply settings |
| `/auto-apply/run-now` | POST | Manual trigger |
| `/auto_apply/respond/<token>` | GET | Email YES/NO handler |
| `/applications` | GET | Application history |
| `/admin` | GET | Admin dashboard |
| `/student/<roll_no>` | GET | Individual student view |

---

## 📧 Email Workflow

```
Scheduler runs every 5 min
     ↓
Loads students with auto-apply enabled
     ↓
For each student:
   - Fetch skills from resume + form
   - Match against jobs.csv
   - Filter by CGPA, backlogs, threshold
   - Send HTML email with YES/NO buttons
     ↓
Student clicks YES → status = 'approved'
Student clicks NO  → status = 'skipped'
```

### Email Template Includes
- Company name, role, location, package
- Match score (%)
- Matched skills (green badges)
- Missing skills (red badges)
- YES, APPLY / NO, SKIP buttons

---

## ⚖️ Fairness Note

**Gender is collected on the prediction form but EXCLUDED from ML features.**

This is done to reduce the risk of using a sensitive attribute in prediction. The model trains on the other 14 fields only.

---

## ⚠️ Limitations

- **Demo Dataset:** Auto-generated synthetic data — NOT real placement data
- **Small Feature Set:** Real placement depends on many more factors
- **ATS Scoring:** Keyword-based, not semantic
- **SQLite:** Not ideal for production (use PostgreSQL for scale)
- **Gmail Limit:** 500 emails/day free (use SendGrid for bulk)

---

## 🚨 Disclaimer

Sample rows and demo data are **not a real placement dataset** and should not be treated as scientifically valid training data.

This tool is for **educational demonstration only**. Predictions are based on the trained ML model and **do not guarantee actual placement**.

---

## 🌐 Deployment (Render.com)

1. Push code to GitHub
2. Create new Web Service on https://render.com
3. Connect GitHub repo
4. Configure:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app`
5. Add environment variables:
   - `SENDER_EMAIL` = your Gmail
   - `SENDER_PASSWORD` = App Password
   - `SECRET_KEY` = random string
   - `BASE_URL` = your Render URL
   - `PYTHON_VERSION` = 3.11.0

---

## 🧪 Testing

### Test Email Setup
```bash
python -c "from auto_apply import send_email; ok, err = send_email('your_email@gmail.com', 'Test', '<h1>Hi</h1>'); print('OK' if ok else err)"
```

### Test Auto Apply
```bash
python -c "from auto_apply import run_auto_apply_all; total, log = run_auto_apply_all(); print(f'Total: {total}'); [print(l) for l in log]"
```

---

## 🛠️ Common Errors & Fixes

| Error | Fix |
|---|---|
| `TemplateNotFound` | File must be inside `templates/` folder |
| `Model not found` | Run `python train_model.py` |
| `SMTP not configured` | Update `config.py` |
| `535 Authentication failed` | Use Gmail App Password, not regular |
| `Port already in use` | `taskkill /F /IM python.exe` |
| `No new matches` | Lower minimum match % |

---

## 🚀 Future Enhancements

- [ ] Migrate to PostgreSQL for scale
- [ ] Add SendGrid for bulk emails
- [ ] Real job scraping from Naukri/LinkedIn
- [ ] Advanced NLP for resume parsing
- [ ] Skill-based learning recommendations
- [ ] Mobile app (React Native)

---

## 👨‍💻 Author

**Jatin Maurya**
- GitHub: [@jatinkmaurya09](https://github.com/jatinkmaurya09)
- Email: jatinkmaurya09@gmail.com

---

## 📜 License

This project is built for **educational purposes** as part of a college ML project.

---

## 🙏 Acknowledgments

- scikit-learn for ML tools
- Flask for web framework
- Chart.js for visualizations
- pdfplumber for PDF parsing

---

**Made with ❤️ for students preparing for placements**