"""
Page 5 — Student Detail Drill-down (Admin view).
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from pages.page_utils import inject_css, require_auth, render_sidebar, readiness_badge, level_color
from services.student_service import get_student_by_id, get_student_history, update_student
from services.scoring_service import get_component_scores_dict
from services.recommendation_service import generate_recommendations
from services.report_service import generate_student_pdf_report
import config

st.set_page_config(page_title="Student Detail | TalentForge", page_icon="🔍", layout="wide")
inject_css()
require_auth(role="admin")
render_sidebar("admin")

student_id = st.session_state.get("selected_student_id")

# Allow fallback to query param (for future deep-linking)
if not student_id:
    st.warning("No student selected. Go to the **Student Database** page and click **Detail**.")
    if st.button("← Back to Student Table"):
        st.switch_page("pages/3_Student_Table.py")
    st.stop()

student = get_student_by_id(student_id)
if not student:
    st.error("Student not found.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
if st.button("← Back to Student Table", key="back_btn"):
    st.switch_page("pages/3_Student_Table.py")

lc = level_color(student.readiness_level)
badge_html = readiness_badge(student.readiness_level)
st.markdown(f"""
<div class="score-hero" style="margin-top:12px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div>
      <h2 style="margin:0 0 4px;">{student.full_name}</h2>
      <div style="opacity:.8;font-size:.88rem;">
        {student.roll_no} &nbsp;·&nbsp; {student.department} &nbsp;·&nbsp;
        Class of {student.graduation_year} &nbsp;·&nbsp; {student.email}
      </div>
      <div style="margin-top:8px;">{badge_html}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:3rem;font-weight:900;">{student.overall_score:.1f}</div>
      <div style="opacity:.75;font-size:.82rem;">/ 100 Readiness Score</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

tab_detail, tab_edit, tab_rec = st.tabs(["📊 Score Analysis", "✏️ Edit Scores", "🎯 Recommendations"])

