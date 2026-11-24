"""
Page 7 — Analytics: cohort comparison, trends over time, year-wise breakdown.
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
import numpy as np

from pages.page_utils import inject_css, require_auth, render_sidebar
from services.student_service import get_all_students
import config

st.set_page_config(page_title="Analytics | TalentForge", page_icon="📈", layout="wide")
inject_css()
require_auth(role="admin")
render_sidebar("admin")

st.markdown('<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">📈 Cohort Analytics</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-bottom:20px;">Deep-dive into placement readiness trends across departments and batches.</p>', unsafe_allow_html=True)

students = get_all_students()
if not students:
    st.warning("No data available.")
    st.stop()

df = pd.DataFrame([{
    "dept": s.department,
    "year": s.graduation_year,
    "overall": s.overall_score,
    "level": s.readiness_level,
    "technical": s.technical_score,
    "aptitude": s.aptitude_score,
    "communication": s.communication_score,
    "projects": s.project_score,
    "certs": s.certifications_score,
    "mock": s.mock_interview_score,
    "cgpa": s.cgpa,
} for s in students])

# ── Year × Readiness Level grouped bar ───────────────────────────────────────
st.markdown('<div class="section-header">📅 Readiness Levels by Graduation Year</div>', unsafe_allow_html=True)
year_level = df.groupby(["year", "level"]).size().reset_index(name="count")
fig_yl = px.bar(
    year_level, x="year", y="count", color="level",
    barmode="group",
    color_discrete_map={
        "Ready": "#10B981", "Almost Ready": "#F59E0B", "Needs Improvement": "#EF4444"
    },
    labels={"year": "Graduation Year", "count": "Number of Students"},
)
fig_yl.update_layout(
    height=320, paper_bgcolor="white", plot_bgcolor="white",
    font={"family": "Inter"}, legend=dict(orientation="h", yanchor="bottom", y=-0.3),
)
st.plotly_chart(fig_yl, use_container_width=True)

# ── Box plots per department ──────────────────────────────────────────────────
st.markdown('<div class="section-header">🏫 Score Distribution by Department (Box Plot)</div>', unsafe_allow_html=True)
df["dept_short"] = df["dept"].apply(lambda x: x.split("&")[0].strip()[:20])
fig_box = px.box(
    df, x="dept_short", y="overall", color="dept_short",
    color_discrete_sequence=px.colors.qualitative.Set2,
    labels={"dept_short": "Department", "overall": "Overall Score"},
    points="outliers",
)
fig_box.add_hline(y=75, line_dash="dash", line_color="#10B981", annotation_text="Ready Threshold")
fig_box.add_hline(y=55, line_dash="dash", line_color="#F59E0B", annotation_text="Almost Ready Threshold")
fig_box.update_layout(
    height=360, paper_bgcolor="white", plot_bgcolor="white",
    font={"family": "Inter"}, showlegend=False,
)
st.plotly_chart(fig_box, use_container_width=True)

# ── Scatter: CGPA vs. Overall Score ──────────────────────────────────────────
col_sc, col_violin = st.columns(2, gap="large")

with col_sc:
    st.markdown('<div class="section-header">📉 CGPA vs. Overall Score</div>', unsafe_allow_html=True)
    df["dept_short2"] = df["dept"].apply(lambda x: x.split("&")[0].strip()[:15])
    fig_sc = px.scatter(
        df, x="cgpa", y="overall", color="dept_short2",
        trendline="ols",
        labels={"cgpa": "CGPA (10-point scale)", "overall": "Readiness Score"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_sc.update_layout(
        height=320, paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Inter"}, legend=dict(title=""),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

with col_violin:
    st.markdown('<div class="section-header">🎻 Score Violin by Level</div>', unsafe_allow_html=True)
    colors_v = {"Ready": "#10B981", "Almost Ready": "#F59E0B", "Needs Improvement": "#EF4444"}
    fig_v = go.Figure()
    for level in ["Ready", "Almost Ready", "Needs Improvement"]:
        sub = df[df["level"] == level]["overall"]
        if not sub.empty:
            fig_v.add_trace(go.Violin(
                y=sub, name=level,
                fillcolor=colors_v[level], opacity=0.7,
                line_color=colors_v[level], box_visible=True,
                meanline_visible=True,
            ))
    fig_v.update_layout(
        height=320, paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Inter"}, yaxis_title="Overall Score",
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ── Dept × Year heatmap ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🌡️ Avg. Score: Department × Graduation Year</div>', unsafe_allow_html=True)
pivot = df.pivot_table(values="overall", index="dept", columns="year", aggfunc="mean").round(1)
pivot.index = [i.split("&")[0].strip()[:20] for i in pivot.index]
fig_heat2 = px.imshow(
    pivot,
    color_continuous_scale=[[0, "#FEE2E2"], [0.5, "#FEF3C7"], [1, "#D1FAE5"]],
    text_auto=".1f", aspect="auto",
    labels={"x": "Year", "y": "Department"},
)
fig_heat2.update_layout(
    height=280, paper_bgcolor="white", font={"family": "Inter"},
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig_heat2, use_container_width=True)

# ── Summary statistics table ───────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Summary Statistics by Department</div>', unsafe_allow_html=True)
summary = df.groupby("dept").agg(
    Count=("overall", "count"),
    Mean=("overall", "mean"),
    Median=("overall", "median"),
    Std=("overall", "std"),
    Min=("overall", "min"),
    Max=("overall", "max"),
    Ready=("level", lambda x: (x == "Ready").sum()),
).round(1).reset_index()
summary["% Ready"] = (summary["Ready"] / summary["Count"] * 100).round(1)
summary["dept"] = summary["dept"].apply(lambda x: x.split("&")[0].strip()[:25])
summary = summary.rename(columns={"dept": "Department"})
st.dataframe(summary, use_container_width=True, hide_index=True)
