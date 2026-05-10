import uuid
import socket
import requests
import time
import os
from control_plane.core.state import init_state, is_provisioned, mark_provisioned


from control_plane.core.state import (
    init_state,
    is_provisioned,
    mark_provisioned
)

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

BOOTSTRAP_SERVER = "http://192.168.1.10:9000"

STATE_NODE_ID_PATH = "/etc/hyperswarm/node_id"


# ─────────────────────────────
# NODE ID PERSISTENTE
# ─────────────────────────────

def get_or_create_node_id():

    os.makedirs("/etc/hyperswarm", exist_ok=True)

    if os.path.exists(STATE_NODE_ID_PATH):

        with open(STATE_NODE_ID_PATH, "r") as f:
            return f.read().strip()

    node_id = str(uuid.uuid4())

    with open(STATE_NODE_ID_PATH, "w") as f:
        f.write(node_id)

    return node_id


# ─────────────────────────────
# NODE INFO
# ─────────────────────────────

def build_node(node_id):

    return {
        "node_id": node_id,
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "role": "auto",
        "model": "phi3:mini",
        "capabilities": [
            "ollama",
            "cpu"
        ]
    }


# ─────────────────────────────
# REGISTER
# ─────────────────────────────

def register(node):

    try:

        r = requests.post(
            f"{BOOTSTRAP_SERVER}/register",
            json=node,
            timeout=5
        )

        print("[BOOTSTRAP] registered:", r.json())

        return True

    except Exception as e:

        print("[BOOTSTRAP ERROR]", e)

        return False


# ─────────────────────────────
# HEARTBEAT LOOP
# ─────────────────────────────

def heartbeat(node_id):

    while True:

        try:

            requests.post(
                f"{BOOTSTRAP_SERVER}/heartbeat",
                json={"node_id": node_id},
                timeout=5
            )

            print("[HEARTBEAT] ok")

        except Exception as e:

            print("[HEARTBEAT ERROR]", e)

        time.sleep(10)


# ─────────────────────────────
# MAIN
# ─────────────────────────────

def main():

    node_id = get_or_create_node_id()

    # 1. init local state
    init_state(node_id=node_id)

    # 2. skip if already provisioned
    if is_provisioned():

        print("[BOOTSTRAP] already provisioned, skipping deploy")

        heartbeat(node_id)
        return

    # 3. build node payload
    node = build_node(node_id)

    # 4. register to bootstrap server
    ok = register(node)

    if not ok:
        print("[BOOTSTRAP] failed registration, retrying loop")
        heartbeat(node_id)
        return

    # 5. mark provisioned locally (idempotenza)
    mark_provisioned()

    print("[BOOTSTRAP] provisioning complete")

    # 6. start heartbeat
    heartbeat(node_id)


if __name__ == "__main__":
    main()