# ── Tab 1: Score Analysis ─────────────────────────────────────────────────────
with tab_detail:
    col_radar, col_hist = st.columns(2, gap="large")

    with col_radar:
        st.markdown('<div class="section-header">Competency Radar</div>', unsafe_allow_html=True)
        comp_scores = get_component_scores_dict(student)
        labels = [config.COMPONENT_LABELS[k] for k in comp_scores]
        values = list(comp_scores.values())

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=labels + [labels[0]],
            fill="toself", fillcolor="rgba(37,99,235,.15)",
            line=dict(color="#2563EB", width=2), name="Student",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[75] * (len(labels) + 1), theta=labels + [labels[0]],
            fill="toself", fillcolor="rgba(16,185,129,.06)",
            line=dict(color="#10B981", width=1.5, dash="dash"), name="Target",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=320, margin=dict(t=20, b=50),
            paper_bgcolor="white", font={"family": "Inter"},
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_hist:
        st.markdown('<div class="section-header">Score vs. Target</div>', unsafe_allow_html=True)
        comp_df = pd.DataFrame([
            {"Component": config.COMPONENT_LABELS[k], "Score": v,
             "Gap": max(0, 75 - v), "Achieved": min(v, 75)}
            for k, v in comp_scores.items()
        ])
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=comp_df["Achieved"], y=comp_df["Component"], orientation="h",
            marker_color="#2563EB", name="Score", text=[f"{v:.0f}" for v in comp_df["Score"]],
            textposition="inside",
        ))
        fig_bar.add_trace(go.Bar(
            x=comp_df["Gap"], y=comp_df["Component"], orientation="h",
            marker_color="#E2E8F0", name="Gap to Target",
        ))
        fig_bar.update_layout(
            barmode="stack", height=320, margin=dict(t=10, b=10, l=10, r=40),
            xaxis=dict(range=[0, 100]), paper_bgcolor="white",
            plot_bgcolor="white", font={"family": "Inter"},
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # History trend
    history = get_student_history(student_id)
    if len(history) >= 2:
        st.markdown('<div class="section-header">Progress Trend</div>', unsafe_allow_html=True)
        hdf = pd.DataFrame([{
            "Month": h.month_label, "Overall": h.overall_score, "Date": h.recorded_at
        } for h in history]).sort_values("Date")
        fig_tr = go.Figure(go.Scatter(
            x=hdf["Month"], y=hdf["Overall"], mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=7), fill="tozeroy", fillcolor="rgba(37,99,235,.07)",
        ))
        fig_tr.add_hline(y=75, line_dash="dash", line_color="#10B981", annotation_text="Ready Threshold")
        fig_tr.update_layout(
            height=220, margin=dict(t=10, b=20, l=0, r=20),
            yaxis=dict(range=[0, 105]), paper_bgcolor="white",
            plot_bgcolor="white", font={"family": "Inter"},
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    # PDF
    if st.button("📄 Download PDF Report", type="primary"):
        pdf = generate_student_pdf_report(student)
        st.download_button("⬇️ Save PDF", pdf, f"report_{student.roll_no}.pdf", "application/pdf")

# ── Tab 2: Edit Scores ────────────────────────────────────────────────────────
with tab_edit:
    st.markdown('<div class="section-header">Edit Student Scores & Profile</div>', unsafe_allow_html=True)
    with st.form("edit_student_form"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            ed_name = st.text_input("Full Name", value=student.full_name)
            ed_dept = st.selectbox("Department", config.DEPARTMENTS,
                                   index=config.DEPARTMENTS.index(student.department)
                                   if student.department in config.DEPARTMENTS else 0)
            ed_year = st.selectbox("Graduation Year", config.ACADEMIC_YEARS,
                                   index=config.ACADEMIC_YEARS.index(student.graduation_year)
                                   if student.graduation_year in config.ACADEMIC_YEARS else 0)
            ed_cgpa = st.number_input("CGPA", 0.0, 10.0, float(student.cgpa), 0.01)
        with ec2:
            ed_tech = st.slider("Technical Score", 0, 100, int(student.technical_score))
            ed_apt  = st.slider("Aptitude Score",  0, 100, int(student.aptitude_score))
            ed_comm = st.slider("Communication",   0, 100, int(student.communication_score))
            ed_proj = st.slider("Project Score",   0, 100, int(student.project_score))
        with ec3:
            ed_cert = st.slider("Certifications",  0, 100, int(student.certifications_score))
            ed_mock = st.slider("Mock Interviews",  0, 100, int(student.mock_interview_score))
            ed_skills = st.text_area("Key Skills", value=student.key_skills or "")
            ed_certs_list = st.text_area("Certifications List", value=student.certifications_list or "")

        if st.form_submit_button("💾 Save Changes", type="primary"):
            try:
                update_student(student_id, {
                    "full_name": ed_name, "department": ed_dept,
                    "graduation_year": ed_year, "cgpa": ed_cgpa,
                    "technical_score": float(ed_tech), "aptitude_score": float(ed_apt),
                    "communication_score": float(ed_comm), "project_score": float(ed_proj),
                    "certifications_score": float(ed_cert), "mock_interview_score": float(ed_mock),
                    "key_skills": ed_skills, "certifications_list": ed_certs_list,
                })
                st.success("✅ Student record updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

# ── Tab 3: Recommendations ───────────────────────────────────────────────────
with tab_rec:
    st.markdown('<div class="section-header">🎯 Personalised Improvement Roadmap</div>', unsafe_allow_html=True)
    rec_data = generate_recommendations(student)

    if rec_data["strengths"]:
        st.markdown("**💪 Identified Strengths**")
        for s_item in rec_data["strengths"]:
            st.markdown(f'<div class="alert alert-success">✅ {s_item}</div>', unsafe_allow_html=True)

    if rec_data["growth_areas"]:
        st.markdown("**🎯 Priority Growth Areas**")
        for g_item in rec_data["growth_areas"]:
            st.markdown(f'<div class="alert alert-warning">⚡ {g_item}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    for rec in rec_data["recommendations"][:5]:
        tier_class = rec.get("tier", "medium")
        priority = rec.get("priority", "Medium")
        p_color = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}.get(priority, "#64748B")
        actions_html = "".join(f"<li>{a}</li>" for a in rec.get("actions", []))
        st.markdown(f"""
        <div class="rec-card {tier_class}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div class="rec-title">{rec['label']} — {rec['title']}</div>
            <span style="font-size:.75rem;font-weight:700;color:{p_color};">{priority} Priority</span>
          </div>
          <ul class="rec-actions">{actions_html}</ul>
          <div style="font-size:.78rem;color:#64748B;margin-top:6px;">
            📚 {rec.get('resources','')} &nbsp;·&nbsp; ⏱️ {rec.get('timeline','')}
          </div>
        </div>
        """, unsafe_allow_html=True)
