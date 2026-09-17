import os

# SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Environment variables se lo, warna fallback
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "jatinkmaurya09@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

# Base URL — Render pe deploy hone ke baad update karo
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

# Auto Apply
AUTO_APPLY_INTERVAL_MINUTES = 5
DEFAULT_MIN_MATCH = 70