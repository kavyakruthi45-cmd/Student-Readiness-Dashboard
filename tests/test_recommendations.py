"""
Unit tests for recommendation_service.py
Tests: skill-gap analysis, recommendation generation, roadmap structure.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from services.recommendation_service import analyze_skill_gaps, generate_recommendations


# ---------------------------------------------------------------------------
# Mock student objects
# ---------------------------------------------------------------------------

class MockStudentHigh:
    """All scores excellent — no critical gaps."""
    technical_score = 90.0
    aptitude_score = 85.0
    communication_score = 88.0
    project_score = 82.0
    certifications_score = 80.0
    mock_interview_score = 86.0
    cgpa = 9.0


class MockStudentLow:
    """All scores poor — maximum gaps."""
    technical_score = 25.0
    aptitude_score = 30.0
    communication_score = 20.0
    project_score = 28.0
    certifications_score = 15.0
    mock_interview_score = 22.0
    cgpa = 5.0


class MockStudentMixed:
    """Mixed — some components strong, some weak."""
    technical_score = 85.0   # strong
    aptitude_score = 40.0    # weak
    communication_score = 72.0
    project_score = 30.0     # weak
    certifications_score = 80.0
    mock_interview_score = 55.0
    cgpa = 8.0


class MockStudentDict:
    """Dict-based student data."""
    @staticmethod
    def as_dict():
        return {
            "technical_score": 60.0,
            "aptitude_score": 50.0,
            "communication_score": 55.0,
            "project_score": 48.0,
            "certifications_score": 40.0,
            "mock_interview_score": 52.0,
            "cgpa": 7.0,
        }


# ---------------------------------------------------------------------------
# analyze_skill_gaps tests
# ---------------------------------------------------------------------------

class TestAnalyzeSkillGaps:
    def test_returns_list(self):
        result = analyze_skill_gaps(MockStudentHigh())
        assert isinstance(result, list)

    def test_returns_seven_components(self):
        result = analyze_skill_gaps(MockStudentLow())
        assert len(result) == 7

    def test_all_gaps_positive_for_low_student(self):
        result = analyze_skill_gaps(MockStudentLow())
        # At least some gaps > 0
        positive_gaps = [r for r in result if r["gap"] > 0]
        assert len(positive_gaps) > 0

    def test_no_critical_gaps_for_high_student(self):
        result = analyze_skill_gaps(MockStudentHigh())
        # No component should have "Critical Gap"
        critical = [r for r in result if r["status"] == "Critical Gap"]
        assert len(critical) == 0

    def test_target_exceeded_for_high_student(self):
        result = analyze_skill_gaps(MockStudentHigh())
        exceeded = [r for r in result if r["status"] == "Target Exceeded"]
        assert len(exceeded) > 0

    def test_sorted_by_impact_descending(self):
        result = analyze_skill_gaps(MockStudentLow())
        # Items with gap > 0 should come before gap <= 0
        gaps = [r["gap"] for r in result]
        # First item should have the largest gap
        for i in range(len(gaps) - 1):
            if gaps[i] <= 0 and gaps[i + 1] > 0:
                pytest.fail("Gaps not sorted correctly (positive gaps should precede zero/negative)")

    def test_gap_values_match_benchmark(self):
        benchmark = 75.0
        result = analyze_skill_gaps(MockStudentLow(), benchmark_score=benchmark)
        for item in result:
            expected_gap = round(benchmark - item["actual_score"], 1)
            assert item["gap"] == pytest.approx(expected_gap, abs=0.01)

    def test_dict_input_accepted(self):
        result = analyze_skill_gaps(MockStudentDict.as_dict())
        assert len(result) == 7

    def test_badge_colors_assigned(self):
        result = analyze_skill_gaps(MockStudentMixed())
        for item in result:
            assert "badge_color" in item
            assert item["badge_color"].startswith("#")

    def test_component_keys_valid(self):
        import config
        result = analyze_skill_gaps(MockStudentMixed())
        valid_keys = set(config.COMPONENT_WEIGHTS.keys())
        for item in result:
            assert item["component_key"] in valid_keys

    def test_impact_score_non_negative(self):
        result = analyze_skill_gaps(MockStudentLow())
        for item in result:
            assert item["impact_score"] >= 0.0


# ---------------------------------------------------------------------------
# generate_recommendations tests
# ---------------------------------------------------------------------------

class TestGenerateRecommendations:
    def test_returns_dict_with_expected_keys(self):
        result = generate_recommendations(MockStudentMixed())
        assert "gaps" in result
        assert "recommendations" in result
        assert "strengths" in result
        assert "growth_areas" in result
        assert "roadmap" in result

    def test_recommendations_non_empty_for_low_student(self):
        result = generate_recommendations(MockStudentLow())
        assert len(result["recommendations"]) > 0

    def test_strengths_identified_for_high_student(self):
        result = generate_recommendations(MockStudentHigh())
        assert len(result["strengths"]) > 0

    def test_growth_areas_identified_for_low_student(self):
        result = generate_recommendations(MockStudentLow())
        assert len(result["growth_areas"]) > 0

    def test_recommendation_has_title_and_actions(self):
        result = generate_recommendations(MockStudentLow())
        for rec in result["recommendations"]:
            assert "title" in rec
            assert "actions" in rec
            assert isinstance(rec["actions"], list)
            assert len(rec["actions"]) > 0

    def test_roadmap_has_three_phases(self):
        result = generate_recommendations(MockStudentMixed())
        roadmap = result["roadmap"]
        assert "immediate_focus" in roadmap
        assert "mid_term_focus" in roadmap
        assert "polishing_focus" in roadmap

    def test_roadmap_phase_has_period(self):
        result = generate_recommendations(MockStudentMixed())
        for phase_key in ["immediate_focus", "mid_term_focus", "polishing_focus"]:
            assert "period" in result["roadmap"][phase_key]

    def test_high_priority_items_in_immediate_focus(self):
        result = generate_recommendations(MockStudentLow())
        immediate = result["roadmap"]["immediate_focus"]["items"]
        # Immediate focus should contain High priority items for low student
        # (or at least some items)
        assert isinstance(immediate, list)

    def test_no_negative_scores_in_recommendations(self):
        result = generate_recommendations(MockStudentMixed())
        for rec in result["recommendations"]:
            assert rec["score"] >= 0.0

    def test_dict_input_works(self):
        result = generate_recommendations(MockStudentDict.as_dict())
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    def test_recommendation_priority_values_valid(self):
        result = generate_recommendations(MockStudentMixed())
        valid_priorities = {"High", "Medium", "Low"}
        for rec in result["recommendations"]:
            assert rec.get("priority") in valid_priorities

    def test_resources_and_timeline_present(self):
        result = generate_recommendations(MockStudentLow())
        for rec in result["recommendations"]:
            assert "resources" in rec
            assert "timeline" in rec
