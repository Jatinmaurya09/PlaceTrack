# Company database with required skills + location + role type
COMPANIES = [
    {
        "name": "TCS",
        "logo": "🟦",
        "role": "Graduate Engineer Trainee",
        "role_type": "Software Developer",
        "package": "3.5 - 7 LPA",
        "location": "Pune · Hybrid",
        "required_skills": ["python", "java", "sql", "communication", "aptitude"],
        "min_cgpa": 6.0,
        "max_backlogs": 1,
    },
    {
        "name": "Infosys",
        "logo": "🟩",
        "role": "Systems Engineer",
        "role_type": "Software Developer",
        "package": "3.6 - 6.5 LPA",
        "location": "Bengaluru · On-site",
        "required_skills": ["java", "sql", "data structures", "communication"],
        "min_cgpa": 6.0,
        "max_backlogs": 1,
    },
    {
        "name": "Wipro",
        "logo": "🟨",
        "role": "Project Engineer",
        "role_type": "Software Developer",
        "package": "3.5 - 6 LPA",
        "location": "Hyderabad · Hybrid",
        "required_skills": ["java", "c", "sql", "communication"],
        "min_cgpa": 6.0,
        "max_backlogs": 2,
    },
    {
        "name": "Accenture",
        "logo": "🟪",
        "role": "Associate Software Engineer",
        "role_type": "Software Developer",
        "package": "4.5 - 6.5 LPA",
        "location": "Hyderabad · Hybrid",
        "required_skills": ["python", "sql", "web development", "react", "communication"],
        "min_cgpa": 6.5,
        "max_backlogs": 0,
    },
    {
        "name": "Cognizant",
        "logo": "🟦",
        "role": "Programmer Analyst Trainee",
        "role_type": "Software Developer",
        "package": "4 - 6.5 LPA",
        "location": "Chennai · On-site",
        "required_skills": ["java", "sql", "dbms", "spring boot", "teamwork"],
        "min_cgpa": 6.0,
        "max_backlogs": 1,
    },
    {
        "name": "Amazon",
        "logo": "🟧",
        "role": "SDE-1",
        "role_type": "Software Developer",
        "package": "18 - 32 LPA",
        "location": "Bangalore · On-site",
        "required_skills": ["data structures", "algorithms", "dsa", "problem solving",
                            "python", "java", "oop", "rest api"],
        "min_cgpa": 7.5,
        "max_backlogs": 0,
    },
    {
        "name": "Microsoft",
        "logo": "🔷",
        "role": "Software Engineer",
        "role_type": "Software Developer",
        "package": "20 - 40 LPA",
        "location": "Hyderabad · On-site",
        "required_skills": ["data structures", "algorithms", "dsa", "oop",
                            "problem solving", "cloud", "c++"],
        "min_cgpa": 8.0,
        "max_backlogs": 0,
    },
    {
        "name": "Flipkart",
        "logo": "🟨",
        "role": "SDE-1",
        "role_type": "Software Developer",
        "package": "16 - 24 LPA",
        "location": "Bangalore · On-site",
        "required_skills": ["data structures", "algorithms", "dsa", "sql",
                            "problem solving", "java"],
        "min_cgpa": 7.5,
        "max_backlogs": 0,
    },
    {
        "name": "Deloitte",
        "logo": "🟩",
        "role": "Analyst",
        "role_type": "Data Analyst",
        "package": "6 - 9 LPA",
        "location": "Mumbai · Hybrid",
        "required_skills": ["sql", "excel", "communication", "problem solving",
                            "tableau", "power bi"],
        "min_cgpa": 7.0,
        "max_backlogs": 0,
    },
    {
        "name": "Goldman Sachs",
        "logo": "🔵",
        "role": "Analyst",
        "role_type": "Data Analyst",
        "package": "20 - 30 LPA",
        "location": "Bangalore · On-site",
        "required_skills": ["python", "sql", "data structures", "algorithms",
                            "problem solving", "communication"],
        "min_cgpa": 8.0,
        "max_backlogs": 0,
    },
    {
        "name": "Zoho",
        "logo": "🟥",
        "role": "Member Technical Staff",
        "role_type": "Software Developer",
        "package": "5 - 9 LPA",
        "location": "Chennai · On-site",
        "required_skills": ["java", "sql", "html", "css", "javascript",
                            "problem solving"],
        "min_cgpa": 6.5,
        "max_backlogs": 0,
    },
    {
        "name": "Freshworks",
        "logo": "🟢",
        "role": "Software Engineer",
        "role_type": "Software Developer",
        "package": "8 - 14 LPA",
        "location": "Chennai · Hybrid",
        "required_skills": ["javascript", "react", "node", "sql",
                            "rest api", "git"],
        "min_cgpa": 7.0,
        "max_backlogs": 0,
    },
    {
        "name": "Tata Elxsi",
        "logo": "🟫",
        "role": "Software Engineer",
        "role_type": "Software Developer",
        "package": "4 - 7 LPA",
        "location": "Bangalore · On-site",
        "required_skills": ["c", "c++", "linux", "embedded", "communication"],
        "min_cgpa": 6.5,
        "max_backlogs": 0,
    },
    {
        "name": "Mu Sigma",
        "logo": "🟪",
        "role": "Decision Scientist",
        "role_type": "Data Analyst",
        "package": "5 - 8 LPA",
        "location": "Bangalore · On-site",
        "required_skills": ["python", "sql", "statistics", "excel", "problem solving"],
        "min_cgpa": 7.0,
        "max_backlogs": 0,
    },
    {
        "name": "L&T Infotech",
        "logo": "🟦",
        "role": "Graduate Engineer Trainee",
        "role_type": "Software Developer",
        "package": "4 - 6 LPA",
        "location": "Mumbai · On-site",
        "required_skills": ["java", "sql", "html", "communication", "dbms"],
        "min_cgpa": 6.0,
        "max_backlogs": 1,
    },
]


