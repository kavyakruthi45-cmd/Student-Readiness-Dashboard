"""
Shared page helpers: sidebar navigation, auth guard, CSS injection.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

def inject_css() -> None:
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def require_auth(role: str | None = None) -> dict:
    """
    Redirect to login if unauthenticated. Optionally enforce a specific role.
    Returns session dict on success.
    """
    if not st.session_state.get("authenticated"):
        st.switch_page("app.py")
    if role and st.session_state.get("role") != role:
        st.error("⛔ You do not have permission to view this page.")
        st.stop()
    return dict(st.session_state)


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

def render_sidebar(active_role: str) -> None:
    username = st.session_state.get("username", "User")
    role = st.session_state.get("role", "student")

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:16px 0 10px;">
            <span style="font-size:2.2rem;">🎓</span>
            <div style="font-size:1rem;font-weight:800;color:#2563EB;margin-top:4px;">
                TalentForge
            </div>
            <div style="font-size:.72rem;color:#64748B;letter-spacing:.06em;">
                READINESS PLATFORM
            </div>
        </div>
        <hr style="border-color:#E2E8F0;margin:0 0 12px;">
        """, unsafe_allow_html=True)

        # User chip
        role_badge_color = "#2563EB" if role == "admin" else "#10B981"
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;'
            f'padding:10px 14px;margin-bottom:16px;">'
            f'<div style="font-size:.8rem;font-weight:700;color:#334155;">{username}</div>'
            f'<div style="font-size:.7rem;color:{role_badge_color};font-weight:600;'
            f'text-transform:uppercase;letter-spacing:.06em;">'
            f'{"Admin / Faculty" if role == "admin" else "Student"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if role == "admin":
            st.markdown("**📋 Faculty Portal**", unsafe_allow_html=False)
            st.page_link("pages/2_Admin_Overview.py",    label="📊 Overview & KPIs")
            st.page_link("pages/3_Student_Table.py",     label="🗂️ Student Database")
            st.page_link("pages/7_Analytics.py",         label="📈 Analytics")
            st.page_link("pages/6_Bulk_Upload.py",       label="📂 Bulk CSV Upload")
            st.markdown("---")
            st.markdown("**🔧 Admin Tools**")
            st.page_link("pages/5_Student_Detail.py",    label="🔍 Student Detail")
        else:
            st.markdown("**🏠 My Dashboard**")
            st.page_link("pages/1_Student_Dashboard.py", label="🏠 My Readiness")
            st.page_link("pages/8_Skill_Gap.py",         label="🎯 Skill Gap Analysis")
            st.page_link("pages/9_Update_Profile.py",    label="✏️ Update My Profile")

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in ["authenticated", "user_id", "username", "role", "student_id"]:
                st.session_state.pop(key, None)
            st.switch_page("app.py")

        st.markdown(
            '<div style="text-align:center;color:#94A3B8;font-size:.7rem;'
            'padding-top:16px;">v2.4.0</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def readiness_badge(level: str) -> str:
    css = {
        "Ready": "badge-ready",
        "Almost Ready": "badge-almost",
        "Needs Improvement": "badge-needs",
    }
    cls = css.get(level, "badge-almost")
    return f'<span class="badge {cls}">{level}</span>'


def level_color(level: str) -> str:
    return {
        "Ready": "#10B981",
        "Almost Ready": "#F59E0B",
        "Needs Improvement": "#EF4444",
    }.get(level, "#64748B")
