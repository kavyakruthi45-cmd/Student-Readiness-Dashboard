"""
CSV / Excel import-export utilities for the Student Readiness Dashboard.
"""
from __future__ import annotations

import io
import logging
from typing import List, Dict, Any, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Columns expected in bulk-upload CSV
CSV_REQUIRED_COLS = [
    "roll_no", "full_name", "email", "department",
    "graduation_year", "cgpa",
    "technical_score", "aptitude_score", "communication_score",
    "project_score", "certifications_score", "mock_interview_score",
]
CSV_OPTIONAL_COLS = ["key_skills", "project_summary", "certifications_list"]
CSV_ALL_COLS = CSV_REQUIRED_COLS + CSV_OPTIONAL_COLS


def get_csv_template_bytes() -> bytes:
    """Return a downloadable CSV template with headers and one example row."""
    example = {
        "roll_no": "CSE2025001",
        "full_name": "Example Student",
        "email": "example@university.edu",
        "department": "Computer Science & Engineering",
        "graduation_year": 2025,
        "cgpa": 8.5,
        "technical_score": 72.0,
        "aptitude_score": 65.0,
        "communication_score": 70.0,
        "project_score": 68.0,
        "certifications_score": 55.0,
        "mock_interview_score": 60.0,
        "key_skills": "Python, SQL, React",
        "project_summary": "Built a full-stack inventory management system",
        "certifications_list": "AWS Cloud Practitioner, Python PCEP",
    }
    df = pd.DataFrame([example])
    return df.to_csv(index=False).encode("utf-8")


def parse_uploaded_csv(
    file_bytes: bytes,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse a CSV upload, validate structure, and return
    (valid_rows, error_messages).
    """
    errors: List[str] = []
    valid_rows: List[Dict[str, Any]] = []

    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        return [], [f"Could not parse CSV: {exc}"]

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = [c for c in CSV_REQUIRED_COLS if c not in df.columns]
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}"]

    for idx, row in df.iterrows():
        row_errors = []
        try:
            roll_no = str(row["roll_no"]).strip().upper()
            full_name = str(row["full_name"]).strip()
            email = str(row["email"]).strip().lower()
            dept = str(row["department"]).strip()

            grad_year = int(float(row["graduation_year"]))
            if not (2020 <= grad_year <= 2035):
                row_errors.append(f"Row {idx+2}: graduation_year {grad_year} out of range.")

            cgpa = float(row["cgpa"])
            if not (0.0 <= cgpa <= 10.0):
                row_errors.append(f"Row {idx+2}: cgpa {cgpa} must be 0–10.")

            score_cols = [
                "technical_score", "aptitude_score", "communication_score",
                "project_score", "certifications_score", "mock_interview_score",
            ]
            scores = {}
            for col in score_cols:
                val = float(row[col])
                if not (0.0 <= val <= 100.0):
                    row_errors.append(f"Row {idx+2}: {col}={val} must be 0–100.")
                scores[col] = round(val, 2)

            if row_errors:
                errors.extend(row_errors)
                continue

            rec: Dict[str, Any] = {
                "roll_no": roll_no,
                "full_name": full_name,
                "email": email,
                "department": dept,
                "graduation_year": grad_year,
                "cgpa": round(cgpa, 2),
                **scores,
                "key_skills": str(row.get("key_skills", "")).strip(),
                "project_summary": str(row.get("project_summary", "")).strip(),
                "certifications_list": str(row.get("certifications_list", "")).strip(),
            }
            valid_rows.append(rec)
        except Exception as exc:
            errors.append(f"Row {idx+2}: Unexpected error — {exc}")

    return valid_rows, errors


def students_to_dataframe(students: list) -> pd.DataFrame:
    """Convert a list of Student ORM objects (or dicts) to a pandas DataFrame."""
    rows = []
    for s in students:
        if isinstance(s, dict):
            rows.append(s)
        else:
            rows.append({
                "ID": s.id,
                "Roll No": s.roll_no,
                "Name": s.full_name,
                "Email": s.email,
                "Department": s.department,
                "Graduation Year": s.graduation_year,
                "CGPA": s.cgpa,
                "Technical": s.technical_score,
                "Aptitude": s.aptitude_score,
                "Communication": s.communication_score,
                "Projects": s.project_score,
                "Certifications": s.certifications_score,
                "Mock Interviews": s.mock_interview_score,
                "Overall Score": s.overall_score,
                "Readiness Level": s.readiness_level,
            })
    return pd.DataFrame(rows)


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to Excel (.xlsx) bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
    return buf.getvalue()
