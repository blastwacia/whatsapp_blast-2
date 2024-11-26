from flask import Flask, request, render_template, jsonify
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
from time import sleep
from random import randint
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

# Global Variables
sent_numbers = []
failed_numbers = []
last_sent_index = 0
driver = None

# Helper functions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_number(nomor):
    pattern = r'^\+62\d{8,15}$'
    return re.match(pattern, nomor) is not None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        return jsonify({"status": "success", "message": f"File {filename} uploaded successfully.", "file_path": file_path})
    else:
        return jsonify({"status": "error", "message": "Invalid file type. Only CSV allowed."}), 400

@app.route("/login", methods=["GET"])
def login_whatsapp():
    global driver
    try:
        # Initialize WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        service = Service(executable_path="chromedriver")  # Adjust this if necessary
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get("https://web.whatsapp.com")
        WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH, "//div[@id='app']")))
        return jsonify({"status": "success", "message": "QR Code is shown, scan to login."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/start", methods=["POST"])
def start_blasting():
    global sent_numbers, failed_numbers, last_sent_index, driver
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be in JSON format."}), 400

    request_data = request.get_json()
    file_path = request_data.get("file_path")
    message_template = request_data.get("message", "").strip()

    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Uploaded file not found."}), 400
    if not message_template:
        return jsonify({"status": "error", "message": "Message cannot be empty."}), 400

    try:
        data = pd.read_csv(file_path, dtype={"NO HANDPHONE": str}).dropna(subset=["NO HANDPHONE"])
        data["NO HANDPHONE"] = data["NO HANDPHONE"].apply(lambda x: x.strip())

        for index, row in data.iloc[last_sent_index:].iterrows():
            nomor = row["NO HANDPHONE"]
            if not is_valid_number(nomor):
                failed_numbers.append(nomor)
                continue

            pesan = message_template.replace("{USER_ID}", row.get("USER ID", "Unknown"))
            try:
                pesan_encoded = urllib.parse.quote(pesan)
                url = f"https://web.whatsapp.com/send?phone={nomor}&text={pesan_encoded}"
                driver.get(url)
                sleep(5)

                tombol_kirim = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send']"))
                )
                tombol_kirim.click()
                sent_numbers.append(nomor)
                last_sent_index += 1
            except Exception as e:
                failed_numbers.append(nomor)
            sleep(randint(90, 180))

        driver.quit()
        return jsonify({"status": "success", "message": "Blasting completed."})
    except Exception as e:
        if driver:
            driver.quit()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
