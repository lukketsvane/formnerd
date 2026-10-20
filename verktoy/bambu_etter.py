import json, re, sys, zipfile, pathlib

BBL, maskinfil, fil, ut = map(pathlib.Path, sys.argv[1:5])
maskin = json.loads(maskinfil.read_text())
modell = json.loads((BBL / "machine" / f'{maskin["printer_model"]}.json').read_text())["model_id"]
z = zipfile.ZipFile(fil)
filer = {n: z.read(n) for n in z.namelist()}
z.close()
info = re.sub(r'(key="printer_model_id" value=")[^"]*"', rf'\g<1>{modell}"', filer["Metadata/slice_info.config"].decode())
filer["Metadata/slice_info.config"] = info.encode()
with zipfile.ZipFile(fil, "w", zipfile.ZIP_DEFLATED) as z:
    for n, d in filer.items():
        z.writestr(n, d)
ps = json.loads(filer["Metadata/project_settings.config"])
temp = re.findall(r"\d+", str(ps["nozzle_temperature"]))[0]
plater = []
for n in sorted((k for k in filer if re.match(r"Metadata/plate_\d+\.gcode$", k)), key=lambda k: int(re.findall(r"\d+", k)[0])):
    g = filer[n].decode(errors="ignore")
    start = g[g.index("; EXECUTABLE_BLOCK_START"):g.index("; MACHINE_START_GCODE_END")]
    sjekk = {"p1s_startkode": "machine: P1S" in start, "ams_lasting": "M620" in start and "M621" in start,
             f"dysetemp_{temp}": f"M109 S{temp}" in g, "printer_model_id": modell}
    assert all(sjekk.values()), (str(fil), n, sjekk)
    plater.append({"fil": n, "tid": re.search(r"total estimated time: ([^\n;]+)", g).group(1).strip(),
                   "lag": int(re.search(r"total layer number: (\d+)", g).group(1)), "kontroll": sjekk})
res = {"programvare": re.search(r'X-BBL-Client-Version" value="([^"]+)', info).group(1),
       "skrivar": ps["printer_settings_id"], "prosess": ps["print_settings_id"], "filament": ps["filament_settings_id"][0],
       "plate": ps["curr_bed_type"], "stotte": f'{ps["support_type"]}, berre fraa plata={ps["support_on_build_plate_only"]}',
       "veggar": ps["wall_loops"], "veggmotor": ps["wall_generator"], "fyll": ps["sparse_infill_density"], "lag_mm": ps["layer_height"],
       "plater": plater, "vekt_g": [float(v) for v in re.findall(r'key="weight" value="([\d.]+)', info)],
       "objekt": re.findall(r'<object identify_id="\d+" name="([^"]+)"', info),
       "åtvaringar": re.findall(r'<warning msg="([^"]+)"', info)}
ut.write_text(json.dumps(res, indent=2, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
