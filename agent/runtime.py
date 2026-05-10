import time
import requests
import socket

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

CONTROL_PLANE = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

NODE_ID = socket.gethostname()


# ─────────────────────────────
# OLLAMA CALL
# ─────────────────────────────

def run_llm(prompt):

    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "phi3:mini",
            "prompt": prompt,
            "stream": False
        }
    )

    return r.json()["response"]


# ─────────────────────────────
# CONTROL PLANE CALL
# ─────────────────────────────

def get_tasks():

    r = requests.get(f"{CONTROL_PLANE}/tasks")
    return r.json()


def send_result(task_id, result):

    requests.post(
        f"{CONTROL_PLANE}/tasks/{task_id}/result",
        json={"result": result}
    )


# ─────────────────────────────
# AGENT LOOP (CORE)
# ─────────────────────────────

while True:

    tasks = get_tasks()

    for task_id, task in tasks.items():

        if task["status"] != "assigned":
            continue

        if task["assigned_to"] != NODE_ID:
            continue

        print(f"[{NODE_ID}] executing task: {task['title']}")

        result = run_llm(task["title"])

        send_result(task_id, result)

        print(f"[{NODE_ID}] done task: {task_id}")

    time.sleep(5)