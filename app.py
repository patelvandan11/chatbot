from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import openai
from groq import Groq
import base64
from IPython.display import Image

 
# Define image encoding function
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Interact with model for image descriptions
def image_to_text(client, model, base64_images, prompt):
    responses = []
    for base64_image in base64_images:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model=model
        )
        response = chat_completion.choices[0].message.content
        responses.append(response)
    return responses

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Set your OpenAI API key
openai.api_key = 'your_openai_api_key'

# In-memory user database for demo purposes
users = {'test@example.com': {'password': 'password'}}

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            session['email'] = email
            return redirect(url_for('chatbot'))
        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users:
            flash('Email already registered.')
        else:
            users[email] = {'password': password}
            flash('Successfully registered. Please log in.')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/chatbot')
def chatbot():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('chatbot.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')  # Support multiple files
    if len(files) == 0:
        return jsonify({'error': 'No selected files'}), 400

    # Store the image file paths and base64 encoded images
    base64_images = []

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            # Save the file to the upload folder
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Encode the file into base64
            base64_image = encode_image(filepath)
            base64_images.append(base64_image)

    # Initialize Groq client and model
    client = Groq(api_key='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')
    model = 'llava-v1.5-7b-4096-preview'

    # Get a prompt from the user or use a default one
    prompt = request.form.get('prompt', 'Describe this image.')

    # Call the Groq model for all uploaded images
    responses = image_to_text(client, model, base64_images, prompt)

    # Return the model's response for each image
    return jsonify({'responses': responses}), 200

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Save the file to the upload folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Create the URL for the uploaded file
        image_url = url_for('uploaded_file', filename=file.filename, _external=True)
        
        # Send the image URL to OpenAI API for analysis
        response = analyze_image(image_url)

        return jsonify({'message': 'File successfully uploaded', 'response': response}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('static', filename='uploads/' + filename))

def analyze_image(image_url):
    try:
        # Interact with OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What’s in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "high"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
