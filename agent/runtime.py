import time
import requests
import socket
import logging
from collections import deque
from datetime import datetime

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

CONTROL_PLANE = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

NODE_ID = socket.gethostname()

POLL_INTERVAL = 3
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds base


# ─────────────────────────────
# LOGGING SERIO
# ─────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("agent")


# ─────────────────────────────
# QUEUE LOCALE
# ─────────────────────────────

task_queue = deque()


# ─────────────────────────────
# OLLAMA CALL SAFE
# ─────────────────────────────

def run_llm(prompt: str):

    try:

        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "phi3:mini",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        r.raise_for_status()

        return r.json().get("response", "")

    except Exception as e:

        log.error(f"LLM error: {e}")

        return None


# ─────────────────────────────
# CONTROL PLANE CALLS
# ─────────────────────────────

def fetch_tasks():

    try:

        r = requests.get(f"{CONTROL_PLANE}/tasks", timeout=5)
        return r.json()

    except Exception as e:

        log.error(f"fetch_tasks error: {e}")
        return {}


def send_result(task_id: str, result: str):

    try:

        requests.post(
            f"{CONTROL_PLANE}/tasks/{task_id}/result",
            json={"result": result},
            timeout=5
        )

    except Exception as e:

        log.error(f"send_result error: {e}")


# ─────────────────────────────
# TASK FILTERING
# ─────────────────────────────

def is_valid_task(task):

    return (
        task.get("status") == "assigned"
        and task.get("assigned_to") == NODE_ID
    )


# ─────────────────────────────
# RETRY WRAPPER
# ─────────────────────────────

def execute_with_retry(task):

    prompt = task["title"]

    for attempt in range(1, MAX_RETRIES + 1):

        log.info(f"Task {task['id']} attempt {attempt}")

        result = run_llm(prompt)

        if result:

            return result

        wait_time = RETRY_BACKOFF * attempt

        log.warning(f"Retrying in {wait_time}s")

        time.sleep(wait_time)

    return None


# ─────────────────────────────
# TASK PROCESSOR
# ─────────────────────────────

def process_task(task):

    task_id = task["id"]

    log.info(f"Processing task {task_id}")

    result = execute_with_retry(task)

    if result is None:

        log.error(f"Task failed permanently {task_id}")

        send_result(task_id, "ERROR: failed after retries")

        return

    send_result(task_id, result)

    log.info(f"Task completed {task_id}")


# ─────────────────────────────
# FETCH + QUEUE
# ─────────────────────────────

def update_queue():

    tasks = fetch_tasks()

    for task_id, task in tasks.items():

        if is_valid_task(task):

            task_queue.append(task)


# ─────────────────────────────
# MAIN LOOP
# ─────────────────────────────

def main():

    log.info(f"Agent started on {NODE_ID}")

    while True:

        try:

            # 1. aggiorna queue
            update_queue()

            # 2. processa queue
            while task_queue:

                task = task_queue.popleft()

                process_task(task)

        except Exception as e:

            log.error(f"main loop error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()