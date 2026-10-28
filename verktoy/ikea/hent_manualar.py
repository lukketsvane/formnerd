#!/usr/bin/env python3
import argparse
import csv
import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) formnerd-hent-manualar/1.0"
SITEMAP_INDEX = "https://www.ikea.com/sitemaps/sitemap.xml"
SOK = "https://sik.search.blue.cdtapps.com/{cc}/{lang}/search-result-page?q={q}&size=1000"
KATEGORI = "https://sik.search.blue.cdtapps.com/{cc}/{lang}/product-list-page?category={k}&size=1000"
PRODUKT_ID = re.compile(r"-(s?\d{8})/?$")
AA = re.compile(r"(AA-\d+-\d+)")
PDOC = re.compile(r"/pdoc/\d+_(\d+)_(\d+)_\d+\.pdf")
FELT = '"itemNo":"{}","visibleItemNo":"([^"]*)","name":"([^"]*)","type":"([^"]*)","typeName":"([^"]*)"'
LD = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
lokal = threading.local()
samanhengande_feil = 0
feil_laas = threading.Lock()


def okt():
    s = getattr(lokal, "s", None)
    if s is None:
        s = requests.Session()
        s.headers["User-Agent"] = UA
        lokal.s = s
    return s


def hent(url, forsok=5):
    global samanhengande_feil
    feil = ""
    for i in range(forsok):
        try:
            r = okt().get(url, timeout=90)
        except requests.RequestException as e:
            feil, r = str(e), None
        if r is not None and (r.status_code < 400 or r.status_code == 404):
            with feil_laas:
                samanhengande_feil = 0
            return r
        if r is not None:
            feil = f"HTTP {r.status_code}"
        time.sleep(15 * (i + 1) if r is not None and r.status_code in (403, 429) else 2 ** i)
    with feil_laas:
        samanhengande_feil += 1
        if samanhengande_feil >= 40:
            sys.exit(f"avbryt: {samanhengande_feil} feil på rad, sist {url}: {feil}")
    raise RuntimeError(f"{url}: {feil}")


def produkt_liste(marknad, arbeid):
    cc, lang = marknad.split("/")
    fil = arbeid / f"sitemap-{cc}-{lang}.json"
    if fil.exists():
        return json.loads(fil.read_text())
    idx = hent(SITEMAP_INDEX).text
    filer = re.findall(rf'<loc>(https://www\.ikea\.com/sitemaps/prod-{lang}-{cc.upper()}_\d+\.xml)</loc>', idx)
    if not filer:
        sys.exit(f"fann ingen sitemap for {marknad}")
    ut = {}
    for f in filer:
        for url in re.findall(rf'<loc>(https://www\.ikea\.com/{cc}/{lang}/p/[^<]+)</loc>', hent(f).text):
            m = PRODUKT_ID.search(url)
            if m:
                ut.setdefault(m.group(1), url)
        print(f"  {f.rsplit('/', 1)[1]}: {len(ut)} produkt så langt", file=sys.stderr)
    fil.write_text(json.dumps(ut))
    return ut


def sok_liste(marknad, sok, kategoriar):
    cc, lang = marknad.split("/")
    ut = {}

    def legg_til(produkt):
        for p in produkt:
            for v in [p] + ((p.get("gprDescription") or {}).get("variants") or []):
                m = PRODUKT_ID.search(v.get("pipUrl") or "")
                if m:
                    ut.setdefault(m.group(1), v["pipUrl"])

    for q in sok:
        d = hent(SOK.format(cc=cc, lang=lang, q=requests.utils.quote(q))).json()
        treff = (((d.get("searchResultPage") or {}).get("products") or {}).get("main") or {}).get("items") or []
        legg_til([t.get("product") or {} for t in treff])
        print(f"  søk «{q}»: {len(treff)} treff, {len(ut)} produkt så langt", file=sys.stderr)
    for k in kategoriar:
        d = hent(KATEGORI.format(cc=cc, lang=lang, k=k)).json()
        plp = d.get("productListPage") or {}
        legg_til(plp.get("productWindow") or [])
        print(f"  kategori {k}: {plp.get('productCount')} produkt i kategorien, {len(ut)} produkt så langt", file=sys.stderr)
    return ut


def json_blokk(h, nokkel):
    i = h.find(f'"{nokkel}":')
    if i < 0:
        return None
    try:
        return json.JSONDecoder().raw_decode(h, h.index("{", i))[0]
    except (ValueError, json.JSONDecodeError):
        return None


