from flask import Flask, render_template, request, send_from_directory
import os
import cv2
import sqlite3
import pytesseract

app = Flask(__name__)

# Configure Upload Folder
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Set Tesseract OCR Path (Modify this path as needed)
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

# Scam Keywords
SCAM_KEYWORDS = ["bank", "password", "urgent", "verify", "lottery", "prize", "free", "account", "credit card"]

# Initialize Database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scam_analysis (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            extracted_text TEXT,
            scam_score INTEGER,
            result TEXT
        )
    """)
    conn.commit()
    conn.close()

# Extract text from an image
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

# Analyze text for scam detection
def analyze_text(text):
    words = text.lower().split()
    scam_count = sum(1 for word in words if word in SCAM_KEYWORDS)
    scam_score = (scam_count / len(words)) * 100 if words else 0
    result = "Safe ✅" if scam_score < 10 else "Scam ❌"
    return scam_score, result

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            extracted_text = extract_text(filepath)
            scam_score, result = analyze_text(extracted_text)

            # Save to Database
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("INSERT INTO scam_analysis (filename, extracted_text, scam_score, result) VALUES (?, ?, ?, ?)",
                      (file.filename, extracted_text, scam_score, result))
            conn.commit()
            conn.close()

            return render_template("index.html", filename=file.filename, text=extracted_text, scam_score=scam_score, result=result)
    
    return render_template("index.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
 
