import streamlit as st

from datetime import datetime
from src.recommender import score_job_match

def get_job_value(job, possible_keys, default="Not available"):
    """
    Safely get values from different Apify job result formats.
    Supports nested keys using dot notation.

    Examples:
    - salary.salaryText
    - location.formattedAddressShort
    - companyLinks.corporateWebsite
    """
    for key in possible_keys:
        keys = key.split(".")
        value = job

        for nested_key in keys:
            if isinstance(value, dict):
                value = value.get(nested_key)
            else:
                value = None
                break

        if value:
            return value

    return default


def format_date(date_value):
    """
    Convert ISO datetime like:
    2026-05-03T00:00:00.000

    into:
    May 03, 2026
    """

    if not date_value:
        return "Not listed"

    date_value = str(date_value).strip()

    # Keep natural text like "Just posted", "3 days ago"
    if "T" not in date_value:
        return date_value

    try:
        clean_value = date_value.replace("Z", "").split(".")[0]
        parsed_date = datetime.fromisoformat(clean_value)
        return parsed_date.strftime("%b %d, %Y")
    except ValueError:
        return date_value.split("T")[0]

def format_salary_amount(amount):
    """
    Format salary safely whether it is int, float, or string.
    """
    if amount is None:
        return None

    try:
        return f"{float(amount):,.0f}"
    except (ValueError, TypeError):
        return str(amount)


def get_job_location(job):
    """
    Get location from Global Jobs result format.
    """
    location = get_job_value(
        job,
        [
            "location.formattedAddressShort",
            "location.formattedAddressLong",
            "location.fullAddress",
            "location.city",
            "location",
            "jobLocation",
            "city",
            "place",
        ],
        "Location not listed",
    )

    if isinstance(location, dict):
        return (
            location.get("formattedAddressShort")
            or location.get("formattedAddressLong")
            or location.get("fullAddress")
            or location.get("city")
            or "Location not listed"
        )

    return location


def get_job_link(job):
    """
    Get best available job link.

    Priority:
    1. Direct job/apply links
    2. Platform URLs
    3. Company website fallback
    """
    return get_job_value(
        job,
        [
            "jobUrl",
            "job_url",
            "jobLink",
            "job_link",
            "applyUrl",
            "applyURL",
            "apply_url",
            "applyLink",
            "apply_link",
            "externalApplyLink",
            "external_apply_link",
            "platform_url",
            "official_url",
            "url",
            "link",
            "redirectUrl",
            "company_website",
            "companyWebsite",
            "companyLinks.corporateWebsite",
            "company_url",
            "companyUrl",
        ],
        "#",
    )


def get_company_link(job):
    """
    Get company website/company page if available.
    """
    return get_job_value(
        job,
        [
            "company_website",
            "companyWebsite",
            "companyLinks.corporateWebsite",
            "company_url",
            "companyUrl",
        ],
        "#",
    )


def get_salary_text(job):
    """
    Get salary from Global Jobs  result format.
    """
    indeed_salary = get_job_value(
        job,
        ["salary.salaryText"],
        None,
    )

    if indeed_salary:
        return indeed_salary

    salary_min = get_job_value(job, ["salary_minimum", "salaryMin"], None)
    salary_max = get_job_value(job, ["salary_maximum", "salaryMax"], None)
    salary_currency = get_job_value(job, ["salary_currency", "currency"], "")
    salary_period = get_job_value(job, ["salary_period", "salaryPeriod"], "")

    salary_min_text = format_salary_amount(salary_min)
    salary_max_text = format_salary_amount(salary_max)

    if salary_min_text and salary_max_text:
        return f"{salary_currency} {salary_min_text} - {salary_max_text} / {salary_period}"

    if salary_min_text:
        return f"{salary_currency} {salary_min_text}+ / {salary_period}"

    if salary_max_text:
        return f"Up to {salary_currency} {salary_max_text} / {salary_period}"

    return "Salary not listed"


def get_job_type_text(job):
    """
    Get job type from Global Jobs or Indeed format.
    """
    job_type = get_job_value(
        job,
        ["job_type", "jobType", "employmentType"],
        "Job type not listed",
    )

    if isinstance(job_type, list):
        return ", ".join(str(item) for item in job_type)

    return job_type


def get_remote_text(job):
    """
    Get remote / hybrid / onsite status.
    """
    work_from_home = get_job_value(
        job,
        ["work_from_home", "workFromHome"],
        None,
    )

    if work_from_home:
        return work_from_home

    is_remote = get_job_value(
        job,
        ["is_remote", "isRemote", "remote"],
        None,
    )

    if is_remote is True:
        return "Remote"

    if is_remote is False:
        return "On-site / Not remote"

    return "Remote status not listed"


def get_posted_text(job):
    """
    Get posted date / job age.
    """

    posted = get_job_value(
        job,
        [
            "posted_date",
            "postedDate",
            "datePublished",
            "age",
            "processed_at",
            "createdAt",
        ],
        None,
    )

    return format_date(posted)

