import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import struct
import sys
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy


RX90 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
RXN90 = RX90.T
RX180 = np.diag([1.0, -1.0, -1.0])
RYN90 = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)
RY90 = RYN90.T
NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"


def read_stl(path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.MergingOn()
    reader.Update()
    mesh = reader.GetOutput()
    vertices = vtk_to_numpy(mesh.GetPoints().GetData()).astype(float)
    polygons = vtk_to_numpy(mesh.GetPolys().GetData()).reshape((-1, 4))
    if np.any(polygons[:, 0] != 3):
        raise ValueError(f"Non-triangle STL: {path.name}")
    return vertices, polygons[:, 1:].astype(np.int64)


def volume(vertices, triangles):
    v = vertices[triangles]
    return float(np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6.0)


def topology(vertices, triangles):
    directed = np.concatenate((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]))
    _, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    signs = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    orientations = np.bincount(inverse, weights=signs)
    v = vertices[triangles]
    return {
        "triangles": int(len(triangles)),
        "boundary_or_nonmanifold_edges": int(np.count_nonzero(counts != 2)),
        "inconsistent_winding_edges": int(np.count_nonzero((counts == 2) & (orientations != 0))),
        "degenerate_triangles": int(np.count_nonzero(np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]), axis=1) < 1e-10)),
    }


