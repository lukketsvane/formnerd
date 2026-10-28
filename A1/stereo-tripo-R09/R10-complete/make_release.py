import hashlib
import json
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
R09=HERE.parent
archive=HERE/"ENTROPI_R10_MEKANISK_PROTOTYPE.zip"
inputs=[
 ("reference/TRIPO_R09_SELECTED_REFERENCE.jpg",R09/"reference"/"TRIPO_R09_SELECTED_REFERENCE.jpg"),
 ("source/outer_volume_grid.npz",R09/"cad"/"outer_volume_grid.npz"),
 ("source/H11_dual_ESP32CAM_MB_harness.step",R09/"harness"/"step"/"H11_dual_ESP32CAM_MB_harness.step"),
 ("source/H11_dual_ESP32CAM_MB_harness.stl",R09/"harness"/"stl"/"H11_dual_ESP32CAM_MB_harness.stl"),
 ("source/T11_MB_edge_fit_coupon.stl",R09/"harness"/"stl"/"T11_MB_edge_fit_coupon.stl"),
 ("source/T12_Linocell_corner_fit_coupon.stl",R09/"harness"/"stl"/"T12_Linocell_corner_fit_coupon.stl")
]
for name in ["README.md","R10_hybrid_assembly.glb","R10_analytic_inserts.step","build_r10.py","build_fittings.py","smooth_shell.py","restore_clearance.py","check_finish.py","package_r10.py","render_r10.py","render_plates.py"]:
    inputs.append((name,HERE/name))
for d in ["qa","print"]:
    for f in sorted((HERE/d).glob("*")):
        if f.is_file(): inputs.append((d+"/"+f.name,f))
for p in sorted((HERE/"parts").glob("*")):
    if p.is_file() and (
        p.stem in ("P01_R10_Tripo_front_shell_SMOOTH_CLEAR","P02_R10_Tripo_rear_shell_SMOOTH_CLEAR")
        or "SMOOTH" not in p.name and not p.stem.startswith(("P01_R10_Tripo_front_shell","P02_R10_Tripo_rear_shell"))
    ):
        inputs.append(("parts/"+p.name,p))
for d in [HERE/"review"/"smooth_CLEAR",HERE/"review"/"smooth_55"]:
    for p in sorted(d.glob("*.png")):
        inputs.append(("review/"+d.name+"/"+p.name,p))
for p in sorted((HERE/"review").glob("*_layout.png")):
    inputs.append(("review/"+p.name,p))
assert len(inputs)>25
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in inputs:
        if not p.is_file():raise RuntimeError("Missing "+str(p))
        z.write(p,name)
with zipfile.ZipFile(archive) as z:
    bad=z.testzip()
    if bad:raise RuntimeError("ZIP CRC: "+bad)
    if len(z.namelist())!=len(inputs):raise RuntimeError("ZIP item mismatch")
print(json.dumps({"package":str(archive),"files":len(inputs),"bytes":archive.stat().st_size,"sha256":hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2))