def ld_produkt(h):
    for m in LD.finditer(h):
        try:
            d = json.loads(m[1])
        except json.JSONDecodeError:
            continue
        for o in d if isinstance(d, list) else [d]:
            if isinstance(o, dict) and o.get("@type") == "Product":
                return o
    return {}


def dok_nokkel(url):
    m = AA.search(url) or PDOC.search(url)
    if m:
        return m[1] if m.re is AA else f"AA-{m[1]}-{m[2]}"
    return re.sub(r"\.pdf$", "", url.rsplit("/", 1)[1])


def les_produkt(h, pid, marknad, url):
    p = {"itemNo": pid, "marknad": marknad, "url": url, "status": 200}
    m = re.search(FELT.format(pid), h) or re.search(FELT.format(r"s?\d{8}"), h)
    if m:
        p.update(visibleItemNo=m[1], name=m[2], type=m[3], typeName=m[4])
    ld = ld_produkt(h)
    if ld.get("name"):
        p["tittel"] = ld["name"]
    if ld.get("category"):
        p["kategori"] = ld["category"]
    dok = json_blokk(h, "assemblyAndDocuments") or {}
    cp = dok.get("contentProps") or {}
    p["dokument"] = [
        {"slag": slag, "id": a.get("id"), "url": a.get("url"), "label": a.get("label")}
        for slag, g in (cp.get("attachments") or {}).items()
        for a in (g.get("attachments") or [])
        if a.get("url")
    ]
    p["video"] = [v.get("url") or v.get("src") for v in cp.get("assemblyVideos") or [] if isinstance(v, dict)]
    return p


def hent_produkt(pid, marknad, url, arbeid):
    fil = arbeid / "produkt" / f"{pid}.json"
    if fil.exists():
        return json.loads(fil.read_text())
    r = hent(url)
    p = {"itemNo": pid, "marknad": marknad, "url": url, "status": r.status_code, "dokument": []} if r.status_code == 404 else les_produkt(r.text, pid, marknad, r.url)
    fil.write_text(json.dumps(p, ensure_ascii=False))
    return p


def last_ned(url, mal):
    if mal.exists() and mal.stat().st_size > 0:
        return mal.stat().st_size, False
    r = hent(url)
    if r.status_code == 404 or not r.content.startswith(b"%PDF"):
        return 0, False
    tmp = mal.with_suffix(".del")
    tmp.write_bytes(r.content)
    tmp.replace(mal)
    return len(r.content), True


def sidetal(pdf):
    try:
        ut = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"Pages:\s+(\d+)", ut)
    return int(m[1]) if m else None


def render_sider(pdf, mappe, n, dpi):
    mappe.mkdir(parents=True, exist_ok=True)
    if any(mappe.glob("s-*.jpg")):
        return
    subprocess.run(["pdftoppm", "-r", str(dpi), "-jpeg", "-f", "1", "-l", str(n), str(pdf), str(mappe / "s")], check=False, timeout=300)


def kjoyr(fn, jobbar, tradar, namn):
    ut, ferdig, feil = [], 0, 0
    with ThreadPoolExecutor(tradar) as ex:
        for f in as_completed([ex.submit(fn, *j) for j in jobbar]):
            ferdig += 1
            try:
                ut.append(f.result())
            except Exception as e:
                feil += 1
                print(f"  feil: {e}", file=sys.stderr)
            if ferdig % 250 == 0 or ferdig == len(jobbar):
                print(f"  {namn}: {ferdig}/{len(jobbar)} ({feil} feil)", file=sys.stderr)
    return ut


