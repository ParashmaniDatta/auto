from flask import Flask, render_template, request, jsonify, url_for, redirect
import dropbox
import time
import os
import re
from datetime import datetime, timezone

app = Flask(__name__)

# ✅ Dropbox setup
DROPBOX_ACCESS_TOKEN = "sl.u.AFhIN2ruf-ZdmkM3U2cQiV2_xMTuGH_Mi4Gs7ygN8UY2B2VDWa0yRNNHFaXJlviXSwsmw_iEvAFCScNtJaKPGvBeqxqLLDpfL0-NS4ljL7X4vsomiuaqz4_hfWrut06WlBFwskvQ9uwb5obDARSyyLSARDYIcfM-ouvn27fA8NyRrxj-cp5udNJj_WLPBpGeO39DsKHtrov-aEwkwNHjnfihOeHhlZNZYmfBmWkZTS87M6cnE-UJYjve1W4t_q3SJpfXMXJ6Qo1PnLspZWKMrY-ohCGdoH7MzlIjGUEZMIuOP9CH26509Nux4o_fq3bFCDWZGeCJAyCN5cis2vDrLQ05REO9KgCsBakEcN9PevoVZSwr4XwDqnz7-ZTwWTj1S6oiaaTFm6MOy2_bHc88uTCambfbwR6GJNcyG20WV65WBX9TGQM9IVsUZWQaQIxnRgAjTMRc7FS90K3-oBkWyvZIpmACJL-i1Xr7o977Qe7-URoOqpj3RiEaKmz8VyrtWJc6KHjJ_zx-8OosR5sgHRy4J39Losr1yel44DmkJlFwa3yo9NRucB1UpC0BCB8cCHImJH2A2B3fVJfn_IskO4QMu-NLduNlvmEs-YYmmbGTXye2-OoEhvtTASNRpCkZNLUyu-CxB1-_7zqM8PNXKpRqpuQ-DWTC1AJxVyOPmt2vLw1qO3-3gl77R6mb1MWjrGckFWQJb0mAERkmMEpPgf15eEFRrpR83raFCKv8ZtEZJZyVYOFeFD9YODc1Tv_XwJpQXOZY0CsKR5cpg_K9AJtCGNwidz2aDUWG5LyDkZmClTNGLHct_qobxNuth4pVCZ--yR7amvoy1Ov1Cx4_4GpehpL_Muc8Un3GbNOsD3bd2qJoGLfs4mkmLJWQwgJALOyIPYq3lHNm_xiaCsQsti31hOsZxvO4_MFacOxp9_icu2sIBvUFUGZtSYnPUnQC-o4tXxauhHSiUHAFHzHqEo0ja_FSEcoDbVaSEOWvIqu3DneuWRRSRgZoHomi1YOKhbh672VnyHCWtcuTBhwP-1zU7K9GFSX_tKE6vWMQ_7mpd9EJ-gT9XXnSuitjTkfUr6G75W208AAlKGAtZ9aJfMYmYlbD4ZTSsuKKK4K9wT-JkMxO8FKyGKcYt18bqxSVxCVu03twAysUuG8Q7G92hyfZf4rnFkW7PlYyMnECZpChbUx5Yc3pItiEMc5uKtN-3yKpl53DuPBJvwoSXg5a_qOP6blfwvAv_2CjFUo2PgBZlzx7F9n0r08DBuPA_V7E7K-XdgsaR01Iak_Fyyt1dBElTnfnsY_sCn6Lk210UgzG1VuNMVkpfuyXQAjeRh-SZDzhUr-udn6oao5FCj5gdYjQgbYl0T1lW70WsTUJcQ1gV0B-Gz4L_j8tmoIe-Nh5LQUK-Nh3Vp744YobyiC6H2VahDjs-SZip-zyh4Z__dfr90LQ2282BligFd0w71CHBCQ"
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
    """Uploads a file directly to Dropbox and removes the local copy."""
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
    os.remove(file_path)  # ✅ Delete local file after upload

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
    """Log the start of the proctoring session instead of using OpenCV."""
    test = tests.get(test_id)
    if test:
        camera_active[test_id] = True  # ✅ Log that proctoring has started
        print(f"Screen recording started for test {test_id}")  # ✅ Debugging log
        return jsonify({"message": "Screen recording simulation started!"})  # ✅ No actual camera used
    return jsonify({"error": "Invalid test ID"}), 404

@app.route('/upload_recording/<test_id>', methods=['POST'])
def upload_recording(test_id):
    """Handles video uploads from the frontend (camera/screen recordings)."""
    if "recording" not in request.files:
        return jsonify({"error": "No recording file uploaded"}), 400

    file = request.files["recording"]
    filename = f"{test_id}.webm"
    file_path = filename  # ✅ Save in the current directory

    file.save(file_path)  # ✅ Save locally
    try:
        upload_to_dropbox(file_path, f"/Test_Recordings/{filename}")  # ✅ Upload to Dropbox
    except Exception as e:
        return jsonify({"error": f"Failed to upload to Dropbox: {str(e)}"}), 500  # ✅ Handle upload errors

    return jsonify({"message": "Recording uploaded successfully!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

