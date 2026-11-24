"""
Page 2 — Admin / Faculty Overview Dashboard
KPIs, distribution charts, department comparison, heatmap, at-risk students.
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

from pages.page_utils import inject_css, require_auth, render_sidebar, readiness_badge, level_color
from services.student_service import get_all_students
from services.scoring_service import get_component_scores_dict
import config

st.set_page_config(page_title="Admin Overview | TalentForge", page_icon="📊", layout="wide")
inject_css()
require_auth(role="admin")
render_sidebar("admin")

st.markdown('<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">📊 Overview Dashboard</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-bottom:24px;">Real-time snapshot of cohort placement readiness.</p>', unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────
students = get_all_students()

if not students:
    st.warning("No student data found. Please run seed_data.py or upload students.")
    st.stop()

df = pd.DataFrame([{
    "id": s.id,
    "name": s.full_name,
    "roll_no": s.roll_no,
    "dept": s.department,
    "year": s.graduation_year,
    "cgpa": s.cgpa,
    "overall": s.overall_score,
    "level": s.readiness_level,
    "technical": s.technical_score,
    "aptitude": s.aptitude_score,
    "communication": s.communication_score,
    "projects": s.project_score,
    "certs": s.certifications_score,
    "mock": s.mock_interview_score,
} for s in students])

total = len(df)
avg_score = df["overall"].mean()
pct_ready = (df["level"] == "Ready").sum() / total * 100
pct_needs  = (df["level"] == "Needs Improvement").sum() / total * 100
pct_almost = (df["level"] == "Almost Ready").sum() / total * 100

# ── KPI Row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("👥 Total Students", f"{total:,}")
with k2: st.metric("📊 Avg. Readiness", f"{avg_score:.1f}/100")
with k3: st.metric("✅ Ready", f"{pct_ready:.1f}%", f"{(df['level']=='Ready').sum()} students")
with k4: st.metric("⚠️ Almost Ready", f"{pct_almost:.1f}%")
with k5: st.metric("🔴 Needs Improvement", f"{pct_needs:.1f}%", f"{(df['level']=='Needs Improvement').sum()} students", delta_color="inverse")

st.markdown("<br>", unsafe_allow_html=True)

# ── Top Performers ────────────────────────────────────────────────────────────
col_top, col_dist = st.columns([1, 1.2], gap="large")

with col_top:
    st.markdown('<div class="section-header">🏆 Top Performers</div>', unsafe_allow_html=True)
    top5 = df.nlargest(5, "overall")[["name", "dept", "overall", "level"]]
    for i, row in enumerate(top5.itertuples(), 1):
        dept_short = row.dept.split("&")[0].strip()[:18]
        badge = readiness_badge(row.level)
        lc = level_color(row.level)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                    background:white;border:1px solid #E2E8F0;border-radius:10px;
                    margin-bottom:8px;">
          <div style="font-size:1.1rem;font-weight:800;color:#2563EB;min-width:24px;">#{i}</div>
          <div style="flex:1;">
            <div style="font-weight:600;font-size:.9rem;color:#0F172A;">{row.name}</div>
            <div style="font-size:.75rem;color:#64748B;">{dept_short}</div>
          </div>
          <div style="font-size:1.3rem;font-weight:800;color:{lc};">{row.overall:.0f}</div>
          {badge}
        </div>
        """, unsafe_allow_html=True)

