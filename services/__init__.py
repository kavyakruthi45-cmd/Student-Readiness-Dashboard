"""
services package — convenience re-exports.
"""
from services.scoring_service import (
    cgpa_to_score,
    calculate_readiness_score,
    get_readiness_level,
    get_component_scores_dict,
    calculate_cohort_rank_and_percentile,
)
from services.recommendation_service import (
    analyze_skill_gaps,
    generate_recommendations,
)
from services.auth_service import (
    hash_password,
    verify_password,
    authenticate_user,
    create_user,
    get_user_by_id,
    get_user_by_username,
)
from services.student_service import (
    get_all_students,
    get_student_by_id,
    get_student_by_roll_no,
    create_student,
    update_student,
    delete_student,
    bulk_upsert_students,
    get_student_history,
    count_students,
    get_all_scores,
)
from services.report_service import generate_student_pdf_report

__all__ = [
    "cgpa_to_score", "calculate_readiness_score", "get_readiness_level",
    "get_component_scores_dict", "calculate_cohort_rank_and_percentile",
    "analyze_skill_gaps", "generate_recommendations",
    "hash_password", "verify_password", "authenticate_user",
    "create_user", "get_user_by_id", "get_user_by_username",
    "get_all_students", "get_student_by_id", "get_student_by_roll_no",
    "create_student", "update_student", "delete_student",
    "bulk_upsert_students", "get_student_history", "count_students", "get_all_scores",
    "generate_student_pdf_report",
]
