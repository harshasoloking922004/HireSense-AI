from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime

import os
import re
import joblib
import pandas as pd


# ============================================================
# PATHS AND ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

app.secret_key = "hiresense-development-secret-key"

mongo_uri = os.getenv("MONGO_URI")

print("MONGO_URI loaded:", bool(mongo_uri))


# ============================================================
# MONGODB
# ============================================================

try:

    if not mongo_uri:
        raise ValueError("MONGO_URI was not found in .env")

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    print("✅ MongoDB connection successful")

    db = client["HireSenseDB"]

    users_collection = db["users"]
    resumes_collection = db["resumes"]
    jobs_collection = db["jobs"]
    applications_collection = db["applications"]

    print("✅ Database:", db.name)
    print("✅ Users collection:", users_collection.name)
    print("✅ Resumes collection:", resumes_collection.name)
    print("✅ Jobs collection:", jobs_collection.name)
    print(
        "✅ Applications collection:",
        applications_collection.name
    )
    try:
        applications_collection.create_index(
            [
                ("candidate_id", 1),
                ("job_id", 1)
            ],
            unique=True
        )

    except Exception as e:
        print(
            "⚠️ Applications unique index could not be created:"
        )
        print(e)
except Exception as e:

    print("❌ MongoDB connection failed:")
    print(e)

    raise SystemExit(
        "Application stopped because MongoDB connection failed."
    )


# ============================================================
# LOAD TRAINED AI MODELS
# ============================================================

try:

    score_pipeline = joblib.load(
        BASE_DIR / "models" / "ai_resume_pipeline.pkl"
    )

    job_role_classifier = joblib.load(
        BASE_DIR / "models" / "job_role_classifier.pkl"
    )

    print("✅ AI resume score pipeline loaded")
    print("✅ Job role classifier loaded")

except Exception as e:

    print("❌ AI model loading failed:")
    print(e)

    raise SystemExit(
        "Application stopped because AI models could not be loaded."
    )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        role = request.form.get("role", "").strip().lower()


        if not name or not email or not password or not role:

            return """
            <h1>Registration Failed ❌</h1>
            <p>All fields are required.</p>
            <a href="/register">Try Again</a>
            """


        if role not in ["candidate", "recruiter"]:

            return """
            <h1>Invalid Role ❌</h1>
            <a href="/register">Try Again</a>
            """


        try:

            existing_user = users_collection.find_one({
                "email": email
            })


            if existing_user:

                return """
                <h1>User Already Exists</h1>
                <p>This email is already registered.</p>
                <a href="/login">Go to Login</a>
                """


            result = users_collection.insert_one({

                "name": name,

                "email": email,

                "password": password,

                "role": role

            })


            print("✅ User inserted!")

            print(
                "Inserted ID:",
                result.inserted_id
            )


            return """
            <h1>Registration Successful ✅</h1>

            <p>Your account has been saved to MongoDB.</p>

            <a href="/login">
                Go to Login
            </a>
            """


        except Exception as e:

            print("❌ Registration failed:")

            print(e)


            return """
            <h1>Registration Failed ❌</h1>

            <p>Could not create your account.</p>

            <a href="/register">
                Try Again
            </a>
            """


    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            ""
        ).strip().lower()


        user = users_collection.find_one({

            "email": email,

            "password": password,

            "role": role

        })


        if user:

            session["user_id"] = str(
                user["_id"]
            )

            session["name"] = user["name"]

            session["email"] = user["email"]

            session["role"] = user["role"]


            if role == "candidate":

                return redirect(
                    url_for(
                        "candidate_dashboard"
                    )
                )


            if role == "recruiter":

                return redirect(
                    url_for(
                        "recruiter_dashboard"
                    )
                )


        return """
        <h1>Login Failed ❌</h1>

        <p>
        Invalid email, password, or role.
        </p>

        <a href="/login">
            Try Again
        </a>
        """


    return render_template("login.html")


# ============================================================
# CANDIDATE DASHBOARD
# ============================================================

