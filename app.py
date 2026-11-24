"""
app.py — TalentForge Student Readiness Dashboard
Landing / Login page. Auto-seeds the database on first run.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path (needed when launched via streamlit run)
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

# ── Bootstrap DB + seed on first run ──────────────────────────────────────
from database.connection import init_db
from services.student_service import count_students

def _bootstrap():
    init_db()
    if count_students() == 0:
        from seed_data import seed_database
        seed_database()

_bootstrap()

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentForge | Student Readiness",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject CSS ─────────────────────────────────────────────────────────────
CSS_PATH = ROOT / "assets" / "style.css"
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

# ── Auth helpers ───────────────────────────────────────────────────────────
from services.auth_service import authenticate_user


def _do_login(username: str, password: str) -> bool:
    user = authenticate_user(username, password)
    if user:
        st.session_state["authenticated"] = True
        st.session_state["user_id"]       = user.id
        st.session_state["username"]      = user.username
        st.session_state["role"]          = user.role
        st.session_state["student_id"]    = user.student_id
        return True
    return False


def _logout():
    for key in ["authenticated", "user_id", "username", "role", "student_id"]:
        st.session_state.pop(key, None)


# ── If already authenticated, redirect to appropriate dashboard ────────────
if st.session_state.get("authenticated"):
    role = st.session_state.get("role", "student")
    if role == "admin":
        st.switch_page("pages/2_Admin_Overview.py")
    else:
        st.switch_page("pages/1_Student_Dashboard.py")

# ── LANDING / LOGIN PAGE ──────────────────────────────────────────────────
# Hero section
col_hero, col_form = st.columns([1.1, 0.9], gap="large")

with col_hero:
    st.markdown("""
    <div style="padding: 48px 32px 32px;">
        <div style="display:inline-block;background:#EFF6FF;border-radius:12px;
                    padding:10px 20px;margin-bottom:20px;">
            <span style="color:#2563EB;font-weight:700;font-size:.85rem;
                         letter-spacing:.08em;">🎓 PLACEMENT READINESS PLATFORM</span>
        </div>
        <h1 style="font-size:2.8rem;font-weight:800;color:#0F172A;
                   line-height:1.15;margin-bottom:16px;">
            TalentForge<br/>
            <span style="color:#2563EB;">Career Readiness</span><br/>
            Dashboard
        </h1>
        <p style="font-size:1.05rem;color:#64748B;line-height:1.65;
                  max-width:460px;margin-bottom:28px;">
            Measure, track and accelerate student placement readiness using
            multi-dimensional competency analytics, skill-gap diagnostics and
            personalised AI-guided roadmaps.
        </p>
    """, unsafe_allow_html=True)

    # Feature pills
    features = [
        ("📊", "7-Component Readiness Score"),
        ("🎯", "Skill-Gap Analysis & Roadmaps"),
        ("📈", "Progress Trend Tracking"),
        ("🔍", "Faculty Analytics & At-Risk Detection"),
        ("📄", "Personalised PDF Reports"),
        ("📂", "Bulk CSV Import / Export"),
    ]
    for icon, text in features:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;'
            f'margin-bottom:10px;">'
            f'<span style="font-size:1.1rem;">{icon}</span>'
            f'<span style="font-size:.88rem;font-weight:500;color:#334155;">{text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with col_form:
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("""
        <div class="login-wrapper">
            <div class="login-logo" style="font-size:2.8rem;">🎓</div>
            <div class="login-title">Welcome Back</div>
            <div class="login-sub">Sign in to access your readiness dashboard</div>
        </div>
        """, unsafe_allow_html=True)

        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username or Email", placeholder="admin or student1")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            elif _do_login(username.strip(), password):
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

        st.markdown("---")
        st.markdown("""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                    padding:14px 18px;margin-top:4px;">
            <div style="font-size:.78rem;font-weight:700;color:#64748B;
                        text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">
                Demo Credentials
            </div>
            <div style="font-size:.85rem;color:#334155;margin-bottom:4px;">
                <b>Admin:</b>&nbsp; admin &nbsp;/&nbsp; admin123
            </div>
            <div style="font-size:.85rem;color:#334155;">
                <b>Student:</b>&nbsp; student1 &nbsp;/&nbsp; student123
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#94A3B8;font-size:.78rem;padding:12px 0;">
    TalentForge v2.4.0 &nbsp;·&nbsp; Student Placement Readiness System<br/>
    Built with Streamlit · Plotly · SQLAlchemy · ReportLab
</div>
""", unsafe_allow_html=True)
