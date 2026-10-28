"""Independent audit of exported assembly, without executing or editing build.py.

Checks nominal purchased fastener envelopes as well as printed parts. Translation
checks are discrete samples, never a certification of continuous motion or fit.
The two PCB rectangles are nominal bare laminates, NOT populated ESP32/MB stacks.
"""
from pathlib import Path
import hashlib
import json
import sys

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 0.01


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tracked = [ROOT / "source/build.py", ROOT / "cad/assembly-manifest.json", ROOT / "cad/assembly.glb", ROOT / "reference/outer-regularized.glb"]
    manifest = json.loads(tracked[1].read_text())
    tracked.extend(ROOT / p["stl"] for p in manifest["parts"])
    start = {str(p.relative_to(ROOT)): digest(p) for p in tracked}
    scene = trimesh.load(tracked[2], force="scene")
    meshes = dict(scene.geometry)
    solids = {k: mf.Manifold(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32))) for k, m in meshes.items()}
    printed = sorted(k for k in solids if k.startswith("P"))
    nominal = []
    for i, center in enumerate(manifest["datum"].get("pcb_centres_mm", []), 1):
        size = np.asarray(manifest["datum"]["pcb_nominal_envelope_mm"])
        name = f"PCB{i}_bare_nominal"
        solids[name] = mf.Manifold.cube(size).translate(np.asarray(center) - size / 2)
        nominal.append(name)

    def overlap(a, b):
        return max(0.0, float((a ^ b).volume()))

    def union(ids):
        return mf.Manifold.batch_boolean([solids[k] for k in ids], mf.OpType.Add)

    collisions, allowed_threads = [], []
    ids = sorted(solids)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            v = overlap(solids[a], solids[b])
            if v <= LIMIT:
                continue
            item = {"a": a, "b": b, "intersection_mm3": round(v, 6)}
            if a.startswith("H") and b == "N" + a[1:]:
                item["reason"] = "Nominal smooth screw shaft intersects nominal nut bore; thread engagement intentionally approximated."
                allowed_threads.append(item)
            else:
                collisions.append(item)

    paths = []
    def path(name, moving, fixed, axis, offsets, purpose, base_translation=(0, 0, 0)):
        moving_shape, fixed_shape = union(moving), union(fixed)
        tests = []
        for offset in offsets:
            displacement = np.asarray(base_translation, dtype=float).copy()
            displacement[axis] += offset
            v = overlap(moving_shape.translate(displacement), fixed_shape)
            tests.append({"offset_mm": float(offset), "intersection_mm3": round(v, 6)})
        paths.append({"name": name, "moving": moving, "fixed": fixed,
                      "translation_axis": "XYZ"[axis], "base_translation_mm": list(base_translation), "purpose": purpose,
                      "method": "discrete sampled translations; reverse offsets describe insertion",
                      "samples": tests, "max_intersection_mm3": max(t["intersection_mm3"] for t in tests),
                      "all_sampled_positions_clear": all(t["intersection_mm3"] <= LIMIT for t in tests)})

    outward = sorted(set([0, .25, .5, .75, 1, 1.5, 2, 3, 4, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 35, 40, 50, 60]))
    cassette = ["P03", "P08", "P09"] + [f"{prefix}{i:02}" for prefix in "HN" for i in range(7, 11)] + nominal
    path("loaded_cassette_from_rear", cassette, ["P01", "P04", "P05", "P06"] + [f"N{i:02}" for i in range(1, 7)], 1, outward,
         "Cassette is preloaded outside housing; H05/H06 are installed after seating. Bare PCB approximation only.")
    fixed_rear = [k for k in solids if k != "P02" and k not in [f"H{i:02}" for i in range(1, 5)]]
    path("rear_shell_insertion", ["P02"], fixed_rear, 1, outward,
         "Closure screws are absent until rear shell is seated; checks capture fork and loaded cassette.")
    for part in ["P04", "P05"]:
        path(f"{part}_collar_insertion", [part], ["P01"], 1, outward,
             "Rear-to-front axial insertion before cassette installation.")
    for i in range(1, 5):
        sign = 1 if i <= 2 else -1
        path(f"N{i:02}_closure_nut_vertical_access", [f"N{i:02}"], ["P01"], 2, [sign * v for v in [0, .5, 1, 2, 3, 4, 6, 8, 10, 12, 15, 18]],
             "N01/N02 withdraw upward (+Z); N03/N04 withdraw downward (-Z). Tests insertion slot only, not hand/tool access.")
    for i in [5, 6]:
        path(f"N{i:02}_carrier_nut_side_access", [f"N{i:02}"], ["P01"], 0, [0, .5, 1, 2, 3, 4, 6, 8, 10, 12, 16],
             "Side-load slot in +X direction, before cassette installation.")
    for i in range(7, 11):
        path(f"N{i:02}_keeper_nut_front_access", [f"N{i:02}"], ["P03"], 1, [0, -.5, -1, -2, -3, -4, -6, -8, -10, -12],
             "Front access before boards/keepers are fitted; excludes shell because cassette is outside housing.")
    entry_z = float(manifest["datum"].get("shutter_insertion_entry_z_mm", -2.0))
    lift = np.linspace(0, entry_z, int(np.ceil(abs(entry_z) / .25)) + 1).tolist()
    shutter_offsets = np.arange(0, 28.001, .25).tolist() + [35, 40, 50, 60]
    path("shutter_cap_rear_access_at_declared_entry_height", ["P06"], ["P01"], 1, shutter_offsets,
         f"Compound shutter insertion segment 1: slide in from rear at Z offset {entry_z} mm.", (0, 0, entry_z))
    path("shutter_cap_final_lift", ["P06"], ["P01"], 2, lift,
         f"Compound shutter insertion segment 2: lift {-entry_z} mm into assembled position after rear slide.")
    for board in nominal:
        path(f"{board}_loading_outside_housing", [board], ["P03"], 2, [0, .25, .5, 1, 2, 5, 10, 20, 30, 40, 45],
             "Nominal bare PCB slides downward into empty carrier before keepers are fitted.")

    topology = []
    for name in printed:
        m = meshes[name]
        topology.append({"id": name, "watertight": bool(m.is_watertight), "winding_consistent": bool(m.is_winding_consistent),
                         "positive_volume": bool(m.volume > 0), "volume_mm3": float(m.volume),
                         "positive_components_above_0_01_mm3": len([x for x in solids[name].decompose() if x.volume() > .01]),
                         "manifold_status": str(solids[name].status())})
    stl_topology = []
    for p in manifest["parts"]:
        m = trimesh.load(ROOT / p["stl"], force="mesh", process=True)
        components = m.split(only_watertight=False)
        stl_topology.append({"id": p["id"], "path": p["stl"], "watertight": bool(m.is_watertight),
                             "winding_consistent": bool(m.is_winding_consistent), "positive_volume": bool(m.volume > 0),
                             "connected_components": len(components), "volume_mm3": float(m.volume),
                             "bounds_vs_manifest_max_abs_mm": float(np.abs(m.bounds - np.asarray(p["bounds_mm"])).max())})
    stl_failures = [t["id"] for t in stl_topology if not (t["watertight"] and t["winding_consistent"] and t["positive_volume"] and t["connected_components"] == 1 and t["bounds_vs_manifest_max_abs_mm"] < .001)]
    end = {str(p.relative_to(ROOT)): digest(p) for p in tracked}
    if end != start:
        raise RuntimeError("Assembly changed during audit; rerun on stable export.")
    failed_paths = [p["name"] for p in paths if not p["all_sampled_positions_clear"]]
    output = {"audit_version": 1, "source_hashes": start, "revision": manifest["revision"], "units": "mm",
              "intersection_reporting_threshold_mm3": LIMIT, "printed_topology": topology,
              "stl_roundtrip_all_print_parts_including_coupon": stl_topology,
              "stl_roundtrip_failures": stl_failures,
              "unexpected_assembled_intersections": collisions, "intentional_thread_envelope_intersections": allowed_threads,
              "translation_checks": paths, "failed_sampled_paths": failed_paths,
              "status": "digital_checks_pass_for_tested_nominal_geometry" if not collisions and not failed_paths and not stl_failures and all(t["positive_components_above_0_01_mm3"] == 1 and t["watertight"] for t in topology) else "digital_check_blockers_found",
              "limitations": ["Discrete translations do not certify continuous motion or collision-free rotations.", "Bare nominal PCB geometry is not populated ESP32-CAM, MB programmer, camera flex, optics, connectors, cables, battery, switch or electronics.", "Aperture fit is not clearance, tool accessibility, structural strength, tolerance stack, printability, slicing or physical validation.", "Thread envelopes are nominal smooth cylinders and bores; corresponding screw/nut intersection is intentional.", "This independent audit does not alter geometry."]}
    destination = ROOT / "verification/independent-audit.json"
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"status": output["status"], "stl_roundtrip_failures": stl_failures, "unexpected_intersections": collisions, "failed_paths": [{"name": p["name"], "max_intersection_mm3": p["max_intersection_mm3"]} for p in paths if not p["all_sampled_positions_clear"]], "audit": str(destination)}, indent=2))


if __name__ == "__main__":
    main()
