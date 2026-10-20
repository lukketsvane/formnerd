import json, re, sys, zipfile, pathlib

P, BBL = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
maskin = json.loads((P / "bambu" / "profil" / "maskin.json").read_text())
modell = json.loads((BBL / "machine" / f'{maskin["printer_model"]}.json').read_text())["model_id"]


def rett_og_les(f):
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


hovud, info, ps = rett_og_les(P / "A3-Entropi-P1S.gcode.3mf")
out = {
    "programvare": re.search(r'X-BBL-Client-Version" value="([^"]+)', info).group(1),
    "skrivar": ps["printer_settings_id"], "prosess": ps["print_settings_id"], "filament": ps["filament_settings_id"][0],
    "plate": ps["curr_bed_type"], "stotte": f'{ps["support_type"]}, berre fraa plata={ps["support_on_build_plate_only"]}',
    "veggar": ps["wall_loops"], "veggmotor": ps["wall_generator"], "fyll": ps["sparse_infill_density"], "lag_mm": ps["layer_height"],
    **hovud, "miniatyr": False, "filer": {},
}
for f in [P / "A3-Entropi-P1S-utan-haldar.gcode.3mf"] + sorted((P / "haldar-p1s").glob("*.gcode.3mf")):
    out["filer"][str(f.relative_to(P))] = rett_og_les(f)[0]
(P / "bambu" / "slicing.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(json.dumps({k: (v if k != "filer" else {n: (x["tid"], x["vekt_g"]) for n, x in v.items()}) for k, v in out.items()}, indent=1, ensure_ascii=False))
