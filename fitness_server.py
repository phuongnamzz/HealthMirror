from flask import Flask, jsonify
from threading import Thread
import time

app = Flask(__name__)

# Dữ liệu thống kê
stats = {
    "pushups": 0,
    "pullups": 0,
    "heart_rate": 0,
    "breath_rate": 0
}

@app.route("/data")
def get_data():
    return jsonify(stats)

def run_server():
    app.run(host="0.0.0.0", port=5001)

if __name__ == "__main__":
    Thread(target=run_server).start()

    # Giả lập dữ liệu (thay bằng code AI + cảm biến của bạn)
    while True:
        stats["pushups"] += 1
        stats["pullups"] += 2
        stats["heart_rate"] = 70 + (stats["pushups"] % 20)  # random tăng nhẹ
        stats["breath_rate"] = 16 + (stats["pullups"] % 5)  # random tăng nhẹ
        time.sleep(5)