@app.route("/candidate-dashboard")
def candidate_dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )


    return render_template(

        "candidate_dashboard.html",

        name=session.get("name")

    )


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.route(
    "/upload-resume",
    methods=["GET", "POST"]
)
def upload_resume():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        resume = request.files.get(
            "resume"
        )


        if not resume or not resume.filename:

            return """
            <h1>No Resume Selected ❌</h1>

            <a href="/upload-resume">
                Try Again
            </a>
            """


        filename = secure_filename(
            resume.filename
        )


        allowed_extensions = [
            ".pdf",
            ".docx"
        ]


        extension = os.path.splitext(
            filename
        )[1].lower()


        if extension not in allowed_extensions:

            return """
            <h1>Invalid File Type ❌</h1>

            <p>
            Only PDF and DOCX files are allowed.
            </p>

            <a href="/upload-resume">
                Try Again
            </a>
            """


        upload_folder = BASE_DIR / "uploads"

        upload_folder.mkdir(
            parents=True,
            exist_ok=True
        )


        file_path = upload_folder / filename


        resume.save(file_path)


        resumes_collection.insert_one({

            "user_id":
                session["user_id"],

            "name":
                session["name"],

            "email":
                session["email"],

            "filename":
                filename,

            "file_path":
                str(file_path)

        })


        return """
        <h1>Resume Uploaded Successfully ✅</h1>

        <p>
        Your resume has been saved.
        </p>

        <a href="/candidate-dashboard">
            Go to Candidate Dashboard
        </a>
        """


    return render_template(

        "resume_upload.html",

        name=session.get("name")

    )


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_resume_text(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()


    # -------------------------
    # PDF
    # -------------------------

    if extension == ".pdf":

        reader = PdfReader(
            file_path
        )

        text = ""


        for page in reader.pages:

            page_text = page.extract_text()


            if page_text:

                text += (
                    page_text +
                    "\n"
                )


        return text


    # -------------------------
    # DOCX
    # -------------------------

    if extension == ".docx":

        document = Document(
            file_path
        )

        text = []


        for paragraph in document.paragraphs:

            value = paragraph.text.strip()


            if value:

                text.append(value)


        return "\n".join(text)


    return ""


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text):

    skills_database = [

        "python",
        "java",
        "c++",
        "c",
        "javascript",
        "html",
        "css",
        "react",
        "node.js",
        "flask",
        "django",
        "sql",
        "mongodb",
        "mysql",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "data analysis",
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "docker",
        "git",
        "github",
        "aws",
        "power bi",
        "tableau"

    ]


    text_lower = text.lower()

    found_skills = []


    # Check longer skills first
    # to avoid c being selected inside c++

    skills_database.sort(
        key=len,
        reverse=True
    )


    for skill in skills_database:

        pattern = (
            r"(?<!\w)"
            + re.escape(skill)
            + r"(?!\w)"
        )


        if re.search(
            pattern,
            text_lower
        ):

            found_skills.append(
                skill
            )


    return sorted(
        set(found_skills)
    )


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience(text):

    text_lower = text.lower()


    patterns = [

        r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+of\s+experience',

        r'experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)',

        r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)'

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text_lower
        )


        if match:

            return float(
                match.group(1)
            )


    return 0.0


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def extract_education(text):

    text_lower = text.lower()


    education_keywords = [

        "phd",
        "doctorate",

        "m.tech",
        "mtech",
        "master of technology",

        "m.e",
        "master of engineering",

        "mba",
        "mca",

        "m.sc",
        "msc",
        "master's",
        "masters",

        "b.tech",
        "btech",

        "b.e",
        "be degree",

        "bachelor of engineering",
        "bachelor of technology",

        "bca",

        "b.sc",
        "bsc",

        "bachelor's",
        "bachelors",

        "diploma"

    ]


    for education in education_keywords:

        if education in text_lower:

            return education


    return "Unknown"


# ============================================================
# CERTIFICATION EXTRACTION
# ============================================================

def extract_certifications(text):

    text_lower = text.lower()


    certification_keywords = [

        "aws certified",

        "microsoft certified",

        "azure certification",

        "google cloud certification",

        "google certified",

        "oracle certified",

        "cisco certified",

        "python certification",

        "java certification",

        "machine learning certification",

        "data science certification",

        "certification",

        "certified"

    ]


    found = []


    for certification in certification_keywords:

        if certification in text_lower:

            found.append(
                certification
            )


    if found:

        return ", ".join(
            sorted(set(found))[:5]
        )


    return "None"


# ============================================================
# PROJECT COUNT EXTRACTION
# ============================================================

def extract_projects_count(text):

    text_lower = text.lower()


    patterns = [

        r'(\d+)\s*\+?\s*projects?',

        r'(\d+)\s*\+?\s*academic projects?',

        r'(\d+)\s*\+?\s*personal projects?'

    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text_lower
        )


        if match:

            return int(
                match.group(1)
            )


    # Fallback:
    # count project-like lines in a Projects section

    section_match = re.search(

        r'projects?\s*(.*?)(?:'
        r'experience|'
        r'education|'
        r'certifications?|'
        r'skills|'
        r'achievements|'
        r'$)',

        text_lower,

        re.DOTALL

    )


    if section_match:

        lines = [

            line.strip()

            for line in
            section_match.group(1).split("\n")

            if line.strip()

        ]


        if lines:

            return min(
                len(lines),
                10
            )


    return 0


# ============================================================
# AI RESUME SCORE
# ============================================================

def predict_resume_score(
    text,
    skills,
    job_role
):

    experience = extract_experience(
        text
    )

    education = extract_education(
        text
    )

    certifications = extract_certifications(
        text
    )

    projects = extract_projects_count(
        text
    )


    model_input = pd.DataFrame([{

        "Skills": ", ".join(skills),

        "Experience (Years)": experience,

        "Education": education,

        "Certifications": certifications,

        "Job Role": job_role,

        "Projects Count": projects

    }])


    print("\n========== MODEL INPUT ==========")

    print(
        model_input.to_string(
            index=False
        )
    )


    prediction = score_pipeline.predict(
        model_input
    )


    score = float(
        prediction[0]
    )


    # Keep displayed score between 0 and 100

    score = max(
        0.0,
        min(100.0, score)
    )


    return {

        "score":
            round(score, 2),

        "experience":
            experience,

        "education":
            education,

        "certifications":
            certifications,

        "projects":
            projects

    }


# ============================================================
# ANALYZE RESUME
# ============================================================

