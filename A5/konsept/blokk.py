import json
import os
import subprocess
import sys

import manifold3d as mf
import numpy as np
import trimesh

HER = os.path.dirname(os.path.abspath(__file__))
UT = sys.argv[1] if len(sys.argv) > 1 else f"{HER}/blokk"
os.makedirs(UT, exist_ok=True)
B, H, D, R = 57.3, 39.1, 33.0, 4.0


def avrunda(x0, x1, y0, y1, z0, z1, r):
    s = mf.Manifold.sphere(r, 48)
    return mf.Manifold.batch_hull([s.translate([x, y, z]) for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r) for z in (z0 + r, z1 - r)])


def sylinder(c, akse, r, h, n=64):
    m = mf.Manifold.cylinder(h, r, r, n)
    if akse == "x":
        m = m.rotate([0, 90, 0])
    elif akse == "y":
        m = m.rotate([-90, 0, 0])
    return m.translate(c)


def tm(m):
    g = m.to_mesh()
    return trimesh.graph.smooth_shade(trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts), angle=np.radians(25))


kropp = avrunda(0, D, 0, H, 0, B, R) - sylinder([D - 4, 16.0, 24.0], "x", 5.5, 6)
delar = {
    "kropp": (kropp, "#d9dbd9"),
    "ring": (sylinder([D, 16.0, 24.0], "x", 8.0, 3.0) - sylinder([D - 1, 16.0, 24.0], "x", 5.5, 5), "#9a9c9a"),
    "linse": (sylinder([D - 2.5, 16.0, 24.0], "x", 4.0, 2.5), "#2a2c2e"),
    "blits": (avrunda(D - 0.6, D + 0.3, 27.1 - 2.6, 27.1 + 2.6, 44.6 - 2.7, 44.6 + 2.7, 0.8), "#f4f4ee"),
    "utloysar": (sylinder([15.5, H - 0.5, 40.1], "y", 4.0, 1.3), "#55585a"),
    "brytar": (avrunda(12.4, 16.5, H - 0.4, H + 0.7, 46.8, 48.9, 0.4), "#55585a"),
    "usbc": (avrunda(18.7 - 4.6, 18.7 + 4.6, 32.5 - 1.7, 32.5 + 1.7, -0.2, 0.4, 1.6), "#2a2c2e"),
}
filer = []
for namn, (m, farge) in delar.items():
    sti = f"{UT}/{namn}.glb"
    tm(m).export(sti)
    filer.append({"fil": sti, "flytt": [0, 0, 0], "farge": farge})
for namn, d in {"34-framme": [1.0, 0.45, 0.75], "framme": [1.0, 0.05, 0.0], "34-bak": [-0.9, 0.5, -0.7]}.items():
    sc = {"storleik": 1600, "retning": d, "opp": [0, 1, 0], "flat": False, "zoom": 1.25, "objekt": filer}
    json.dump(sc, open(f"{UT}/scene-{namn}.json", "w"))
    subprocess.run(["node", f"{HER}/../../verktoy/ikea/strek.mjs", f"{UT}/scene-{namn}.json", f"{UT}/{namn}"], check=True)
    os.replace(f"{UT}/{namn}/farge.png", f"{UT}/blokk-{namn}.png")
print(UT)
