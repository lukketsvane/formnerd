import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import tripo

NAMN = {"generated_image_url": "bilete", "model_url": "model", "rendered_image_url": "preview", "seg_model_url": "seg_model"}


def run(job):
    task_id = job.get("task_id")
    try:
        task_id = task_id or tripo.submit(job["endpoint"], job["body"])
        print(job["name"], task_id, flush=True)
        d = tripo.wait(task_id)
        if d["status"] == "success":
            d = tripo.task(task_id)
    except Exception as e:
        return {**job, "task_id": task_id, "status": "error", "error": str(e)}
    rec = {**job, "task_id": task_id, "status": d["status"], "credits": d.get("credits_consumed"), "filer": {}}
    for key, url in (d.get("output") or {}).items():
        if not (key.endswith("_url") and isinstance(url, str) and url.startswith("http")):
            continue
        ext = os.path.splitext(urlparse(url).path)[1] or ".bin"
        try:
            sti = tripo.download(url, f"{job['dir']}/{NAMN.get(key, key[:-4])}{ext}")
            rec["filer"][key] = {"sti": sti, "sha256": hashlib.sha256(open(sti, "rb").read()).hexdigest()}
        except Exception as e:
            rec["download_error"] = str(e)
    if d["status"] != "success":
        rec["error"] = {k: d.get(k) for k in ("error_code", "error_message")}
    os.makedirs(job["dir"], exist_ok=True)
    json.dump({k: rec[k] for k in ("name", "endpoint", "body", "task_id", "status", "credits", "filer") if k in rec}, open(f"{job['dir']}/task.json", "w"), indent=2, ensure_ascii=False)
    return rec


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    for job in jobs:
        if not job.get("task_id"):
            tripo.valider(job["endpoint"], job["body"])
    parallelle = min([int(sys.argv[3]) if len(sys.argv) > 3 else 8] + [tripo.pool(j["endpoint"], j["body"]) for j in jobs])
    with ThreadPoolExecutor(parallelle) as ex:
        recs = list(ex.map(run, jobs))
    json.dump(recs, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    for r in recs:
        print(r["name"], r["status"], r.get("credits"), r.get("error", ""))
    print(json.dumps(tripo.balance()))
