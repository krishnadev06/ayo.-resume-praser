# app.py
import os
import re
import fitz  # PyMuPDF for PDFs
import docx  # python-docx for DOCX
from flask import Flask, request, jsonify, render_template

# Initialize the Flask application
app = Flask(__name__)

# --- Helper Functions for Resume Analysis ---

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def analyze_resume(text):
    """
    Analyzes the resume text to extract details and calculate an ATS score.
    This is a simplified heuristic model.
    """
    score = 0
    details = {
        "email": "Not Found",
        "phone": "Not Found",
        "skills": [],
        "analysis_notes": []
    }

    # 1. Contact Information Extraction (Weight: 30%)
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_regex = r'(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    
    email = re.search(email_regex, text)
    if email:
        details["email"] = email.group(0)
        score += 15
        details["analysis_notes"].append("✔️ Email found.")
    else:
        details["analysis_notes"].append("❌ Email not found. ATS may miss it.")

    phone = re.search(phone_regex, text)
    if phone:
        details["phone"] = phone.group(0)
        score += 15
        details["analysis_notes"].append("✔️ Phone number found.")
    else:
        details["analysis_notes"].append("❌ Phone number not found.")

    # 2. Keyword and Section Analysis (Weight: 50%)
    common_skills = ['python', 'java', 'c++', 'javascript', 'sql', 'git', 'react', 'aws', 'docker', 'machine learning', 'data analysis''python', 'java', 'c++', 'javascript', 'sql', 'git', 'react', 'aws', 'docker', 'machine learning', 'data analysis', 'c#', 'typescript', 'go', 'php', 'swift', 'kotlin', 'node.js', 'angular', 'vue.js', 'django', 'spring boot', 'html5', 'css3', 'restful apis', 'mysql', 'postgresql', 'mongodb', 'nosql', 'azure', 'google cloud platform', 'kubernetes', 'ci/cd', 'jenkins', 'terraform', 'agile methodologies', 'scrum', 'jira', 'linux', 'system design', 'api design', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'data visualization', 'project management', 'problem solving', 'communication', 'leadership', 'ruby on rails', 'scala', 'perl', 'bash scripting', 'powershell', 'asp.net', 'laravel', 'graphql', 'next.js', 'svelte', 'bootstrap', 'tailwind css', 'sass', 'webpack', 'microservices architecture', 'serverless architecture', 'aws lambda', 'apache spark', 'hadoop', 'kafka', 'tableau', 'power bi', 'natural language processing (nlp)', 'computer vision', 'deep learning', 'android development', 'ios development', 'react native', 'flutter', 'xamarin', 'ansible', 'chef', 'puppet', 'prometheus', 'grafana', 'elasticsearch', 'redis', 'object-oriented programming (oop)', 'functional programming', 'test-driven development (tdd)', 'unit testing', 'network security', 'penetration testing', 'cryptography', 'ui/ux design', 'product management', 'business analysis', 'technical writing', 'seo', 'data warehousing', 'big data technologies']
    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found_skills.append(skill.capitalize())
    
    details["skills"] = found_skills
    if len(found_skills) > 0:
        score += min(len(found_skills) * 5, 25) # Max 25 points for skills
        details["analysis_notes"].append(f"✔️ Found {len(found_skills)} relevant skills.")
    else:
        details["analysis_notes"].append("⚠️ No common skills found. Add a skills section.")

    common_headers = ['experience', 'education', 'skills', 'projects', 'summary', 'objective']
    found_headers = 0
    for header in common_headers:
        if re.search(r'\b' + re.escape(header) + r'\b', text, re.IGNORECASE):
            found_headers += 1
    
    if found_headers >= 3:
        score += 25 # Max 25 points for standard headers
        details["analysis_notes"].append("✔️ Well-structured with standard headers.")
    else:
        details["analysis_notes"].append("⚠️ Lacks standard headers (Experience, Skills, etc.).")


    # 3. Readability & Formatting (Weight: 20%)
    # Simple check for text length. Very short resumes are often bad.
    if len(text) > 500:
        score += 20
        details["analysis_notes"].append("✔️ Good length, likely parseable.")
    else:
        details["analysis_notes"].append("❌ Resume is too short or text extraction failed.")
        score = min(score, 30) # Penalize heavily if unreadable

    return score, details


# --- Flask Routes ---

@app.route('/')
def home():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyzes the uploaded resume file."""
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        # Save file temporarily
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

        # Extract text based on file type
        text = ""
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
        
        # Clean up the uploaded file
        os.remove(file_path)

        if not text:
            return jsonify({"error": "Could not extract text from the document. It might be an image-based file or corrupted."}), 500
            
        # Analyze the text
        score, details = analyze_resume(text)
        
        return jsonify({
            "score": score,
            "details": details
        })

    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)