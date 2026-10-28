from pathlib import Path
import hashlib
import json
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
results = []
for name in ('Stereo-Multigrip-R03', ROOT.name):
    root = ROOT.parent / name
    p = json.loads((root / 'source/parameters.json').read_text())
    carrier_path = root / 'STEP/02_multigrip_carrier.step'
    carrier = cq.importers.importStep(str(carrier_path)).val()
    lens_x = p['baseline'] / 2
    board_x = lens_x - p['lens_offset']
    board_bottom = p['mb_bottom_z'] + p['mb_pcb_t'] + p['socket_height']
    board_top = board_bottom + p['camera_pcb_t']
    sweep_start = -25.0
    for side in (-1, 1):
        def board_prism(z, height):
            return cq.Workplane('XY').box(
                p['camera_pcb_w'], p['camera_pcb_h'], height,
                centered=(True, True, False)
            ).edges('|Z').fillet(1).translate((side * board_x, 0, z)).val().rotate(
                (side * lens_x, 0, 0), (side * lens_x, 0, 1), p['module_roll_deg']
            )
        final = board_prism(board_bottom, p['camera_pcb_t'])
        sweep = board_prism(sweep_start, board_top - sweep_start)
        collision = carrier.intersect(sweep)
        results.append({
            'revision': name,
            'side': 'L' if side == -1 else 'R',
            'carrier_sha256': hashlib.sha256(carrier_path.read_bytes()).hexdigest(),
            'final_camera_pcb_intersection_mm3': round(carrier.intersect(final).Volume(), 6),
            'continuous_rear_pcb_sweep_intersection_mm3': round(collision.Volume(), 6),
            'sweep_z_mm': [sweep_start, board_top],
            'collision_regions': [
                {'volume_mm3': round(s.Volume(), 6), 'center_mm': [round(x, 6) for x in s.Center().toTuple()]}
                for s in collision.Solids()
            ]
        })
report = {
    'method': 'Exact continuous negative-Z extrusion of the nominal CAM PCB footprint, intersected with the exported carrier STEP.',
    'scope': 'Rigid straight rear insertion of nominal CAM PCB alone; other stack components can only add obstructions.',
    'interpretation': 'The documented straight rear insertion has nominal interference. Final seated PCB clearance is insufficient to prove assembly access.',
    'limitations': 'Actual board dimensions, tilted paths and elastic insertion are not evaluated. This does not establish that the physical assembly is impossible.',
    'results': results
}
out = ROOT / 'checks/manual-insertion-review.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
