from flask import Flask, request, jsonify, render_template, g, send_file, session,redirect, url_for, make_response
import sqlite3
from flask_cors import CORS
from PIL import Image
from io import BytesIO
import os
import base64
import cv2
import random
import requests
""""============BELOW LINES ARE USE FOR INDEX.HTML CODES============="""
app = Flask(__name__)
CORS(app)
app.secret_key = "c2bb3ddd9799018520103d9c5d35e9635650b0e2932f6600aae2a7bd6a2de1d8"  # Set a secret key for session management


    


# Set the path to the directory containing your static files (JavaScript)
app.static_folder = 'static'

# SQLite database setup
DATABASE = 'biometric_data.db'


# Function to get the database connection from the g object
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Function to initialize the database
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aadhaar_number TEXT,
                fingerprint BLOB,
                age INTEGER
            )
        ''')

        db.commit()

# Initialize the database
init_db()

# Set the path to the directory where images are saved
static_directory = 'static'
if not os.path.exists(static_directory):
    os.makedirs(static_directory)

# match fingers using open-cv
def match_fingerprints(image_path1, image_path2):
    # Extract minutiae from the two fingerprint images
    keypoints1, descriptors1 = extract_minutiae(image_path1)
    keypoints2, descriptors2 = extract_minutiae(image_path2)

    # Create a Brute-Force Matcher
    matcher = cv2.BFMatcher()

    # Match the keypoints
    matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

    # Lowe's ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # Define a threshold for matching (adjust as needed)
    matching_threshold = 5  # You may need to adjust this based on your images and application

    # Check if the number of good matches exceeds the threshold
    return len(good_matches) > matching_threshold

# Extract minutiae from fingerprint image
def extract_minutiae(image_path):
    # Read the fingerprint image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Convert the image to binary using adaptive thresholding
    _, binarized = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Create a Fingerprint Minutiae Recognizer
    minutiae_recognizer = cv2.AKAZE_create()

    # Detect keypoints and descriptors
    keypoints, descriptors = minutiae_recognizer.detectAndCompute(binarized, None)

    return keypoints, descriptors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Match', methods=['POST'])
def match_endpoint():
    try:
        # Example usage with image paths received from the client
        image_path1 = os.path.join(static_directory, 'fingerprint_1.png')
        image_path2 = os.path.join(static_directory, 'captured_fingerprint.png') 
    
        # Perform fingerprint matching
        is_match = match_fingerprints(image_path1, image_path2)

        # Return a message indicating whether the fingerprint matched or not
        if is_match:
            # Delete fingerprint images after matching
            os.remove(image_path1)
            os.remove(image_path2)
            result_message="Fingerprint matched!" 
        else:
            result_message="Fingerprint did not match."
        
        return jsonify({'status': 'success', 'message': result_message})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    # Set a flag in session to indicate that the index page is visited


@app.route('/save_image', methods=['POST'])
def save_image():
    try:
        # Get the base64-encoded image data from the request
        img_data = request.form['img_data']
        
        # Ensure proper padding
        padding = len(img_data) % 4
        if padding > 0:
            img_data += '=' * (4 - padding)

        # Replace URL-safe characters
        img_data = img_data.replace('-', '+').replace('_', '/')

        # Decode the base64 data to bytes
        img_binary = base64.b64decode(img_data)
        
        file_name = "captured_fingerprint.png"
        
        # Save the image in the static directory
        existing_file_path = os.path.join(static_directory, file_name)
        with open(existing_file_path, 'wb') as f:
            f.write(img_binary)
        
        print(f"Image '{file_name}' saved in the static directory.")
        return "Image saved successfully."
    except Exception as e:
        return f"Error saving image: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    aadhaar_number = request.form['inputField']
    session['aadhaar_number'] = aadhaar_number

    # Check if Aadhaar number exists and retrieve fingerprint
    stored_fingerprint = retrieve_fingerprint(aadhaar_number)

    if stored_fingerprint is not None:
        # Create an Image object from BytesIO
        image = Image.open(BytesIO(stored_fingerprint))
        
        
        # Get the file name from the stored fingerprint (you may need a better way to generate unique names)
        file_name = f"fingerprint_1.png"

        # Check if the file already exists in the static directory
        existing_file_path = os.path.join(static_directory, file_name)
        if os.path.exists(existing_file_path):
            # Replace the existing file
            os.remove(existing_file_path)

        # Save the image in the static directory
        image.save(existing_file_path)
        print(f"Image '{file_name}' saved in the static directory.")

        # Render the image in the browser
        output="AADHAAR NUMBER VERIFIED SUCCESSFULLY"
        return render_template('index.html',output=output)
    else:
        # Handle the case where the fingerprint is not found or the Aadhaar number is invalid
        output = "Invalid Aadhaar number or not eligible (age less than 18).\nPlease enter a valid Aadhaar number."
        return render_template('index.html', output=output)
    


def retrieve_fingerprint(aadhaar_number):
    # Replace this with your actual database connection and query
    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    # Example query assuming you have a table named 'users' with 'fingerprint' and 'age' columns
    query = f"SELECT fingerprint, age FROM users WHERE aadhaar_number = '{aadhaar_number}'"

    cursor.execute(query)
    result = cursor.fetchone()

    connection.close()

    # Check if the result is not None (data exists)
    if result:
        fingerprint, age = result
        # Check if age is greater than or equal to 18
        if age >= 18:
            return fingerprint
        else:
            # Return None and handle the case where age is less than 18
            return None
    else:
        return None

""""============BELOW LINES ARE USE FOR NEXT.HTML CODES============="""

@app.route('/next')
def next_page():
    # Render the next HTML page
    return render_template('next.html')

def retrieve_mobile_number(aadhaar_number):
    # Replace this with your actual database connection and query
    connection = sqlite3.connect('biometric_data.db')
    cursor = connection.cursor()

    # Example query assuming you have a table named 'users'
    query = f"SELECT mobile_number FROM users WHERE aadhaar_number = {aadhaar_number}"
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    connection.close()

    return result[0] if result else None

def send_sms(aadhaar_number):
    api_secret = "d2ee5d55becbf35ef22b0652480f55969a3d0073"
    device_id = "00000000-0000-0000-ce94-c49b7c4b297d"

    # Valid Aadhar number, retrieve mobile number
    mobile_number = retrieve_mobile_number(aadhaar_number)

    if mobile_number:
        otp = generate_otp()
        message_text = f"DEAR VOTER,\nYour One Time Password (OTP) is {otp} to login to Dvote. Don't share OTP with anyone,Passcode for add voter: 978707."
        message = {
            "secret": api_secret,
            "mode": "devices",
            "device": device_id,
            "sim": 1,
            "priority": 1,
            "phone": mobile_number,
            "message": message_text
        }

        try:
            response = requests.post(url="https://www.cloud.smschef.com/api/send/sms", params=message)
            result = response.json()
            print(result)

            # Store Aadhar number and generated OTP in the session
            session['aadhaar_number'] = aadhaar_number
            session['generated_otp'] = otp

            return True  # OTP sent successfully
        except requests.RequestException as e:
            print(f"Error sending OTP: {e}")
            return False
    else:
        print("Mobile number not found for the given Aadhar number.")
        return False

def generate_otp():
    return random.randint(100000, 999999)

def validate_otp(entered_otp, generated_otp):
    return str(entered_otp) == str(generated_otp)


@app.route('/send', methods=['POST'])
def send():
    aadhaar__number = request.form['inputField']
     # Perform Aadhaar validation (replace this with your validation logic)
    aadhaar_number = session.get('aadhaar_number')
    
    if (aadhaar__number==aadhaar_number):
    # Check if Aadhar number exists before sending SMS
        send_sms(aadhaar_number)
        return render_template('next.html', aadhaar_number=aadhaar_number, show_otp_input=True)
    else:
        output = "invalid Aadhar number."
        return render_template('next.html', output=output)

@app.route('/button', methods=['POST'])
def button():
    aadhaar_number = session.get('aadhaar_number')
    entered_otp = request.form['otpForm']

    # Validate the entered OTP
    generated_otp = session.get('generated_otp')
    
    if aadhaar_number and generated_otp:
        if validate_otp(entered_otp, generated_otp):
            output = "OTP is valid. Authentication successful!"
            return redirect('http://192.168.183.1:3000')
        else:
            output = "Invalid OTP. Authentication failed."
    else:
        output = "Error: Aadhaar number or OTP not found in the session."

    # Clear session data
    #session.pop('aadhaar_number', None)
    #session.pop('generated_otp', None)
    
    return render_template('next.html', output=output)

"""
def save_credentials(aadhaar_number, generated_otp):
    # Specify the directory to store the file
    directory = r'D:\project\client'
    
    # Ensure the directory exists
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            print(f"Error creating directory: {e}")
            return
    
    # Define the file path
    file_path = os.path.join(directory, 'pass.txt')
    
    # Save the data to the text file
    try:
        with open(file_path, 'w') as file:
            file.write(f"Aadhaar Number: {aadhaar_number}\n")
            file.write(f"Generated OTP: {generated_otp}\n")
        print("Credentials saved successfully.")
    except Exception as e:
        print(f"Error saving credentials: {e}")
"""

if __name__ == '__main__':
    port = 8000 
    app.run(debug=True, port=port)
