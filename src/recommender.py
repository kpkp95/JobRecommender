import re
from src.constant import SKILL_KEYWORDS, FIELDS





def normalize_text(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9+#. ]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def flatten_value(value):
    """
    Convert nested job fields into readable text.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(flatten_value(item) for item in value)

    if isinstance(value, dict):
        return " ".join(flatten_value(item) for item in value.values())

    return str(value)


def build_job_text(job):
    """
    Combine useful job fields into one text block for matching.
    """

   
    parts = []

    for field in FIELDS:
        if field in job:
            parts.append(flatten_value(job.get(field)))

    return normalize_text(" ".join(parts))


def extract_known_skills(text):
    """
    Extract known skill keywords from text.
    """

    text = normalize_text(text)

    found = set()

    for skill in SKILL_KEYWORDS:
        if skill in text:
            found.add(skill.title())

    return found


def score_job_match(resume_analysis, job):
    """
    Rule-based job match scoring.

    Returns:
        dict with score, matched_skills, missing_skills, and reason.
    """

    resume_skills = extract_known_skills(resume_analysis)
    job_text = build_job_text(job)
    job_skills = extract_known_skills(job_text)

    matched_skills = sorted(resume_skills.intersection(job_skills))
    missing_skills = sorted(job_skills.difference(resume_skills))

    if job_skills:
        raw_score = int((len(matched_skills) / len(job_skills)) * 100)
    else:
        raw_score = 50

    # Keep scores realistic for portfolio demo
    if matched_skills:
        score = max(55, min(raw_score, 95))
    else:
        score = max(35, min(raw_score, 60))

    if matched_skills:
        reason = (
            "This role is recommended because your resume shows alignment with "
            f"{', '.join(matched_skills[:4])}."
        )
    else:
        reason = (
            "This role may still be relevant based on the job title and search keywords, "
            "but the job data did not expose many clear matching skills."
        )

    return {
        "score": score,
        "matched_skills": matched_skills[:8],
        "missing_skills": missing_skills[:8],
        "reason": reason,
    }