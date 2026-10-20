import argparse
import ast
from itertools import combinations
import json
from pathlib import Path
import sys
import time

import cadquery as cq
from verify_baffle import verify_baffle
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def boxes_overlap(a, b, tolerance):
    return all(min(a[i + 1], b[i + 1]) - max(a[i], b[i]) > tolerance for i in (0, 2, 4))


def overlap(a, b, volume_tolerance, bounds_a=None, bounds_b=None):
    a_bounds = bounds(a) if bounds_a is None else bounds_a
    b_bounds = bounds(b) if bounds_b is None else bounds_b
    if not boxes_overlap(a_bounds, b_bounds, 1e-7):
        return {"volume_mm3": 0.0, "method": "disjoint_bounding_boxes", "collision": False}
    started = time.monotonic()
    common = a.intersect(b)
    volume = sum(s.Volume() for s in common.Solids())
    return {"volume_mm3": float(volume), "method": "BRep_common", "elapsed_seconds": time.monotonic() - started, "collision": bool(volume > volume_tolerance)}


def mesh_check(path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.MergingOn()
    reader.Update()
    mesh = reader.GetOutput()
    edge = vtk.vtkFeatureEdges()
    edge.SetInputData(mesh)
    edge.FeatureEdgesOff()
    edge.ManifoldEdgesOff()
    edge.BoundaryEdgesOn()
    edge.NonManifoldEdgesOn()
    edge.Update()
    bad_edges = int(edge.GetOutput().GetNumberOfCells())
    connected = vtk.vtkPolyDataConnectivityFilter()
    connected.SetInputData(mesh)
    connected.SetExtractionModeToAllRegions()
    connected.ColorRegionsOn()
    connected.Update()
    components = int(connected.GetNumberOfExtractedRegions())
    cells = vtk_to_numpy(mesh.GetPolys().GetData())
    triangles = cells.reshape((-1, 4))[:, 1:]
    vertices = vtk_to_numpy(mesh.GetPoints().GetData()).astype(float)
    v = vertices[triangles]
    signed_volume = float(np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6.0)
    directed = np.concatenate((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]))
    undirected = np.sort(directed, axis=1)
    _, inverse, counts = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
    signs = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    orientations = np.bincount(inverse, weights=signs)
    inconsistent = int(np.count_nonzero((counts == 2) & (orientations != 0)))
    degenerate = int(np.count_nonzero(np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1) < 1e-10))
    return {
        "vertices": int(len(vertices)),
        "triangles": int(len(triangles)),
        "boundary_or_nonmanifold_edges": bad_edges,
        "connected_components": components,
        "inconsistent_winding_edges": inconsistent,
        "degenerate_triangles": degenerate,
        "signed_volume_mm3": signed_volume,
        "watertight": bool(bad_edges == 0 and components == 1 and inconsistent == 0 and signed_volume > 0),
    }


