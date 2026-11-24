"""
Page 9 — Student Update Profile: scores, skills, projects, certifications.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from pages.page_utils import inject_css, require_auth, render_sidebar, readiness_badge
from services.student_service import get_student_by_id, update_student
from services.scoring_service import calculate_readiness_score, get_readiness_level
import config

st.set_page_config(page_title="Update Profile | TalentForge", page_icon="✏️", layout="wide")
inject_css()
sess = require_auth()
render_sidebar("student")

student_id = sess.get("student_id")
if not student_id:
    st.error("Your account is not linked to a student profile. Contact admin.")
    st.stop()

student = get_student_by_id(student_id)
if not student:
    st.error("Student not found.")
    st.stop()

st.markdown('<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">✏️ Update My Profile</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-bottom:20px;">Update your competency scores, skills, projects and certifications to keep your readiness score current.</p>', unsafe_allow_html=True)

# Live score preview (before saving)
st.markdown('<div class="section-header">📊 Score Preview</div>', unsafe_allow_html=True)
prev_col1, prev_col2, prev_col3 = st.columns(3)

with prev_col1:
    new_tech  = st.slider("Technical Skills", 0, 100, int(student.technical_score), key="pv_tech")
    new_apt   = st.slider("Aptitude & Logic", 0, 100, int(student.aptitude_score),  key="pv_apt")
    new_comm  = st.slider("Communication",    0, 100, int(student.communication_score), key="pv_comm")
with prev_col2:
    new_proj  = st.slider("Project Quality",  0, 100, int(student.project_score),   key="pv_proj")
    new_cert  = st.slider("Certifications",   0, 100, int(student.certifications_score), key="pv_cert")
    new_mock  = st.slider("Mock Interviews",  0, 100, int(student.mock_interview_score),  key="pv_mock")
with prev_col3:
    new_cgpa  = st.number_input("CGPA (0–10)", 0.0, 10.0, float(student.cgpa), 0.01, key="pv_cgpa")

# Live calculation
preview_score = calculate_readiness_score(
    new_tech, new_apt, new_comm, new_proj, new_cgpa, new_cert, new_mock
)
preview_level = get_readiness_level(preview_score)
prev_color = "#10B981" if preview_level == "Ready" else "#F59E0B" if preview_level == "Almost Ready" else "#EF4444"
delta_val = round(preview_score - student.overall_score, 1)
delta_disp = f"+{delta_val}" if delta_val >= 0 else str(delta_val)
delta_color = "#10B981" if delta_val >= 0 else "#EF4444"

st.markdown(f"""
<div style="background:white;border:1px solid #E2E8F0;border-radius:12px;
            padding:18px 24px;display:flex;align-items:center;gap:24px;margin:16px 0;">
  <div style="text-align:center;">
    <div style="font-size:2.8rem;font-weight:900;color:{prev_color};">{preview_score:.1f}</div>
    <div style="font-size:.8rem;color:#64748B;">/ 100 Score</div>
  </div>
  <div>
    <div style="font-size:.85rem;font-weight:700;color:{prev_color};">{preview_level}</div>
    <div style="font-size:.8rem;color:{delta_color};font-weight:600;">
      {delta_disp} from current score ({student.overall_score:.1f})
    </div>
  </div>
  {readiness_badge(preview_level)}
</div>
""", unsafe_allow_html=True)

# ── Qualitative profile ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">📝 Skills & Profile Details</div>', unsafe_allow_html=True)

with st.form("update_profile_form"):
    sk1, sk2 = st.columns(2)
    with sk1:
        new_skills = st.text_area(
            "Key Technical Skills (comma-separated)",
            value=student.key_skills or "",
            height=100,
            placeholder="Python, React, SQL, Machine Learning, AWS..."
        )
        new_proj_summary = st.text_area(
            "Project Summary",
            value=student.project_summary or "",
            height=100,
            placeholder="Describe your most significant project..."
        )
    with sk2:
        new_certs_list = st.text_area(
            "Certifications (one per line or semicolon-separated)",
            value=student.certifications_list or "",
            height=100,
            placeholder="AWS Cloud Practitioner; Google Data Analytics..."
        )
        st.markdown("**Current Score Details**")
        st.markdown(f"""
        <div style="font-size:.82rem;color:#64748B;line-height:1.9;">
          Current Overall: <b>{student.overall_score:.1f}</b><br/>
          CGPA: <b>{student.cgpa:.2f}/10.0</b><br/>
          Dept: <b>{student.department}</b><br/>
          Batch: <b>{student.graduation_year}</b>
        </div>
        """, unsafe_allow_html=True)

    submitted = st.form_submit_button("💾 Save All Changes", type="primary", use_container_width=True)

    if submitted:
        try:
            update_student(student_id, {
                "technical_score": float(new_tech),
                "aptitude_score": float(new_apt),
                "communication_score": float(new_comm),
                "project_score": float(new_proj),
                "certifications_score": float(new_cert),
                "mock_interview_score": float(new_mock),
                "cgpa": float(new_cgpa),
                "key_skills": new_skills.strip(),
                "project_summary": new_proj_summary.strip(),
                "certifications_list": new_certs_list.strip(),
            })
            st.success(f"✅ Profile updated! New readiness score: **{preview_score:.1f}/100** ({preview_level})")
            st.balloons()
        except Exception as e:
            st.error(f"Update failed: {e}")

st.markdown("""
<div class="alert alert-info" style="margin-top:16px;">
  💡 <b>Tip:</b> Every update is logged with a timestamp to track your progress over time.
  Visit <b>My Readiness</b> to see your trend chart.
</div>
""", unsafe_allow_html=True)
