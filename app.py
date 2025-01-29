from flask import Flask, render_template, request, jsonify, url_for, redirect
import dropbox
import time
import os
import re
from datetime import datetime, timezone

app = Flask(__name__)

# ✅ Dropbox setup
DROPBOX_ACCESS_TOKEN = "sl.u.AFg7XDz5k5c4rp-eb6QDKrOLFQDzx9CnGZNapfpidJSn3lXH0HlpO_fuX46sSKqa8LO43zqo0CTLjIaParwCWI9ffvFVstkZ0KeKh-VzmF6Gluct0fqqpx3Qtr2gQpoD6j2ZkZqi2r6G3BSZ0lIkwy5g1OufSPKIJoqg-jVqE0zdj3wJcsmDuKMVS3GR1_DcSqVLapCWVHQGQ5G5GEjXa4Aq98BjZVDLwEZ7MbS5bZ_p7vg7BA-RS-n_gdMxgxBLIgrgslpL6GhfHB-rxOdky3trH88rmf-oJNvprO6D6WbcEugjnRMVuPA48A9GmbWnhWeGvjVku0cf-VXI0z6LKV-MHuzZWF0KpQKtJZFNZGkeak_yhMKj_Dt8I-o9aWxrCxOuCuTbF2bb36wUx5ye1Gg9YdwM34yML096NCXz7eKV2u0OjPYwQrSlf73Is0MyWeLJweRdum88DRx-JMgwJvWL-B-36dCYW92zZrZV12gF-fAkdZ-DPmTLUgtls-8kY-QYUV_NtTD1PcXRW559rjLSrMZ0-0mCi98RZ401sp7rWAB7OlmsS1Mw58UQ4JEnpipSCPavwu8d-2nF7vIntGY7_FsI3Fqu6JQWyJBsEL1ntM-7H4ITE4hvuFlpjh25z-aM288Op_2OQp301WY0YqWZZxqbVj6AJ-iZHxUfIwMvjrvvCFWWurcdhJxZ9kNG9ols4s6zB7UA-0vdZtaG63nZ-Po-hFMvB27d-IVag-ToGgMWZYu9feD_qe1mOfrXuQfl_C7xtppBfHhmjD5iSw35eRf5LuxNecqQDXTfThR7sb_84zFs8n9sqAzp9B8WqvgYOZeBt9cGqS1N6VwIwRhhkqNlM-DCQGRqoUZJ0j7Jrt8yz-jR8bFwdOTPhsXzjBn0iROkXxkTghgnYJ_Kfg6ndjdfIfwvrEFhVCAcAESd2bKMEIrRoyIOj2_N7swmvjV8NIYNzFBxqtw0YA_eqdl-ePslR9x7fIb0CaeXGft_ZJq8JYQAHOnix4RoGaYX94WIdy4Fb30naczldmJN7mPBD2eIt0SYoyVQEI-__FprWwwfJOcqrD53Fr0LQMb4YMutNGNGG7Cvi2ONzf_v5-lekX2wXXE-Xx27aFaOxCT-49KqjquIkTwlQ3_DQJlKVVk5uyV6gRe8gteGEIh9TtC7GCNxfFZ6E_QqNVnlvQNflpfN9eAS1VrPawk5u7GetBn-8BP2vjmQEB7SbncBqJX0zflWWgZ6hMMsO24tyReiwNw82lrk7gzkc7xPEHWbfoCvchozkwVuK1MLTx8pHIqKybfV86yZbdrPWy28YUPtegydwi80PL2Y5NWxEN8XlF6RH11l7tYIcCzrNb9RW1UdKO9iXMdtbxrRbGVdkWP65EEEHGFci8vSJlLyDyigNFf_TQIOqCrHKrBDsyb3_gyo2hZRe-bAC9G8IUqP1APBJsjxEdbmJ-iw_dFpOZ_qWuM"
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

