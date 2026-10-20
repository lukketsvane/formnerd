import json
import sys
from concurrent.futures import ThreadPoolExecutor

import tripo


def run(job):
    task_id = job.get("task_id")
    try:
        task_id = task_id or tripo.submit(job["endpoint"], job["body"])
        print(job["name"], task_id, flush=True)
        d = tripo.wait(task_id)
    except Exception as e:
        return {**job, "task_id": task_id, "status": "error", "error": str(e)}
    rec = {**job, "task_id": task_id, "status": d["status"], "credits": d.get("credits_consumed")}
    out = d.get("output") or {}
    for key, ext in (("generated_image_url", "png"), ("model_url", "glb"), ("rendered_image_url", "png")):
        if out.get(key):
            name = {"rendered_image_url": "preview"}.get(key, "model" if ext == "glb" else "bilete")
            try:
                rec[key] = tripo.download(out[key], f"{job['dir']}/{name}.{ext}")
            except Exception as e:
                rec[key] = None
                rec["download_error"] = str(e)
    if d["status"] != "success":
        rec["error"] = {k: d.get(k) for k in ("error_code", "error_message")}
    return rec


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    with ThreadPoolExecutor(int(sys.argv[3]) if len(sys.argv) > 3 else 8) as ex:
        recs = list(ex.map(run, jobs))
    json.dump(recs, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    for r in recs:
        print(r["name"], r["status"], r.get("credits"), r.get("error", ""))
    print(json.dumps(tripo.balance()))
