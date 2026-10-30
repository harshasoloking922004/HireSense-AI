# 🚀 HireSense AI – AI-Powered Resume Screening & Job Matching Platform

HireSense AI is an intelligent recruitment platform that uses Machine Learning to analyze resumes, calculate AI-based resume scores, match candidates with job requirements, identify skill gaps, and recommend suitable jobs. It helps recruiters rank candidates and manage job postings while helping job seekers discover relevant career opportunities.

## 🌟 Key Features

### 👨‍💻 Candidate Features
- Candidate registration and login.
- Upload resumes in PDF and DOCX formats.
- AI-powered resume analysis and scoring.
- Automatic job role classification.
- Browse available job opportunities.
- AI-based job matching percentage.
- Identify matching and missing skills.
- Skill gap analysis.
- Recommended job opportunities.
- Apply for available jobs.

### 🏢 Recruiter Features
- Recruiter registration and login.
- Recruiter dashboard.
- Post new job vacancies.
- Manage posted jobs.
- Edit and delete job postings.
- View candidate information.
- AI-based candidate ranking.
- Analyze candidate skills and experience.
- Compare candidate resumes with job requirements.

## 🧠 Machine Learning Features

HireSense AI integrates Machine Learning models to improve the recruitment process.

- **Resume Scoring:** Predicts a resume score based on skills, experience, education, certifications, projects, and job role.
- **Job Role Classification:** Predicts the suitable job category from resume information.
- **Job Matching:** Compares candidate skills with employer requirements.
- **Candidate Ranking:** Ranks candidates using job match scores and AI resume scores.
- **Skill Gap Analysis:** Identifies missing skills required for a particular job.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| HTML5 | Web page structure |
| CSS3 | Website styling |
| JavaScript | Frontend interactions |
| MongoDB Atlas | Database |
| PyMongo | MongoDB connectivity |
| Pandas | Data processing |
| Scikit-learn | Machine Learning |
| Joblib | Saving and loading ML models |
| PyPDF | PDF text extraction |
| Python-docx | DOCX text extraction |

## 📂 Project Structure

```text
HireSense-AI/
│
├── app.py
├── .env
├── requirements.txt
│
├── models/
│   ├── ai_resume_pipeline.pkl
│   ├── ai_resume_score_model.pkl
│   ├── job_role_classifier.pkl
│   └── resume_preprocessor.pkl
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── candidate_dashboard.html
│   ├── recruiter_dashboard.html
│   ├── resume_upload.html
│   ├── resume_analysis.html
│   ├── available_jobs.html
│   ├── manage_jobs.html
│   ├── job_post.html
│   ├── job_match_result.html
│   ├── skill_gap.html
│   └── recommended_jobs.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
```

*The structure above is illustrative; adjust it to match your actual project folders.*

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/HireSense-AI.git
```

### 2. Navigate to the Project Folder

```bash
cd HireSense-AI
```

### 3. Install Required Packages

```bash
py -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

```env
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key
```

Replace the placeholder values with your own configuration. Never upload your actual database credentials or secret key to GitHub.

### 5. Run the Application

```bash
py app.py
```

### 6. Open in Browser

```text
http://127.0.0.1:5000/
```

## 🗄️ Database

HireSense AI uses MongoDB Atlas for storing application data.

Database name:

```text
HireSenseDB
```

Collections:

- `users` – Candidate and recruiter information.
- `resumes` – Uploaded resume information and analysis results.
- `jobs` – Recruiter job postings.
- `applications` – Candidate job applications and their statuses.

## 📊 Project Workflow

1. Candidates and recruiters register and log in.
2. Candidates upload their resumes.
3. The system extracts resume information.
4. Machine Learning models analyze the resume.
5. Candidates receive AI resume scores and job role predictions.
6. The platform compares resumes with available job requirements.
7. Candidates explore matching jobs and apply.
8. Recruiters post jobs and view suitable candidates.
9. AI ranking helps recruiters compare candidates.

## 🔮 Future Enhancements

- AI-powered resume recommendations.
- Direct job application integration.
- Advanced recruiter analytics dashboard.
- Email notifications for application updates.
- Interview scheduling system.
- Advanced NLP-based resume understanding.
- Improved candidate ranking algorithms.

## 🎯 Project Objective

The main objective of HireSense AI is to simplify and improve the recruitment process using Artificial Intelligence and Machine Learning. It aims to reduce manual resume screening, improve candidate-job matching, and help recruiters make more informed hiring decisions.

## 👨‍💻 Project Information

**Project Name:** HireSense AI

**Category:** Artificial Intelligence / Machine Learning / Web Development

**Domain:** Intelligent Recruitment and HR Technology

**Developer:** Harsha Vardhan

---

⭐ If you find this project interesting, consider giving the repository a star!