from flask import Flask, render_template, request, Response
import os
from PyPDF2 import PdfReader
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


def find_skills(text):
    skills = [
        "python",
        "java",
        "c",
        "c++",
        "sql",
        "mysql",
        "javascript",
        "html",
        "css",
        "react",
        "flask",
        "django",
        "git",
        "github",
        "rest api",
        "machine learning",
        "data analysis",
        "pandas"
    ]

    text = text.lower()

    found_skills = []

    for skill in skills:
        if skill in text:
            found_skills.append(skill)

    return found_skills


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    resume = request.files["resume"]
    job_title = request.form["job_title"]
    job_description = request.form["job_description"]

    if resume:
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            resume.filename
        )

        resume.save(file_path)

        reader = PdfReader(file_path)

        resume_text = ""

        for page in reader.pages:
            text = page.extract_text()

            if text:
                resume_text += text + "\n"

        resume_skills = find_skills(resume_text)
        job_skills = find_skills(job_description)

        matched_skills = []

        for skill in job_skills:
            if skill in resume_skills:
                matched_skills.append(skill)

        missing_skills = []

        for skill in job_skills:
            if skill not in resume_skills:
                missing_skills.append(skill)

        suggestions = []

        for skill in missing_skills:
            suggestions.append(
                "Consider learning or gaining experience in " + skill
            )

        if len(job_skills) > 0:
            match_score = round(
                len(matched_skills) / len(job_skills) * 100,
                2
            )
        else:
            match_score = 0

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO analyses
            (job_title, job_description, match_score,
             matched_skills, missing_skills)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                job_title,
                job_description,
                match_score,
                ", ".join(matched_skills),
                ", ".join(missing_skills)
            )
        )

        db.commit()
        cursor.close()

        return render_template(
            "result.html",
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            match_score=match_score,
            suggestions=suggestions
        )

    return "Please select a resume."

@app.route("/history")
def history():
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM analyses ORDER BY id DESC"
    )

    analyses = cursor.fetchall()

    cursor.close()

    return render_template(
        "history.html",
        analyses=analyses
    )
@app.route("/download")
def download():
    job_title = request.args.get("job_title", "")
    match_score = request.args.get("match_score", "")
    matched_skills = request.args.get("matched_skills", "")
    missing_skills = request.args.get("missing_skills", "")

    report = f"""
CareerAI - Resume Analysis Report
=================================

Job Title:
{job_title}

Match Score:
{match_score}%

Matched Skills:
{matched_skills}

Missing Skills:
{missing_skills}

Thank you for using CareerAI.
"""

    return Response(
        report,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=careerai_report.txt"
        }
    )


if __name__ == "__main__":
    app.run(debug=True)