def _skill_level_to_keywords(dsa_level, coding_practice, internship, projects):
    """Convert form data → skill keywords"""
    skills = set()

    if dsa_level == "Advanced":
        skills.update(["dsa", "data structures", "algorithms"])
    elif dsa_level == "Intermediate":
        skills.update(["dsa", "data structures"])

    if coding_practice == "Regularly":
        skills.update(["problem solving", "python", "java"])
    elif coding_practice == "Occasionally":
        skills.add("python")

    if internship == "Yes":
        skills.update(["communication", "teamwork", "problem solving"])

    if projects >= 3:
        skills.update(["oop", "git", "github"])

    skills.update(["communication", "aptitude"])

    return skills


def match_companies(student_skills, cgpa, backlogs, dsa_level="", coding_practice="",
                    internship="", projects=0, role_filter="", location_filter="",
                    min_match=0):
    """
    Match companies based on skill overlap, CGPA, backlogs + filters.
    """
    all_skills = set(s.lower().strip() for s in student_skills if s)
    all_skills |= _skill_level_to_keywords(dsa_level, coding_practice, internship, projects)

    results = []

    for comp in COMPANIES:
        # Role filter
        if role_filter and role_filter != "All Roles":
            if comp["role_type"] != role_filter:
                continue

        # Location filter
        if location_filter and location_filter != "All locations":
            if location_filter.lower() not in comp["location"].lower():
                continue

        req = set(comp["required_skills"])
        matched = req & all_skills
        missing = req - all_skills

        skill_score = (len(matched) / len(req) * 100) if req else 0

        eligible = (cgpa >= comp["min_cgpa"]) and (backlogs <= comp["max_backlogs"])
        final_score = skill_score if eligible else skill_score * 0.3

        # Minimum match filter
        if final_score < min_match:
            continue

        results.append({
            "name": comp["name"],
            "logo": comp["logo"],
            "role": comp["role"],
            "role_type": comp["role_type"],
            "package": comp["package"],
            "location": comp["location"],
            "skill_score": round(skill_score, 1),
            "final_score": round(final_score, 1),
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing),
            "eligible": eligible,
            "min_cgpa": comp["min_cgpa"],
            "max_backlogs": comp["max_backlogs"],
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results


def get_role_types():
    return ["All Roles", "Software Developer", "Data Analyst"]


def get_locations():
    return ["All locations", "Bangalore", "Hyderabad", "Chennai", "Pune", "Mumbai"]