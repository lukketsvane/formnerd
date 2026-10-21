import json, re, sys, zipfile, pathlib



def modell_id(P, BBL):
    maskin = json.loads((P / "bambu" / "profil" / "maskin.json").read_text())
    return json.loads((BBL / "machine" / f'{maskin["printer_model"]}.json').read_text())["model_id"]


def rett_og_les(f, modell):
    z = zipfile.ZipFile(f)
    filer = {n: z.read(n) for n in z.namelist()}
    z.close()
    info = filer["Metadata/slice_info.config"].decode()
    info = re.sub(r'(key="printer_model_id" value=")[^"]*"', rf'\g<1>{modell}"', info)
    filer["Metadata/slice_info.config"] = info.encode()
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as ut:
        for n, d in filer.items():
            ut.writestr(n, d)
    g = filer["Metadata/plate_1.gcode"].decode(errors="ignore")
    start = g[g.index("; EXECUTABLE_BLOCK_START"):g.index("; MACHINE_START_GCODE_END")]
    ps = json.loads(filer["Metadata/project_settings.config"])
    sjekk = {"p1s_startkode": "machine: P1S" in start, "ams_lasting": "M620" in start and "M621" in start,
             "dysetemp_220": "M109 S220" in g, "printer_model_id": modell}
    assert all(sjekk.values()), (f, sjekk)
    return {
        "tid": re.search(r"total estimated time: ([^\n;]+)", g).group(1).strip(),
        "vekt_g": float(re.search(r'key="weight" value="([\d.]+)', info).group(1)),
        "lag": int(re.search(r"total layer number: (\d+)", g).group(1)),
        "objekt": re.findall(r'<object identify_id="\d+" name="([^"]+)"', info),
        "kontroll": sjekk,
    }, info, ps
