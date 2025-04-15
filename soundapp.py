import os
import re
import librosa
import numpy as np
import whisper
import noisereduce as nr
import smtplib
from flask import Flask, request, jsonify
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
CORS(app)

# Load Whisper Model
whisper_model = whisper.load_model("base")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def denoise_audio(audio, sr):
    """Applies noise reduction to the audio."""
    return nr.reduce_noise(y=audio, sr=sr)

def detect_human_voice(audio):
    """Basic human voice detection based on energy levels."""
    energy = np.sum(audio ** 2)
    return energy > 0.01  # Threshold for voice detection

def extract_email(text):
    """Extracts email from transcribed text using regex."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def transcribe_audio(file_path):
    """Loads, denoises, and transcribes audio using Whisper."""

    # Load audio with Librosa (bypassing FFmpeg)
    audio, sr = librosa.load(file_path, sr=16000)  # Whisper prefers 16kHz

    # Run Whisper transcription
    result = whisper_model.transcribe(audio, language="en", task="transcribe")
    
    return result["text"]

def send_email(transcribed_text):
    sender_email = "lohitakshabc12345@gmail.com"
    sender_password = "wfcmztwvqekhgyln"
    recipient_email = "lohitakshabc12345@gmail.com"

    subject = "Transcribed Audio Result"
    body = f"Here is the transcribed text:\n\n{transcribed_text}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Load audio and detect human voice
    audio, sr = librosa.load(file_path, sr=16000)
    human_voice_detected = detect_human_voice(audio)

    transcription = transcribe_audio(file_path) if human_voice_detected else "No human speech detected."
    
    # Extract email from transcription
    email_detected = extract_email(transcription)

    if human_voice_detected:
        transcription = transcribe_audio(file_path)
        #send_email(transcription)  # Send email with transcribed text
        word_count = len(transcription.split())  # **Count words in transcription**

        # Send email only if transcription contains more than 3 words**
        if word_count > 3:
            send_email(transcription)
    else:
        transcription = "No human speech detected."


    response = {
        "message": "Processing complete!",
        "human_voice": bool(human_voice_detected),
        "transcription": transcription,
        "email": email_detected if email_detected else "No email found"
    }

    print(response)  # Backend console log
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
