from flask import Flask, render_template, request, jsonify, url_for, redirect
import dropbox
import time
import cv2
import threading
import os
from datetime import datetime, timezone
import re  # ✅ Import regex module

app = Flask(__name__)

# ✅ Dropbox setup
DROPBOX_ACCESS_TOKEN = "sl.CFYavqrj2MwQqb-oIBlbinNLt2OzOhFlaxHXMkw7s5i-V-0EslIuZ6KCC6OyqL4i_vbbdVyRAS2Vqye61js0lxeQcr49UCTOYr3opeKWwC7id4WtRyDEyHag-gBC1IBSxwEtnhvOtyXxYNOiC8eN"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Store active test data
tests = {}
camera_active = {}  # ✅ Track active cameras

def utc_now():
    """Return the current time in UTC as a timestamp."""
    return datetime.now(timezone.utc).timestamp()

def extract_drive_id(drive_url):
    """Extracts the Google Drive file ID from different link formats."""
    match = re.search(r"/d/([a-zA-Z0-9_-]+)/", drive_url)
    return match.group(1) if match else drive_url  # ✅ Returns ID if found, else returns input

def upload_to_dropbox(file_path, dropbox_path):
    """Uploads a file directly to Dropbox and removes local copy."""
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
    os.remove(file_path)  # ✅ Delete local file after upload

def record_video(test_id, duration):
    """Records webcam video and uploads directly to Dropbox."""
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    filename = f"{test_id}.avi"
    out = cv2.VideoWriter(filename, fourcc, 10.0, (640, 480))

    start_time = time.time()
    camera_active[test_id] = True  # ✅ Track active camera

    while time.time() - start_time < duration:
        if not camera_active.get(test_id, False):  # ✅ Stop recording on submission
            break

        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        out.write(frame)

    cap.release()
    out.release()

    upload_to_dropbox(filename, f"/Test_Recordings/{filename}")  # ✅ Upload to Dropbox

@app.route('/')
def dashboard():
    """Display the dashboard with all active tests."""
    return render_template("dashboard.html", tests=tests, datetime=datetime)

@app.route('/create_test', methods=['POST'])
def create_test():
    """Create a new test and generate a shareable test link."""
    test_id = str(int(time.time()))
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")  
    question_link = request.form.get("question_link")
    answer_link = request.form.get("answer_link")

    # ✅ Ensure all fields are provided
    if not all([start_time, end_time, duration, question_link, answer_link]):
        return jsonify({"error": "All fields are required!"}), 400

    try:
        start_timestamp = datetime.strptime(start_time, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp()
        end_timestamp = datetime.strptime(end_time, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp()
        duration = int(duration)
    except ValueError:
        return jsonify({"error": "Invalid date format or duration!"}), 400

    max_duration = end_timestamp - start_timestamp
    if duration * 60 > max_duration:
        return jsonify({"error": "Duration exceeds allowed time range!"}), 400

    # ✅ Convert Google Drive link to embed format
    question_id = extract_drive_id(question_link)
    answer_id = extract_drive_id(answer_link)
    question_embed = f"https://drive.google.com/file/d/{question_id}/preview"
    answer_embed = f"https://drive.google.com/file/d/{answer_id}/preview"

    tests[test_id] = {
        "start_time": start_timestamp,
        "end_time": end_timestamp,
        "duration": duration * 60,
        "question_link": question_embed,  # ✅ Use embed link
        "answer_link": answer_embed,  # ✅ Use embed link
        "submitted": False
    }

    test_link = url_for('waiting_page', test_id=test_id, _external=True)
    return jsonify({"message": "Test created!", "test_id": test_id, "test_link": test_link})

@app.route('/waiting/<test_id>')
def waiting_page(test_id):
    """Displays the test waiting page before the test starts."""
    test = tests.get(test_id)
    if not test:
        return "Invalid test ID!", 404
    return render_template("waiting.html", test_id=test_id, test=test)

@app.route('/test/<test_id>')
def test_page(test_id):
    """Displays the test page with the question PDF from Google Drive."""
    test = tests.get(test_id)
    if not test:
        return "Invalid test ID!", 404
    return render_template("test.html", test_id=test_id, pdf_link=test["question_link"], duration=test["duration"])

@app.route('/submit_test/<test_id>', methods=['POST'])
def submit_test(test_id):
    """Handles test submission and stops the camera."""
    test = tests.get(test_id)
    if not test:
        return "Invalid test ID!", 404

    camera_active[test_id] = False  # ✅ Stop camera recording

    log_file = f"{test_id}_activity.log"
    activity_log = request.form.get("activity_log", "No activity log recorded.")  # ✅ Prevent missing log error

    with open(log_file, "w") as f:
        f.write(activity_log)  # ✅ Ensure log file is created

    try:
        upload_to_dropbox(log_file, f"/Test_Logs/{log_file}")  # ✅ Upload logs to Dropbox
    except Exception as e:
        return jsonify({"error": f"Failed to upload logs: {str(e)}"}), 500  # ✅ Catch upload errors

    tests[test_id]["submitted"] = True  # ✅ Mark test as submitted before redirecting

    return redirect(url_for("answers_page", test_id=test_id))  # ✅ Correct redirection


@app.route('/answers/<test_id>')
def answers_page(test_id):
    """Displays the answer page only after test submission."""
    test = tests.get(test_id)
    if not test:
        return "Invalid test ID!", 404
    if not test.get("submitted", False):  # ✅ Ensure submission before access
        return "You have not submitted the test yet!", 403
    return render_template("answers.html", test_id=test_id, pdf_link=test["answer_link"])


@app.route('/start_camera/<test_id>')
def start_camera(test_id):
    """Start webcam recording in a separate thread when the test starts."""
    test = tests.get(test_id)
    if test:
        camera_active[test_id] = True  # ✅ Track active camera
        threading.Thread(target=record_video, args=(test_id, test["duration"]), daemon=True).start()
        return jsonify({"message": "Camera started!"})
    return jsonify({"error": "Invalid test ID"}), 404

if __name__ == '__main__':
    app.run(debug=True)
