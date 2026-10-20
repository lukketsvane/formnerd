import json, os, sys, time, pathlib, requests

BASE = "https://openapi.tripo3d.ai/v3"
HDR = {"Authorization": f"Bearer {os.environ['TRIPO_API_KEY']}"}


def check(r):
    j = r.json()
    if j.get("code") != 0:
        raise RuntimeError(json.dumps(j))
    return j["data"]


def upload(path):
    with open(path, "rb") as f:
        return check(requests.post(f"{BASE}/files", headers=HDR, files={"file": (pathlib.Path(path).name, f)}, timeout=120))["file_token"]


def create(endpoint, payload):
    return check(requests.post(f"{BASE}/{endpoint}", headers=HDR, json=payload, timeout=120))["task_id"]


def wait(task_id, timeout=1800):
    t0 = time.time()
    while time.time() - t0 < timeout:
        d = check(requests.get(f"{BASE}/tasks/{task_id}", headers=HDR, timeout=60))
        if d["status"] not in ("queued", "running"):
            return d
        time.sleep(5)
    raise TimeoutError(task_id)


def download(url, dest):
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    pathlib.Path(dest).write_bytes(r.content)
    return dest


def balance():
    return check(requests.get(f"{BASE}/account/balance", headers=HDR, timeout=60))["balance"]


def run(endpoint, payload_json, out_prefix):
    payload = json.loads(pathlib.Path(payload_json[1:]).read_text() if payload_json.startswith("@") else payload_json)
    for key in ("input",):
        v = payload.get(key)
        if isinstance(v, str) and os.path.exists(v):
            payload[key] = upload(v)
    if "inputs" in payload:
        payload["inputs"] = [upload(v) if os.path.exists(v) else v for v in payload["inputs"]]
    tid = create(endpoint, payload)
    d = wait(tid)
    out = d.get("output") or {}
    saved = {}
    for k, url in out.items():
        if isinstance(url, str) and url.startswith("http"):
            ext = pathlib.Path(url.split("?")[0]).suffix or ".bin"
            saved[k] = download(url, f"{out_prefix}_{k}{ext}")
    rec = {"task_id": tid, "status": d["status"], "credits": d.get("credits_consumed"), "files": saved, "payload": payload, "raw": d}
    pathlib.Path(f"{out_prefix}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    print(json.dumps({k: rec[k] for k in ("task_id", "status", "credits", "files")}, ensure_ascii=False))
    return rec


if __name__ == "__main__":
    if sys.argv[1] == "balance":
        print(balance())
    elif sys.argv[1] == "upload":
        print(upload(sys.argv[2]))
    else:
        run(sys.argv[1], sys.argv[2], sys.argv[3])
