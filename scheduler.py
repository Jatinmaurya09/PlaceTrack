import time
import threading
from auto_apply import run_auto_apply_all
import config


def _loop():
    """Background loop — runs auto-apply every N minutes."""
    interval = config.AUTO_APPLY_INTERVAL_MINUTES * 60  # convert to seconds

    # Initial delay so app starts cleanly
    time.sleep(10)

    while True:
        try:
            print(f"\n⏰ [Scheduler] Running auto-apply scan...")
            total, log = run_auto_apply_all()
            print(f"✅ [Scheduler] Total emails sent: {total}")
            for line in log:
                print("  " + line)
        except Exception as e:
            print(f"❌ [Scheduler] Error: {e}")

        time.sleep(interval)


def start_scheduler():
    """Start the background scheduler thread."""
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    print(f"🔄 Auto-apply scheduler started (every {config.AUTO_APPLY_INTERVAL_MINUTES} min)")