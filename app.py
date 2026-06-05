from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import json
import os
import re

app = Flask(__name__, static_folder=".")

# 安全檢查：確保暱稱只能是英文、數字或中文，不能包含特殊符號（防止檔案路徑出錯）
def sanitize_nickname(nickname):
    if not nickname:
        return "guest"
    return re.sub(r'[^\w\u4e00-\u9fa5]', '_', nickname).strip()

def get_db_file():
    # 從前端的 Request Header 中抓取使用者暱稱
    nickname = request.headers.get("X-User-Nickname", "guest")
    safe_name = sanitize_nickname(nickname)
    return f"db_{safe_name}.json"

def load_data():
    db_file = get_db_file()
    if not os.path.exists(db_file):
        return {"tasks": [], "history": []}
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"tasks": [], "history": []}

def save_data(tasks, history):
    db_file = get_db_file()
    data = {"tasks": tasks, "history": history}
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/api/init", methods=["GET"])
def init_app():
    return jsonify(load_data())

@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = load_data()
    req = request.json
    new_task = {
        "id": len(data["tasks"]) + 1,
        "title": req.get("title", "未命名任務"),
        "est_pomodoros": int(req.get("est_pomodoros", 1)),
        "act_pomodoros": 0,
        "streak": 0,
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["tasks"].append(new_task)
    save_data(data["tasks"], data["history"])
    return jsonify({"status": "success", "task": new_task})

@app.route("/api/tasks/<int:index>", methods=["PUT"])
def update_task(index):
    data = load_data()
    if 0 <= index < len(data["tasks"]):
        req = request.json
        data["tasks"][index].update(req)
        save_data(data["tasks"], data["history"])
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "找不到該任務"}), 404

@app.route("/api/tasks/<int:index>", methods=["DELETE"])
def delete_task(index):
    data = load_data()
    if 0 <= index < len(data["tasks"]):
        data["tasks"].pop(index)
        save_data(data["tasks"], data["history"])
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "刪除失敗"}), 404

@app.route("/api/history", methods=["POST"])
def add_history():
    data = load_data()
    req = request.json
    history_item = {
        "task_id": req.get("task_id"),
        "task_title": req.get("task_title", "無特定任務"),
        "type": "WORK",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["history"].append(history_item)
    save_data(data["tasks"], data["history"])
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)