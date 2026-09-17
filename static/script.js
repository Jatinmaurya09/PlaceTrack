/* ============================================================
   PlaceTrack — Frontend Scripts
   ============================================================ */

/* ---------- Predictor Form Handler ---------- */
const predictForm = document.getElementById("predict-form");

if (predictForm) {
  predictForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = document.getElementById("submit-btn");
    const errBox = document.getElementById("error-box");
    const placeholder = document.getElementById("result-placeholder");
    const resultPanel = document.getElementById("result-panel");

    errBox.style.display = "none";
    resultPanel.style.display = "none";
    placeholder.style.display = "block";

    // Collect form data
    const formData = new FormData(predictForm);
    const payload = {};
    formData.forEach((value, key) => {
      payload[key] = value.trim();
    });

    // Client-side validation ranges
    const ranges = {
      age: [18, 30],
      cgpa: [0, 10],
      tenth_percentage: [0, 100],
      twelfth_percentage: [0, 100],
      backlogs: [0, 10],
      attendance_percentage: [0, 100],
      projects_completed: [0, 10],
      mock_interviews: [0, 20],
    };

    for (const [field, [lo, hi]] of Object.entries(ranges)) {
      const v = parseFloat(payload[field]);
      if (isNaN(v) || v < lo || v > hi) {
        showError(`${field.replace(/_/g, " ")} must be between ${lo} and ${hi}`);
        return;
      }
    }

    // Loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Predicting...';

    try {
      const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        showError(data.error || "Something went wrong");
        return;
      }

      showResult(data);
    } catch (err) {
      showError("Network error: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = "🔍 Generate Prediction";
    }
  });
}

function showError(msg) {
  const errBox = document.getElementById("error-box");
  const placeholder = document.getElementById("result-placeholder");
  const resultPanel = document.getElementById("result-panel");
  const btn = document.getElementById("submit-btn");

  if (placeholder) placeholder.style.display = "block";
  if (resultPanel) resultPanel.style.display = "none";

  errBox.textContent = "❌ " + msg;
  errBox.style.display = "block";

  if (btn) {
    btn.disabled = false;
    btn.innerHTML = "🔍 Generate Prediction";
  }
  errBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

function showResult(data) {
  const placeholder = document.getElementById("result-placeholder");
  const resultPanel = document.getElementById("result-panel");
  const inner = document.getElementById("result-inner");
  const probEl = document.getElementById("result-prob");
  const labelEl = document.getElementById("result-label");
  const bar = document.getElementById("result-bar");
  const dashLink = document.getElementById("dashboard-link");

  const placed = data.prediction === "Placed";

  // Update panel
  inner.className = "result-panel " + (placed ? "placed" : "not-placed");

  if (data.probability !== null && data.probability !== undefined) {
    const pct = (data.probability * 100).toFixed(0);
    probEl.textContent = pct + "%";
    probEl.className = "result-big " + (placed ? "green" : "red");
    bar.style.width = pct + "%";
    bar.className = "progress-bar " + (placed ? "green" : "red");
  } else {
    probEl.textContent = "—";
    probEl.className = "result-big";
    bar.style.width = "0%";
  }

  labelEl.innerHTML = placed
    ? '✅ <span class="text-success">Likely to be Placed</span>'
    : '❌ <span class="text-danger">Likely Not Placed</span>';

  // Dashboard link
  dashLink.style.display = "block";
  dashLink.href = data.redirect || "/dashboard";

  placeholder.style.display = "none";
  resultPanel.style.display = "block";
  resultPanel.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------- ATS Upload Handler ---------- */
const atsForm = document.getElementById("ats-form");

if (atsForm) {
  atsForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const box = document.getElementById("ats-result");
    const btn = document.getElementById("ats-submit");
    const rollNo = atsForm.dataset.roll;

    box.innerHTML = '<div class="alert alert-info">⏳ Analyzing resume...</div>';

    if (btn) btn.disabled = true;

    const fd = new FormData(atsForm);

    try {
      const res = await fetch(`/upload_resume/${rollNo}`, {
        method: "POST",
        body: fd,
      });
      const data = await res.json();

      if (data.error) {
        box.innerHTML = `<div class="alert alert-error">${data.error}</div>`;
        return;
      }

      const pct = data.ats_score;
      const color = pct >= 60 ? "green" : pct >= 40 ? "blue" : "red";

      box.innerHTML = `
        <div class="result-panel" style="text-align:left;margin-top:1rem;">
          <h3 style="margin-bottom:.75rem;">Analysis Result</h3>
          <div style="text-align:center;">
            <div class="result-big ${color === 'green' ? 'green' : color === 'red' ? 'red' : ''}"
                 style="font-size:2.5rem;">${pct}%</div>
            <p class="text-muted" style="margin-top:.5rem;">ATS Match Score</p>
            <div class="progress" style="max-width:280px;margin:.75rem auto 0;">
              <div class="progress-bar ${color}" style="width:${pct}%"></div>
            </div>
          </div>
          <hr style="margin:1.25rem 0;border:none;border-top:1px solid var(--border);">
          <p style="font-size:.9rem;margin-bottom:.5rem;">
            <b>✅ Matched Skills (${data.matched_skills.length}):</b>
          </p>
          <p style="font-size:.85rem;color:#475569;margin-bottom:1rem;">
            ${data.matched_skills.map(s => `<span class="badge badge-success" style="margin:2px;">${s}</span>`).join("") || "None"}
          </p>
          <p style="font-size:.9rem;margin-bottom:.5rem;">
            <b>❌ Missing Skills (top 10):</b>
          </p>
          <p style="font-size:.85rem;color:#475569;">
            ${data.missing_skills.map(s => `<span class="badge badge-danger" style="margin:2px;">${s}</span>`).join("") || "None"}
          </p>
        </div>`;

      setTimeout(() => location.reload(), 4000);
    } catch (err) {
      box.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}

/* ---------- Smooth Scroll for Sidebar on Mobile ---------- */
const menuBtn = document.getElementById("menu-toggle");
if (menuBtn) {
  menuBtn.addEventListener("click", () => {
    document.querySelector(".sidebar").classList.toggle("open");
  });
}