#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

MOBEL = re.compile(r"hylle|skap|seng|bord|stol|sofa|kommode|benk|garderobe|reol|krakk|skrivebord|vitrine|skjenk|puff|stativ|ramme|system|seksjon|oppbevaring|barnerom|vogge|servant|trille|sminke|tv-|medie|kjøkken|møbl|madrass|ribbebunn|gavl|vegg|skuff|dør")
RUBRIKK = ["strek", "layout", "klarleik", "heilskap", "wow"]


def kjor(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def info(pdf):
    ut = kjor(["pdfinfo", str(pdf)], 60)
    if ut.returncode:
        return None
    d = {}
    for l in ut.stdout.splitlines():
        if ":" in l:
            k, v = l.split(":", 1)
            d[k.strip()] = v.strip()
    m = re.search(r"([\d.]+) x ([\d.]+)", d.get("Page size", ""))
    aar = re.search(r"\d{4}", d.get("CreationDate", "") or d.get("ModDate", ""))
    return {
        "sider": int(d.get("Pages", 0) or 0),
        "breidd": float(m[1]) if m else 0,
        "hogd": float(m[2]) if m else 0,
        "aar": int(aar[0]) if aar else None,
        "produsent": d.get("Producer", ""),
    }


def raster(pdf):
    ut = kjor(["pdfimages", "-list", str(pdf)], 120)
    return max(0, len(ut.stdout.splitlines()) - 2) if ut.returncode == 0 else None


def sideutval(sider, n):
    if sider <= n:
        return list(range(1, sider + 1))
    return sorted({1 + round(i * (sider - 1) / (n - 1)) for i in range(n)})


def kontaktark(pdf, mal, sider, n, dpi, kol):
    if mal.exists():
        return str(mal)
    tmp = mal.parent / "_tmp" / mal.stem
    tmp.mkdir(parents=True, exist_ok=True)
    val = sideutval(sider, n)
    for s in val:
        kjor(["pdftoppm", "-r", str(dpi), "-png", "-f", str(s), "-l", str(s), "-singlefile", str(pdf), str(tmp / f"s-{s:03d}")])
    filer = sorted(tmp.glob("s-*.png"))
    if not filer:
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    ims = [Image.open(f).convert("L") for f in filer]
    w, h = max(i.width for i in ims), max(i.height for i in ims)
    rader = -(-len(ims) // kol)
    ark = Image.new("L", (kol * w + (kol + 1) * 10, rader * h + (rader + 1) * 10), 190)
    for k, im in enumerate(ims):
        ark.paste(im, (10 + (k % kol) * (w + 10), 10 + (k // kol) * (h + 10)))
    ark.save(mal, optimize=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return str(mal)


def er_mobel(e):
    tekst = " ".join(str(p.get(k) or "") for p in e["produkt"] for k in ("typeName", "kategori")).lower()
    return bool(MOBEL.search(tekst))


def maal(e, rot):
    fil = rot / e["fil"]
    i = info(fil)
    if not i:
        return None
    e = dict(e, **i, raster=raster(fil))
    e["mobel"] = er_mobel(e)
    e["staande"] = e["hogd"] >= e["breidd"]
    return e


def kandidatar(a):
    rot = a.korpus
    rekker = [json.loads(l) for l in (rot / "indeks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rekker = [e for e in rekker if e["slag"] == "assembly" and e.get("fil") and (rot / e["fil"]).exists()]
    print(f"{len(rekker)} nedlasta monteringsrettleiingar", file=sys.stderr)
    with ThreadPoolExecutor(a.tradar) as ex:
        malte = [e for e in ex.map(lambda e: maal(e, rot), rekker) if e]
    filtrert = [e for e in malte if a.min_sider <= e["sider"] <= a.maks_sider and e["staande"] and (e["raster"] or 0) <= a.maks_raster]
    print(f"{len(filtrert)} etter filter (sider {a.min_sider}-{a.maks_sider}, ståande, raster<={a.maks_raster})", file=sys.stderr)
    for e in filtrert:
        e["forpoeng"] = (10 if e["mobel"] else 0) + min(e["sider"], 48) / 4 + (2 if (e["aar"] or 0) >= 2018 else 0)
    filtrert.sort(key=lambda e: (-e["forpoeng"], e["aa"]))
    per_namn, valde = Counter(), []
    for e in filtrert:
        namn = (e["produkt"][0].get("name") or e["label"] or "").split()[0].upper() if e["produkt"] else e["label"]
        if per_namn[namn] >= a.per_namn:
            continue
        per_namn[namn] += 1
        valde.append(e)
        if len(valde) >= a.tal:
            break
    print(f"{len(valde)} kandidatar (maks {a.per_namn} per namn)", file=sys.stderr)
    ark = a.ut / "kontaktark"
    ark.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.tradar) as ex:
        arkfiler = list(ex.map(lambda e: kontaktark(rot / e["fil"], ark / f"{e['aa']}.png", e["sider"], a.sider, a.dpi, a.kol), valde))
    for e, f in zip(valde, arkfiler):
        e["kontaktark"] = f
    valde = [e for e in valde if e.get("kontaktark")]
    with (a.ut / "kandidatar.jsonl").open("w", encoding="utf-8") as f:
        for e in valde:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(json.dumps({"nedlasta": len(rekker), "malte": len(malte), "filtrert": len(filtrert), "kandidatar": len(valde), "mobel": sum(e["mobel"] for e in valde)}, ensure_ascii=False))


def utval(a):
    kand = {json.loads(l)["aa"]: json.loads(l) for l in (a.ut / "kandidatar.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rang = json.loads(a.rangering.read_text(encoding="utf-8"))
    mal = a.utval_mappe
    (mal / "kontaktark").mkdir(parents=True, exist_ok=True)
    linjer = ["# Utval: dei finaste IKEA-monteringsrettleiingane", "", f"{len(rang)} rettleiingar valde av eit dommarpanel (sjå `rangering.json`) frå {len(kand)} kandidatar. Kvar rad: plass, produkt, sider, poeng og grunngjeving.", "", "| # | Produkt | AA | Sider | Poeng | Grunngjeving |", "| --- | --- | --- | --- | --- | --- |"]
    for n, r in enumerate(rang, 1):
        e = kand.get(r["aa"])
        if not e:
            continue
        p0 = e["produkt"][0] if e["produkt"] else {}
        namn = re.sub(r"[^A-Za-z0-9ÆØÅæøåÄÖäö]+", "-", (p0.get("name") or e["label"] or "x")).strip("-")
        stamme = f"{n:02d}-{namn}-{e['aa']}"
        shutil.copy2(a.korpus / e["fil"], mal / f"{stamme}.pdf")
        shutil.copy2(e["kontaktark"], mal / "kontaktark" / f"{stamme}.png")
        linjer.append(f"| {n} | {p0.get('tittel') or e['label']} | [{e['aa']}]({e['url']}) | {e['sider']} | {r.get('poeng', '')} | {r.get('grunn', '')} |")
    (mal / "UTVAL.md").write_text("\n".join(linjer) + "\n", encoding="utf-8")
    shutil.copy2(a.rangering, mal / "rangering.json")
    print(f"{len(rang)} rettleiingar kopierte til {mal}")


def main():
    rot = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description="Kurerer dei finaste monteringsrettleiingane i korpuset frå hent_manualar.py.")
    ap.add_argument("steg", choices=["kandidatar", "utval"])
    ap.add_argument("--korpus", type=Path, default=rot / "referansar" / "ikea-manualar")
    ap.add_argument("--ut", type=Path, default=rot / "referansar" / "ikea-manualar" / "_arbeid" / "kurering")
    ap.add_argument("--tal", type=int, default=600)
    ap.add_argument("--per-namn", type=int, default=3)
    ap.add_argument("--min-sider", type=int, default=8)
    ap.add_argument("--maks-sider", type=int, default=80)
    ap.add_argument("--maks-raster", type=int, default=0)
    ap.add_argument("--sider", type=int, default=8, help="sider per kontaktark")
    ap.add_argument("--dpi", type=int, default=55)
    ap.add_argument("--kol", type=int, default=4)
    ap.add_argument("--tradar", type=int, default=4)
    ap.add_argument("--rangering", type=Path, help="JSON-liste [{aa, poeng, grunn}] frå dommarpanelet")
    ap.add_argument("--utval-mappe", type=Path, default=rot / "referansar" / "ikea-manualar" / "utval")
    a = ap.parse_args()
    a.ut.mkdir(parents=True, exist_ok=True)
    if a.steg == "kandidatar":
        kandidatar(a)
    else:
        if not a.rangering:
            sys.exit("--rangering må setjast")
        utval(a)


if __name__ == "__main__":
    main()