def motion_check(shapes, name, moving, removed, direction, distance, step, tolerance, shape_bounds=None):
    shape_bounds = {key: bounds(shape) for key, shape in shapes.items()} if shape_bounds is None else shape_bounds
    fixed = [key for key in shapes if key not in set(moving + removed)]
    samples = np.unique(np.r_[0.0, np.arange(step, distance, step), distance])
    blockers = []
    checked = 0
    for offset in samples:
        if offset == 0 or abs(offset % 10) < 1e-7 or offset == distance:
            print(json.dumps({"motion": name, "translation_distance_mm": float(offset), "status": "checking"}), flush=True)
        delta = tuple(float(offset * c) for c in direction)
        for moving_name in moving:
            shifted = shapes[moving_name].translate(delta)
            base_bounds = shape_bounds[moving_name]
            shifted_bounds = [value + delta[index // 2] for index, value in enumerate(base_bounds)]
            for fixed_name in fixed:
                result = overlap(shifted, shapes[fixed_name], tolerance, shifted_bounds, shape_bounds[fixed_name])
                checked += 1
                if result["collision"]:
                    blockers.append({"moving_part": moving_name, "fixed_part": fixed_name, "translation_mm": delta, **result})
        if blockers:
            break
    return {
        "name": name,
        "moving_parts": moving,
        "previously_removed_parts": removed,
        "direction": direction,
        "travel_mm": distance,
        "sample_step_mm": step,
        "sample_count_requested": int(len(samples)),
        "pair_checks_completed": checked,
        "blockers": blockers,
        "sampled_path_clear": not blockers,
        "scope": "Discrete translation samples after fastener removal; not a continuous swept-volume certificate or hardware fit test.",
    }


def parameter_check(root):
    parameters = json.loads((root / "cad/parameters.json").read_text())
    used = set()
    for source in (root / "cad").glob("*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "P":
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    used.add(node.slice.value)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "P" and node.func.attr == "get" and node.args:
                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    used.add(node.args[0].value)
    metadata = {"units", "release_status", "hardware_fit_measured", "layer_height_suggested", "nozzle_diameter"}
    return {"used_by_builder": sorted(used), "declared_but_not_used_by_builder": sorted(set(parameters) - used - metadata)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skip-motion", action="store_true")
    parser.add_argument("--only-motion", choices=("rear_cover_removal", "cassette_removal", "baffle_removal", "chassis_removal", "service_cover_removal"))
    parser.add_argument("--motion-step", type=float, default=1.0)
    parser.add_argument("--volume-tolerance", type=float, default=1e-4)
    args = parser.parse_args()
    if args.skip_motion and args.only_motion:
        parser.error("--skip-motion and --only-motion cannot be combined")
    root = args.root.resolve()
    manifest = json.loads((root / "cad/assembly_manifest.json").read_text())
    parts = manifest["parts"] if isinstance(manifest, dict) else manifest
    shapes = {}
    shape_bounds = {}
    report = {"units": "mm", "volume_tolerance_mm3": args.volume_tolerance, "check_scope": "targeted_motion_only" if args.only_motion else "full_assembly", "motion_selector": args.only_motion, "parts": [], "intersections": [], "motions": [], "parameters": parameter_check(root)}
    errors = []
    for item in parts:
        name = item["name"]
        step_path = root / Path(item["file"]).with_suffix(".step")
        shape = cq.importers.importStep(str(step_path)).val()
        shapes[name] = shape
        bb = shape.BoundingBox()
        shape_bounds[name] = [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]
        row = {"name": name, "step_valid": bool(shape.isValid()), "solid_count": len(shape.Solids()), "volume_mm3": float(shape.Volume()), "size_mm": [bb.xlen, bb.ylen, bb.zlen], "within_250mm_cube_axis_aligned": max(bb.xlen, bb.ylen, bb.zlen) <= 250.0, "mesh": ({"not_rechecked_in_targeted_motion": True} if args.only_motion else mesh_check(root / item["file"]))}
        report["parts"].append(row)
        if not row["step_valid"] or row["solid_count"] != 1 or row["volume_mm3"] <= 0 or not row["within_250mm_cube_axis_aligned"] or not row["mesh"].get("watertight", True):
            errors.append({"kind": "part_check", "part": name})
        print(json.dumps({"part": name, "valid": row["step_valid"], "solids": row["solid_count"], "watertight": row["mesh"].get("watertight")}), flush=True)
    for a, b in (() if args.only_motion else combinations(shapes, 2)):
        print(json.dumps({"pair": [a, b], "status": "checking"}), flush=True)
        result = overlap(shapes[a], shapes[b], args.volume_tolerance, shape_bounds[a], shape_bounds[b])
        report["intersections"].append({"parts": [a, b], **result})
        print(json.dumps({"pair": [a, b], "status": "complete", **result}), flush=True)
        if result["collision"]:
            errors.append({"kind": "part_intersection", "parts": [a, b], "volume_mm3": result["volume_mm3"]})
            print(json.dumps(errors[-1]), flush=True)
    if not args.skip_motion:
        optical_parts = [key for key in ("06_optical_baffle", "12_lens_blank", "13_lens_blank_retainer", "17_camera_saddle", "18_camera_clamp") if key in shapes]
        chassis_parts = [key for key in ("02_chassis", "09_rear_dial", "10_io_plate", "14_dial_retainer", "19_usb_retainer") if key in shapes]
        motions = [
            ("service_cover_removal", ["20_shutter_service_cover"], [], [0,1,0], 30),
            ("rear_cover_removal", ["03_rear_cover"], [], [0, 1, 0], 85),
            ("cassette_removal", ["04_esp32_carrier", "05_board_clamp"], ["03_rear_cover"], [0, 1, 0], 85),
            ("baffle_removal", optical_parts, ["03_rear_cover", "04_esp32_carrier", "05_board_clamp"], [0, -1, 0], 50),
            ("chassis_removal", chassis_parts, ["03_rear_cover", "04_esp32_carrier", "05_board_clamp"] + optical_parts, [0, 1, 0], 105),
        ]
        for name, moving, removed, direction, travel in motions:
            if args.only_motion and name != args.only_motion:
                continue
            if not all(key in shapes for key in moving + removed):
                report["motions"].append({"name": name, "status": "not_run", "reason": "Expected part names unavailable"})
                errors.append({"kind": "motion_not_run", "motion": name})
                continue
            result = verify_baffle(shapes, root=root, tolerance=args.volume_tolerance) if name == "baffle_removal" else motion_check(shapes, name, moving, removed, direction, travel, args.motion_step, args.volume_tolerance, shape_bounds)
            report["motions"].append(result)
            if not result["sampled_path_clear"]:
                errors.append({"kind": "motion_blocked", "motion": name, "blockers": result["blockers"]})
            print(json.dumps({"motion": name, "sampled_path_clear": result["sampled_path_clear"], "blockers": result["blockers"]}), flush=True)
    report["errors"] = errors
    report["geometry_pass"] = not errors
    report["physical_hardware_fit_verified"] = False
    report["usb_charge_transfer_function_verified"] = False
    report["battery_and_thermal_design_verified"] = False
    report["release_status"] = ("TARGETED_MOTION_ONLY" if args.only_motion else "DIGITAL_GEOMETRY_ONLY") if not errors else "DIGITAL_GEOMETRY_CHECKS_FAILED"
    report_path = Path("cad") / (f"verification_{args.only_motion}.json" if args.only_motion else "verification_report.json")
    (root / report_path).write_text(json.dumps(report, indent=2))
    print(json.dumps({"geometry_pass": report["geometry_pass"], "errors": len(errors), "report": str(report_path)}), flush=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
