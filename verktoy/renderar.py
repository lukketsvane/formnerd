import glob
import json
import os
import shutil
import sys

import numpy as np
import trimesh

import hus
import strek

SKAL = "#c9cbc8"
FARGE = {"mb": "#2b6cb0", "usb": "#b8b8b8", "hylse": "#222222", "list": "#222222", "esp32s": "#c0c0c0", "cam": "#2f855a",
         "sd": "#d0d0d0", "kamera": "#333333", "linse": "#111111", "blits": "#ffeb99"}


def stablar(flytt=(0, 0, 0)):
    ut = []
    for f in sorted(glob.glob(f"{M}/stabel_*.glb")):
        namn = os.path.basename(f)[9:-4].split("_")[0]
        ut.append({"fil": f, "farge": FARGE.get(namn, "#888888"), "flytt": list(flytt)})
    return ut


def visir(k, P):
    """Mørkt visirfelt på fremre skal, som eige objekt til rendering (valfri måling)."""
    front = trimesh.load(f"{M}/fremre_skal.glb", force="mesh")
    ly = P["linser"]["y"]["verdi"]
    zs = P["linser"]["z"]["verdi"]
    c, n = front.triangles_center, front.face_normals
    s = k["stablar"]
    xv = min(st["visir_x"] for st in s)
    maske = (n[:, 0] > 0.75) & (np.abs(c[:, 1] - ly) < 13) & (c[:, 2] > min(zs) - 22) & (c[:, 2] < max(zs) + 14) & (c[:, 0] > xv - 3)
    v = front.submesh([np.flatnonzero(maske)], append=True)
    v.apply_translation((0.05, 0, 0))
    v.export(f"{TMP}/visir.glb")


def snitt(y):
    os.makedirs(f"{TMP}/snitt", exist_ok=True)
    ut = []
    for f in sorted(glob.glob(f"{M}/*.glb")):
        m = trimesh.load(f, force="mesh")
        if m.bounds[0][1] > y:
            continue
        S = hus.til_mf(m) ^ hus.boks((-1e3, -1e3, -1e3), (1e3, y, 1e3)) if m.is_watertight else None
        if S is None or S.is_empty():
            mm = m.slice_plane((0, y, 0), (0, -1, 0))
            if mm is None or not len(mm.faces):
                continue
        else:
            mm = hus.til_tm(S)
        sti = f"{TMP}/snitt/{os.path.basename(f)}"
        mm.export(sti)
        namn = os.path.basename(f)[:-4]
        nøkkel = namn[9:].split("_")[0] if namn.startswith("stabel") else namn
        ut.append({"fil": sti, "farge": FARGE.get(nøkkel, {"innmatsramme": "#e8e2d0"}.get(namn, SKAL))})
    return ut


def lag(namn, scene):
    mappe = f"{TMP}/{namn}"
    strek.render(scene, mappe)
    shutil.copy(f"{mappe}/farge.png", f"{UT}/{namn}.png")


if __name__ == "__main__":
    PROSJEKT = sys.argv[1]
    PR = f"{PROSJEKT}/print"
    M, UT, TMP = f"{PR}/montert", f"{PR}/renderar", f"/tmp/hus-{PROSJEKT}/render"
    os.makedirs(UT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    k = json.load(open(f"{PR}/kontroll.json"))
    P = json.load(open(f"{PR}/parametrar.json"))
    visir(k, P)
    FR = [1.0, 0.62, 0.72]
    lag("samla", {"storleik": 2400, "retning": FR, "zoom": 0.95, "objekt": [
        {"fil": f"{M}/fremre_skal.glb", "farge": SKAL}, {"fil": f"{M}/bakre_skal.glb", "farge": SKAL}, {"fil": f"{TMP}/visir.glb", "farge": "#3a3d40"}]})
    lag("samla_bak", {"storleik": 2400, "retning": [-1.0, 0.55, -0.7], "zoom": 0.95, "objekt": [
        {"fil": f"{M}/fremre_skal.glb", "farge": SKAL}, {"fil": f"{M}/bakre_skal.glb", "farge": SKAL}]})
    lag("eksplodert", {"storleik": 2400, "retning": [1.0, 0.7, 0.9], "zoom": 1.0, "objekt": [
        {"fil": f"{M}/bakre_skal.glb", "farge": SKAL, "flytt": [-45, 0, 0]},
        {"fil": f"{M}/innmatsramme.glb", "farge": "#e8e2d0", "flytt": [-18, 0, 0]}] + stablar() + [
        {"fil": f"{M}/fremre_skal.glb", "farge": SKAL, "flytt": [45, 0, 0]}]})
    ly = P["linser"]["y"]["verdi"]
    lag("snitt", {"storleik": 2400, "retning": [0.35, 1.0, 0.25], "zoom": 0.95, "opp": [1, 0, 0], "objekt": snitt(ly)})
    print("ok")
