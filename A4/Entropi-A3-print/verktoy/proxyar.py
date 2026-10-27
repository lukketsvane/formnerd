"""Skriv proxyen for magnetane frå konfigurasjonen; dei andre proxyane er uendra frå elektronikkmåla."""
import json, pathlib
import numpy as np, trimesh
from manifold3d import Manifold

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
dz, d, h = K["skal"]["deling_z"], K["magnetar"]["d"], K["magnetar"]["h"]
m = sum((Manifold.cylinder(2 * h, d / 2, d / 2, 48).translate([x, y, dz - h]) for x, y in K["skal"]["magnetar"]), Manifold())
g = m.to_mesh()
trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)).export(HER.parent / "print" / "proxy" / "magnetar.stl")
print("magnetar.stl", len(K["skal"]["magnetar"]), "magnetar")
