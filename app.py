from flask import Flask, render_template, request, Response, jsonify, send_from_directory
import cv2
import torch
from ultralytics import YOLO
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load YOLO model
model = YOLO("final.pt")

# Global variable for video feed
camera = None


def generate_frames():
    """ Generate frames from webcam with YOLO inference. """
    global camera
    while camera and camera.isOpened():
        success, frame = camera.read()
        if not success:
            break

        # Perform YOLO inference
        results = model.predict(frame)
        annotated_frame = results[0].plot()

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        # Yield frame for live streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    """ Render homepage. """
    return render_template('index.html')


@app.route('/start_feed')
def start_feed():
    """ Start video capture. """
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(1)
    return jsonify({"status": "started"})


@app.route('/stop_feed')
def stop_feed():
    """ Stop video capture. """
    global camera
    if camera and camera.isOpened():
        camera.release()
    return jsonify({"status": "stopped"})


@app.route('/video_feed')
def video_feed():
    """ Stream live video. """
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/upload', methods=['POST'])
def upload():
    """ Upload and process an image. """
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Perform YOLO inference
    img = cv2.imread(filepath)
    results = model.predict(img)
    output_filename = f"output_{file.filename}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    results[0].save(filename=output_path)

    return jsonify({"output": output_filename})


@app.route('/output/<filename>')
def get_output(filename):
    """ Serve processed output image. """
    return send_from_directory(OUTPUT_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
