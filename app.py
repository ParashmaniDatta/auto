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
DROPBOX_ACCESS_TOKEN = "sl.u.AFj8-CVJCmBswDTRuDKp9E1dBvhYKaJc5psXrJck984eLKYLjwu-obRvOcL7izfQhn7du4L9YK-rXw-2TLKbMWQVcrDOUbLQ7i178BaNEmE8lHK0Yc33MFtY4yZ4iNKyKm60Irgvu1sc8aNRnlTVtR7rBKt7uhJld6q5NyoSlvT-496yuyh8Xbx9mB471RL-3JW4s3c5X1ND324Hfqjn3DgK1HevTYKhxF2eB6TsCy4hboNVeoVP39rL2A6_4FpnHnJaPGKkuSVpxb6U5tlTQMHBBXdHs4EzDZKh9oaCMxg0jeaqgGB3wTtkVOECaSg0Pp3bXdjWCZRSZLBLgsVsXIh9i5V4awS6SYqXoNI5npXgm3aOVWJJrT7IC4q8a3vEQMPvnlZsTOcAmVkEg-TdkvUBNXC2I4gu12O09Iu4eSpaDvArm-EPJaAYczOkg8itnuU0cEcpY5nsi4wa3ov1AYPDo9Ok0G8H5OcWZGowyl9i0VdkQ8ou_W9WEv8j_3X9H6Bbt7-lv5HD5cv74_73RnyH9ANnCllHVFvcycOcEe9RgbnhHGXKP_zQpoB_5aUv5YuAzUowaoZ0fndkfSbgA4JpbuW5grkiMfMio6gCBrzQMCbv-LZ6xSZ7dSTMI_30gE1lOR-8GVVIXryr1qDpTb6CiThYAsTbCDkcy-G14yvUJToCQ26nBiNieBarOS4nEhxxS0EyFUMqqGR5vA5h0fk0IcwFLaTCkpLObLZOCGy46jUA5lI3ezg4qquHcpDu96gw4bZfjZiV4DzMtUq1DUhxJ2TJObzafot__oqaQzZsRxwUObA3YUOAqp6XUE4D8SzHVDGuJBKYBwVHkBPqYZMJZDFx8-GcH1oD4Ilu7BYkP1ZEkViEidUF7h83rSnRXc_Y0-AZKlN9mM0J8YxBBg6uCZi9af0y43IbrflG8k471Q3ZQaplN-JKG5uM6AFi43Cyq8sLGWXVq5veLgzJpvQZ8s89r3kYhcAhT_4-KSQ8PIYb3gmpzGzAWElkqrGj9boK6qU_FPVi6D_WWHXz0PJy9s55kRyKd8xTeXXL3NmdQuOXDULQKXnO42IDO28MHj82YZ5Fpph0ErSesYI9INIvkaTfBuiUcgvlAO3ws8pwjCqi6WMXHOmQwhQYcgSZQHDjmueepaJEJklhubr8YLWDQcI_gooo3nIlClUeZMXyJWG0Yv64pxUGv6jxi-ltwg_9gCzk_md8h2RDfknKPGBPukYL2ud21-At9fq_mtA5SnLp3IHDDCcyyF-gmq1m9dAMwbzZm_2NLaYnXfkUSSEXiHFXdv32xad4aLD66n2JeMNIOxebos-m9w2psNDattvc7Pq3HYO8XF_0U3poKbJPUUMuDnsjhTpuTtUrKtdN-GO0DK1i2rjqQb5CnJcQQQQ8tqvYCwuyeoS_aQM6QWhfkjIk_ejntFwoCjKHtwlSft2ua7E96wcr0GkQL1NFNfE"
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
