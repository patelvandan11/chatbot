from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import openai

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

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Send the image to OpenAI API for analysis
        image_url = url_for('uploaded_file', filename=file.filename, _external=True)
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
