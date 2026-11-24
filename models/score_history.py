"""
Score history snapshot model for longitudinal readiness tracking and trend visualization.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base


class ScoreHistory(Base):
    __tablename__ = "score_histories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    month_label = Column(String(20), nullable=False)  # e.g. "Jun 2026"

    # Snapshots of scores at that point in time
    overall_score = Column(Float, nullable=False)
    readiness_level = Column(String(30), nullable=False)
    technical_score = Column(Float, nullable=False)
    aptitude_score = Column(Float, nullable=False)
    communication_score = Column(Float, nullable=False)
    project_score = Column(Float, nullable=False)
    academics_score = Column(Float, nullable=False)  # Scaled CGPA (0-100)
    certifications_score = Column(Float, nullable=False)
    mock_interview_score = Column(Float, nullable=False)

    # Relationship
    student = relationship("Student", back_populates="history")

    def __repr__(self):
        return f"<ScoreHistory(student_id={self.student_id}, month='{self.month_label}', score={self.overall_score:.1f})>"
