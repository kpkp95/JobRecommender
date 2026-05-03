import streamlit as st
import pandas as pd
from src.helper_gemini import (
    extract_text_from_pdf,
    analyze_resume_with_gemini,
    extract_job_keywords,
)

from src.api_job import fetch_global_jobs
from src.helper import display_jobs, normalize_jobs_for_csv
# ----------------------------
# Page config
# ----------------------------

st.set_page_config(
    page_title="AI Job Recommender",
    layout="wide",
)


st.title("📄 AI Job Recommender")
st.markdown(
    "Upload your resume and get AI-powered resume analysis, skill gap suggestions, "
    "career roadmap, and real-time job recommendations."
)

# ----------------------------
# Helper functions
# ----------------------------
def reset_resume_analysis():
    """
    Reset stored resume analysis when a new file is uploaded
    or when user manually wants to re-analyze.
    """

    st.session_state.resume_analysis_done = False
    st.session_state.resume_text = ""
    st.session_state.resume_analysis = ""
    st.session_state.job_keywords = ""
    st.session_state.global_jobs = []
    st.session_state.jobs_loaded = False
    st.session_state.job_page = 1
# ----------------------------
# Session state initialization
# ----------------------------

if "resume_analysis_done" not in st.session_state:
    st.session_state.resume_analysis_done = False

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_analysis" not in st.session_state:
    st.session_state.resume_analysis = ""

if "job_keywords" not in st.session_state:
    st.session_state.job_keywords = ""

if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None

if "global_jobs" not in st.session_state:
    st.session_state.global_jobs = []

if "jobs_loaded" not in st.session_state:
    st.session_state.jobs_loaded = False

if "job_page" not in st.session_state:
    st.session_state.job_page = 1

# ----------------------------
# Sidebar settings
# ----------------------------
st.sidebar.header("Search Filters")

rows = st.sidebar.slider(
    "Number of jobs",
    min_value=10,
    max_value=60,
    value=20,
    step=10,
)

country = st.sidebar.selectbox(
    "Job country",
    ["Canada", "United States", "United Kingdom", "India"],
    index=0,
)

location = st.sidebar.text_input(
    "City / location",
    value="Toronto",
)

posted_since = st.sidebar.selectbox(
    "Posted since",
    ["24 hours", "1 week", "1 month", "6 months"],
    index=1,
)

remote_only = st.sidebar.checkbox("Remote only", value=False)

job_type = st.sidebar.selectbox(
    "Job type",
    ["all", "fulltime", "parttime", "contract", "internship"],
    index=0,
)

distance = st.sidebar.slider(
    "Search distance",
    min_value=25,
    max_value=300,
    value=50,
    step=25,
)

currency = st.sidebar.selectbox(
    "Salary currency",
    ["USD", "CAD", "GBP", "INR"],
    index=1,
)
debug_mode = st.sidebar.checkbox("Debug mode", value=False)
# ----------------------------
# Resume upload
# ----------------------------

uploaded_file = st.file_uploader(
    "Upload your resume PDF",
    type=["pdf"],
)


if not uploaded_file:
    st.info("Please upload your resume PDF to start the analysis.")
    st.stop()


current_file_id = f"{uploaded_file.name}-{uploaded_file.size}"

if st.session_state.uploaded_file_id != current_file_id:
    st.session_state.uploaded_file_id = current_file_id
    reset_resume_analysis()


if st.button("Re-analyze Resume"):
    reset_resume_analysis()
    st.rerun()

# ----------------------------
# Resume analysis
# ----------------------------

