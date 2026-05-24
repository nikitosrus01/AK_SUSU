from flask import Flask, render_template, request, jsonify
import csv

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]

    data = []
    decoded = file.stream.read().decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)

    for row in reader:
        data.append({
            "timestamp": float(row["timestamp"]),
            "altitude": float(row["altitude"]),
            "velocity": float(row["velocity"]),
            "acceleration": float(row["acceleration"]),
            "pressure": float(row["pressure"]),
        })

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)