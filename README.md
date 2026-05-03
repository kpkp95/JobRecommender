# AI Job Recommender

AI Job Recommender is an AI-powered portfolio project that analyzes a resume PDF, identifies the candidate's strengths and skill gaps, generates a 30-day career roadmap, and recommends real-time jobs using an external job API.

The app uses **Gemini on Vertex AI** for resume analysis and **Apify Global / All-Source Jobs** for fetching job listings. It also adds a rule-based recommendation layer that shows match score, matched skills, missing skills, and a short explanation for why each job is recommended.

---

## Live Demo

Add your deployed Cloud Run URL here:

```text
https://ai-job-recommender-778318657000.us-central1.run.app
```

---

## Demo Usage Note

This deployed demo uses a free/trial Apify account, so job fetching may be limited by available Apify credits. If the free credits are exhausted, the resume analysis may still work, but real-time job recommendations may fail or return limited results until the Apify quota resets or more credits are added.

## Features

- Upload a resume PDF
- Extract resume text using PyMuPDF
- Analyze resume using Gemini / Vertex AI
- Generate resume snapshot, skill gap analysis, 30-day action plan, and job search keywords
- Fetch real-time job recommendations using Apify
- Display job title, company, location, salary, remote status, posted date, and links
- Show match score for each job
- Show matched skills and missing skills
- Explain why each job is recommended
- Paginate job results
- Export job recommendations to CSV
- Debug mode for inspecting raw job API results
- Deployed on Google Cloud Run

---

## Tech Stack

- Python
- Streamlit
- Google Gemini / Vertex AI
- Google Cloud Run
- Apify Client
- PyMuPDF
- Pandas
- python-dotenv

---

## Project Architecture

```text
Resume PDF
   ↓
Text extraction with PyMuPDF
   ↓
Gemini / Vertex AI resume analysis
   ↓
Extract job-search keywords
   ↓
Apify Global / All-Source Jobs API
   ↓
Job recommendation results
   ↓
Rule-based match score + matched/missing skills
   ↓
Streamlit UI + CSV export
```

---

## Project Structure

```text
AI-Job-Recommender-System/
│
├── app.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── README.md
├── .env.example
│
├── screenshots/
│   ├── resume-analysis.png
│   ├── job-recommendations.png
│   └── csv-export.png
│
└── src/
    ├── __init__.py
    ├── api_job.py
    ├── constant.py
    ├── helper.py
    ├── helper_gemini.py
    ├── prompts.py
    └── recommender.py
```

---

## How It Works

### 1. Resume Upload

The user uploads a resume PDF through the Streamlit interface.

### 2. Resume Text Extraction

The app uses PyMuPDF to extract raw text from the uploaded resume.

### 3. Resume Analysis with Gemini

Gemini analyzes the resume and generates a compact career-readiness report containing:

- Resume snapshot
- Top skills
- Strongest projects or experience
- Best-fit roles
- Key gaps
- 30-day action plan
- Job search keywords

### 4. Job Fetching

The extracted job keywords are sent to the Apify Global / All-Source Jobs actor. The app fetches jobs based on filters such as:

- Country
- City / location
- Posted since
- Remote only
- Job type
- Distance
- Currency

### 5. Recommendation Layer

The app compares known skills from the resume analysis with skills or attributes found in job data. It then calculates:

- Match score
- Matched skills
- Missing skills
- Recommendation reason

### 6. CSV Export

Fetched jobs are normalized into a clean table and can be downloaded as a CSV file.

---

## Environment Variables

Create a `.env` file locally:

```env
APIFY_API_TOKEN=your_apify_token_here
GLOBAL_JOBS_ACTOR_ID=your_global_jobs_actor_id_here

GEMINI_BACKEND=vertex
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

Do not push `.env` to GitHub.

Use `.env.example` for placeholder values:

```env
APIFY_API_TOKEN=your_apify_token_here
GLOBAL_JOBS_ACTOR_ID=your_global_jobs_actor_id_here

GEMINI_BACKEND=vertex
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/kpkp95/JobRecommender.git
cd AI-Job-Recommender-System
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Authenticate with Google Cloud

For local Vertex AI usage:

```bash
gcloud auth application-default login
gcloud config set project your_google_cloud_project_id
```

### 5. Run the App

```bash
streamlit run app.py
```

---

## Deployment on Google Cloud Run

This app can be deployed to Cloud Run using the included `Dockerfile`.

### 1. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Create a Service Account

```bash
gcloud iam service-accounts create ai-job-recommender-sa \
  --display-name="AI Job Recommender Cloud Run Service Account"
```

### 3. Grant Vertex AI Access

```bash
gcloud projects add-iam-policy-binding your_project_id \
  --member="serviceAccount:ai-job-recommender-sa@your_project_id.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 4. Store Apify Token in Secret Manager

```bash
echo "your_apify_token_here" | gcloud secrets create APIFY_API_TOKEN --data-file=-
```

Grant the Cloud Run service account access:

```bash
gcloud secrets add-iam-policy-binding APIFY_API_TOKEN \
  --member="serviceAccount:ai-job-recommender-sa@your_project_id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Deploy

```bash
gcloud run deploy ai-job-recommender \
  --source . \
  --region us-central1 \
  --service-account ai-job-recommender-sa@your_project_id.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your_project_id,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,GLOBAL_JOBS_ACTOR_ID=your_actor_id \
  --set-secrets APIFY_API_TOKEN=APIFY_API_TOKEN:latest
```

---

## Screenshots

Add screenshots inside the `screenshots/` folder.

### Resume Analysis

```text
screenshots/resume-analysis.png
```

### Job Recommendations

```text
screenshots/job-recommendations.png
```

### CSV Export

```text
screenshots/csv-export.png
```

Example markdown for screenshots:

```markdown
![Resume Analysis](screenshots/resume-analysis.png)

![Job Recommendations](screenshots/job-recommendations.png)

![CSV Export](screenshots/csv-export.png)
```

---

## Portfolio Highlights

This project demonstrates:

- LLM integration with Gemini / Vertex AI
- Resume parsing and prompt engineering
- Real-time API integration with Apify
- Cloud deployment using Google Cloud Run
- Secret management with Google Secret Manager
- Streamlit UI development
- Rule-based recommendation logic
- Match scoring and explainability
- CSV export and pagination
- Practical error handling for external APIs

---

## Current Limitations

- Match scoring is rule-based, not semantic.
- Job data depends on external Apify actor availability.
- The deployed demo uses limited Apify free/trial credits, so job fetching may stop working temporarily if the quota is exhausted.
- Some jobs may not include direct application links.
- Resume analysis quality depends on the PDF text extraction quality.
- No user authentication or saved job tracking yet.

---

## Future Improvements

- Add semantic job matching using embeddings
- Add resume optimization for a selected job
- Add cover letter generation
- Add saved jobs / application tracker
- Add database storage
- Add MCP tools so external AI clients can call the job search system
- Add Docker-based CI/CD pipeline
- Add stronger UI styling and analytics dashboard

---

## Disclaimer

This project is for educational and portfolio demonstration purposes. Job data is fetched from external APIs, so availability, completeness, and formatting may vary depending on the external data source.
