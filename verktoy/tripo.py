import json
import os
import sys
import time

import requests

BASE = "https://openapi.tripo3d.ai/v3"
VENTAR = ("queued", "running")
BILETE = ("generation/text-to-image", "generation/image-to-image", "generation/image-to-multiview", "generation/edit-multiview")


def headers():
    return {"Authorization": f"Bearer {os.environ['TRIPO_API_KEY']}"}


def check(r):
    d = r.json()
    if d.get("code") != 0:
        raise RuntimeError(json.dumps(d))
    return d["data"]


def pool(endpoint, body):
    if endpoint in BILETE:
        return 1
    if endpoint.startswith("generation/"):
        return 5 if str(body.get("model", "")).startswith("P") else 10
    return 5 if endpoint.startswith("models/") else 10


def valider(endpoint, body):
    feil = []
    if endpoint.startswith("generation/") and "model" not in body:
        feil.append("set model eksplisitt")
    if body.get("generate_parts"):
        if body.get("texture") is not False or body.get("pbr") is not False:
            feil.append("generate_parts krev texture=false og pbr=false")
        if body.get("smart_low_poly") or body.get("quad"):
            feil.append("generate_parts kan ikkje kombinerast med smart_low_poly eller quad")
    if str(body.get("model", "")).startswith("P"):
        if any(body.get(k) for k in ("generate_parts", "smart_low_poly", "geometry_quality")):
            feil.append("P-serien støttar ikkje generate_parts, smart_low_poly eller geometry_quality")
        if body.get("quad") and str(body["model"]).startswith("P1"):
            feil.append("P1 avviser quad")
    if endpoint == "mesh/decimate":
        m, fl = body.get("model", "v2.0"), body.get("face_limit")
        if "model" not in body:
            feil.append("set model eksplisitt på decimate (default er v2.0)")
        if m == "v1.0" and fl is None:
            feil.append("decimate v1.0 krev face_limit")
        if m in ("v2.0", "v3.0") and fl is not None and not 500 <= fl <= (10000 if body.get("quad") else 20000):
            feil.append("decimate v2/v3: face_limit 500–20 000 (quad 500–10 000)")
        if body.get("smart_uv") and m != "v3.0":
            feil.append("smart_uv berre på decimate v3.0")
    if feil:
        raise ValueError(f"{endpoint}: " + "; ".join(feil))


def upload(path):
    with open(path, "rb") as f:
        return check(requests.post(f"{BASE}/files", headers=headers(), files={"file": f}, timeout=120))["file_token"]


def submit(endpoint, body, tries=60):
    valider(endpoint, body)
    for i in range(tries):
        r = requests.post(f"{BASE}/{endpoint}", headers=headers(), json=body, timeout=60)
        d = r.json()
        if d.get("code") not in (2000, 1007):
            break
        vent = r.headers.get("Retry-After") or r.headers.get("X-RateLimit-Reset")
        time.sleep(min(float(vent) if vent and vent.replace(".", "").isdigit() else 2 ** min(i + 1, 5), 32))
    if d.get("code") != 0:
        raise RuntimeError(json.dumps(d))
    return d["data"]["task_id"]


def task(task_id):
    return check(requests.get(f"{BASE}/tasks/{task_id}", headers=headers(), timeout=60))


def wait(task_id, poll=4, timeout=1800):
    t0 = time.time()
    while True:
        d = task(task_id)
        if d["status"] not in VENTAR:
            return d
        if time.time() - t0 > timeout:
            raise TimeoutError(f"{task_id} køyrer framleis; vent vidare med same task-ID, ikkje send på nytt")
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
    return check(requests.get(f"{BASE}/account/balance", headers=headers(), timeout=30))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "upload":
        print(upload(sys.argv[2]))
    elif cmd == "balance":
        print(json.dumps(balance()))
    elif cmd == "task":
        print(json.dumps(wait(sys.argv[2]), indent=2))
    elif cmd == "valider":
        for job in json.load(open(sys.argv[2])):
            valider(job["endpoint"], job["body"])
            print(job["name"], "ok", "pool", pool(job["endpoint"], job["body"]))
