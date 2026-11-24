"""
Scoring service containing the weighted readiness model, level classification,
and cohort percentile/ranking logic.
"""

from typing import Dict, Any, List, Tuple, Optional
import config


def cgpa_to_score(cgpa: float) -> float:
    """
    Convert a 10-point CGPA to a 0-100 percentage scale.
    Clamps between 0.0 and 100.0.
    """
    if cgpa is None:
        return 0.0
    scaled = (float(cgpa) / 10.0) * 100.0
    return round(min(max(scaled, 0.0), 100.0), 2)


def calculate_readiness_score(
    technical_score: float,
    aptitude_score: float,
    communication_score: float,
    project_score: float,
    cgpa: float,
    certifications_score: float,
    mock_interview_score: float,
    custom_weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Compute composite readiness score (0-100) using weighted multi-component model.
    Weights defaults to config.COMPONENT_WEIGHTS:
      - Technical skills: 25%
      - Aptitude: 20%
      - Communication: 15%
      - Projects: 15%
      - Academics (CGPA): 10%
      - Certifications: 5%
      - Mock interviews: 10%
    """
    weights = custom_weights or config.COMPONENT_WEIGHTS

    # Normalize inputs to 0-100 bounds
    tech = min(max(float(technical_score or 0), 0.0), 100.0)
    apt = min(max(float(aptitude_score or 0), 0.0), 100.0)
    comm = min(max(float(communication_score or 0), 0.0), 100.0)
    proj = min(max(float(project_score or 0), 0.0), 100.0)
    acad = cgpa_to_score(cgpa)
    cert = min(max(float(certifications_score or 0), 0.0), 100.0)
    mock = min(max(float(mock_interview_score or 0), 0.0), 100.0)

    score = (
        tech * weights.get("technical_skills", 0.25) +
        apt * weights.get("aptitude", 0.20) +
        comm * weights.get("communication", 0.15) +
        proj * weights.get("projects", 0.15) +
        acad * weights.get("academics", 0.10) +
        cert * weights.get("certifications", 0.05) +
        mock * weights.get("mock_interviews", 0.10)
    )

    return round(min(max(score, 0.0), 100.0), 2)


def get_readiness_level(overall_score: float) -> str:
    """
    Map an overall readiness score (0-100) to its readiness classification level:
      - Ready (>= 75.0)
      - Almost Ready (55.0 - 74.99)
      - Needs Improvement (< 55.0)
    """
    score = float(overall_score or 0.0)
    if score >= config.LEVEL_THRESHOLDS["READY"]:
        return "Ready"
    elif score >= config.LEVEL_THRESHOLDS["ALMOST_READY"]:
        return "Almost Ready"
    else:
        return "Needs Improvement"


def get_component_scores_dict(student: Any) -> Dict[str, float]:
    """
    Extract normalized 0-100 component scores for a student object or dict.
    """
    if isinstance(student, dict):
        cgpa_val = student.get("cgpa", 0.0)
        return {
            "technical_skills": float(student.get("technical_score", 0.0)),
            "aptitude": float(student.get("aptitude_score", 0.0)),
            "communication": float(student.get("communication_score", 0.0)),
            "projects": float(student.get("project_score", 0.0)),
            "academics": cgpa_to_score(cgpa_val),
            "certifications": float(student.get("certifications_score", 0.0)),
            "mock_interviews": float(student.get("mock_interview_score", 0.0))
        }

    return {
        "technical_skills": float(getattr(student, "technical_score", 0.0)),
        "aptitude": float(getattr(student, "aptitude_score", 0.0)),
        "communication": float(getattr(student, "communication_score", 0.0)),
        "projects": float(getattr(student, "project_score", 0.0)),
        "academics": cgpa_to_score(getattr(student, "cgpa", 0.0)),
        "certifications": float(getattr(student, "certifications_score", 0.0)),
        "mock_interviews": float(getattr(student, "mock_interview_score", 0.0))
    }


def calculate_cohort_rank_and_percentile(
    target_score: float,
    all_scores: List[float]
) -> Tuple[int, float]:
    """
    Calculate 1-indexed descending rank and percentile rank within a list of scores.
    Returns: (rank, percentile)
    """
    if not all_scores:
        return 1, 100.0

    sorted_scores = sorted(all_scores, reverse=True)
    total = len(sorted_scores)

    # 1-indexed rank (handles ties gracefully)
    rank = 1
    for s in sorted_scores:
        if s > target_score:
            rank += 1
        else:
            break

    # Percentile: percentage of scores <= target_score
    count_below_or_equal = sum(1 for s in sorted_scores if s <= target_score)
    percentile = round((count_below_or_equal / total) * 100.0, 1)

    return rank, percentile
