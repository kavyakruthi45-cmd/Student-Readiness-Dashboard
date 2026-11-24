"""
Page 3 — Student Table with Search, Filters, Sorting, and Export.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from pages.page_utils import inject_css, require_auth, render_sidebar, readiness_badge
from services.student_service import get_all_students, delete_student
from utils.csv_utils import students_to_dataframe, dataframe_to_excel_bytes
import config

st.set_page_config(page_title="Student Database | TalentForge", page_icon="🗂️", layout="wide")
inject_css()
require_auth(role="admin")
render_sidebar("admin")

st.markdown('<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">🗂️ Student Database</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-bottom:20px;">Search, filter, sort and export student records.</p>', unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters & Search", expanded=True):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        search = st.text_input("Search name / roll no / email", placeholder="Type to search...")
    with fc2:
        dept_filter = st.selectbox("Department", ["All"] + config.DEPARTMENTS)
    with fc3:
        year_opts = ["All"] + [str(y) for y in sorted(config.ACADEMIC_YEARS)]
        year_filter = st.selectbox("Graduation Year", year_opts)
    with fc4:
        level_filter = st.selectbox("Readiness Level", ["All", "Ready", "Almost Ready", "Needs Improvement"])

year_val = int(year_filter) if year_filter != "All" else None

students = get_all_students(
    department=dept_filter if dept_filter != "All" else None,
    graduation_year=year_val,
    readiness_level=level_filter if level_filter != "All" else None,
    search=search if search else None,
    sort_by="overall_score",
    sort_desc=True,
)

st.markdown(f'<div style="color:#64748B;font-size:.85rem;margin-bottom:12px;">Showing <b>{len(students)}</b> student(s)</div>', unsafe_allow_html=True)

if not students:
    st.info("No students match the current filters.")
    st.stop()

# ── Action bar ────────────────────────────────────────────────────────────────
ab1, ab2, ab3, ab4 = st.columns([1, 1, 1, 3])
df_all = students_to_dataframe(students)

with ab1:
    csv_data = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export CSV", csv_data, "students_export.csv", "text/csv", use_container_width=True)
with ab2:
    xlsx_data = dataframe_to_excel_bytes(df_all)
    st.download_button("⬇️ Export Excel", xlsx_data, "students_export.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
with ab3:
    if st.button("➕ Add Student", use_container_width=True):
        st.session_state["show_add_form"] = not st.session_state.get("show_add_form", False)

# ── Add Student form ──────────────────────────────────────────────────────────
if st.session_state.get("show_add_form", False):
    with st.form("add_student_form"):
        st.markdown("**Add New Student**")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_roll = st.text_input("Roll No", placeholder="CSE25001")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
        with c2:
            new_dept = st.selectbox("Department", config.DEPARTMENTS)
            new_year = st.selectbox("Graduation Year", config.ACADEMIC_YEARS)
            new_cgpa = st.number_input("CGPA (0-10)", 0.0, 10.0, 7.5, 0.01)
        with c3:
            new_tech = st.slider("Technical Score", 0, 100, 60)
            new_apt = st.slider("Aptitude Score", 0, 100, 60)
            new_comm = st.slider("Communication Score", 0, 100, 60)
            new_proj = st.slider("Project Score", 0, 100, 60)
            new_cert = st.slider("Certifications Score", 0, 100, 50)
            new_mock = st.slider("Mock Interview Score", 0, 100, 55)

        if st.form_submit_button("Add Student", type="primary"):
            try:
                from services.student_service import create_student
                from utils.validators import validate_roll_no, validate_email, validate_cgpa
                create_student({
                    "roll_no": validate_roll_no(new_roll),
                    "full_name": new_name.strip(),
                    "email": validate_email(new_email),
                    "department": new_dept,
                    "graduation_year": new_year,
                    "cgpa": validate_cgpa(new_cgpa),
                    "technical_score": float(new_tech),
                    "aptitude_score": float(new_apt),
                    "communication_score": float(new_comm),
                    "project_score": float(new_proj),
                    "certifications_score": float(new_cert),
                    "mock_interview_score": float(new_mock),
                })
                st.success("✅ Student added successfully!")
                st.session_state["show_add_form"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── Student Table ─────────────────────────────────────────────────────────────
st.markdown("---")

level_colors_bg = {
    "Ready": "#D1FAE5",
    "Almost Ready": "#FEF3C7",
    "Needs Improvement": "#FEE2E2",
}

for s in students:
    bg = level_colors_bg.get(s.readiness_level, "#F8FAFC")
    badge_html = readiness_badge(s.readiness_level)
    dept_short = s.department.split("&")[0].strip()[:20]

    col_info, col_scores, col_level, col_actions = st.columns([3, 3, 1.5, 1.5])

    with col_info:
        st.markdown(f"""
        <div style="padding:8px 0;">
          <div style="font-weight:700;font-size:.92rem;color:#0F172A;">{s.full_name}</div>
          <div style="font-size:.75rem;color:#64748B;">{s.roll_no} &nbsp;·&nbsp; {dept_short}</div>
          <div style="font-size:.73rem;color:#94A3B8;">Class of {s.graduation_year} &nbsp;·&nbsp; CGPA: {s.cgpa:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_scores:
        st.markdown(f"""
        <div style="padding:8px 0;font-size:.78rem;color:#334155;">
          Tech: <b>{s.technical_score:.0f}</b> &nbsp;
          Apt: <b>{s.aptitude_score:.0f}</b> &nbsp;
          Comm: <b>{s.communication_score:.0f}</b><br/>
          Proj: <b>{s.project_score:.0f}</b> &nbsp;
          Cert: <b>{s.certifications_score:.0f}</b> &nbsp;
          Mock: <b>{s.mock_interview_score:.0f}</b>
        </div>
        """, unsafe_allow_html=True)

    with col_level:
        score_color = "#10B981" if s.overall_score >= 75 else "#F59E0B" if s.overall_score >= 55 else "#EF4444"
        st.markdown(f"""
        <div style="padding:8px 0;text-align:center;">
          <div style="font-size:1.5rem;font-weight:800;color:{score_color};">{s.overall_score:.0f}</div>
          {badge_html}
        </div>
        """, unsafe_allow_html=True)

    with col_actions:
        if st.button("🔍 Detail", key=f"detail_{s.id}", use_container_width=True):
            st.session_state["selected_student_id"] = s.id
            st.switch_page("pages/5_Student_Detail.py")
        if st.button("🗑️ Delete", key=f"del_{s.id}", use_container_width=True):
            st.session_state[f"confirm_delete_{s.id}"] = True

        if st.session_state.get(f"confirm_delete_{s.id}"):
            st.warning(f"Delete {s.full_name}?")
            conf_c1, conf_c2 = st.columns(2)
            if conf_c1.button("Yes", key=f"yes_{s.id}"):
                delete_student(s.id)
                st.success("Deleted.")
                st.rerun()
            if conf_c2.button("No", key=f"no_{s.id}"):
                st.session_state[f"confirm_delete_{s.id}"] = False
                st.rerun()

    st.markdown('<hr style="margin:4px 0;border-color:#F1F5F9;">', unsafe_allow_html=True)
