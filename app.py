from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import PyPDF2
import pytesseract
from PIL import Image
import pdfplumber

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Function to extract text from images
def extract_text_from_image(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

# HTML form to upload files
@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>File Upload API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 20px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
                h1 {
                    color: #333;
                }
                p {
                    font-size: 16px;
                }
                form {
                    margin-top: 20px;
                }
                input[type="file"] {
                    padding: 10px;
                    margin-right: 10px;
                }
                input[type="submit"] {
                    padding: 10px 15px;
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                input[type="submit"]:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <h1>File Upload API</h1>
            <p>Use this API endpoint to upload PDF documents or images (PNG, JPG, JPEG) to extract text.</p>
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <label for="file">Select a file:</label>
                <input type="file" name="file" id="file" accept=".pdf, .png, .jpg, .jpeg" required>
                <input type="submit" value="Upload">
            </form>
            <p>After uploading, you will receive the extracted text in response.</p>
        </body>
    </html>
    '''


# API route to upload and extract text from files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported"}), 400
    
    # Save file
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    except Exception as e:
        return jsonify({"error": f"File saving error: {str(e)}"}), 500

    try:
        # Extract text based on file type
        if filename.endswith(('pdf')):
            extracted_text = extract_text_from_pdf(file_path)
        else:
            extracted_text = extract_text_from_image(file_path)
    except Exception as e:
        return jsonify({"error": f"Text extraction error: {str(e)}"}), 500
    finally:
        # Always clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    return jsonify({"extracted_text": extracted_text}), 200


if __name__ == '__main__':
    app.run(debug=True)
