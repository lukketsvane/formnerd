import json
import os
import sys
import time

import requests

BASE = "https://openapi.tripo3d.ai/v3"
HEADERS = {"Authorization": f"Bearer {os.environ['TRIPO_API_KEY']}"}


def check(r):
    d = r.json()
    if d.get("code") != 0:
        raise RuntimeError(json.dumps(d))
    return d["data"]


def upload(path):
    with open(path, "rb") as f:
        return check(requests.post(f"{BASE}/files", headers=HEADERS, files={"file": f}, timeout=120))["file_token"]


def submit(endpoint, body, tries=60):
    for _ in range(tries):
        d = requests.post(f"{BASE}/{endpoint}", headers=HEADERS, json=body, timeout=60).json()
        if d.get("code") not in (2000, 1007):
            break
        time.sleep(15)
    if d.get("code") != 0:
        raise RuntimeError(json.dumps(d))
    return d["data"]["task_id"]


def wait(task_id, poll=4, timeout=900):
    t0 = time.time()
    while True:
        d = check(requests.get(f"{BASE}/tasks/{task_id}", headers=HEADERS, timeout=60))
        if d["status"] in ("success", "failed", "cancelled"):
            return d
        if time.time() - t0 > timeout:
            raise TimeoutError(task_id)
        time.sleep(poll)


def download(url, path, tries=5):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    for i in range(tries):
        try:
            r = requests.get(url, timeout=300)
            r.raise_for_status()
            break
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def balance():
    return check(requests.get(f"{BASE}/account/balance", headers=HEADERS, timeout=30))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "upload":
        print(upload(sys.argv[2]))
    elif cmd == "balance":
        print(json.dumps(balance()))
    elif cmd == "task":
        print(json.dumps(wait(sys.argv[2]), indent=2))
