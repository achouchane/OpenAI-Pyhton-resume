import os
import openai
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from docx import Document
import fitz

openai.api_key = os.getenv("MY_OPENAI_API_KEY")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'docx', 'pdf'}

chat_history = []

# Helper function to extract text from uploaded files
def extract_text(file_path, file_extension):
    if file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    elif file_extension == 'docx':
        doc = Document(file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    elif file_extension == 'pdf':
        doc = fitz.open(file_path)
        text = ''
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
        return text
    return ''

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to handle the main page
@app.route('/', methods=['GET', 'POST'])
def index():
    assistant_message = ''
    if request.method == 'POST':
        if 'resume' in request.files and 'job_description' in request.files:
            resume_file = request.files['resume']
            job_description_file = request.files['job_description']

            if resume_file and allowed_file(resume_file.filename) and job_description_file and allowed_file(job_description_file.filename):
                # Save the uploaded files
                resume_filename = secure_filename(resume_file.filename)
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
                resume_file.save(resume_path)

                job_description_filename = secure_filename(job_description_file.filename)
                job_description_path = os.path.join(app.config['UPLOAD_FOLDER'], job_description_filename)
                job_description_file.save(job_description_path)

                # Extract text from the uploaded files
                resume_content = extract_text(resume_path, resume_filename.split('.')[-1])
                job_description_content = extract_text(job_description_path, job_description_filename.split('.')[-1])

                # Prompt for OpenAI comparison
                prompt = f"Resume: {resume_content}\nJob Description: {job_description_content}\nIs the resume adequate for this job? :"

                assistant_message = get_assistant_response(prompt)

                # Add to chat history
                chat_history.append({"role": "user", "content": "Uploaded resume and job description."})
                chat_history.append({"role": "assistant", "content": assistant_message})

    return render_template('index.html', chat_history=chat_history)

# Route to handle the upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    return render_template('upload.html')

# Main function to get assistant response
def get_assistant_response(message):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=message,
        max_tokens=50
    )
    return response.choices[0].text.strip()

if __name__ == '__main__':
    app.run(debug=True)