def main():
    rot = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description="Hentar monteringsrettleiingar (PDF) frå ikea.com og lagar ein indeks.")
    ap.add_argument("--marknad", nargs="+", default=["no/no"], help="marknad/språk slik det står i URL-en, t.d. no/no us/en de/de")
    ap.add_argument("--ut", type=Path, default=rot / "referansar" / "ikea-manualar")
    ap.add_argument("--sok", nargs="+", default=[], help="søkjeord; hentar berre produkta søket gjev (inntil 1000 per ord) i staden for heile sitemapet")
    ap.add_argument("--kategori", nargs="+", default=[], help="kategori-ID-ar frå ikea.com/…/cat/…-<id>/, t.d. 10382 for bokhyller")
    ap.add_argument("--tradar", type=int, default=12)
    ap.add_argument("--maks", type=int, help="berre dei N første produkta (til testing)")
    ap.add_argument("--slag", nargs="+", default=["assembly"], help="dokumentslag som skal lastast ned: assembly manual other declaration customerDisassembly professionalDisassembly software")
    ap.add_argument("--berre-indeks", action="store_true", help="ikkje last ned PDF-ar")
    ap.add_argument("--sider", type=int, default=0, help="render dei N første sidene av kvar nedlasta PDF som JPG")
    ap.add_argument("--dpi", type=int, default=50)
    a = ap.parse_args()

    arbeid = a.ut / "_arbeid"
    (arbeid / "produkt").mkdir(parents=True, exist_ok=True)
    produkt = {}
    for marknad in a.marknad:
        print(f"{'søk' if a.sok or a.kategori else 'sitemap'} {marknad}", file=sys.stderr)
        liste = sok_liste(marknad, a.sok, a.kategori) if a.sok or a.kategori else produkt_liste(marknad, arbeid)
        for pid, url in liste.items():
            produkt.setdefault(pid, (marknad, url))
    ids = sorted(produkt)[: a.maks] if a.maks else sorted(produkt)
    print(f"{len(ids)} produkt å slå opp", file=sys.stderr)
    produkta = kjoyr(hent_produkt, [(pid, *produkt[pid], arbeid) for pid in ids], a.tradar, "produkt")

    dok = {}
    for p in produkta:
        for d in p["dokument"]:
            nokkel = dok_nokkel(d["url"])
            e = dok.setdefault(nokkel, {"aa": nokkel, "slag": d["slag"], "url": d["url"], "label": d["label"], "produkt": []})
            e["produkt"].append({"itemNo": p["itemNo"], "name": p.get("name"), "typeName": p.get("typeName"), "tittel": p.get("tittel"), "kategori": p.get("kategori"), "marknad": p["marknad"]})

    if not a.berre_indeks:
        for slag in a.slag:
            (a.ut / "pdf" / slag).mkdir(parents=True, exist_ok=True)
        jobbar = [(e["url"], a.ut / "pdf" / e["slag"] / f"{e['aa']}.pdf") for e in dok.values() if e["slag"] in a.slag]
        res = dict(zip([j[1] for j in jobbar], kjoyr(last_ned, jobbar, a.tradar, "pdf")))
        for e in dok.values():
            fil = a.ut / "pdf" / e["slag"] / f"{e['aa']}.pdf"
            if fil in res and res[fil][0]:
                e["fil"] = str(fil.relative_to(a.ut))
                e["bytes"] = res[fil][0]
                e["sider"] = sidetal(fil)
                if a.sider:
                    render_sider(fil, a.ut / "sider" / e["aa"], a.sider, a.dpi)

    rekker = sorted(dok.values(), key=lambda e: e["aa"])
    with (a.ut / "indeks.jsonl").open("w", encoding="utf-8") as f:
        for e in rekker:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with (a.ut / "indeks.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["aa", "slag", "url", "fil", "bytes", "sider", "produkt", "namn", "type", "kategori"])
        for e in rekker:
            p0 = e["produkt"][0]
            w.writerow([e["aa"], e["slag"], e["url"], e.get("fil", ""), e.get("bytes", ""), e.get("sider", ""), ";".join(p["itemNo"] for p in e["produkt"]), p0.get("name") or "", p0.get("typeName") or "", p0.get("kategori") or ""])

    per_slag = {}
    for e in rekker:
        s = per_slag.setdefault(e["slag"], {"dokument": 0, "lasta_ned": 0, "bytes": 0, "sider": 0})
        s["dokument"] += 1
        if e.get("fil"):
            s["lasta_ned"] += 1
            s["bytes"] += e["bytes"]
            s["sider"] += e.get("sider") or 0
    opps = {
        "marknad": a.marknad,
        "produkt": len(produkta),
        "produkt_404": sum(p["status"] == 404 for p in produkta),
        "produkt_med_dokument": sum(bool(p["dokument"]) for p in produkta),
        "produkt_med_monteringsrettleiing": sum(any(d["slag"] == "assembly" for d in p["dokument"]) for p in produkta),
        "unike_dokument": len(rekker),
        "per_slag": per_slag,
    }
    (a.ut / "oppsummering.json").write_text(json.dumps(opps, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(opps, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
