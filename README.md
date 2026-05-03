# AI Job Recommender

An AI-powered job recommendation app that analyzes a resume PDF, identifies skills and gaps, generates a career roadmap, and recommends real-time jobs using external job APIs.

## Features

- Upload resume PDF
- Extract resume text using PyMuPDF
- Analyze resume using Gemini / Vertex AI
- Generate resume snapshot, skill gaps, roadmap, and job keywords
- Fetch real-time jobs using Apify
- Display salary, posted date, remote status, job link, and company link
- Show job match score
- Show matched and missing skills
- Explain why each job is recommended
- Export job recommendations as CSV
- Paginated job results

## Tech Stack

- Python
- Streamlit
- Google Gemini / Vertex AI
- PyMuPDF
- Apify
- Pandas

## Project Structure

```text
ai-job-recommender/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── api_job.py
│   ├── helper_gemini.py
│   ├── job_display.py
│   └── recommender.py
└── screenshots/
```

## Environment Variables

APIFY_API_TOKEN=your_apify_token_here
GLOBAL_JOBS_ACTOR_ID=actor_id_for_global_jobs

GEMINI_BACKEND=vertex
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

## Run Locally

pip install -r requirements.txt
streamlit run app.py

## Disclaimer

This project uses external job data APIs and is intended for educational and portfolio demonstration purposes.
