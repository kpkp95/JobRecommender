from apify_client import ApifyClient
import os
from dotenv import load_dotenv, find_dotenv
import re

load_dotenv(find_dotenv())

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_TOKEN is missing. Add it to your .env file.")

apify_client = ApifyClient(APIFY_API_TOKEN)


GLOBAL_JOBS_ACTOR_ID = os.getenv(
    "GLOBAL_JOBS_ACTOR_ID"
)






def clean_run_input(run_input):
    """
    Remove empty values before sending input to Apify.
    Some actors may fail or behave strangely when they receive None or empty strings.
    """
    return {
        key: value
        for key, value in run_input.items()
        if value is not None and value != ""
    }

def split_search_keywords(search_query):
    """
    Convert Gemini's comma-separated keywords into clean individual searches.
    """

    if not search_query:
        return ["Data Engineer"]

    cleaned = search_query.replace("\n", " ").strip()

    keywords = [
        keyword.strip()
        for keyword in cleaned.split(",")
        if keyword.strip()
    ]

    cleaned_keywords = []

    for keyword in keywords:
        keyword = re.sub(r"\(.*?\)", "", keyword).strip()
        keyword = keyword.replace("EntryLevel", "Entry Level")

        if keyword:
            cleaned_keywords.append(keyword)

    # Trying stronger, broader searches first
    priority_keywords = []

    for keyword in cleaned_keywords:
        lower_keyword = keyword.lower()

        if any(term in lower_keyword for term in ["machine learning", "data", "python", "ai engineer", "ml"]):
            priority_keywords.append(keyword)

    final_keywords = priority_keywords or cleaned_keywords

    # Limit Apify calls so it does not get too slow/expensive
    return final_keywords[:3] or ["machine learning"]

def run_apify_actor(actor_id, run_input):
    """
    Run an Apify actor and return dataset items.
    """
    if not actor_id:
        raise ValueError("Actor ID is missing.")

    cleaned_input = clean_run_input(run_input)

    run = apify_client.actor(actor_id).call(
        run_input=cleaned_input,
    )

    jobs = list(
        apify_client
        .dataset(run["defaultDatasetId"])
        .iterate_items()
    )

    return jobs

def get_dedup_value(job, keys):
    """
    Safely get values for deduplication.
    """

    for key in keys:
        value = job.get(key)

        if value:
            if isinstance(value, dict):
                return str(value)
            return str(value)

    return ""

def deduplicate_jobs(jobs):
    """
    Remove duplicate jobs by title + company + location.
    """

    seen = set()
    unique_jobs = []

    for job in jobs:
        title = get_dedup_value(job,["title", "jobTitle", "positionName", "name"],
        ).lower().strip()
        company = get_dedup_value(
            job,["company_name", "companyName", "company", "organization", "source"],
        ).lower().strip()
        location = get_dedup_value(job,["location", "jobLocation", "city", "place"],).lower().strip()

        key = (title, company, location)

        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs



def fetch_global_jobs(
    search_query,
    rows=10,
    country="Canada",
    posted_since="1 month",
    remote_only=False,
    job_type="all",
    location=None,
    distance=200,
    currency="CAD",
):
    """
    Fetch jobs from Global / All-Source Apify actor.
    Tries multiple keywords, but keeps max_results >= 10 because the actor requires it.
    """
    rows = max(10, int(rows))
    keywords = split_search_keywords(search_query)

    all_jobs = []

    # Actor requires max_results >= 10
    rows_per_keyword = max(10, rows // max(1, len(keywords)))

    for keyword in keywords:
        run_input = {
            "keyword": keyword,
            "country": country,
            "max_results": rows_per_keyword,
            "posted_since": posted_since,
            "remote_only": remote_only,
            "job_type": job_type,
            "location": location,
            "distance": distance,
            "currency": currency,
        }

        jobs = run_apify_actor(
            actor_id=GLOBAL_JOBS_ACTOR_ID,
            run_input=run_input,
        )

        all_jobs.extend(jobs)

    unique_jobs = deduplicate_jobs(all_jobs)

    # Fallback if specific searches return nothing
    if not unique_jobs:
        fallback_input = {
            "keyword": "Data Engineer",
            "country": country,
            "max_results": max(10, rows),
            "posted_since": posted_since,
            "remote_only": remote_only,
            "job_type": job_type,
            "location": location,
            "distance": distance,
            "currency": currency,
        }

        fallback_jobs = run_apify_actor(
            actor_id=GLOBAL_JOBS_ACTOR_ID,
            run_input=fallback_input,
        )
        unique_jobs = deduplicate_jobs(fallback_jobs)

    return unique_jobs[:rows]

    



# Backward compatibility:
# If any old file still imports fetch_jobs(), it will still work.
def fetch_jobs(*args, **kwargs):
    return fetch_global_jobs(*args, **kwargs)