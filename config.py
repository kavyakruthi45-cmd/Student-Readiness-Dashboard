"""
Application Configuration for Student Readiness Dashboard System.
Contains configurable weights, thresholds, paths, and metadata.
"""

from pathlib import Path
import os

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Database Configuration
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "student_readiness.db"

# Allow override via environment or Streamlit secrets
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# App Metadata
APP_TITLE = "TalentForge | Student Placement Readiness System"
APP_SUBTITLE = "Predictive Career Readiness & Skill-Gap Analytics Platform"
APP_VERSION = "2.4.0"

# Component Weights in Readiness Score Calculation (Sum must equal 1.0)
COMPONENT_WEIGHTS = {
    "technical_skills": 0.25,    # 25%
    "aptitude": 0.20,            # 20%
    "communication": 0.15,       # 15%
    "projects": 0.15,            # 15%
    "academics": 0.10,           # 10% (CGPA scaled to 100)
    "certifications": 0.05,      # 5%
    "mock_interviews": 0.10      # 10%
}

# Display labels for components
COMPONENT_LABELS = {
    "technical_skills": "Technical Skills",
    "aptitude": "Aptitude & Logic",
    "communication": "Communication Skills",
    "projects": "Project Quality & Scope",
    "academics": "Academic CGPA",
    "certifications": "Certifications",
    "mock_interviews": "Mock Interviews"
}

# Readiness Level Thresholds
LEVEL_THRESHOLDS = {
    "READY": 75.0,
    "ALMOST_READY": 55.0
}

# Level Metadata (label, color, badge style)
READINESS_LEVELS = {
    "Ready": {
        "color": "#10B981",          # Emerald / Vibrant Green
        "bg_color": "#D1FAE5",
        "description": "Demonstrates high placement readiness across core competencies."
    },
    "Almost Ready": {
        "color": "#F59E0B",          # Amber / Warm Orange
        "bg_color": "#FEF3C7",
        "description": "On track for placements with targeted improvement required in a few areas."
    },
    "Needs Improvement": {
        "color": "#EF4444",          # Crimson / Red
        "bg_color": "#FEE2E2",
        "description": "Requires structured intervention and focused mentoring before placement drives."
    }
}

# Department List
DEPARTMENTS = [
    "Computer Science & Engineering",
    "Information Technology",
    "Electronics & Communication",
    "Electrical & Electronics",
    "Mechanical Engineering"
]

# Academic Batches / Years
ACADEMIC_YEARS = [2024, 2025, 2026, 2027]

# Default Component Benchmark (Target score out of 100 for gap calculations)
BENCHMARK_TARGET_SCORE = 75.0
