"""
Skill-gap analysis and rule-based personalized recommendation engine.
Analyzes competency deficits relative to placement benchmarks and produces
actionable roadmaps.
"""

from typing import Dict, Any, List
import config
from services.scoring_service import get_component_scores_dict


# Domain-specific rule catalog for targeted placement recommendations
RECOMMENDATION_RULES = {
    "technical_skills": {
        "low": {
            "title": "Build Core Data Structures & Algorithms Foundation",
            "actions": [
                "Solve 2 easy/medium problems daily on LeetCode or HackerRank focusing on Arrays, Strings, and HashMaps.",
                "Review time and space complexity analysis (Big-O notation) for standard sorting and searching algorithms.",
                "Complete a foundational programming course in Python, Java, or C++ with hands-on exercises."
            ],
            "resources": "NeetCode 150, LeetCode Explore, GeeksforGeeks DSA Course",
            "timeline": "3-4 weeks"
        },
        "medium": {
            "title": "Master Advanced Algorithms & System Concepts",
            "actions": [
                "Practice Dynamic Programming, Graph traversals (BFS/DFS), and Tree algorithms.",
                "Implement fundamental Object-Oriented Design (OOP) principles and basic design patterns (Factory, Singleton).",
                "Participate in weekly timed coding contests to improve problem-solving speed under pressure."
            ],
            "resources": "LeetCode Biweekly Contests, Striver's SDE Sheet, Codeforces Div 3",
            "timeline": "2-3 weeks"
        },
        "high": {
            "title": "Hone Competitive Edge & System Design",
            "actions": [
                "Study high-level system design fundamentals (Load balancers, Caching, Sharding, Microservices).",
                "Contribute to open-source repositories and practice writing clean, production-grade code.",
                "Tackle hard-level algorithmic problems and concurrency/multithreading scenarios."
            ],
            "resources": "Grokking the System Design Interview, Designing Data-Intensive Applications",
            "timeline": "Ongoing mastery"
        }
    },
    "aptitude": {
        "low": {
            "title": "Strengthen Quantitative Aptitude & Speed Math",
            "actions": [
                "Master shortcut techniques for Percentages, Profit & Loss, Ratios, and Time-Speed-Distance.",
                "Take 20-minute daily timed quizzes on Quantitative and Analytical reasoning platforms.",
                "Memorize squares (up to 30), cubes (up to 20), and fractional percentages for instant recall."
            ],
            "resources": "IndiaBIX Aptitude, R.S. Aggarwal Quantitative Aptitude, FacePrep",
            "timeline": "3 weeks"
        },
        "medium": {
            "title": "Advance Logical Reasoning & Data Interpretation",
            "actions": [
                "Solve complex syllogisms, seating arrangements, blood relations, and coding-decoding puzzles.",
                "Practice reading and interpreting multi-variable bar charts, pie charts, and radar graphs.",
                "Simulate full-length 60-minute placement aptitude exams under strict time limits."
            ],
            "resources": "PrepInsta Prime, Testbook Placement Tests",
            "timeline": "2 weeks"
        },
        "high": {
            "title": "Maintain Peak Speed & Accuracy",
            "actions": [
                "Target 95%+ accuracy on company-specific aptitude formats (TCS NQT, Cognizant, Infosys).",
                "Practice advanced critical reasoning and verbal ability questions."
            ],
            "resources": "Company Archives & Past Papers",
            "timeline": "Ongoing maintenance"
        }
    },
    "communication": {
        "low": {
            "title": "Overcome Hesitation & Develop Articulation",
            "actions": [
                "Record yourself answering 3 behavioral questions daily and review pacing, filler words, and clarity.",
                "Practice the STAR technique (Situation, Task, Action, Result) for all resume experiences.",
                "Read technology editorial articles aloud for 15 minutes each day to expand professional vocabulary."
            ],
            "resources": "Toastmasters International podcasts, English Central, TED Talks",
            "timeline": "4 weeks"
        },
        "medium": {
            "title": "Refine Professional Presentation & Group Discussions",
            "actions": [
                "Participate in mock Group Discussions (GD) focusing on active listening, structured entry, and synthesis.",
                "Deliver a 5-minute technical walkthrough to peers without relying on presentation slides.",
                "Refine email etiquette, executive summaries, and formal business writing."
            ],
            "resources": "Harvard Business Review Communication Guides, Mock GD Circles",
            "timeline": "2-3 weeks"
        },
        "high": {
            "title": "Master Executive Presence & Cross-Functional Persuasion",
            "actions": [
                "Lead mentorship sessions or technical workshops for junior cohorts.",
                "Practice responding with poise to stressful or ambiguous situational questions."
            ],
            "resources": "Crucial Conversations, Executive Storytelling",
            "timeline": "Ongoing"
        }
    },
    "projects": {
        "low": {
            "title": "Build First End-to-End Deployed Application",
            "actions": [
                "Construct a full-stack CRUD application with database integration, authentication, and API endpoints.",
                "Deploy the project to a public cloud platform (Render, Streamlit Cloud, Vercel, or AWS).",
                "Write a comprehensive GitHub README with architecture diagrams, setup instructions, and feature demo GIFs."
            ],
            "resources": "FreeCodeCamp, FullStackOpen, GitHub Student Developer Pack",
            "timeline": "4 weeks"
        },
        "medium": {
            "title": "Enhance Architecture, Testing & Production Readiness",
            "actions": [
                "Integrate automated unit and integration tests (Pytest/Jest) with CI/CD pipeline (GitHub Actions).",
                "Implement caching (Redis), rate-limiting, and robust database indexing to optimize performance.",
                "Clearly document technical challenges, trade-offs, and metrics achieved in the project documentation."
            ],
            "resources": "GitHub Actions Docs, Modern DevOps Blueprints",
            "timeline": "3 weeks"
        },
        "high": {
            "title": "Architect Novel Solutions & Showcase Real Impact",
            "actions": [
                "Incorporate machine learning or cloud-native microservices into your flagship project.",
                "Acquire real active users or beta testers and measure latency, throughput, and error rates.",
                "Prepare deep-dive architectural talking points for interviewers inquiring about scalability."
            ],
            "resources": "High Scalability Blog, System Design Primer",
            "timeline": "Ongoing"
        }
    },
    "academics": {
        "low": {
            "title": "Solidify Core Computer Science / Engineering Fundamentals",
            "actions": [
                "Focus intensive revision on high-yield placement subjects: DBMS, OS, Computer Networks, and OOP.",
                "Schedule one-on-one doubt clarification sessions with faculty or academic advisors.",
                "Create cheat-sheets summarizing SQL queries, normalization, ACID properties, and paging/scheduling algorithms."
            ],
            "resources": "NPTEL lectures, Gate Smashers, Silberschatz OS Book",
            "timeline": "3 weeks"
        },
        "medium": {
            "title": "Maintain CGPA & Bridge Conceptual Gaps",
            "actions": [
                "Ensure continuous assignment submissions and score 80%+ in internal assessments.",
                "Practice writing complex SQL subqueries, transactions, and index creation on relational databases."
            ],
            "resources": "SQLZoo, LeetCode Database problems",
            "timeline": "2 weeks"
        },
        "high": {
            "title": "Leverage Strong Academic Record",
            "actions": [
                "Highlight high-grade core subjects prominently at the top of your resume.",
                "Explore undergraduate research, conference paper submissions, or academic honors."
            ],
            "resources": "IEEE Xplore, Google Scholar",
            "timeline": "Ongoing"
        }
    },
    "certifications": {
        "low": {
            "title": "Acquire Industry-Recognized Cloud or Domain Credentials",
            "actions": [
                "Earn an entry-level cloud certification (AWS Certified Cloud Practitioner, Azure Fundamentals AZ-900, or GCP Cloud Digital Leader).",
                "Complete a verified credential in specialized tracks like Machine Learning, Cybersecurity, or Full-Stack Development.",
                "Add digital credential badges directly to your LinkedIn profile and resume header."
            ],
            "resources": "AWS Skill Builder, Microsoft Learn, Coursera Professional Certificates",
            "timeline": "3-4 weeks"
        },
        "medium": {
            "title": "Progress to Associate-Level Practical Credentials",
            "actions": [
                "Pursue an associate-level credential such as AWS Certified Solutions Architect Associate or CKA (Kubernetes).",
                "Verify skills with hands-on lab projects required by modern hiring companies."
            ],
            "resources": "A Cloud Guru, KodeKloud",
            "timeline": "4 weeks"
        },
        "high": {
            "title": "Showcase Specialization Depth",
            "actions": [
                "Keep existing credentials renewed and active.",
                "Apply certification competencies directly to production-grade portfolio projects."
            ],
            "resources": "Vendor Specialty Exams",
            "timeline": "Ongoing"
        }
    },
    "mock_interviews": {
        "low": {
            "title": "Initiate Structured Interview Simulations",
            "actions": [
                "Schedule at least 2 peer-to-peer technical mock interviews per week on Pramp or with classmates.",
                "Practice 'thinking out loud' while writing code on a whiteboard or shared editor.",
                "Prepare structured 90-second answers for 'Tell me about yourself' and 'Why should we hire you?'"
            ],
            "resources": "Pramp.com, Interviewing.io, Cracking the Coding Interview",
            "timeline": "2 weeks"
        },
        "medium": {
            "title": "Fine-Tune Live Problem Solving & Behavioral Feedback",
            "actions": [
                "Participate in faculty-led or alumni mock interviews with unexpected follow-up edge cases.",
                "Analyze mock interview feedback sheets to fix repetitive speech pauses or nervous habits.",
                "Practice answering unexpected behavioral curveball questions using the STAR framework."
            ],
            "resources": "Alumni Mentorship Circles, Career Services Mock Drives",
            "timeline": "2 weeks"
        },
        "high": {
            "title": "Peak Interview Readiness & Culture Fit Polish",
            "actions": [
                "Conduct mock interviews for junior peers to gain insights from an interviewer's perspective.",
                "Prepare insightful questions to ask interviewers regarding team culture, engineering practices, and technical roadmaps."
            ],
            "resources": "Reverse Interviewing Repository",
            "timeline": "Ongoing"
        }
    }
}