@app.route("/analyze-resume")
def analyze_resume():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )


    # Get latest resume

    resume = resumes_collection.find_one(

        {
            "user_id":
                session["user_id"]
        },

        sort=[
            ("_id", -1)
        ]

    )


    if not resume:

        return """
        <h1>No Resume Found ❌</h1>

        <p>
        Please upload your resume first.
        </p>

        <a href="/upload-resume">
            Upload Resume
        </a>
        """


    file_path = resume["file_path"]


    if not os.path.exists(file_path):

        return """
        <h1>Resume File Not Found ❌</h1>

        <p>
        Please upload the resume again.
        </p>

        <a href="/upload-resume">
            Upload Resume
        </a>
        """


    try:

        # ------------------------------------------------
        # 1. EXTRACT TEXT
        # ------------------------------------------------

        text = extract_resume_text(
            file_path
        )


        if not text.strip():

            return """
            <h1>Could Not Extract Resume Text ❌</h1>

            <p>
            Please upload a text-based PDF or DOCX resume.
            </p>
            """


        # ------------------------------------------------
        # 2. EXTRACT SKILLS
        # ------------------------------------------------

        skills = extract_skills(
            text
        )


        # ------------------------------------------------
        # 3. PREDICT JOB CATEGORY
        # ------------------------------------------------

        predicted_role = job_role_classifier.predict(
            [text]
        )[0]


        role_confidence = None


        if hasattr(
            job_role_classifier,
            "predict_proba"
        ):

            probabilities = (
                job_role_classifier
                .predict_proba([text])[0]
            )

            role_confidence = round(
                float(
                    max(probabilities)
                ) * 100,
                2
            )


        # ------------------------------------------------
        # 4. PREDICT AI RESUME SCORE
        # ------------------------------------------------

        score_result = predict_resume_score(

            text=text,

            skills=skills,

            job_role=predicted_role

        )


        ai_score = score_result["score"]


        # ------------------------------------------------
        # 5. RECOMMENDATION
        # ------------------------------------------------

        if ai_score >= 80:

            recommendation = (
                "Strong Candidate"
            )

        elif ai_score >= 60:

            recommendation = (
                "Good Candidate"
            )

        elif ai_score >= 40:

            recommendation = (
                "Moderate Candidate"
            )

        else:

            recommendation = (
                "Needs Improvement"
            )


        # ------------------------------------------------
        # 6. SAVE RESULT TO MONGODB
        # ------------------------------------------------

        resumes_collection.update_one(

            {
                "_id":
                    resume["_id"]
            },

            {
                "$set": {

                    "extracted_text":
                        text,

                    "skills":
                        skills,

                    "skill_count":
                        len(skills),

                    "predicted_role":
                        predicted_role,

                    "role_confidence":
                        role_confidence,

                    "ai_resume_score":
                        ai_score,

                    "experience_years":
                        score_result[
                            "experience"
                        ],

                    "education":
                        score_result[
                            "education"
                        ],

                    "certifications":
                        score_result[
                            "certifications"
                        ],

                    "projects_count":
                        score_result[
                            "projects"
                        ],

                    "recommendation":
                        recommendation

                }

            }

        )


        # ------------------------------------------------
        # 7. SHOW RESULTS
        # ------------------------------------------------

        return render_template(

            "resume_analysis.html",

            name=session.get(
                "name"
            ),

            filename=resume[
                "filename"
            ],

            skills=skills,

            skill_count=len(
                skills
            ),

            resume_text=text,

            predicted_role=
                predicted_role,

            role_confidence=
                role_confidence,

            ai_score=
                ai_score,

            recommendation=
                recommendation,

            experience=
                score_result[
                    "experience"
                ],

            education=
                score_result[
                    "education"
                ],

            certifications=
                score_result[
                    "certifications"
                ],

            projects=
                score_result[
                    "projects"
                ]

        )


    except Exception as e:

        print(
            "❌ AI Resume Analysis Failed:"
        )

        print(e)


        return f"""
        <h1>AI Resume Analysis Failed ❌</h1>

        <p>{e}</p>

        <a href="/candidate-dashboard">
            Back to Dashboard
        </a>
        """


# ============================================================
# RECRUITER DASHBOARD
# ============================================================

@app.route("/recruiter-dashboard")
def recruiter_dashboard():

    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    if session.get("role") != "recruiter":
        return redirect(
            url_for("login")
        )

    return render_template(
        "recruiter_dashboard.html",
        name=session.get("name")
    )
# ============================================================
# POST JOB
# ============================================================