with col_dist:
    st.markdown('<div class="section-header">📊 Readiness Distribution</div>', unsafe_allow_html=True)
    level_counts = df["level"].value_counts().reset_index()
    level_counts.columns = ["Level", "Count"]
    colors_map = {"Ready": "#10B981", "Almost Ready": "#F59E0B", "Needs Improvement": "#EF4444"}
    fig_pie = go.Figure(go.Pie(
        labels=level_counts["Level"],
        values=level_counts["Count"],
        hole=0.55,
        marker_colors=[colors_map.get(l, "#64748B") for l in level_counts["Level"]],
        textinfo="percent+label",
        hovertemplate="%{label}: %{value} students (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(
        height=300, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="white", font={"family": "Inter"},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        annotations=[dict(text=f"<b>{total}</b><br>students", x=0.5, y=0.5,
                           font_size=14, showarrow=False, font_color="#0F172A")],
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Score Histogram ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Score Distribution (Histogram)</div>', unsafe_allow_html=True)
fig_hist = px.histogram(
    df, x="overall", nbins=20, color_discrete_sequence=["#2563EB"],
    labels={"overall": "Overall Readiness Score"},
)
fig_hist.add_vline(x=75, line_dash="dash", line_color="#10B981", annotation_text="Ready threshold")
fig_hist.add_vline(x=55, line_dash="dash", line_color="#F59E0B", annotation_text="Almost Ready threshold")
fig_hist.update_layout(
    height=240, margin=dict(t=10, b=20, l=0, r=0),
    paper_bgcolor="white", plot_bgcolor="white",
    font={"family": "Inter"},
    bargap=0.08,
)
st.plotly_chart(fig_hist, use_container_width=True)

# ── Department Comparison ─────────────────────────────────────────────────────
col_dept, col_comp_avg = st.columns(2, gap="large")

with col_dept:
    st.markdown('<div class="section-header">🏫 Department-wise Avg. Score</div>', unsafe_allow_html=True)
    dept_df = df.groupby("dept")["overall"].mean().reset_index().sort_values("overall", ascending=True)
    dept_df.columns = ["Department", "Avg Score"]
    dept_df["Short"] = dept_df["Department"].apply(lambda x: x.split(" &")[0][:20])
    colors_dept = ["#EF4444" if s < 55 else "#F59E0B" if s < 75 else "#10B981"
                   for s in dept_df["Avg Score"]]
    fig_dept = go.Figure(go.Bar(
        x=dept_df["Avg Score"], y=dept_df["Short"],
        orientation="h",
        marker_color=colors_dept,
        text=[f"{v:.1f}" for v in dept_df["Avg Score"]],
        textposition="outside",
    ))
    fig_dept.update_layout(
        height=270, margin=dict(t=10, b=10, l=10, r=40),
        xaxis=dict(range=[0, 100]), paper_bgcolor="white",
        plot_bgcolor="white", font={"family": "Inter"},
    )
    st.plotly_chart(fig_dept, use_container_width=True)

with col_comp_avg:
    st.markdown('<div class="section-header">📋 Component-wise Averages</div>', unsafe_allow_html=True)
    comp_avgs = {
        "Technical": df["technical"].mean(),
        "Aptitude": df["aptitude"].mean(),
        "Communication": df["communication"].mean(),
        "Projects": df["projects"].mean(),
        "Certifications": df["certs"].mean(),
        "Mock Interviews": df["mock"].mean(),
    }
    comp_df = pd.DataFrame(list(comp_avgs.items()), columns=["Component", "Avg Score"])
    comp_df = comp_df.sort_values("Avg Score", ascending=True)
    bar_colors = ["#EF4444" if v < 55 else "#F59E0B" if v < 75 else "#10B981"
                  for v in comp_df["Avg Score"]]
    fig_comp = go.Figure(go.Bar(
        x=comp_df["Avg Score"], y=comp_df["Component"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.1f}" for v in comp_df["Avg Score"]],
        textposition="outside",
    ))
    fig_comp.update_layout(
        height=270, margin=dict(t=10, b=10, l=10, r=40),
        xaxis=dict(range=[0, 100]), paper_bgcolor="white",
        plot_bgcolor="white", font={"family": "Inter"},
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ── Skills Heatmap ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🌡️ Skill Heatmap: Department × Component</div>', unsafe_allow_html=True)
heatmap_data = df.groupby("dept").agg({
    "technical": "mean", "aptitude": "mean", "communication": "mean",
    "projects": "mean", "certs": "mean", "mock": "mean",
}).round(1)
heatmap_data.index = [i.split("&")[0].strip()[:20] for i in heatmap_data.index]
heatmap_data.columns = ["Technical", "Aptitude", "Communication", "Projects", "Certifications", "Mock Interviews"]

fig_heat = px.imshow(
    heatmap_data,
    color_continuous_scale=[[0, "#FEE2E2"], [0.5, "#FEF3C7"], [1, "#D1FAE5"]],
    aspect="auto",
    text_auto=".1f",
)
fig_heat.update_layout(
    height=280, margin=dict(t=10, b=10, l=10, r=10),
    paper_bgcolor="white", font={"family": "Inter"},
    coloraxis_colorbar=dict(title="Score"),
)
st.plotly_chart(fig_heat, use_container_width=True)

# ── At-Risk Students ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🚨 At-Risk Students (Score < 55)</div>', unsafe_allow_html=True)
at_risk = df[df["overall"] < 55].sort_values("overall").head(10)
if at_risk.empty:
    st.markdown('<div class="alert alert-success">✅ No students in the critical zone! Great cohort performance.</div>', unsafe_allow_html=True)
else:
    for _, row in at_risk.iterrows():
        gap_to_ready = round(75 - row["overall"], 1)
        badge = readiness_badge(row["level"])
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;padding:10px 16px;
                    background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;
                    border-left:4px solid #EF4444;margin-bottom:8px;">
          <div style="flex:1;">
            <div style="font-weight:600;font-size:.9rem;color:#0F172A;">{row['name']}</div>
            <div style="font-size:.75rem;color:#64748B;">{row['roll_no']} · {row['dept'].split('&')[0].strip()}</div>
          </div>
          <div style="font-size:1.2rem;font-weight:800;color:#EF4444;">{row['overall']:.1f}</div>
          <div style="font-size:.8rem;color:#EF4444;">▲ {gap_to_ready} to Ready</div>
          {badge}
        </div>
        """, unsafe_allow_html=True)
