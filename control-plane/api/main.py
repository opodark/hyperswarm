from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="HyperSwarm Control Plane")

# ─────────────────────────────
# STATE MINIMO MA STABILE
# ─────────────────────────────

NODES = {}
TASKS = {}
EVENTS = []


# ─────────────────────────────
# ROOT
# ─────────────────────────────

@app.get("/")
def root():

    return {
        "system": "hyperswarm",
        "nodes": len(NODES),
        "tasks": len(TASKS)
    }


# ─────────────────────────────
# NODES
# ─────────────────────────────

@app.post("/nodes/register")
def register_node(node: dict):

    node_id = node["node_id"]

    NODES[node_id] = {
        "id": node_id,
        "hostname": node.get("hostname"),
        "model": node.get("model", "unknown"),
        "role": node.get("role", "auto"),
        "status": "online",
        "last_seen": datetime.utcnow()
    }

    EVENTS.append({
        "type": "node_registered",
        "node_id": node_id,
        "ts": datetime.utcnow().isoformat()
    })

    return NODES[node_id]


@app.post("/nodes/heartbeat")
def heartbeat(data: dict):

    node_id = data["node_id"]

    if node_id in NODES:

        NODES[node_id]["last_seen"] = datetime.utcnow()
        NODES[node_id]["status"] = "online"

    return {"ok": True}


@app.get("/nodes")
def get_nodes():

    return NODES


# ─────────────────────────────
# TASKS
# ─────────────────────────────

@app.post("/tasks")
def create_task(task: dict):

    task_id = task["id"]

    TASKS[task_id] = {
        "id": task_id,
        "title": task["title"],
        "status": "open",
        "assigned_to": None,
        "result": None
    }

    EVENTS.append({
        "type": "task_created",
        "task_id": task_id,
        "ts": datetime.utcnow().isoformat()
    })

    return TASKS[task_id]


@app.get("/tasks")
def get_tasks():

    return TASKS


# ─────────────────────────────
# SIMPLE DISPATCH (BARE METAL VERSION)
# ─────────────────────────────

@app.post("/swarm/dispatch")
def dispatch():

    for task_id, task in TASKS.items():

        if task["status"] != "open":
            continue

        for node_id, node in NODES.items():

            if node["status"] == "online":

                TASKS[task_id]["assigned_to"] = node_id
                TASKS[task_id]["status"] = "assigned"

                EVENTS.append({
                    "type": "task_assigned",
                    "task_id": task_id,
                    "node_id": node_id,
                    "ts": datetime.utcnow().isoformat()
                })

                break

    return {"status": "ok"}


# ─────────────────────────────
# RESULT
# ─────────────────────────────

@app.post("/tasks/{task_id}/result")
def task_result(task_id: str, payload: dict):

    if task_id in TASKS:

        TASKS[task_id]["result"] = payload["result"]
        TASKS[task_id]["status"] = "done"

        EVENTS.append({
            "type": "task_completed",
            "task_id": task_id,
            "ts": datetime.utcnow().isoformat()
        })

    return {"ok": True}