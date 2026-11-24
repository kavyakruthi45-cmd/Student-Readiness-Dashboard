"""
Student CRUD service layer — all DB interactions for student records.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from database.connection import get_db_session
from models.student import Student
from models.score_history import ScoreHistory
from services.scoring_service import calculate_readiness_score, get_readiness_level, cgpa_to_score
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_and_attach(student: Student) -> Student:
    """Recalculate overall score + level and attach to the student object."""
    student.overall_score = calculate_readiness_score(
        technical_score=student.technical_score,
        aptitude_score=student.aptitude_score,
        communication_score=student.communication_score,
        project_score=student.project_score,
        cgpa=student.cgpa,
        certifications_score=student.certifications_score,
        mock_interview_score=student.mock_interview_score,
    )
    student.readiness_level = get_readiness_level(student.overall_score)
    student.updated_at = datetime.utcnow()
    return student


def _snapshot_history(session: Session, student: Student) -> None:
    """Write a ScoreHistory snapshot row for the given student."""
    month_label = datetime.utcnow().strftime("%b %Y")
    snap = ScoreHistory(
        student_id=student.id,
        recorded_at=datetime.utcnow(),
        month_label=month_label,
        overall_score=student.overall_score,
        readiness_level=student.readiness_level,
        technical_score=student.technical_score,
        aptitude_score=student.aptitude_score,
        communication_score=student.communication_score,
        project_score=student.project_score,
        academics_score=cgpa_to_score(student.cgpa),
        certifications_score=student.certifications_score,
        mock_interview_score=student.mock_interview_score,
    )
    session.add(snap)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_students(
    department: Optional[str] = None,
    graduation_year: Optional[int] = None,
    readiness_level: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "overall_score",
    sort_desc: bool = True,
) -> List[Student]:
    """Return filtered + sorted list of Student objects (detached from session)."""
    with get_db_session() as session:
        q = session.query(Student)

        if department and department != "All":
            q = q.filter(Student.department == department)
        if graduation_year:
            q = q.filter(Student.graduation_year == graduation_year)
        if readiness_level and readiness_level != "All":
            q = q.filter(Student.readiness_level == readiness_level)
        if search:
            term = f"%{search.strip()}%"
            q = q.filter(
                Student.full_name.ilike(term) |
                Student.roll_no.ilike(term) |
                Student.email.ilike(term)
            )

        sort_col = getattr(Student, sort_by, Student.overall_score)
        q = q.order_by(sort_col.desc() if sort_desc else sort_col.asc())

        students = q.all()
        for s in students:
            session.expunge(s)
        return students


def get_student_by_id(student_id: int) -> Optional[Student]:
    with get_db_session() as session:
        s = session.query(Student).filter(Student.id == student_id).first()
        if s:
            session.expunge(s)
        return s


def get_student_by_roll_no(roll_no: str) -> Optional[Student]:
    with get_db_session() as session:
        s = session.query(Student).filter(
            Student.roll_no == roll_no.strip().upper()
        ).first()
        if s:
            session.expunge(s)
        return s


def create_student(data: Dict[str, Any]) -> Student:
    """Create a new Student record and write an initial history snapshot."""
    with get_db_session() as session:
        student = Student(
            roll_no=data["roll_no"].strip().upper(),
            full_name=data["full_name"].strip(),
            email=data["email"].strip().lower(),
            department=data["department"].strip(),
            graduation_year=int(data["graduation_year"]),
            cgpa=float(data["cgpa"]),
            technical_score=float(data.get("technical_score", 50.0)),
            aptitude_score=float(data.get("aptitude_score", 50.0)),
            communication_score=float(data.get("communication_score", 50.0)),
            project_score=float(data.get("project_score", 50.0)),
            certifications_score=float(data.get("certifications_score", 50.0)),
            mock_interview_score=float(data.get("mock_interview_score", 50.0)),
            key_skills=data.get("key_skills", ""),
            project_summary=data.get("project_summary", ""),
            certifications_list=data.get("certifications_list", ""),
        )
        _compute_and_attach(student)
        session.add(student)
        session.flush()
        _snapshot_history(session, student)
        session.refresh(student)
        session.expunge(student)
        return student


def update_student(student_id: int, data: Dict[str, Any]) -> Optional[Student]:
    """Update an existing student and snapshot the new scores."""
    with get_db_session() as session:
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None

        updatable = [
            "full_name", "email", "department", "graduation_year", "cgpa",
            "technical_score", "aptitude_score", "communication_score",
            "project_score", "certifications_score", "mock_interview_score",
            "key_skills", "project_summary", "certifications_list",
        ]
        for field in updatable:
            if field in data:
                setattr(student, field, data[field])

        _compute_and_attach(student)
        _snapshot_history(session, student)
        session.refresh(student)
        session.expunge(student)
        return student


def delete_student(student_id: int) -> bool:
    with get_db_session() as session:
        student = session.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False
        session.delete(student)
        return True


def bulk_upsert_students(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insert or update students from a validated row list. Returns counts."""
    created = updated = skipped = 0
    for row in rows:
        try:
            existing = get_student_by_roll_no(row["roll_no"])
            if existing:
                update_student(existing.id, row)
                updated += 1
            else:
                create_student(row)
                created += 1
        except Exception as exc:
            logger.warning(f"Skipping row {row.get('roll_no')}: {exc}")
            skipped += 1
    return {"created": created, "updated": updated, "skipped": skipped}


def get_student_history(student_id: int) -> List[ScoreHistory]:
    """Return time-ordered history snapshots for a student."""
    with get_db_session() as session:
        records = (
            session.query(ScoreHistory)
            .filter(ScoreHistory.student_id == student_id)
            .order_by(ScoreHistory.recorded_at.asc())
            .all()
        )
        for r in records:
            session.expunge(r)
        return records


def count_students() -> int:
    with get_db_session() as session:
        return session.query(Student).count()


def get_all_scores() -> List[float]:
    """Return all current overall scores for percentile calculations."""
    with get_db_session() as session:
        rows = session.query(Student.overall_score).all()
        return [r[0] for r in rows]
