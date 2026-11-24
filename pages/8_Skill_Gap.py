"""
Page 8 — Student Skill-Gap Analysis with actionable recommendations.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go

from pages.page_utils import inject_css, require_auth, render_sidebar
from services.student_service import get_student_by_id
from services.recommendation_service import analyze_skill_gaps, generate_recommendations
import config

st.set_page_config(page_title="Skill Gap Analysis | TalentForge", page_icon="🎯", layout="wide")
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

st.markdown(f'<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">🎯 Skill-Gap Analysis</h2>', unsafe_allow_html=True)
st.markdown(f'<p style="color:#64748B;margin-bottom:20px;">Detailed competency assessment for {student.full_name} against placement benchmarks.</p>', unsafe_allow_html=True)

gaps = analyze_skill_gaps(student)
rec_data = generate_recommendations(student)

# ── Gap Summary Gauge-style row ───────────────────────────────────────────────
st.markdown('<div class="section-header">Component Gap Overview</div>', unsafe_allow_html=True)

cols = st.columns(len(gaps))
for idx, gap_item in enumerate(gaps):
    actual = gap_item["actual_score"]
    benchmark = gap_item["benchmark_score"]
    pct_filled = min(actual / benchmark * 100, 100) if benchmark else 0
    color = gap_item["badge_color"]
    with cols[idx]:
        st.markdown(f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;
                    padding:14px 10px;text-align:center;">
          <div style="font-size:.68rem;color:#64748B;font-weight:600;text-transform:uppercase;
                      letter-spacing:.05em;margin-bottom:8px;line-height:1.3;">
            {gap_item['label']}
          </div>
          <div style="font-size:1.5rem;font-weight:800;color:{color};">{actual:.0f}</div>
          <div style="background:#F1F5F9;border-radius:999px;height:6px;margin:6px 0;">
            <div style="width:{pct_filled:.0f}%;background:{color};height:6px;
                        border-radius:999px;"></div>
          </div>
          <div style="font-size:.7rem;color:#94A3B8;">Target: {benchmark:.0f}</div>
          <div style="font-size:.7rem;font-weight:700;color:{color};">{gap_item['status']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Waterfall gap chart ───────────────────────────────────────────────────────
col_chart, col_items = st.columns([1.2, 1], gap="large")

with col_chart:
    st.markdown('<div class="section-header">Gap Waterfall Chart</div>', unsafe_allow_html=True)
    labels = [g["label"] for g in gaps]
    actual_scores = [g["actual_score"] for g in gaps]
    gap_sizes = [max(g["gap"], 0) for g in gaps]
    colors = [g["badge_color"] for g in gaps]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current Score", x=labels, y=actual_scores,
        marker_color=colors, text=[f"{v:.0f}" for v in actual_scores],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Gap to Target", x=labels, y=gap_sizes,
        marker_color=["#E2E8F0"] * len(gaps),
        hovertemplate="%{x}<br>Gap: %{y:.0f}<extra></extra>",
    ))
    fig.add_hline(y=75, line_dash="dash", line_color="#10B981", annotation_text="Target (75)")
    fig.update_layout(
        barmode="stack", height=360, margin=dict(t=10, b=10, l=0, r=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font={"family": "Inter"}, yaxis=dict(range=[0, 110]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_items:
    st.markdown('<div class="section-header">Priority Gap Summary</div>', unsafe_allow_html=True)
    for g in gaps:
        p_color = g["badge_color"]
        gap_disp = f"-{g['gap']:.0f}" if g["gap"] > 0 else f"+{abs(g['gap']):.0f}"
        icon = "🔴" if g["priority"] == "High" else "🟡" if g["priority"] == "Medium" else "🟢"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:9px 14px;
                    background:white;border:1px solid #E2E8F0;border-left:3px solid {p_color};
                    border-radius:0 8px 8px 0;margin-bottom:7px;">
          <span style="font-size:1rem;">{icon}</span>
          <div style="flex:1;">
            <div style="font-weight:600;font-size:.85rem;color:#0F172A;">{g['label']}</div>
            <div style="font-size:.73rem;color:#64748B;">{g['status']} · Weight: {g['weight_pct']}%</div>
          </div>
          <div style="font-weight:800;font-size:1rem;color:{p_color};">{gap_disp}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Recommendations ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🎯 Personalised Action Plan</div>', unsafe_allow_html=True)
st.markdown('<div class="section-sub">Rule-based roadmap tailored to your current score profile.</div>', unsafe_allow_html=True)

recs = rec_data["recommendations"]
for rec in recs:
    tier = rec.get("tier", "medium")
    priority = rec.get("priority", "Medium")
    p_color = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#10B981"}.get(priority, "#64748B")
    actions_html = "".join(f"<li style='margin-bottom:5px;'>{a}</li>" for a in rec.get("actions", []))

    with st.expander(f"{rec['label']} — {rec['title']} ({priority} Priority)", expanded=(priority == "High")):
        st.markdown(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;">
          <div style="flex:1;">
            <div style="font-weight:700;color:#0F172A;margin-bottom:8px;">{rec['title']}</div>
            <ul style="color:#334155;font-size:.88rem;padding-left:20px;margin:0 0 10px;">
              {actions_html}
            </ul>
            <div style="font-size:.8rem;color:#64748B;">
              📚 <b>Resources:</b> {rec.get('resources', 'N/A')}<br/>
              ⏱️ <b>Timeline:</b> {rec.get('timeline', 'N/A')}
            </div>
          </div>
          <div style="text-align:center;min-width:70px;">
            <div style="font-size:1.6rem;font-weight:800;color:{p_color};">{rec['score']:.0f}</div>
            <div style="font-size:.7rem;color:#64748B;">/100</div>
            <div style="font-size:.72rem;font-weight:700;color:{p_color};">{priority}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── 30-60-90 Day Roadmap ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">🗓️ 75-Day Action Roadmap</div>', unsafe_allow_html=True)
roadmap = rec_data["roadmap"]
road_cols = st.columns(3)
roadmap_keys = ["immediate_focus", "mid_term_focus", "polishing_focus"]
road_colors = ["#EF4444", "#F59E0B", "#10B981"]
road_icons = ["🔥", "⚡", "🏁"]

for i, (key, col) in enumerate(zip(roadmap_keys, road_cols)):
    phase = roadmap.get(key, {})
    items = phase.get("items", [])
    with col:
        st.markdown(f"""
        <div style="background:white;border:1px solid #E2E8F0;border-radius:12px;
                    border-top:3px solid {road_colors[i]};padding:16px;">
          <div style="font-size:.85rem;font-weight:700;color:{road_colors[i]};margin-bottom:8px;">
            {road_icons[i]} {phase.get('period', '')}
          </div>
        """, unsafe_allow_html=True)
        if items:
            for item in items[:2]:
                st.markdown(f"""
                <div style="font-size:.82rem;color:#334155;margin-bottom:6px;
                            padding:6px 10px;background:#F8FAFC;border-radius:6px;">
                  <b>{item['label']}</b><br/>
                  <span style="color:#64748B;">{item['title']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#94A3B8;font-size:.8rem;">No critical items — maintain current progress.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
