from flask import Flask, render_template, request, jsonify
import pdfplumber
import sqlite3
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# SQLite Database
conn = sqlite3.connect("resume.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    skills TEXT,
    education TEXT
)
""")

conn.commit()


def extract_text_from_pdf(pdf_path):
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


def extract_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)

    return match.group() if match else "Not Found"


def extract_phone(text):
    pattern = r'(\+91[\-\s]?)?[0]?(91)?[6789]\d{9}'
    match = re.search(pattern, text)

    return match.group() if match else "Not Found"


def extract_name(text):
    lines = text.split("\n")

    for line in lines[:5]:
        if len(line.strip()) > 2 and len(line.strip()) < 40:
            return line.strip()

    return "Not Found"


def extract_skills(text):

    skills_db = [
        "Python",
        "Java",
        "C",
        "C++",
        "HTML",
        "CSS",
        "JavaScript",
        "SQL",
        "Flask",
        "Django",
        "React",
        "Node.js",
        "Flutter",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "Power BI",
        "PostgreSQL",
        "Data Analytics"
    ]

    found = []

    for skill in skills_db:
        if skill.lower() in text.lower():
            found.append(skill)

    return ", ".join(found)


def extract_education(text):

    education_list = [
        "B.E",
        "B.Tech",
        "B.Sc",
        "M.E",
        "M.Tech",
        "MBA",
        "MCA",
        "Diploma",
        "PhD"
    ]

    found = []

    for edu in education_list:
        if edu.lower() in text.lower():
            found.append(edu)

    return ", ".join(found)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_resume():

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No file selected"})

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    text = extract_text_from_pdf(filepath)

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)

    cursor.execute("""
    INSERT INTO candidates
    (name,email,phone,skills,education)
    VALUES(?,?,?,?,?)
    """,
    (name,email,phone,skills,education))

    conn.commit()

    return jsonify({
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education
    })


@app.route("/search")
def search():

    keyword = request.args.get("keyword", "")

    cursor.execute("""
    SELECT * FROM candidates
    WHERE name LIKE ?
    OR skills LIKE ?
    OR education LIKE ?
    """,
    (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "skills": row[4],
            "education": row[5]
        })

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)