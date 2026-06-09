from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pdfplumber
import docx
import re
import json
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DATA_FILE = "resume_data.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_resumes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_resumes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def extract_text(filepath):
    text = ""

    if filepath.endswith(".pdf"):
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif filepath.endswith(".docx"):
        document = docx.Document(filepath)
        text = "\n".join([p.text for p in document.paragraphs])

    elif filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

    return text


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_resume():
    try:

        if "resume" not in request.files:
            return jsonify({
                "success": False,
                "error": "No file selected"
            })

        file = request.files["resume"]

        if file.filename == "":
            return jsonify({
                "success": False,
                "error": "No file selected"
            })

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Only PDF, DOCX and TXT files allowed"
            })

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(filepath)

        text = extract_text(filepath)

        if not text.strip():
            return jsonify({
                "success": False,
                "error": "Unable to extract text"
            })

        emails = re.findall(
            r'[\w\.-]+@[\w\.-]+\.\w+',
            text
        )

        phones = re.findall(
            r'\+?\d[\d\s\-\(\)]{8,}',
            text
        )

        lines = [
            x.strip()
            for x in text.split("\n")
            if x.strip()
        ]

        data = {
            "name": lines[0] if lines else "Unknown",
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "filename": filename,
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }

        resumes = load_resumes()
        resumes.append(data)
        save_resumes(resumes)

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:
        print(e)

        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route("/api/resumes")
def get_resumes():

    resumes = load_resumes()

    return jsonify({
        "success": True,
        "resumes": resumes
    })


@app.route("/api/search")
def search():

    query = request.args.get(
        "search",
        ""
    ).lower()

    resumes = load_resumes()

    results = []

    for r in resumes:

        if (
            query in r["name"].lower()
            or query in r["email"].lower()
            or query in r["phone"].lower()
        ):
            results.append(r)

    return jsonify({
        "success": True,
        "resumes": results,
        "count": len(results)
    })


@app.route("/api/delete/<int:index>", methods=["POST"])
def delete_resume(index):

    resumes = load_resumes()

    if index < len(resumes):
        resumes.pop(index)
        save_resumes(resumes)

    return jsonify({
        "success": True
    })


if __name__ == "__main__":
    app.run(debug=True)