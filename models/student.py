"""
Student profile model storing academic details, competency scores, and calculated readiness.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from database.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    roll_no = Column(String(30), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    graduation_year = Column(Integer, nullable=False, index=True)
    cgpa = Column(Float, nullable=False, default=7.0)  # On scale of 10.0

    # 7 Component Scores (0 to 100)
    technical_score = Column(Float, nullable=False, default=50.0)
    aptitude_score = Column(Float, nullable=False, default=50.0)
    communication_score = Column(Float, nullable=False, default=50.0)
    project_score = Column(Float, nullable=False, default=50.0)
    certifications_score = Column(Float, nullable=False, default=50.0)
    mock_interview_score = Column(Float, nullable=False, default=50.0)

    # Computed Readiness
    overall_score = Column(Float, nullable=False, default=50.0)
    readiness_level = Column(String(30), nullable=False, default="Almost Ready")

    # Qualitative details for student profile & resume building
    key_skills = Column(Text, nullable=True)  # Comma-separated or bullet list
    project_summary = Column(Text, nullable=True)
    certifications_list = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student", uselist=False)
    history = relationship(
        "ScoreHistory",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="ScoreHistory.recorded_at"
    )

    def __repr__(self):
        return f"<Student(id={self.id}, roll_no='{self.roll_no}', name='{self.full_name}', score={self.overall_score:.1f})>"
