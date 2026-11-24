"""
Unit tests for scoring_service.py
Tests: score calculation, CGPA conversion, readiness level classification,
rank/percentile calculation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from services.scoring_service import (
    cgpa_to_score,
    calculate_readiness_score,
    get_readiness_level,
    calculate_cohort_rank_and_percentile,
    get_component_scores_dict,
)


# ---------------------------------------------------------------------------
# cgpa_to_score
# ---------------------------------------------------------------------------

class TestCgpaToScore:
    def test_perfect_cgpa(self):
        assert cgpa_to_score(10.0) == 100.0

    def test_zero_cgpa(self):
        assert cgpa_to_score(0.0) == 0.0

    def test_mid_cgpa(self):
        assert cgpa_to_score(7.5) == pytest.approx(75.0, abs=0.01)

    def test_negative_clamped(self):
        assert cgpa_to_score(-1.0) == 0.0

    def test_over_10_clamped(self):
        assert cgpa_to_score(11.0) == 100.0

    def test_none_returns_zero(self):
        assert cgpa_to_score(None) == 0.0


# ---------------------------------------------------------------------------
# calculate_readiness_score
# ---------------------------------------------------------------------------

class TestCalculateReadinessScore:
    def test_all_hundred(self):
        score = calculate_readiness_score(100, 100, 100, 100, 10.0, 100, 100)
        assert score == 100.0

    def test_all_zero(self):
        score = calculate_readiness_score(0, 0, 0, 0, 0.0, 0, 0)
        assert score == 0.0

    def test_known_values(self):
        # 80*0.25 + 70*0.20 + 65*0.15 + 70*0.15 + 75*0.10 + 60*0.05 + 65*0.10
        # = 20 + 14 + 9.75 + 10.5 + 7.5 + 3 + 6.5 = 71.25
        score = calculate_readiness_score(80, 70, 65, 70, 7.5, 60, 65)
        assert score == pytest.approx(71.25, abs=0.1)

    def test_weights_sum_to_one(self):
        import config
        total = sum(config.COMPONENT_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_clamping_above_100(self):
        score = calculate_readiness_score(150, 150, 150, 150, 15.0, 150, 150)
        assert score == 100.0

    def test_clamping_below_zero(self):
        score = calculate_readiness_score(-50, -50, -50, -50, -1.0, -50, -50)
        assert score == 0.0

    def test_custom_weights(self):
        custom = {
            "technical_skills": 1.0,
            "aptitude": 0.0, "communication": 0.0, "projects": 0.0,
            "academics": 0.0, "certifications": 0.0, "mock_interviews": 0.0,
        }
        score = calculate_readiness_score(80, 0, 0, 0, 0, 0, 0, custom_weights=custom)
        assert score == pytest.approx(80.0, abs=0.01)

    def test_returns_float(self):
        result = calculate_readiness_score(60, 60, 60, 60, 6.0, 60, 60)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# get_readiness_level
# ---------------------------------------------------------------------------

class TestGetReadinessLevel:
    def test_ready_at_75(self):
        assert get_readiness_level(75.0) == "Ready"

    def test_ready_at_100(self):
        assert get_readiness_level(100.0) == "Ready"

    def test_almost_ready_at_55(self):
        assert get_readiness_level(55.0) == "Almost Ready"

    def test_almost_ready_at_74(self):
        assert get_readiness_level(74.9) == "Almost Ready"

    def test_needs_at_zero(self):
        assert get_readiness_level(0.0) == "Needs Improvement"

    def test_needs_at_54(self):
        assert get_readiness_level(54.9) == "Needs Improvement"

    def test_boundary_exact_75(self):
        assert get_readiness_level(75.0) == "Ready"

    def test_boundary_just_below_75(self):
        assert get_readiness_level(74.99) == "Almost Ready"

    def test_boundary_exact_55(self):
        assert get_readiness_level(55.0) == "Almost Ready"

    def test_boundary_just_below_55(self):
        assert get_readiness_level(54.99) == "Needs Improvement"


# ---------------------------------------------------------------------------
# calculate_cohort_rank_and_percentile
# ---------------------------------------------------------------------------

class TestCohortRankAndPercentile:
    def test_top_scorer(self):
        rank, pct = calculate_cohort_rank_and_percentile(90.0, [90.0, 80.0, 70.0, 60.0])
        assert rank == 1
        assert pct == 100.0

    def test_bottom_scorer(self):
        rank, pct = calculate_cohort_rank_and_percentile(60.0, [90.0, 80.0, 70.0, 60.0])
        assert rank == 4
        assert pct == pytest.approx(25.0, abs=0.1)

    def test_single_student(self):
        rank, pct = calculate_cohort_rank_and_percentile(70.0, [70.0])
        assert rank == 1
        assert pct == 100.0

    def test_empty_list(self):
        rank, pct = calculate_cohort_rank_and_percentile(70.0, [])
        assert rank == 1
        assert pct == 100.0

    def test_tied_scores(self):
        rank, pct = calculate_cohort_rank_and_percentile(80.0, [80.0, 80.0, 80.0])
        # All tied — rank should be 1
        assert rank == 1


# ---------------------------------------------------------------------------
# get_component_scores_dict
# ---------------------------------------------------------------------------

class TestGetComponentScoresDict:
    def test_dict_input(self):
        data = {
            "technical_score": 80.0,
            "aptitude_score": 70.0,
            "communication_score": 65.0,
            "project_score": 75.0,
            "certifications_score": 55.0,
            "mock_interview_score": 60.0,
            "cgpa": 8.0,
        }
        result = get_component_scores_dict(data)
        assert result["technical_skills"] == 80.0
        assert result["academics"] == pytest.approx(80.0, abs=0.01)  # 8.0/10 * 100

    def test_all_keys_present(self):
        import config
        data = {k.replace("ical_skills", "ical_score").replace("itude", "itude_score")
                .replace("unication", "unication_score").replace("ects", "ect_score")
                .replace("demics", "pa").replace("ifications", "ifications_score")
                .replace("_interviews", "_interview_score"): 50.0
                for k in config.COMPONENT_WEIGHTS}
        # Easier: just use a mock object
        class MockStudent:
            technical_score = 70.0
            aptitude_score = 65.0
            communication_score = 60.0
            project_score = 55.0
            certifications_score = 50.0
            mock_interview_score = 58.0
            cgpa = 7.2

        result = get_component_scores_dict(MockStudent())
        assert set(result.keys()) == set(["technical_skills", "aptitude", "communication",
                                          "projects", "academics", "certifications", "mock_interviews"])