def analyze_skill_gaps(
    student_or_data: Any,
    benchmark_score: float = config.BENCHMARK_TARGET_SCORE
) -> List[Dict[str, Any]]:
    """
    Perform a granular skill-gap analysis across all 7 readiness components.
    Returns sorted list of components with gap size, status, and urgency priority.
    """
    scores = get_component_scores_dict(student_or_data)
    gap_analysis = []

    for key, actual in scores.items():
        label = config.COMPONENT_LABELS.get(key, key.replace("_", " ").title())
        gap = round(benchmark_score - actual, 1)
        weight = config.COMPONENT_WEIGHTS.get(key, 0.1)

        # Categorize urgency
        if gap > 25.0:
            status = "Critical Gap"
            priority = "High"
            badge_color = "#EF4444"
        elif gap > 0.0:
            status = "Moderate Gap"
            priority = "Medium"
            badge_color = "#F59E0B"
        else:
            status = "Target Exceeded"
            priority = "Low"
            badge_color = "#10B981"

        # Impact score combines gap size and component weight
        impact_score = round(max(gap, 0.0) * weight, 2)

        gap_analysis.append({
            "component_key": key,
            "label": label,
            "actual_score": actual,
            "benchmark_score": benchmark_score,
            "gap": gap,
            "weight_pct": int(weight * 100),
            "status": status,
            "priority": priority,
            "badge_color": badge_color,
            "impact_score": impact_score
        })

    # Sort so highest impact gaps appear first
    gap_analysis.sort(key=lambda x: (x["gap"] <= 0, -x["impact_score"], -x["gap"]))
    return gap_analysis


