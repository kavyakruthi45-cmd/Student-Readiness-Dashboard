"""
seed_data.py — Generate 150+ realistic students with months of score history
and demo accounts:
  Admin : admin    / admin123
  Student: student1 / student123
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database.connection import init_db, get_db_session
from models.student import Student
from models.score_history import ScoreHistory
from models.user import User
from services.auth_service import hash_password
from services.scoring_service import calculate_readiness_score, get_readiness_level, cgpa_to_score

logger = logging.getLogger(__name__)

random.seed(42)  # Reproducible data

# ---------------------------------------------------------------------------
# Reference data pools
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    "Computer Science & Engineering",
    "Information Technology",
    "Electronics & Communication",
    "Electrical & Electronics",
    "Mechanical Engineering",
]
DEPT_SHORT = {
    "Computer Science & Engineering": "CSE",
    "Information Technology": "IT",
    "Electronics & Communication": "ECE",
    "Electrical & Electronics": "EEE",
    "Mechanical Engineering": "MECH",
}

GRAD_YEARS = [2024, 2025, 2026, 2027]

FIRST_NAMES = [
    "Aarav", "Aditya", "Akshay", "Amit", "Ananya", "Anjali", "Arjun", "Arnav",
    "Ayaan", "Bhavya", "Deepak", "Divya", "Gaurav", "Harini", "Harsh", "Ishaan",
    "Ishita", "Jayesh", "Karthik", "Kavya", "Keerthi", "Kunal", "Lakshmi",
    "Manish", "Meera", "Mihir", "Nandini", "Nikhil", "Nikita", "Pavan",
    "Pooja", "Pranav", "Priya", "Rahul", "Raj", "Ramya", "Riya", "Rohit",
    "Sachin", "Sahil", "Sakshi", "Sameer", "Sandhya", "Sanjay", "Sanya",
    "Siddharth", "Simran", "Sneha", "Srishti", "Suresh", "Swati", "Tanvi",
    "Tejas", "Usha", "Vaibhav", "Vandana", "Vani", "Vikram", "Vinay", "Vishal",
    "Yash", "Zara", "Abhishek", "Aishwarya", "Akash", "Alok", "Alka", "Amrit",
]
LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Patel", "Mehta", "Nair", "Reddy",
    "Joshi", "Gupta", "Mishra", "Pandey", "Kapoor", "Rao", "Iyer", "Pillai",
    "Bhat", "Kulkarni", "Naik", "Desai", "Shah", "Jain", "Agarwal", "Saxena",
    "Murthy", "Krishnan", "Subramaniam", "Hegde", "Shetty", "Menon",
]

SKILLS_POOL = {
    "Computer Science & Engineering": [
        "Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "MongoDB",
        "Docker", "Kubernetes", "AWS", "Git", "Machine Learning", "Deep Learning",
        "Data Structures", "Algorithms", "REST APIs", "GraphQL", "Redis", "Kafka",
    ],
    "Information Technology": [
        "Python", "PHP", "MySQL", "Linux", "Networking", "Cybersecurity", "Cloud Computing",
        "DevOps", "Ansible", "Terraform", "Azure", "GCP", "ITIL", "SAP", "Selenium",
    ],
    "Electronics & Communication": [
        "VLSI Design", "Verilog", "MATLAB", "Embedded C", "Arduino", "Raspberry Pi",
        "Signal Processing", "PCB Design", "IoT", "FPGA", "ARM Cortex", "RF Design",
    ],
    "Electrical & Electronics": [
        "PLC Programming", "SCADA", "AutoCAD Electrical", "MATLAB Simulink",
        "Power Electronics", "Control Systems", "Circuit Analysis", "ETAP", "LabVIEW",
    ],
    "Mechanical Engineering": [
        "SolidWorks", "AutoCAD", "ANSYS", "CATIA", "Fusion 360", "Finite Element Analysis",
        "CNC Machining", "3D Printing", "Thermodynamics", "Fluid Mechanics",
    ],
}

CERT_POOL = {
    "Computer Science & Engineering": [
        "AWS Certified Cloud Practitioner", "Google Associate Cloud Engineer",
        "Coursera Deep Learning Specialization", "Microsoft AZ-900", "Oracle Java SE",
        "LeetCode 50-day Badge", "GitHub Actions Certification", "Cisco CCNA",
    ],
    "Information Technology": [
        "CompTIA Security+", "Microsoft Azure Fundamentals", "Google Cloud Digital Leader",
        "AWS Certified SysOps", "CEH - Certified Ethical Hacker", "ITIL Foundation",
    ],
    "Electronics & Communication": [
        "Cadence Virtuoso Certification", "Texas Instruments Embedded Basics",
        "MATLAB Onramp", "IoT Specialization - Coursera", "Arduino Advanced",
    ],
    "Electrical & Electronics": [
        "NPTEL Power Systems", "PLC SCADA Certification", "MATLAB Simulink Onramp",
        "AutoCAD Electrical Professional", "ETAP Basic Certification",
    ],
    "Mechanical Engineering": [
        "CATIA V5 Certified", "SolidWorks CSWA", "ANSYS Learning Hub Certificate",
        "Autodesk Fusion 360 Badge", "Six Sigma Green Belt",
    ],
}

PROJECT_TEMPLATES = [
    "Built a full-stack {domain} web application with authentication and analytics",
    "Developed an ML model for {domain} prediction achieving 91% accuracy",
    "Designed and deployed a microservices architecture for {domain} management",
    "Created an IoT-based {domain} monitoring system with real-time dashboards",
    "Implemented a {domain} recommendation engine using collaborative filtering",
    "Built a RESTful API backend for a {domain} mobile application",
    "Architected a scalable {domain} data pipeline processing 1M+ daily records",
    "Developed a {domain} chatbot using NLP and deployed on cloud infrastructure",
]
DOMAINS = [
    "inventory", "healthcare", "e-commerce", "student", "employee",
    "expense", "library", "transport", "agriculture", "smart home",
]


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _make_roll_no(dept: str, year: int, seq: int) -> str:
    code = DEPT_SHORT.get(dept, "GEN")
    return f"{code}{str(year)[-2:]}{seq:04d}"


def _gen_scores(profile: str) -> Dict[str, float]:
    """
    Generate component scores based on student performance profile.
    profiles: 'star', 'good', 'average', 'weak'
    """
    profiles = {
        "star":    {"mu": 82, "sigma": 8,  "cgpa_mu": 9.0, "cgpa_sigma": 0.5},
        "good":    {"mu": 70, "sigma": 9,  "cgpa_mu": 7.8, "cgpa_sigma": 0.7},
        "average": {"mu": 57, "sigma": 10, "cgpa_mu": 6.8, "cgpa_sigma": 0.8},
        "weak":    {"mu": 40, "sigma": 11, "cgpa_mu": 5.8, "cgpa_sigma": 0.9},
    }
    cfg = profiles[profile]
    components = [
        "technical_score", "aptitude_score", "communication_score",
        "project_score", "certifications_score", "mock_interview_score",
    ]
    scores = {}
    for c in components:
        val = random.gauss(cfg["mu"], cfg["sigma"])
        scores[c] = round(min(max(val, 10.0), 100.0), 1)
    cgpa_raw = random.gauss(cfg["cgpa_mu"], cfg["cgpa_sigma"])
    scores["cgpa"] = round(min(max(cgpa_raw, 4.0), 10.0), 2)
    return scores


def _gen_history_snapshots(
    student_id: int,
    current_scores: Dict[str, float],
    n_months: int = 6,
) -> List[Dict[str, Any]]:
    """
    Back-generate n_months of history snapshots with a realistic progression.
    Scores improve slightly each month toward current values.
    """
    snapshots = []
    now = datetime.utcnow()

    for i in range(n_months - 1, -1, -1):
        date = now - timedelta(days=30 * i)
        # Earlier months have lower scores (trend upward)
        factor = 0.78 + 0.22 * ((n_months - 1 - i) / max(n_months - 1, 1))
        noise = random.gauss(0, 3)

        t = round(min(max(current_scores["technical_score"] * factor + noise, 10), 100), 1)
        a = round(min(max(current_scores["aptitude_score"] * factor + noise, 10), 100), 1)
        c = round(min(max(current_scores["communication_score"] * factor + noise, 10), 100), 1)
        p = round(min(max(current_scores["project_score"] * factor + noise, 10), 100), 1)
        cert = round(min(max(current_scores["certifications_score"] * factor + noise, 10), 100), 1)
        m = round(min(max(current_scores["mock_interview_score"] * factor + noise, 10), 100), 1)
        acad = cgpa_to_score(current_scores["cgpa"])

        from services.scoring_service import calculate_readiness_score, get_readiness_level
        overall = calculate_readiness_score(t, a, c, p, current_scores["cgpa"], cert, m)
        level = get_readiness_level(overall)

        snapshots.append({
            "student_id": student_id,
            "recorded_at": date,
            "month_label": date.strftime("%b %Y"),
            "overall_score": overall,
            "readiness_level": level,
            "technical_score": t,
            "aptitude_score": a,
            "communication_score": c,
            "project_score": p,
            "academics_score": acad,
            "certifications_score": cert,
            "mock_interview_score": m,
        })

    return snapshots


def seed_database() -> None:
    """Main seeding entrypoint — idempotent: skips if data already exists."""
    # Always ensure tables exist before any query
    init_db()

    from services.student_service import count_students
    if count_students() > 0:
        logger.info("Database already seeded — skipping.")
        return

    logger.info("Seeding database with 150+ sample students...")

    student_records = []
    seq_counter: Dict[str, int] = {d: 1 for d in DEPARTMENTS}

    # Profile distribution: 15% star, 30% good, 35% average, 20% weak
    total = 160
    profiles = (
        ["star"] * 24 +
        ["good"] * 48 +
        ["average"] * 56 +
        ["weak"] * 32
    )
    random.shuffle(profiles)

    for i in range(total):
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        year = random.choice(GRAD_YEARS)
        seq = seq_counter[dept]
        seq_counter[dept] += 1

        name = _random_name()
        roll = _make_roll_no(dept, year, seq)
        email_user = name.lower().replace(" ", ".") + str(random.randint(10, 99))
        email = f"{email_user}@university.edu"

        profile = profiles[i % len(profiles)]
        scores = _gen_scores(profile)

        # Pick skills & certs for this department
        dept_skills = SKILLS_POOL.get(dept, SKILLS_POOL["Computer Science & Engineering"])
        dept_certs = CERT_POOL.get(dept, CERT_POOL["Computer Science & Engineering"])
        num_skills = random.randint(4, 8)
        num_certs = random.randint(1, 3) if profile in ("star", "good") else random.randint(0, 2)

        key_skills = ", ".join(random.sample(dept_skills, min(num_skills, len(dept_skills))))
        cert_list = "; ".join(random.sample(dept_certs, min(num_certs, len(dept_certs)))) if num_certs else ""
        tmpl = random.choice(PROJECT_TEMPLATES)
        domain = random.choice(DOMAINS)
        project_summary = tmpl.format(domain=domain)

        from services.scoring_service import calculate_readiness_score, get_readiness_level
        overall = calculate_readiness_score(
            scores["technical_score"], scores["aptitude_score"],
            scores["communication_score"], scores["project_score"],
            scores["cgpa"], scores["certifications_score"],
            scores["mock_interview_score"],
        )
        level = get_readiness_level(overall)

        student_records.append({
            "roll_no": roll,
            "full_name": name,
            "email": email,
            "department": dept,
            "graduation_year": year,
            "cgpa": scores["cgpa"],
            "technical_score": scores["technical_score"],
            "aptitude_score": scores["aptitude_score"],
            "communication_score": scores["communication_score"],
            "project_score": scores["project_score"],
            "certifications_score": scores["certifications_score"],
            "mock_interview_score": scores["mock_interview_score"],
            "overall_score": overall,
            "readiness_level": level,
            "key_skills": key_skills,
            "project_summary": project_summary,
            "certifications_list": cert_list,
            "profile": profile,
        })

    # Bulk insert students + history
    with get_db_session() as session:
        for rec in student_records:
            profile_tag = rec.pop("profile")
            overall = rec.pop("overall_score")
            level = rec.pop("readiness_level")

            s = Student(**{k: rec[k] for k in rec})
            s.overall_score = overall
            s.readiness_level = level
            session.add(s)
            session.flush()

            # 4-8 months of history
            n_months = random.randint(4, 8)
            comp_scores = {
                "technical_score": rec["technical_score"],
                "aptitude_score": rec["aptitude_score"],
                "communication_score": rec["communication_score"],
                "project_score": rec["project_score"],
                "certifications_score": rec["certifications_score"],
                "mock_interview_score": rec["mock_interview_score"],
                "cgpa": rec["cgpa"],
            }
            snapshots = _gen_history_snapshots(s.id, comp_scores, n_months)
            for snap in snapshots:
                session.add(ScoreHistory(**snap))

    logger.info(f"Inserted {total} students with history snapshots.")

    # --- Demo accounts ---
    _create_demo_accounts(student_records)
    logger.info("Demo accounts created: admin/admin123, student1/student123")


def _create_demo_accounts(student_records: list) -> None:
    """Create admin and one student demo login account."""
    from services.auth_service import create_user, get_user_by_username
    from services.student_service import get_student_by_roll_no

    # Admin account
    if not get_user_by_username("admin"):
        create_user(
            username="admin",
            email="admin@talentforge.edu",
            password="admin123",
            role="admin",
        )

    # Student demo account — link to the first CSE student
    if not get_user_by_username("student1"):
        # Find a CSE star or good student to be the demo
        demo_roll = None
        with get_db_session() as session:
            s = session.query(Student).filter(
                Student.department == "Computer Science & Engineering"
            ).order_by(Student.overall_score.desc()).first()
            if s:
                demo_id = s.id
                demo_roll = s.roll_no

        if demo_roll:
            with get_db_session() as session:
                s = session.query(Student).filter(Student.roll_no == demo_roll).first()
                create_user(
                    username="student1",
                    email="student1@talentforge.edu",
                    password="student123",
                    role="student",
                    student_id=s.id if s else None,
                )


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from utils.validators import setup_logging
    setup_logging()
    seed_database()
    print("Seeding complete.")
