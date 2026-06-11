"""
app.py — The actual application being built and deployed by the CI/CD pipeline.
A simple Flask REST API for a Task Manager.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World from Render"
if __name__=="__main__":
    app.run(debug=True)
    
# In-memory store (simulates a database)
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Write report", "done": True},
]

@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks), 200

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200

@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "Title is required"}), 400
    new_task = {
        "id": len(tasks) + 1,
        "title": data["title"],
        "done": data.get("done", False),
    }
    tasks.append(new_task)
    return jsonify(new_task), 201

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    data = request.get_json()
    task.update({k: v for k, v in data.items() if k in ("title", "done")})
    return jsonify(task), 200

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    global tasks
    original_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) == original_len:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Deleted"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
