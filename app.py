from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import openai
from groq import Groq
import base64
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Set your OpenAI API key
openai.api_key = 'api'

# Initialize Groq client and model (ensure you have the correct API key and model)
client = Groq(api_key='gapi')
model = 'llava-v1.5-7b-4096-preview'

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
    if 'file' not in request.files and 'prompt' not in request.form:
        return jsonify({'error': 'No input provided'}), 400

    files = request.files.getlist('file')  # Support multiple files
    prompt = request.form.get('prompt', '')

    base64_images = []
    responses = []

    # Handle images if they exist
    if files:
        for file in files:
            if file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                base64_image = encode_image(filepath)
                base64_images.append(base64_image)

        # Call the Groq model for image processing
        responses = image_to_text(client, model, base64_images, prompt or 'Describe this image.')

    # If only text is provided, call the OpenAI model for a text response
    if prompt and not base64_images:
        try:
            logging.debug(f"Calling OpenAI API with prompt: {prompt}")
            openai_response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150
            )
            response_text = openai_response.choices[0].text.strip()
            logging.debug(f"OpenAI API response: {response_text}")
            responses.append(response_text)
        except Exception as e:
            logging.error(f"Error calling OpenAI API: {str(e)}")
            return jsonify({'error': 'Error processing request'}), 500

    return jsonify({'responses': responses}), 200

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

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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

if __name__ == '__main__':
    app.run(debug=True)
