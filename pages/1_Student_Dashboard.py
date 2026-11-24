"""
Page 1 — Student Personal Dashboard
Shows: readiness gauge, level badge, radar chart, trend, rank/percentile.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from pages.page_utils import inject_css, require_auth, render_sidebar, readiness_badge, level_color
from services.student_service import get_student_by_id, get_student_history, get_all_scores
from services.scoring_service import (
    get_component_scores_dict,
    calculate_cohort_rank_and_percentile,
    cgpa_to_score,
)
from services.report_service import generate_student_pdf_report
import config

st.set_page_config(page_title="My Dashboard | TalentForge", page_icon="🏠", layout="wide")
inject_css()
sess = require_auth()
render_sidebar("student")

student_id = sess.get("student_id")
if not student_id:
    st.error("Your account is not linked to a student profile. Contact admin.")
    st.stop()

student = get_student_by_id(student_id)
if not student:
    st.error("Student profile not found.")
    st.stop()

# ── Rank & Percentile ───────────────────────────────────────────────────────
all_scores = get_all_scores()
rank, percentile = calculate_cohort_rank_and_percentile(student.overall_score, all_scores)
total_students = len(all_scores)

# ── Hero bar ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="score-hero">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
    <div>
      <div style="font-size:.8rem;font-weight:600;text-transform:uppercase;
                  letter-spacing:.08em;opacity:.75;margin-bottom:4px;">Welcome back</div>
      <h1 style="font-size:2rem;font-weight:800;margin:0 0 6px;">{student.full_name}</h1>
      <div style="font-size:.88rem;opacity:.8;">{student.department} &nbsp;·&nbsp;
           Class of {student.graduation_year} &nbsp;·&nbsp; Roll No: {student.roll_no}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:3.2rem;font-weight:900;line-height:1;">{student.overall_score:.1f}</div>
      <div style="font-size:.8rem;opacity:.75;">Overall Readiness Score / 100</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("🏆 Readiness Score", f"{student.overall_score:.1f} / 100")
with k2:
    badge_html = readiness_badge(student.readiness_level)
    st.markdown(f"**Readiness Level**<br>{badge_html}", unsafe_allow_html=True)
with k3:
    st.metric("📊 Cohort Rank", f"#{rank} of {total_students}")
with k4:
    st.metric("📈 Percentile", f"{percentile:.1f}th")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ──────────────────────────────────────────────────────────────
col_gauge, col_radar = st.columns([1, 1.2], gap="large")

with col_gauge:
    st.markdown('<div class="section-header">Readiness Gauge</div>', unsafe_allow_html=True)
    score = student.overall_score
    lc = level_color(student.readiness_level)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": "#0F172A"}},
        delta={"reference": 75, "increasing": {"color": "#10B981"}, "decreasing": {"color": "#EF4444"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": lc, "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 55],  "color": "#FEE2E2"},
                {"range": [55, 75], "color": "#FEF3C7"},
                {"range": [75, 100],"color": "#D1FAE5"},
            ],
            "threshold": {
                "line": {"color": "#1E3A8A", "width": 3},
                "thickness": 0.75,
                "value": 75,
            },
        },
        title={"text": f"<b>{student.readiness_level}</b>",
               "font": {"size": 16, "color": lc}},
    ))
    fig_gauge.update_layout(
        height=300, margin=dict(t=30, b=10, l=20, r=20),
        paper_bgcolor="white", font={"family": "Inter"},
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_radar:
    st.markdown('<div class="section-header">Competency Radar</div>', unsafe_allow_html=True)
    comp_scores = get_component_scores_dict(student)
    labels = [config.COMPONENT_LABELS[k] for k in comp_scores]
    values = list(comp_scores.values())

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(37,99,235,0.15)",
        line=dict(color="#2563EB", width=2),
        name="Your Scores",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[75] * (len(labels) + 1),
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(16,185,129,0.06)",
        line=dict(color="#10B981", width=1.5, dash="dash"),
        name="Target (75)",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=10)),
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=320,
        margin=dict(t=20, b=50, l=40, r=40),
        paper_bgcolor="white",
        font={"family": "Inter"},
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Component Breakdown ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">Component Score Breakdown</div>', unsafe_allow_html=True)
comp_scores = get_component_scores_dict(student)

cols = st.columns(len(comp_scores))
for idx, (key, score_val) in enumerate(comp_scores.items()):
    weight_pct = int(config.COMPONENT_WEIGHTS[key] * 100)
    label = config.COMPONENT_LABELS[key]
    color = "#10B981" if score_val >= 75 else "#F59E0B" if score_val >= 55 else "#EF4444"
    with cols[idx]:
        st.markdown(f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;
                    padding:14px 12px;text-align:center;">
          <div style="font-size:.7rem;color:#64748B;font-weight:600;
                      text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">
            {label}
          </div>
          <div style="font-size:1.6rem;font-weight:800;color:{color};">{score_val:.0f}</div>
          <div style="font-size:.7rem;color:#94A3B8;">Weight: {weight_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

# ── Progress Trend ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Progress Trend Over Time</div>', unsafe_allow_html=True)
history = get_student_history(student_id)

if len(history) >= 2:
    hist_df = pd.DataFrame([{
        "Month": h.month_label,
        "Overall": h.overall_score,
        "Technical": h.technical_score,
        "Aptitude": h.aptitude_score,
        "Communication": h.communication_score,
        "Projects": h.project_score,
        "Date": h.recorded_at,
    } for h in history]).sort_values("Date")

    tab1, tab2 = st.tabs(["📈 Overall Trend", "🔍 Component Trends"])

    with tab1:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=hist_df["Month"], y=hist_df["Overall"],
            mode="lines+markers",
            line=dict(color="#2563EB", width=3),
            marker=dict(size=8, color="#2563EB"),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
            name="Overall Score",
        ))
        fig_trend.add_hline(y=75, line_dash="dash", line_color="#10B981",
                             annotation_text="Ready Threshold (75)",
                             annotation_position="right")
        fig_trend.update_layout(
            height=280, margin=dict(t=20, b=20, l=0, r=20),
            xaxis_title="", yaxis_title="Score",
            yaxis=dict(range=[0, 105]),
            paper_bgcolor="white", plot_bgcolor="white",
            font={"family": "Inter"},
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with tab2:
        fig_comp = go.Figure()
        colors_map = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"]
        for i, col_name in enumerate(["Technical", "Aptitude", "Communication", "Projects"]):
            fig_comp.add_trace(go.Scatter(
                x=hist_df["Month"], y=hist_df[col_name],
                mode="lines+markers",
                name=col_name,
                line=dict(color=colors_map[i % len(colors_map)], width=2),
                marker=dict(size=6),
            ))
        fig_comp.update_layout(
            height=280, margin=dict(t=20, b=20, l=0, r=20),
            xaxis_title="", yaxis_title="Score",
            yaxis=dict(range=[0, 105]),
            paper_bgcolor="white", plot_bgcolor="white",
            font={"family": "Inter"},
            legend=dict(orientation="h", yanchor="bottom", y=-0.35),
        )
        st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.info("📊 Trend data will appear after multiple score updates.")

# ── PDF Download ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">📄 Download Readiness Report</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating personalised PDF report..."):
            pdf_bytes = generate_student_pdf_report(student, rank, percentile)
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=f"readiness_report_{student.roll_no}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