def get_skills_text(job):
    """
    Get skills or job attributes.
    """
    skills = get_job_value(
        job,
        ["skills", "attributes", "requirements"],
        None,
    )

    if isinstance(skills, list):
        clean_items = []

        for item in skills[:8]:
            if isinstance(item, dict):
                label = item.get("label") or item.get("name") or item.get("value")
                if label:
                    clean_items.append(label)
            else:
                clean_items.append(str(item))

        return ", ".join(clean_items)

    if isinstance(skills, dict):
        return ", ".join(f"{key}: {value}" for key, value in skills.items())

    return skills




def display_jobs(jobs, source_name, resume_analysis=None):
    """
    Compact job card UI.
    """

    if not jobs:
        st.warning(f"No {source_name} jobs found.")
        return

    st.caption(f"Showing {len(jobs)} jobs from {source_name}")

    for job in jobs:
        title = get_job_value(
            job,
            ["title", "jobTitle", "positionName", "name"],
            "No title",
        )

        company = get_job_value(
            job,
            [
                "company_name",
                "companyName",
                "company",
                "organization",
                "source",
            ],
            "Unknown company",
        )

        platform = get_job_value(
            job,
            ["platform", "source"],
            source_name,
        )
        

        location = get_job_location(job)
        posted = get_posted_text(job)
        job_type = get_job_type_text(job)
        remote_status = get_remote_text(job)
        salary = get_salary_text(job)
        skills = get_skills_text(job)

        job_link = get_job_link(job)
        company_link = get_company_link(job)

        with st.container(border=True):
            st.markdown(f"### {title}")

            st.markdown(
                f"""
                **{company}** · {location}
                """
            )
            match = None
            if resume_analysis:
                match = score_job_match(resume_analysis, job)

            if match:
                st.markdown(
                    f"""
                    <div style="
                    display:inline-block;
                    background-color:#123524;
                    color:#7CFFB2;
                    padding:4px 10px;
                    border-radius:999px;
                    font-size:0.85rem;
                    font-weight:600;
                    margin-bottom:0.4rem;
                    ">
                    Match Score: {match["score"]}%
                    </div>
                    """,unsafe_allow_html=True,)
                with st.expander("Why this job is recommended"):
                    matched = ", ".join(match["matched_skills"]) or "No strong skill overlap found"
                    missing = ", ".join(match["missing_skills"]) or "No major missing skills detected"
                    st.markdown(f"**Matched skills:** {matched}")
                    st.markdown(f"**Missing skills:** {missing}")
                    st.markdown(f"**Reason:** {match['reason']}")

            st.markdown(
                f"""
                <div style="font-size: 0.85rem; line-height: 1.8;">
                    <span style="background-color:#132d1f; color:#39ff88; padding:3px 8px; border-radius:6px;">{platform}</span>
                    <span style="background-color:#111827; color:#d1d5db; padding:3px 8px; border-radius:6px;">{posted}</span>
                    <span style="background-color:#111827; color:#d1d5db; padding:3px 8px; border-radius:6px;">{job_type}</span>
                    <span style="background-color:#111827; color:#d1d5db; padding:3px 8px; border-radius:6px;">{remote_status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""
                    <div style="font-size:0.85rem; color:#9ca3af;">Salary</div>
                    <div style="font-size:1rem; font-weight:600;">{salary}</div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    f"""
                    <div style="font-size:0.85rem; color:#9ca3af;">Posted</div>
                    <div style="font-size:1rem; font-weight:600;">{posted}</div>
                    """,
                    unsafe_allow_html=True,
                )

            with col3:
                st.markdown(
                    f"""
                    <div style="font-size:0.85rem; color:#9ca3af;">Remote</div>
                    <div style="font-size:1rem; font-weight:600;">{remote_status}</div>
                    """,
                    unsafe_allow_html=True,
                )

            if skills:
                st.markdown(f"**Skills:** {skills}")

            button_col1, button_col2, spacer = st.columns([1, 1, 4])

            with button_col1:
                if job_link != "#":
                    st.link_button(
                        "🔗 View / Apply",
                        job_link,
                        use_container_width=True,
                    )

            with button_col2:
                if company_link != "#":
                    st.link_button(
                        "🏢 Company",
                        company_link,
                        use_container_width=True,
                    )


def normalize_jobs_for_csv(jobs, source_name, resume_analysis=None):
    """
    Convert raw job dictionaries into clean CSV rows.
    """

    rows = []

    for job in jobs:
        match = None

        if resume_analysis:
            match = score_job_match(resume_analysis, job)

        rows.append(
            {
                "source": source_name,
                "title": get_job_value(
                    job,
                    ["title", "jobTitle", "positionName", "name"],
                    "",
                ),
                "company": get_job_value(
                    job,
                    ["company_name", "companyName", "company", "organization", "source"],
                    "",
                ),
                "location": get_job_location(job),
                "posted": get_posted_text(job),
                "job_type": get_job_type_text(job),
                "remote": get_remote_text(job),
                "salary": get_salary_text(job),
                "job_link": get_job_link(job),
                "company_link": get_company_link(job),
                "skills": get_skills_text(job),
                "match_score": match["score"] if match else "",
                "matched_skills": ", ".join(match["matched_skills"]) if match else "",
                "missing_skills": ", ".join(match["missing_skills"]) if match else "",
                "why_recommended": match["reason"] if match else "",
            }
        )

    return rows