def generate_recommendations(
    student_or_data: Any,
    benchmark_score: float = config.BENCHMARK_TARGET_SCORE
) -> Dict[str, Any]:
    """
    Generate tailored, rule-based recommendations and action plan based on student scores.
    """
    scores = get_component_scores_dict(student_or_data)
    gaps = analyze_skill_gaps(student_or_data, benchmark_score)

    component_recommendations = []
    strengths = []
    growth_areas = []

    for item in gaps:
        key = item["component_key"]
        actual = item["actual_score"]
        label = item["label"]

        # Determine tier
        if actual < 50.0:
            tier = "low"
            growth_areas.append(f"{label} ({actual:.1f}/100 - High Priority)")
        elif actual < 75.0:
            tier = "medium"
            growth_areas.append(f"{label} ({actual:.1f}/100 - Moderate Priority)")
        else:
            tier = "high"
            strengths.append(f"{label} ({actual:.1f}/100 - Placement Asset)")

        rule_data = RECOMMENDATION_RULES.get(key, {}).get(tier, {})
        if rule_data:
            component_recommendations.append({
                "component_key": key,
                "label": label,
                "score": actual,
                "tier": tier,
                "priority": item["priority"],
                "badge_color": item["badge_color"],
                "title": rule_data.get("title", ""),
                "actions": rule_data.get("actions", []),
                "resources": rule_data.get("resources", ""),
                "timeline": rule_data.get("timeline", "2-3 weeks")
            })

    # Build 30-60-90 Day Action Roadmap
    critical_items = [c for c in component_recommendations if c["priority"] == "High"]
    medium_items = [c for c in component_recommendations if c["priority"] == "Medium"]
    low_items = [c for c in component_recommendations if c["priority"] == "Low"]

    roadmap = {
        "immediate_focus": {
            "period": "Next 14 Days (Critical Foundation)",
            "items": critical_items[:2] if critical_items else medium_items[:2]
        },
        "mid_term_focus": {
            "period": "Days 15 - 45 (Competency Acceleration)",
            "items": medium_items[:3] if medium_items else critical_items[2:4]
        },
        "polishing_focus": {
            "period": "Days 46 - 75 (Mock Drives & Placement Polishing)",
            "items": low_items[:2]
        }
    }

    return {
        "gaps": gaps,
        "recommendations": component_recommendations,
        "strengths": strengths,
        "growth_areas": growth_areas,
        "roadmap": roadmap
    }
