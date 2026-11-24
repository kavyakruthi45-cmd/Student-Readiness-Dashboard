"""
Page 6 — Bulk CSV Upload with validation and downloadable template.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from pages.page_utils import inject_css, require_auth, render_sidebar
from services.student_service import bulk_upsert_students
from utils.csv_utils import get_csv_template_bytes, parse_uploaded_csv

st.set_page_config(page_title="Bulk Upload | TalentForge", page_icon="📂", layout="wide")
inject_css()
require_auth(role="admin")
render_sidebar("admin")

st.markdown('<h2 style="font-weight:800;color:#0F172A;margin-bottom:4px;">📂 Bulk CSV Upload</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#64748B;margin-bottom:20px;">Import multiple students at once. Existing roll numbers will be updated.</p>', unsafe_allow_html=True)

# Download template
st.download_button(
    "⬇️ Download CSV Template",
    data=get_csv_template_bytes(),
    file_name="student_upload_template.csv",
    mime="text/csv",
)

st.markdown("""
<div class="alert alert-info">
  <div>
    <b>Required columns:</b> roll_no, full_name, email, department, graduation_year, cgpa,
    technical_score, aptitude_score, communication_score, project_score,
    certifications_score, mock_interview_score<br/>
    <b>Optional:</b> key_skills, project_summary, certifications_list<br/>
    Scores must be 0–100. CGPA must be 0–10. Max file size: 10 MB.
  </div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload CSV file", type=["csv"], label_visibility="collapsed")

if uploaded:
    with st.spinner("Validating file..."):
        file_bytes = uploaded.read()
        valid_rows, errors = parse_uploaded_csv(file_bytes)

    if errors:
        st.markdown('<div class="section-header">⚠️ Validation Errors</div>', unsafe_allow_html=True)
        for err in errors[:20]:
            st.markdown(f'<div class="alert alert-danger">{err}</div>', unsafe_allow_html=True)
        if len(errors) > 20:
            st.warning(f"...and {len(errors)-20} more errors. Please fix the CSV and re-upload.")

    if valid_rows:
        st.success(f"✅ {len(valid_rows)} valid row(s) parsed. {len(errors)} error(s).")

        # Preview
        with st.expander("👁️ Preview valid rows", expanded=len(valid_rows) <= 10):
            import pandas as pd
            prev_df = pd.DataFrame(valid_rows)[
                ["roll_no", "full_name", "department", "graduation_year", "cgpa",
                 "technical_score", "aptitude_score", "overall_score"]
                if "overall_score" in pd.DataFrame(valid_rows).columns
                else ["roll_no", "full_name", "department", "graduation_year", "cgpa",
                      "technical_score", "aptitude_score"]
            ]
            st.dataframe(prev_df, use_container_width=True)

        if st.button("🚀 Import Students", type="primary"):
            with st.spinner(f"Importing {len(valid_rows)} students..."):
                result = bulk_upsert_students(valid_rows)
            st.success(
                f"✅ Import complete! "
                f"Created: **{result['created']}** | "
                f"Updated: **{result['updated']}** | "
                f"Skipped: **{result['skipped']}**"
            )
            st.balloons()