def write_stl(path, vertices, triangles, name):
    points = vertices[triangles].astype(np.float32)
    normals = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    normals /= np.maximum(lengths[:, None], 1e-30)
    records = np.empty(len(triangles), dtype=[("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])
    records["normal"] = normals
    records["vertices"] = points
    records["attribute"] = 0
    with path.open("wb") as stream:
        stream.write(f"Entropi print mesh; millimetres; {name}".encode()[:80].ljust(80, b" "))
        stream.write(struct.pack("<I", len(records)))
        stream.write(records.tobytes())


def align_normal_to_down(normal):
    a = normal / np.linalg.norm(normal)
    b = np.array([0.0, 0.0, -1.0])
    c = float(np.clip(a @ b, -1, 1))
    if c > 1 - 1e-12:
        return np.eye(3)
    if c < -1 + 1e-12:
        return RX180.copy()
    v = np.cross(a, b)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def automatic_flat_rotation(vertices, triangles):
    v = vertices[triangles]
    cross = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    area2 = np.linalg.norm(cross, axis=1)
    valid = area2 > 1e-10
    normals = cross[valid] / area2[valid, None]
    centers = v[valid].mean(axis=1)
    offsets = np.einsum("ij,ij->i", normals, centers)
    groups = np.c_[np.round(normals, 3), np.round(offsets, 2)]
    _, inverse = np.unique(groups, axis=0, return_inverse=True)
    sums = np.bincount(inverse, weights=area2[valid])
    for group in np.argsort(sums)[::-1][:32]:
        selected = inverse == group
        normal = (normals[selected] * area2[valid][selected, None]).sum(axis=0)
        normal /= np.linalg.norm(normal)
        plane = float(np.average(centers[selected] @ normal, weights=area2[valid][selected]))
        if float((vertices @ normal).max()) - plane <= 0.03:
            return align_normal_to_down(normal)
    return np.eye(3)


def orientation(name, vertices, triangles):
    key = name.lower()
    if "calibration" in key or "coupon" in key:
        return np.eye(3), "Original broad base face down; calibration features remain upright.", "Print before the fitted parts. Measure the holes and flexure samples with the intended material and nozzle; retain the calibrated feature sizes."
    if "cage" in key:
        return RX90, "Front annulus face down; arch and grip rise above the plate.", "Supports from the build plate are required beneath elevated ribs and grip. Inspect visible surfaces and support access in the slicer."
    if "chassis" in key:
        return RX90, "Front wall face down; the rear cavity opens upward.", "Inspect local supports beneath internal screw bridges; keep fastener bores and the optical opening clear."
    if "rear_cover" in key:
        return RXN90, "Exterior rear face down; locating lip points upward.", "Normally no supports; inspect countersinks and lip starts."
    if "carrier" in key:
        return RXN90, "Broad rear frame face down; PCB rails point upward.", "Keep PCB grooves free of supports; inspect short bridges over the grooves."
    if "baffle" in key or "lens_blank" in key:
        return RX90, "Broad front disc face down; posts or stem point upward.", "Normally no supports; keep optical bore and screw holes clear. Remove optional blank parts before fitting real optics."
    if "shutter_return_flexure" in key:
        return RY90, "Original positive X face down; flexure length Y and bending direction Z remain in the layer plane.", "Keep the thin leaf free of supports. Inspect adhesion and use a removable brim if needed; validate elastic return with the shutter calibration coupon before assembly."
    if "service_cover" in key:
        return RY90, "Original positive X planar side face down; the curved cap and bearing rise above the plate.", "Use a removable brim for the small contact face. Inspect local supports beneath the bearing overhang and curved skin; keep the fastening bore clear."
    if "shutter_pin" in key:
        return np.eye(3), "Pin axis Y horizontal; split barb bending in X remains in the layer plane.", "Inspect the small barrel contact area and head overhang; use a removable brim and local supports if needed. Keep the barb slit clear and test retention with the shutter calibration coupon."
    if "shutter" in key or "rear_dial" in key:
        return RX180, "Control cap top face down; stem points upward.", "Inspect the cap rim and small horizontal pin hole; avoid support material inside fits."
    if "io_plate" in key:
        return RYN90, "Broad side face down; port opening remains vertical through the print.", "Normally no supports; verify the actual connector and plug envelope before installation."
    if "clamp" in key or "retainer" in key:
        return np.eye(3), "Broad horizontal face down.", "Normally no supports; retain calibrated hole and slot sizes."
    return automatic_flat_rotation(vertices, triangles), "Largest exterior planar support face selected automatically.", "Inspect the selected face, overhangs, fastening access and thin features in the slicer."


def fit_rows(plate, part, margin, gap, bed):
    variants = [(0, part["size_mm"][0], part["size_mm"][1]), (90, part["size_mm"][1], part["size_mm"][0])]
    for row in plate["rows"]:
        choices = [v for v in variants if v[1] <= bed - margin - row["next_x"] + 1e-7 and v[2] <= row["height"] + 1e-7]
        if choices:
            angle, width, height = min(choices, key=lambda v: (v[2], v[1]))
            x, y = row["next_x"], row["y"]
            row["next_x"] += width + gap
            return angle, x, y, width, height
    y = margin if not plate["rows"] else max(row["y"] + row["height"] for row in plate["rows"]) + gap
    choices = [v for v in variants if v[1] <= bed - 2 * margin + 1e-7 and v[2] <= bed - margin - y + 1e-7]
    if not choices:
        return None
    angle, width, height = min(choices, key=lambda v: (v[2], v[1]))
    plate["rows"].append({"y": y, "height": height, "next_x": margin + width + gap})
    return angle, margin, y, width, height


def pack(parts, bed, margin, gap):
    plates = []
    for part in sorted(parts, key=lambda p: (-max(p["size_mm"][:2]), -np.prod(p["size_mm"][:2]), p["name"])):
        group = part["material_group"]
        placement = None
        plate = None
        for candidate in plates:
            if candidate["material_group"] == group:
                placement = fit_rows(candidate, part, margin, gap, bed)
                if placement:
                    plate = candidate
                    break
        if placement is None:
            plate = {"material_group": group, "rows": [], "parts": []}
            placement = fit_rows(plate, part, margin, gap, bed)
            if placement is None:
                raise ValueError(f"Part does not fit within the {bed:g} mm plate and {margin:g} mm margin: {part['name']}")
            plates.append(plate)
        angle, x, y, width, height = placement
        rotate = np.eye(3) if angle == 0 else np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        rotated = part["vertices"] @ rotate.T
        shift = np.array([x - rotated[:, 0].min(), y - rotated[:, 1].min(), 0.0])
        placed = rotated + shift
        placement_row = {"name": part["name"], "rotation_z_degrees": angle, "rotation_3x3": rotate.tolist(), "translation_mm": shift.tolist(), "bounds_mm": [placed.min(axis=0).tolist(), placed.max(axis=0).tolist()]}
        plate["parts"].append(placement_row)
        part["plate_placement"] = placement_row
    return plates


def write_3mf(path, plate, part_lookup, title):
    model = ET.Element(f"{{{NS}}}model", {"unit": "millimeter", "{http://www.w3.org/XML/1998/namespace}lang": "en-US"})
    metadata = ET.SubElement(model, f"{{{NS}}}metadata", {"name": "Title"})
    metadata.text = title
    resources = ET.SubElement(model, f"{{{NS}}}resources")
    materials = ET.SubElement(resources, f"{{{NS}}}basematerials", {"id": "1"})
    group_color = "#AEB2B2FF" if plate["material_group"] == "pale_gray" else "#3D4547FF"
    ET.SubElement(materials, f"{{{NS}}}base", {"name": plate["material_group"], "displaycolor": group_color})
    build = ET.SubElement(model, f"{{{NS}}}build")
    for object_id, placement in enumerate(plate["parts"], start=2):
        part = part_lookup[placement["name"]]
        obj = ET.SubElement(resources, f"{{{NS}}}object", {"id": str(object_id), "type": "model", "name": part["name"], "pid": "1", "pindex": "0"})
        mesh = ET.SubElement(obj, f"{{{NS}}}mesh")
        vertices = ET.SubElement(mesh, f"{{{NS}}}vertices")
        triangles = ET.SubElement(mesh, f"{{{NS}}}triangles")
        for v in part["vertices"]:
            ET.SubElement(vertices, f"{{{NS}}}vertex", {"x": format(v[0], ".9g"), "y": format(v[1], ".9g"), "z": format(v[2], ".9g")})
        for tri in part["triangles"]:
            ET.SubElement(triangles, f"{{{NS}}}triangle", {"v1": str(tri[0]), "v2": str(tri[1]), "v3": str(tri[2])})
        transform = np.r_[np.array(placement["rotation_3x3"]).T.reshape(-1), placement["translation_mm"]]
        ET.SubElement(build, f"{{{NS}}}item", {"objectid": str(object_id), "transform": " ".join(format(v, ".12g") for v in transform)})
    content = b'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels = b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    ET.register_namespace("", NS)
    with ZipFile(path, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("[Content_Types].xml", content)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True))


def verify_plate(path, plate, bed, margin):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Invalid 3MF ZIP: {path.name}")
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    if model.get("unit") != "millimeter":
        raise ValueError("3MF unit mismatch")
    objects = {obj.get("id"): obj for obj in model.findall(f"{{{NS}}}resources/{{{NS}}}object")}
    checked = []
    for item in model.findall(f"{{{NS}}}build/{{{NS}}}item"):
        obj = objects[item.get("objectid")]
        vertices = np.array([[float(v.get(axis)) for axis in ("x", "y", "z")] for v in obj.findall(f"{{{NS}}}mesh/{{{NS}}}vertices/{{{NS}}}vertex")])
        transform = np.fromstring(item.get("transform"), sep=" ")
        rotate = transform[:9].reshape((3, 3)).T
        translated = vertices @ rotate.T + transform[9:]
        low, high = translated.min(axis=0), translated.max(axis=0)
        if abs(low[2]) > 1e-5 or np.any(low[:2] < margin - 1e-5) or np.any(high[:2] > bed - margin + 1e-5):
            raise ValueError(f"3MF plate bounds failed: {obj.get('name')}")
        checked.append({"name": obj.get("name"), "bounds_mm": [low.tolist(), high.tolist()]})
    for a, b in combinations(checked, 2):
        low_a, high_a = np.array(a["bounds_mm"])
        low_b, high_b = np.array(b["bounds_mm"])
        if np.all(np.minimum(high_a[:2], high_b[:2]) - np.maximum(low_a[:2], low_b[:2]) > 1e-5):
            raise ValueError(f"3MF XY bounding boxes overlap: {a['name']}, {b['name']}")
    return {"unit_millimeter": True, "all_parts_z0": True, "within_plate_margin": True, "xy_bounding_boxes_nonoverlapping": True, "object_count": len(checked)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--bed", type=float, default=250.0)
    parser.add_argument("--margin", type=float, default=5.0)
    parser.add_argument("--gap", type=float, default=8.0)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve() if args.out else root / "print"
    stl_dir = out / "stl"
    stl_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / "cad/assembly_manifest.json").read_text())
    entries = manifest["parts"] if isinstance(manifest, dict) else manifest
    entries = [dict(entry) for entry in entries if entry.get("print", True)]
    known = {entry["name"] for entry in entries}
    for coupon in sorted(path for path in (root / "parts").glob("*.stl") if "coupon" in path.stem.lower() or "calibration" in path.stem.lower()):
        if coupon.stem not in known:
            entries.append({"name": coupon.stem, "file": str(coupon.relative_to(root)), "color": [0.68, 0.70, 0.70]})
    parts = []
    for entry in entries:
        source = root / entry["file"]
        vertices, triangles = read_stl(source)
        before = volume(vertices, triangles)
        rotate, description, caution = orientation(entry["name"], vertices, triangles)
        transformed = vertices @ rotate.T
        translation = -transformed.min(axis=0)
        transformed += translation
        destination = stl_dir / f"{entry['name']}.stl"
        write_stl(destination, transformed, triangles, entry["name"])
        result_vertices, result_triangles = read_stl(destination)
        after = volume(result_vertices, result_triangles)
        checks = topology(result_vertices, result_triangles)
        checks.update({"minimum_z_mm": float(result_vertices[:, 2].min()), "source_signed_volume_mm3": before, "print_signed_volume_mm3": after, "volume_preserved": abs(after - before) <= max(0.001, abs(before) * 1e-5), "rigid_rotation": bool(np.allclose(rotate @ rotate.T, np.eye(3), atol=1e-8) and abs(np.linalg.det(rotate) - 1) < 1e-8)})
        if before <= 0 or checks["boundary_or_nonmanifold_edges"] or checks["inconsistent_winding_edges"] or checks["degenerate_triangles"] or not checks["volume_preserved"] or not checks["rigid_rotation"] or abs(checks["minimum_z_mm"]) > 1e-5:
            raise ValueError(f"Print mesh verification failed: {entry['name']}: {checks}")
        low, high = result_vertices.min(axis=0), result_vertices.max(axis=0)
        if high[2] > 250.0 + 1e-5:
            raise ValueError(f"Oriented part exceeds the 250 mm print height limit: {entry['name']}")
        color = entry.get("color", [0.5, 0.5, 0.5])
        part = {"name": entry["name"], "source_file": entry["file"], "source_sha256": sha256(source.read_bytes()).hexdigest(), "print_file": f"stl/{destination.name}", "units": "mm", "orientation": description, "support_caution": caution, "rotation_3x3": rotate.tolist(), "translation_mm": translation.tolist(), "bounds_mm": [low.tolist(), high.tolist()], "size_mm": (high - low).tolist(), "material_group": "pale_gray" if np.mean(color[:3]) >= 0.4 else "dark_gray", "verification": checks, "vertices": result_vertices, "triangles": result_triangles}
        parts.append(part)
        print(json.dumps({"part": part["name"], "size_mm": part["size_mm"], "print_mesh_pass": True}), flush=True)
    plates = pack(parts, args.bed, args.margin, args.gap)
    lookup = {part["name"]: part for part in parts}
    for index, plate in enumerate(plates, start=1):
        plate["file"] = f"plate_{index:02d}_{plate['material_group']}.3mf"
        write_3mf(out / plate["file"], plate, lookup, f"Entropi print plate {index:02d}")
        plate["verification"] = verify_plate(out / plate["file"], plate, args.bed, args.margin)
        plate.pop("rows")
    for part in parts:
        part.pop("vertices")
        part.pop("triangles")
    result = {"units": "mm", "source_assembly_manifest": "cad/assembly_manifest.json", "plate_size_mm": [args.bed, args.bed], "maximum_print_height_mm": 250.0, "plate_edge_margin_mm": args.margin, "part_gap_mm": args.gap, "suggested_maximum_brim_mm": min(args.margin, args.gap / 2 - 0.5), "part_count": len(parts), "plate_count": len(plates), "parts": parts, "plates": plates, "geometry_verification_pass": True, "slicer_profile_included": False, "support_geometry_included": False, "machine_gcode_included": False, "physical_fit_verified": False, "instructions": "Generic standards-based 3MF geometry in millimetres. Open in the slicer, select the actual printer/nozzle/material, add the indicated supports or brim, inspect toolpaths, then slice. Colours indicate suggested filament groups only and do not assign extruders. Print the fit coupon first."}
    (out / "print_manifest.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"print_preparation_pass": True, "parts": len(parts), "plates": len(plates), "manifest": str(out / "print_manifest.json")}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
