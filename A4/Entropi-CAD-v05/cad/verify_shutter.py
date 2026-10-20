import json
from pathlib import Path
import cadquery as cq
from shutter_details import shutter_motion


ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "cad/parameters.json").read_text())
TOLERANCE = 0.0001


def intersection(a, b):
    return a.intersect(b).Volume()


def main():
    cage = cq.importers.importStep(str(ROOT / "parts/01_rib_cage.step")).val()
    manifest = json.loads((ROOT / "cad/assembly_manifest.json").read_text())
    moving_names = {"01_rib_cage", "07_shutter", "08_shutter_pin", "15_shutter_return_flexure"}
    fixed = {row["name"]: cq.importers.importStep(str(ROOT / "parts" / f'{row["name"]}.step')).val() for row in manifest if row["name"] not in moving_names}
    pairs = (("cage", "shutter"), ("cage", "pin"), ("cage", "spring"), ("shutter", "pin"), ("shutter", "spring"), ("pin", "spring"))
    errors = []
    states = []
    for displacement in (0, 0.25, 0.5, 0.75, 1.0):
        shutter, pin, spring = shutter_motion(P, displacement)
        parts = {"cage": cage, "shutter": shutter.val(), "pin": pin.val(), "spring": spring.val()}
        validity = {name: {"valid": part.isValid(), "solids": len(part.Solids())} for name, part in parts.items()}
        for name, result in validity.items():
            if not result["valid"] or result["solids"] != 1:
                errors.append(f"Invalid {name} at {displacement} mm")
        overlaps = {f"{a}/{b}": intersection(parts[a], parts[b]) for a, b in pairs}
        for name, volume in overlaps.items():
            if volume > TOLERANCE:
                errors.append(f"Unexpected {name} overlap at {displacement} mm: {volume} mm3")
        world_overlaps = {}
        for moving_name in ("shutter", "pin", "spring"):
            for fixed_name, fixed_part in fixed.items():
                a, b = parts[moving_name].BoundingBox(), fixed_part.BoundingBox()
                disjoint = a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin
                volume = 0.0 if disjoint else intersection(parts[moving_name], fixed_part)
                world_overlaps[f"{moving_name}/{fixed_name}"] = volume
                if volume > TOLERANCE:
                    errors.append(f"Unexpected {moving_name}/{fixed_name} overlap at {displacement} mm: {volume} mm3")
        states.append({"displacement_mm": displacement, "validity": validity, "intersection_volumes_mm3": overlaps, "fixed_assembly_intersection_volumes_mm3": world_overlaps})
    stops = []
    for displacement, moving_name, index in ((-0.25, "pin", 1), (1.25, "shutter", 0)):
        moving = shutter_motion(P, displacement)[index].val()
        volume = intersection(cage, moving)
        blocked = volume > TOLERANCE
        stops.append({"displacement_mm": displacement, "moving_part": moving_name, "intersection_with_cage_mm3": volume, "positive_stop_blocks_overtravel": blocked})
        if not blocked:
            errors.append(f"Missing {moving_name} stop at {displacement} mm")
    rest = shutter_motion(P, 0)
    baseline = []
    for name, expected in zip(("07_shutter", "08_shutter_pin", "15_shutter_return_flexure"), rest):
        actual = cq.importers.importStep(str(ROOT / "parts" / f"{name}.step")).val()
        difference = actual.cut(expected.val()).Volume() + expected.val().cut(actual).Volume()
        baseline.append({"part": name, "symmetric_difference_mm3": difference})
        if difference > TOLERANCE:
            errors.append(f"Exported {name} differs from the verified motion geometry")
    flexible_span = P["shutter_flexure_length"] - 1.2
    thickness = P["shutter_flexure_thickness"]
    report = {
        "units": "mm",
        "cage_source": "parts/01_rib_cage.step",
        "other_fixed_assembly_parts": list(fixed),
        "volume_tolerance_mm3": TOLERANCE,
        "nominal_motion_states": states,
        "overtravel_stops": stops,
        "exported_geometry_comparison": baseline,
        "beam": {
            "root_to_contact_mm": P["shutter_flexure_length"],
            "flexible_span_mm": flexible_span,
            "width_mm": P["shutter_flexure_width"],
            "thickness_mm": thickness,
            "analytic_small_deflection_max_strain_at_1mm": 3 * thickness / (2 * flexible_span ** 2),
            "fatigue_or_material_verification": False,
        },
        "scope": "Exact BRep intersections at five prescribed deformation states; analytic spring sizing only. The deformed beam is a geometric kinematic approximation, not an FEA or physical spring-force test. Snap insertion, actual switch fit and cyclic life are not verified.",
        "errors": errors,
        "nominal_geometry_and_positive_stops_pass": not errors,
    }
    (ROOT / "cad/shutter_verification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"motion_states": len(states), "pair_checks": len(states) * len(pairs), "additional_fixed_assembly_pair_checks": len(states) * 3 * len(fixed), "positive_stops": stops, "errors": errors, "pass": not errors}))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
