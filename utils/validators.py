"""
Utility helpers: validators, CSV import/export, logging configuration.
"""
import logging
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root logger with console + file handlers."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ],
    )
    return logging.getLogger("student_readiness")


logger = setup_logging()


# ---------------------------------------------------------------------------
# Input Validators
# ---------------------------------------------------------------------------

def validate_score(value: float, name: str = "Score") -> float:
    """Clamp and validate a 0-100 score field."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number, got: {value!r}")
    if not (0.0 <= v <= 100.0):
        raise ValueError(f"{name} must be between 0 and 100, got {v}.")
    return round(v, 2)


def validate_cgpa(value: float) -> float:
    """Validate CGPA on a 0.0 – 10.0 scale."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"CGPA must be a number, got: {value!r}")
    if not (0.0 <= v <= 10.0):
        raise ValueError(f"CGPA must be between 0.0 and 10.0, got {v}.")
    return round(v, 2)


def validate_email(email: str) -> str:
    """Basic RFC-5322 email format check."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    email = email.strip().lower()
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email!r}")
    return email


def validate_roll_no(roll_no: str) -> str:
    """Roll number must be 3-30 alphanumeric/dash/underscore chars."""
    rn = roll_no.strip().upper()
    if not re.match(r"^[A-Z0-9\-_]{3,30}$", rn):
        raise ValueError(
            f"Roll number '{roll_no}' is invalid. Use 3-30 alphanumeric characters."
        )
    return rn


def validate_graduation_year(year: int) -> int:
    """Graduation year must be a sensible academic year."""
    y = int(year)
    if not (2020 <= y <= 2035):
        raise ValueError(f"Graduation year {y} is out of range (2020-2035).")
    return y