if not st.session_state.resume_analysis_done:
    try:
        with st.spinner("Extracting text from your resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if not resume_text:
            st.error("Could not extract text from this PDF. Try another resume file.")
            st.stop()

        with st.spinner("Analyzing your resume with Gemini..."):
            resume_analysis = analyze_resume_with_gemini(
                resume_text,
                max_tokens=3000,
            )

        st.session_state.resume_text = resume_text
        st.session_state.resume_analysis = resume_analysis
        st.session_state.resume_analysis_done = True

    except Exception as e:
        st.error("Something went wrong while analyzing your resume.")
        st.exception(e)
        st.stop()


resume_analysis = st.session_state.resume_analysis


# ----------------------------
# Display resume analysis
# ----------------------------

st.markdown("---")
st.markdown(resume_analysis)

st.success("✅ Resume analysis completed successfully!")


# ----------------------------
# Job recommendation section
# ----------------------------

st.markdown("---")
st.header("🔎 Job Recommendations")

st.info(
    "Using Global / All-Source Jobs. "
    "This source may include jobs from platforms like Indeed and may provide platform, job, or company links."
)

if st.button("Get Job Recommendations"):
    if "quota" in resume_analysis.lower() or "rate limit" in resume_analysis.lower():
        st.error(
            "Cannot generate job recommendations because Gemini quota/rate limit was reached during resume analysis."
        )
        st.stop()

    with st.spinner("Extracting job search keywords..."):
        search_keywords_clean = extract_job_keywords(resume_analysis)

    if not search_keywords_clean:
        st.error("Could not extract job keywords.")
        st.stop()

    st.session_state.job_keywords = search_keywords_clean

    st.success(f"Extracted job keywords: {search_keywords_clean}")

    global_jobs = []

    try:
        with st.spinner("Fetching Global / All-Source jobs..."):
            global_jobs = fetch_global_jobs(
                search_query=search_keywords_clean,
                rows=rows,
                country=country,
                posted_since=posted_since,
                remote_only=remote_only,
                job_type=job_type,
                location=location,
                distance=distance,
                currency=currency,
            )
        st.session_state.global_jobs = global_jobs
        st.session_state.jobs_loaded = True
        st.session_state.job_page = 1
        
    

    except Exception as e:
        st.warning(
        "Job recommendations are currently unavailable. "
        "Please try again later or adjust your search filters."
        )
        print(f"Global job fetch failed: {e}")
        st.stop()

    # ----------------------------
# Display paginated jobs
# ----------------------------

if st.session_state.jobs_loaded:
    global_jobs = st.session_state.global_jobs

    st.markdown("---")
    st.subheader("🌍 Global / All-Source Jobs")

    if debug_mode:
        st.write(f"Jobs fetched: {len(global_jobs)}")

        if global_jobs:
            with st.expander("Debug: first raw job"):
                st.json(global_jobs[0])

    if not global_jobs:
        st.warning(
            "No matching jobs found. Try a broader keyword, larger distance, "
            "or longer posted-since filter."
        )
        st.stop()

    jobs_per_page = 10
    total_jobs = len(global_jobs)
    total_pages = max(1, (total_jobs + jobs_per_page - 1) // jobs_per_page)

    if st.session_state.job_page > total_pages:
        st.session_state.job_page = total_pages

    start_index = (st.session_state.job_page - 1) * jobs_per_page
    end_index = start_index + jobs_per_page

    current_jobs = global_jobs[start_index:end_index]

    st.caption(
        f"Showing jobs {start_index + 1}-{min(end_index, total_jobs)} of {total_jobs}"
    )

    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if st.button(
            "⬅️ Previous",
            disabled=st.session_state.job_page <= 1,
            use_container_width=True,
        ):
            st.session_state.job_page -= 1
            st.rerun()

    with nav_col2:
        st.markdown(
            f"""
            <div style="text-align:center; padding-top:0.5rem;">
                Page {st.session_state.job_page} of {total_pages}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav_col3:
        if st.button(
            "Next ➡️",
            disabled=st.session_state.job_page >= total_pages,
            use_container_width=True,
        ):
            st.session_state.job_page += 1
            st.rerun()
    csv_rows = normalize_jobs_for_csv(
        global_jobs,
        "Global",
        resume_analysis=resume_analysis,
    )

    if csv_rows:
        jobs_df = pd.DataFrame(csv_rows)

        st.download_button(
            label="⬇️ Download Jobs as CSV",
            data=jobs_df.to_csv(index=False),
            file_name="job_recommendations.csv",
            mime="text/csv",
            use_container_width=True,
        )
    display_jobs(current_jobs, "Global",resume_analysis=resume_analysis,)