@app.route("/post-job", methods=["GET", "POST"])
def post_job():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "recruiter":

        return redirect(
            url_for("login")
        )


    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        company = request.form.get(
            "company",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        required_skills_text = request.form.get(
            "required_skills",
            ""
        ).strip()

        experience = request.form.get(
            "experience",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()


        if not title or not company or not location or not required_skills_text or not description:

            return render_template(
                "job_post.html",
                message="Please fill all required fields."
            )


        required_skills = [
            skill.strip().lower()
            for skill in required_skills_text.split(",")
            if skill.strip()
        ]


        try:

            experience_value = float(
                experience
            ) if experience else 0.0

        except ValueError:

            return render_template(
                "job_post.html",
                message="Experience must be a valid number."
            )


        job_data = {

            "title":
                title,

            "company":
                company,

            "location":
                location,

            "required_skills":
                required_skills,

            "experience":
                experience_value,

            "description":
                description,

            "recruiter_id":
                session["user_id"]

        }


        try:

            result = jobs_collection.insert_one(
                job_data
            )

            print("✅ Job inserted!")
            print(
                "Inserted Job ID:",
                result.inserted_id
            )


            return render_template(
                "job_post.html",
                message="Job posted successfully!"
            )

        except Exception as e:

            print("❌ Job posting failed:")
            print(e)

            return render_template(
                "job_post.html",
                message="Could not post the job. Please try again."
            )


    return render_template(
        "job_post.html"
    )



# ============================================================
# AVAILABLE JOBS
# ============================================================

@app.route("/jobs")
def available_jobs():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )


    try:

        jobs = list(
            jobs_collection.find().sort(
                "_id",
                -1
            )
        )

        message = request.args.get(
            "message",
            ""
        )

        existing_applications = list(
            applications_collection.find(
                {
                    "candidate_id": session["user_id"]
                },
                {
                    "job_id": 1
                }
            )
        )

        applied_job_ids = {
            str(application["job_id"])
            for application in existing_applications
            if application.get("job_id")
        }

        return render_template(
            "available_jobs.html",
            jobs=jobs,
            applied_job_ids=applied_job_ids,
            message=message,
            name=session.get("name")
        )

    except Exception as e:

        print("❌ Could not load jobs:")
        print(e)

        return render_template(
            "available_jobs.html",
            jobs=[],
            message="Could not load jobs. Please try again.",
            name=session.get("name")
        )

# ============================================================
# APPLY FOR JOB
# ============================================================

@app.route(
    "/apply/<job_id>",
    methods=["POST"]
)
def apply_job(job_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )

    # --------------------------------------------------------
    # Validate Job ID
    # --------------------------------------------------------

    try:

        job_object_id = ObjectId(
            job_id
        )

    except Exception:

        return redirect(
            url_for(
                "available_jobs",
                message="Invalid job."
            )
        )

    # --------------------------------------------------------
    # Find Job
    # --------------------------------------------------------

    job = jobs_collection.find_one({
        "_id": job_object_id
    })

    if not job:

        return redirect(
            url_for(
                "available_jobs",
                message="Job not found."
            )
        )

    # --------------------------------------------------------
    # Get Candidate Resume
    # --------------------------------------------------------

    resume = resumes_collection.find_one(
        {
            "user_id":
                session["user_id"]
        },
        sort=[
            ("_id", -1)
        ]
    )

    if not resume:

        return redirect(
            url_for(
                "available_jobs",
                message=
                    "Please upload your resume before applying."
            )
        )

    # --------------------------------------------------------
    # Prevent Duplicate Application
    # --------------------------------------------------------

    existing_application = applications_collection.find_one({

        "candidate_id":
            session["user_id"],

        "job_id":
            str(job["_id"])

    })

    if existing_application:

        return redirect(
            url_for(
                "available_jobs",
                message=
                    "You have already applied for this job."
            )
        )

    # --------------------------------------------------------
    # Candidate Skills
    # --------------------------------------------------------

    candidate_skills = resume.get(
        "skills",
        []
    )

    candidate_skill_set = {

        str(skill).strip().lower()

        for skill in candidate_skills

        if str(skill).strip()

    }

    # --------------------------------------------------------
    # Required Job Skills
    # --------------------------------------------------------

    required_skills = job.get(
        "required_skills",
        []
    )

    required_skill_set = {

        str(skill).strip().lower()

        for skill in required_skills

        if str(skill).strip()

    }

    # --------------------------------------------------------
    # Matching Skills
    # --------------------------------------------------------

    matching_skills = sorted(

        candidate_skill_set.intersection(
            required_skill_set
        )

    )

    missing_skills = sorted(

        required_skill_set
        - candidate_skill_set

    )

    total_required = len(
        required_skill_set
    )

    if total_required > 0:

        match_percentage = (

            len(matching_skills)
            / total_required

        ) * 100

    else:

        match_percentage = 0.0

    match_percentage = round(
        match_percentage,
        2
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    try:

        candidate_experience = float(
            resume.get(
                "experience_years",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        candidate_experience = 0.0

    try:

        required_experience = float(
            job.get(
                "experience",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        required_experience = 0.0

    # --------------------------------------------------------
    # AI Resume Score
    # --------------------------------------------------------

    try:

        ai_resume_score = float(
            resume.get(
                "ai_resume_score",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        ai_resume_score = 0.0

    # --------------------------------------------------------
    # Create Application
    # --------------------------------------------------------

    application_data = {

        "candidate_id":
            session["user_id"],

        "candidate_name":
            session["name"],

        "candidate_email":
            session["email"],

        "resume_id":
            str(resume["_id"]),

        "job_id":
            str(job["_id"]),

        "job_title":
            job.get(
                "title",
                ""
            ),

        "company":
            job.get(
                "company",
                ""
            ),

        "location":
            job.get(
                "location",
                ""
            ),

        "recruiter_id":
            job.get(
                "recruiter_id",
                ""
            ),

        "ai_resume_score":
            round(
                ai_resume_score,
                2
            ),

        "job_match_score":
            match_percentage,

        "matching_skills":
            matching_skills,

        "missing_skills":
            missing_skills,

        "candidate_experience":
            candidate_experience,

        "required_experience":
            required_experience,

        "status":
            "Applied",

        "applied_at":
            datetime.utcnow()

    }

    # --------------------------------------------------------
    # Save Application
    # --------------------------------------------------------

    try:

        result = applications_collection.insert_one(
            application_data
        )

        print(
            "✅ Application created:",
            result.inserted_id
        )

    except Exception as e:

        print(
            "❌ Application insert failed:"
        )

        print(e)

        return redirect(
            url_for(
                "available_jobs",
                message=
                    "Could not submit application."
            )
        )

    return redirect(
        url_for(
            "available_jobs",
            message=
                "Application submitted successfully!"
        )
    )


# ============================================================
# MY APPLICATIONS
# ============================================================

@app.route("/applications")
def my_applications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "candidate":
        return redirect(url_for("login"))

    try:
        applications = list(
            applications_collection.find({
                "candidate_id": session["user_id"]
            }).sort("applied_at", -1)
        )

        return render_template(
            "my_applications.html",
            applications=applications,
            name=session.get("name")
        )

    except Exception as e:
        print("Could not load applications:", e)

        return render_template(
            "my_applications.html",
            applications=[],
            name=session.get("name"),
            message="Could not load your applications. Please try again."
        )

# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@app.route("/update-application-status/<application_id>", methods=["POST"])
def update_application_status(application_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    allowed_statuses = [
        "Applied",
        "Under Review",
        "Shortlisted",
        "Rejected"
    ]

    new_status = request.form.get("status", "").strip()

    if new_status not in allowed_statuses:
        return "Invalid application status", 400

    if not ObjectId.is_valid(application_id):
        return "Invalid application ID", 400

    try:
        application = applications_collection.find_one({
            "_id": ObjectId(application_id)
        })

        if not application:
            return "Application not found", 404

        job_id = application.get("job_id", "")

        if not ObjectId.is_valid(job_id):
            return "Invalid job ID", 400

        job = jobs_collection.find_one({
            "_id": ObjectId(job_id),
            "recruiter_id": session["user_id"]
        })

        if not job:
            return "You are not authorized to update this application", 403

        applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {
                "$set": {
                    "status": new_status,
                    "status_updated_at": datetime.utcnow()
                }
            }
        )

        return redirect(url_for(
            "recruiter_candidates",
            message="Application status updated successfully."
        ))

    except Exception as e:
        print("Could not update application status:", e)
        return "Could not update application status", 500
# ============================================================
# AI JOB MATCH
# ============================================================

@app.route("/job-match/<job_id>")
def job_match(job_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("role") != "candidate":

        return redirect(
            url_for("login")
        )


    # --------------------------------------------------------
    # Validate MongoDB job ID
    # --------------------------------------------------------

    try:

        job_object_id = ObjectId(
            job_id
        )

    except Exception:

        return """
        <h1>Invalid Job ID ❌</h1>
        <p>The selected job ID is not valid.</p>
        <a href="/jobs">Back to Jobs</a>
        """


    # --------------------------------------------------------
    # Get job
    # --------------------------------------------------------

    try:

        job = jobs_collection.find_one({
            "_id": job_object_id
        })

    except Exception as e:

        print("❌ Job lookup failed:")
        print(e)

        return """
        <h1>Job Lookup Failed ❌</h1>
        <p>Could not access the selected job.</p>
        <a href="/jobs">Back to Jobs</a>
        """


    if not job:

        return """
        <h1>Job Not Found ❌</h1>
        <p>The selected job does not exist.</p>
        <a href="/jobs">Back to Jobs</a>
        """


    # --------------------------------------------------------
    # Get candidate's latest resume
    # --------------------------------------------------------

    resume = resumes_collection.find_one(

        {
            "user_id":
                session["user_id"]
        },

        sort=[
            ("_id", -1)
        ]

    )


    if not resume:

        return redirect(
            url_for(
                "available_jobs",
                message="Please upload your resume before checking job matches."
            )
        )


    # --------------------------------------------------------
    # Get candidate skills
    # --------------------------------------------------------

    candidate_skills = resume.get(
        "skills",
        []
    )


    # If the resume was uploaded but not analyzed yet,
    # extract skills directly from the stored file.
    if not candidate_skills:

        file_path = resume.get(
            "file_path"
        )

        if file_path and os.path.exists(file_path):

            try:

                resume_text = extract_resume_text(
                    file_path
                )

                candidate_skills = extract_skills(
                    resume_text
                )

            except Exception as e:

                print("❌ Skill extraction during job match failed:")
                print(e)

                candidate_skills = []


    # --------------------------------------------------------
    # Normalize skills
    # --------------------------------------------------------

    def normalize_skill(skill):

        value = str(skill).strip().lower()

        value = value.replace(
            "_",
            " "
        )

        aliases = {
            "scikit learn":
                "scikit-learn",

            "scikit learn library":
                "scikit-learn",

            "node js":
                "node.js",

            "nodejs":
                "node.js",

            "powerbi":
                "power bi"
        }

        return aliases.get(
            value,
            value
        )


    candidate_skill_set = {
        normalize_skill(skill)
        for skill in candidate_skills
        if str(skill).strip()
    }


    required_skills = job.get(
        "required_skills",
        []
    )


    required_skill_list = []

    for skill in required_skills:

        normalized = normalize_skill(
            skill
        )

        if normalized and normalized not in required_skill_list:

            required_skill_list.append(
                normalized
            )


    # --------------------------------------------------------
    # Calculate skill match
    # --------------------------------------------------------

    matching_skills = sorted(
        candidate_skill_set.intersection(
            set(required_skill_list)
        )
    )

    missing_skills = sorted(
        set(required_skill_list)
        - candidate_skill_set
    )


    total_required = len(
        required_skill_list
    )

    matched_count = len(
        matching_skills
    )


    if total_required > 0:

        match_percentage = (
            matched_count
            / total_required
        ) * 100

    else:

        match_percentage = 0.0


    match_percentage = round(
        match_percentage,
        2
    )


    # --------------------------------------------------------
    # Compare experience
    # --------------------------------------------------------

    candidate_experience = resume.get(
        "experience_years"
    )

    if candidate_experience is None:

        file_path = resume.get(
            "file_path"
        )

        if file_path and os.path.exists(file_path):

            try:

                resume_text = extract_resume_text(
                    file_path
                )

                candidate_experience = extract_experience(
                    resume_text
                )

            except Exception:

                candidate_experience = 0.0

        else:

            candidate_experience = 0.0


    try:

        candidate_experience = float(
            candidate_experience
        )

    except (TypeError, ValueError):

        candidate_experience = 0.0


    try:

        required_experience = float(
            job.get(
                "experience",
                0
            )
        )

    except (TypeError, ValueError):

        required_experience = 0.0


    experience_met = (
        candidate_experience >= required_experience
    )


    # --------------------------------------------------------
    # Match status
    # --------------------------------------------------------

    if match_percentage >= 80:

        match_status = "Excellent Match"

    elif match_percentage >= 60:

        match_status = "Good Match"

    elif match_percentage >= 40:

        match_status = "Moderate Match"

    else:

        match_status = "Low Match"


    # --------------------------------------------------------
    # Save latest job match result
    # --------------------------------------------------------

    try:

        resumes_collection.update_one(

            {
                "_id":
                    resume["_id"]
            },

            {
                "$set": {
                    "latest_job_match": {
                        "job_id":
                            str(job["_id"]),

                        "job_title":
                            job.get(
                                "title",
                                ""
                            ),

                        "match_percentage":
                            match_percentage,

                        "matching_skills":
                            matching_skills,

                        "missing_skills":
                            missing_skills,

                        "candidate_experience":
                            candidate_experience,

                        "required_experience":
                            required_experience,

                        "experience_met":
                            experience_met
                    }
                }
            }

        )

    except Exception as e:

        print("⚠️ Could not save job match result:")
        print(e)


    return render_template(

        "job_match_result.html",

        name=session.get(
            "name"
        ),

        job=job,

        candidate_skills=sorted(
            candidate_skill_set
        ),

        matching_skills=matching_skills,

        missing_skills=missing_skills,

        match_percentage=match_percentage,

        match_status=match_status,

        candidate_experience=candidate_experience,

        required_experience=required_experience,

        experience_met=experience_met

    )


# ============================================================
# SKILL GAP ANALYSIS
# ============================================================

@app.route("/skill-gap")
def skill_gap():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "candidate":
        return redirect(url_for("login"))

    resume = resumes_collection.find_one(
        {
            "user_id": session["user_id"]
        },
        sort=[
            ("_id", -1)
        ]
    )

    if not resume:
        return render_template(
            "skill_gap.html",
            name=session.get("name"),
            candidate_skills=[],
            missing_skills=[],
            job_title=None,
            match_percentage=None,
            message="Please upload and analyze your resume first."
        )

    candidate_skills = resume.get("skills", [])

    latest_match = resume.get("latest_job_match")

    if latest_match:

        missing_skills = latest_match.get(
            "missing_skills",
            []
        )

        job_title = latest_match.get(
            "job_title",
            "Selected Job"
        )

        match_percentage = latest_match.get(
            "match_percentage"
        )

        message = ""

    else:

        missing_skills = []
        job_title = None
        match_percentage = None

        message = (
            "Check an AI Job Match first. "
            "Your missing skills for that job will appear here."
        )

    return render_template(
        "skill_gap.html",
        name=session.get("name"),
        candidate_skills=sorted(set(candidate_skills)),
        missing_skills=sorted(set(missing_skills)),
        job_title=job_title,
        match_percentage=match_percentage,
        message=message
    )

# ============================================================
# RECOMMENDED JOBS
# ============================================================

@app.route("/recommended-jobs")
def recommended_jobs():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "candidate":
        return redirect(url_for("login"))

    # Get latest candidate resume
    resume = resumes_collection.find_one(
        {
            "user_id": session["user_id"]
        },
        sort=[
            ("_id", -1)
        ]
    )

    if not resume:
        return render_template(
            "recommended_jobs.html",
            name=session.get("name"),
            jobs=[],
            message="Please upload and analyze your resume first."
        )

    candidate_skills = resume.get(
        "skills",
        []
    )

    candidate_skill_set = {
        str(skill).strip().lower()
        for skill in candidate_skills
        if str(skill).strip()
    }

    try:

        jobs = list(
            jobs_collection.find().sort(
                "_id",
                -1
            )
        )

    except Exception as e:

        print("❌ Could not load recommended jobs:")
        print(e)

        return render_template(
            "recommended_jobs.html",
            name=session.get("name"),
            jobs=[],
            message="Could not load jobs."
        )

    recommended = []

    for job in jobs:

        required_skills = job.get(
            "required_skills",
            []
        )

        required_skill_set = {
            str(skill).strip().lower()
            for skill in required_skills
            if str(skill).strip()
        }

        matching_skills = sorted(
            candidate_skill_set.intersection(
                required_skill_set
            )
        )

        missing_skills = sorted(
            required_skill_set
            - candidate_skill_set
        )

        total_required = len(
            required_skill_set
        )

        if total_required > 0:

            match_percentage = (
                len(matching_skills)
                / total_required
            ) * 100

        else:

            match_percentage = 0

        job_data = dict(job)

        job_data["match_percentage"] = round(
            match_percentage,
            2
        )

        job_data["matching_skills"] = matching_skills

        job_data["missing_skills"] = missing_skills

        recommended.append(
            job_data
        )

    # Highest skill match first
    recommended.sort(
        key=lambda job: job["match_percentage"],
        reverse=True
    )

    return render_template(
        "recommended_jobs.html",
        name=session.get("name"),
        jobs=recommended,
        message=""
    )


# ============================================================
# RECRUITER - VIEW CANDIDATES
# ============================================================

@app.route("/recruiter-candidates")
def recruiter_candidates():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    status_counts = {
        "total": 0,
        "applied": 0,
        "under_review": 0,
        "shortlisted": 0,
        "rejected": 0
    }

    try:
        recruiter_jobs = list(jobs_collection.find({
            "recruiter_id": session["user_id"]
        }))

        owned_job_ids = [
            str(job["_id"]) for job in recruiter_jobs
        ]

        applications = list(applications_collection.find({
            "job_id": {"$in": owned_job_ids}
        }).sort("applied_at", -1))

        status_counts["total"] = len(applications)

        for application in applications:
            status = application.get("status", "Applied")

            if status == "Applied":
                status_counts["applied"] += 1
            elif status == "Under Review":
                status_counts["under_review"] += 1
            elif status == "Shortlisted":
                status_counts["shortlisted"] += 1
            elif status == "Rejected":
                status_counts["rejected"] += 1

        return render_template(
            "recruiter_candidates.html",
            applications=applications,
            status_counts=status_counts,
            name=session.get("name"),
            message=request.args.get("message", "")
        )

    except Exception as e:
        print("Could not load recruiter applications:", e)

        return render_template(
            "recruiter_candidates.html",
            applications=[],
            status_counts=status_counts,
            name=session.get("name"),
            message="Could not load applications. Please try again."
        )
# ============================================================
# RECRUITER - CANDIDATE DETAILS
# ============================================================

@app.route("/candidate/<candidate_id>")
def candidate_details(candidate_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    try:
        candidate_object_id = ObjectId(candidate_id)

    except Exception:

        return """
        <h1>Invalid Candidate ID ❌</h1>
        <a href="/recruiter-candidates">Back to Candidates</a>
        """

    try:

        candidate = resumes_collection.find_one({
            "_id": candidate_object_id
        })

    except Exception as e:

        print("❌ Candidate lookup failed:")
        print(e)

        return """
        <h1>Candidate Lookup Failed ❌</h1>
        <a href="/recruiter-candidates">Back to Candidates</a>
        """

    if not candidate:

        return """
        <h1>Candidate Not Found ❌</h1>
        <p>The selected candidate does not exist.</p>
        <a href="/recruiter-candidates">Back to Candidates</a>
        """

    return render_template(
        "candidate_details.html",
        candidate=candidate,
        name=session.get("name")
    )

# ============================================================
# AI CANDIDATE RANKING - SELECT JOB
# ============================================================

@app.route("/ai-ranking")
def ai_ranking_jobs():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    try:

        jobs = list(
            jobs_collection.find({
                "recruiter_id": session["user_id"]
            }).sort(
                "_id",
                -1
            )
        )

        return render_template(
            "ai_ranking_jobs.html",
            jobs=jobs,
            name=session.get("name")
        )

    except Exception as e:

        print("❌ Could not load recruiter jobs:")
        print(e)

        return render_template(
            "ai_ranking_jobs.html",
            jobs=[],
            name=session.get("name")
        )


# ============================================================
# AI CANDIDATE RANKING
# ============================================================

@app.route("/ai-ranking/<job_id>")
def ai_candidate_ranking(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "recruiter":
        return redirect(url_for("login"))

    try:

        job_object_id = ObjectId(job_id)

    except Exception:

        return """
        <h1>Invalid Job ID ❌</h1>
        <a href="/ai-ranking">
            Back to Jobs
        </a>
        """

    try:

        job = jobs_collection.find_one({
            "_id": job_object_id,
            "recruiter_id": session["user_id"]
        })

    except Exception as e:

        print("❌ Job lookup failed:")
        print(e)

        return """
        <h1>Job Lookup Failed ❌</h1>
        <a href="/ai-ranking">
            Back to Jobs
        </a>
        """

    if not job:

        return """
        <h1>Job Not Found ❌</h1>
        <p>This job does not exist or does not belong to you.</p>
        <a href="/ai-ranking">
            Back to Jobs
        </a>
        """

    required_skills = {
        str(skill).strip().lower()
        for skill in job.get(
            "required_skills",
            []
        )
        if str(skill).strip()
    }

    try:

        resumes = list(
            resumes_collection.find()
        )

    except Exception as e:

        print("❌ Could not load candidates:")
        print(e)

        resumes = []

    ranked_candidates = []

    for resume in resumes:

        candidate_skills = {
            str(skill).strip().lower()
            for skill in resume.get(
                "skills",
                []
            )
            if str(skill).strip()
        }

        matching_skills = sorted(
            candidate_skills.intersection(
                required_skills
            )
        )

        missing_skills = sorted(
            required_skills
            - candidate_skills
        )

        total_required = len(
            required_skills
        )

        if total_required > 0:

            job_match = (
                len(matching_skills)
                / total_required
            ) * 100

        else:

            job_match = 0.0

        job_match = round(
            job_match,
            2
        )

        ai_resume_score = resume.get(
            "ai_resume_score",
            0
        )

        try:

            ai_resume_score = float(
                ai_resume_score
            )

        except (TypeError, ValueError):

            ai_resume_score = 0.0

        ranking_score = (
            job_match * 0.70
            +
            ai_resume_score * 0.30
        )

        ranking_score = round(
            ranking_score,
            2
        )

        ranked_candidates.append({

            "id":
                resume["_id"],

            "name":
                resume.get(
                    "name",
                    "Unknown"
                ),

            "email":
                resume.get(
                    "email",
                    ""
                ),

            "ai_resume_score":
                round(
                    ai_resume_score,
                    2
                ),

            "job_match":
                job_match,

            "ranking_score":
                ranking_score,

            "matching_skills":
                matching_skills,

            "missing_skills":
                missing_skills,

            "experience":
                resume.get(
                    "experience_years",
                    0
                ),

            "predicted_role":
                resume.get(
                    "predicted_role",
                    "Not Available"
                )

        })

    ranked_candidates.sort(
        key=lambda candidate:
            candidate["ranking_score"],
        reverse=True
    )

    return render_template(
        "ai_candidate_ranking.html",
        job=job,
        candidates=ranked_candidates,
        name=session.get("name")
    )
# ============================================================
# MANAGE JOBS - RECRUITER
# ============================================================
@app.route("/manage-jobs")
def manage_jobs():

    if "user_id" not in session or session.get("role") != "recruiter":
        return redirect(url_for("login"))

    recruiter_id = session["user_id"]

    jobs = list(
        jobs_collection.find(
            {"recruiter_id": recruiter_id}
        ).sort("_id", -1)
    )

    return render_template(
        "manage_jobs.html",
        jobs=jobs,
        name=session.get("name")
    )
@app.route("/edit-job/<job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    if "user_id" not in session or session.get("role") != "recruiter":
        return redirect(url_for("login"))

    if not ObjectId.is_valid(job_id):
        return "Invalid Job ID", 400

    recruiter_id = session["user_id"]

    job = jobs_collection.find_one({
        "_id": ObjectId(job_id),
        "recruiter_id": recruiter_id
    })

    if not job:
        return "Job not found or access denied", 404

    if request.method == "POST":

        updated_job = {
            "title": request.form.get("title", "").strip(),
            "company": request.form.get("company", "").strip(),
            "location": request.form.get("location", "").strip(),
            "required_skills": [
                skill.strip().lower()
                for skill in request.form.get("required_skills", "").split(",")
                if skill.strip()
            ],
            "experience": float(request.form.get("experience", 0)),
            "description": request.form.get("description", "").strip()
        }

        if not updated_job["title"] or not updated_job["company"]:
            return "Job title and company are required", 400

        jobs_collection.update_one(
            {
                "_id": ObjectId(job_id),
                "recruiter_id": recruiter_id
            },
            {"$set": updated_job}
        )

        return redirect(url_for("manage_jobs"))

    return render_template("edit_job.html", job=job)

@app.route("/delete-job/<job_id>", methods=["POST"])
def delete_job(job_id):

    if "user_id" not in session or session.get("role") != "recruiter":
        return redirect(url_for("login"))

    if not ObjectId.is_valid(job_id):
        return "Invalid Job ID", 400

    result = jobs_collection.delete_one({
        "_id": ObjectId(job_id),
        "recruiter_id": session["user_id"]
    })

    if result.deleted_count == 0:
        return "Job not found or access denied", 404

    return redirect(url_for("manage_jobs"))
# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

# ============================================================
# DATABASE TEST
# ============================================================

@app.route("/test-db")
def test_db():
    try:
        result = users_collection.insert_one({

            "name":
                "Database Test User",

            "email":
                "dbtest@hiresense.com",

            "role":
                "candidate"

        })


        return f"""
        <h1>MongoDB Test Successful ✅</h1>

        <p>
        Inserted ID: {result.inserted_id}
        </p>

        <a href="/candidate-dashboard">
            Back to Dashboard
        </a>
        """


    except Exception as e:

        return f"""
        <h1>MongoDB Test Failed ❌</h1>

        <p>{e}</p>
        """


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )