# R04 USB18 manual: content and mechanics audit

Source revision: `88cc8f327fba72e6517ea30dcadc4e978419da37`. The recovered checkout is `/workspace/scratch/185d3eec6f20/formnerd`; no AGENTS.md exists in the repository tree. Source geometry is unchanged. Audit date: 2026-10-25 Europe/Oslo.

## Scope and counts

The camera-only harness has 21 printed parts: carrier 02, keepers 03/04, yokes 05/06, eight camera pins and eight short camera wedges. The optional battery frame adds nine printed parts: cradle 01, four frame pins and four long frame wedges. The complete assembly therefore has 30 printed parts.

The R03-to-R04 replacement plate contains exactly 11 new parts, not a new three-part complete product: three main parts and eight small wedges. Reusing the full R03 assembly accounts for the other 19 printed pieces. The camera-only upgrade reuses ten printed pieces and replaces eleven.

| ID | Part | Full quantity | R04 action |
|---|---|---:|---|
| 01 | Battery cradle | 1 | Reuse R03; optional in camera-only configuration |
| 02 | Camera carrier | 1 | New R04 |
| 03 | Left MB keeper | 1 | New R04 |
| 04 | Right MB keeper | 1 | New R04 |
| 05 | Left sensor yoke | 1 | Reuse R03 |
| 06 | Right sensor yoke | 1 | Reuse R03 |
| 10_frame_*_pin | Frame T-pin | 4 | Reuse R03 |
| 10_frame_*_wedge | Long frame wedge, 16 mm | 4 | Reuse R03 |
| 20_keeper_*_pin | Keeper T-pin | 4 | Reuse R03 |
| 20_keeper_*_wedge | Short keeper wedge, 9.5 mm | 4 | New R04 |
| 30_yoke_*_pin | Yoke T-pin | 4 | Reuse R03 |
| 30_yoke_*_wedge | Short yoke wedge, 9.5 mm | 4 | New R04 |

Hardware: two ESP32-CAM modules, two ESP32-CAM-MB USB bases and two compatible microUSB cables. Optional compatible powerbank; source envelope is nominal 94 x 62 x 15 mm. The model includes no fastening screws, nuts, loose sensor pads or added cable ties. Yoke contact pads are integral printed geometry, four per yoke. Do not invent hardware in the BOM. A soft work surface, flush cutters and a small file may help remove print support; they are preparation tools, not threaded fastener tools.

## Coordinate and handedness convention

Front is the lens side, positive Z. Rear is the MB side, negative Z. Left/right mean the user's view looking at the lens side, not the view from the rear. Both camera pods rotate +18 degrees in the XY plane around their own lens axes. They do not toe inward. Lens optical axes stay parallel and centers remain 76.326 mm apart. The detailed left electronics are rotated 180 degrees relative to the right electronics, not reflected.

The local camera pin direction is `v=(cos18,sin18,0)=(0.951057,0.309017,0)`. All eight camera pins have their T-head on the -v side and enter in +v. The four outer frame pins have their T-head on the -X side and enter +X. The short and long wedges have tabs toward +Z and insert toward -Z. Their tapered tips enter the transverse slots in the T-pins; the wedges are not screws and the T-pins do not twist.

## Mechanical sequence that the figures may legitimately show

1. Disconnect both USB cables. Support the electronics and optional powerbank before dismantling any R03 lock.
2. Separate all old parts carefully and identify the eleven new pieces. Retain 01, 05/06, all twelve T-pins and four long frame wedges. Replace old 02/03/04 and all eight camera wedges. Do not mix long frame wedges with short camera wedges.
3. Remove print supports from R04 holes, channels and bearing surfaces. Check for cracks, bridging debris and distorted parts. Do not force a pin or wedge to correct a blocked hole. Existing fit coupon geometry can test the pin/tongue/fork interface separately.
4. Dry-check actual plug and cable clearance. The optional USB gauge is only a thin support frame, not a substitute for the final holders or an operational housing. The CAD plug/cable values are assumptions, not measurements.
5. Establish an unforced way of putting each actual camera/MB assembly into the new carrier before continuing. This remains UNRESOLVED. The known straight rear route collides in nominal CAD; final placement alone is not evidence of an insertion path. Show only final seated board orientation, with no validated motion arrow. Do not prescribe a tilt path, elastic snap or board bending. Stop and revise/check the route if the board does not enter freely.
6. With the electronics held in their intended final position, insert both new MB keepers 03 and 04 from the rear, translating +Z. Keep the battery frame, yokes, pins, wedges and cables absent during this approach. This order is the condition of the continuous CAD sweep check.
7. Once both keepers are seated, lock them with four reused 20-series T-pins (+v), then four new short 20-series wedges (-Z). Maintain support until locked; check keeper feet support the MB PCB without bowing it.
8. Place reused yokes 05 and 06 from the lens side, translating -Z onto their hard stops. The inward throat must clear the flex ribbon. Four small printed pads should land on stiff sensor shoulders, not the lens, flex or exposed components. Source design is zero nominal pad gap with no designed compression. A wedge must not be used to pull a mismatching yoke down.
9. Insert four reused 30-series T-pins (+v), then four new short 30-series wedges (-Z). Check tabs remain accessible and the electronics are not loaded.
10. Connect both USB plugs while the rear is still open. For source axes, the left plug approaches toward -v and the right plug toward +v; each goes straight along its own socket axis, not along global X. Support the socket/base and push on the plug shell, not the cable. Keep both cable routes clear of wedges and frame joints.
11. Perform an open test of both cameras with their actual USB power/data setup. Check stable images, lens clearance, no cutout caused by cable movement, and correct left/right assignment. Source software/calibration is outside this mechanical manual; 18 degree common pod roll and the 180 degree opposite mounting require image orientation and stereo calibration to match the actual assembly. Do not claim existing calibration stays valid.
12. Optional full assembly: put the compatible powerbank into cradle 01, orient its ports toward the modeled opening, and bring cradle/bank forward from the rear (+Z) while keeping cables out of the joints. This is intended final geometry, not a measured real-bank fit guarantee. No dedicated battery motion sweep was published. Do not give a force or snap instruction.
13. Align all four outer tongue/fork joints. Insert four reused frame T-pins in +X, then four long 16 mm wedges from the front (-Z). These are the only long wedges in the completed assembly.
14. Final inspection: all twelve pins and twelve wedges present for full build (eight/eight for camera-only), no cable/board/flex/lens compression, yokes on stops, both plugs fully seated, both feeds stable, accessible release tabs. Record physical observations as observations, not automatically as a pass.
15. Service: disconnect USB; support bank and camera modules; release long frame wedges then pins and cradle when fitted; unplug both USB leads; remove yoke wedges then pins and yokes; support electronics before keeper wedges/pins/keepers are removed. Board extraction remains subject to the same unresolved insertion geometry; do not prescribe a straight forced extraction.

## Concise insertion page, Nynorsk

**Avklar innføringa før du held fram.**

Teikninga viser den tiltenkte sluttplasseringa. Rett innføring bakfrå kolliderer med kameraberaren i CAD, sjølv om korta har klaring når dei sit på plass. Ein annan innføringsveg er ikkje kontrollert.

Prøv utan straum og utan kraft. Ikkje bøy kretskortet eller press på linsa. Dersom korta ikkje kjem fritt på plass, stopp her. Innføringsvegen må avklarast før bakhaldarane blir låste.

## Nominal dimensional reference

- Pod roll: 18 degrees, increased from R03's 12 degrees.
- Lens baseline: 76.326 mm, same horizontal line, parallel optical axes.
- Nominal CAM/MB fit envelopes: 40.5 x 27 x 1.6 mm each.
- Detailed external CAM render source: 40.0 x 27 mm; its XY was not stretched to 40.5. Render geometry is not dimensional certification.
- CAM bottom Z: 32.1 mm; MB bottom Z: 22.0 mm; nominal header height: 8.5 mm.
- Short camera wedge length: 9.5 mm. Long frame wedge length: 16.0 mm. Both retain the same pin engagement zone; short tip removes 6.5 mm of former tip.
- Nominal T-pin: local length 24.3 mm, head width 10 mm, thickness 4.4 mm.
- USB plug-body reference: 24 mm projection x 16 mm width x 10 mm height, 0.8 mm service clearance added around.
- Nominal cable: 6 mm diameter, 8 mm straight strain relief, 12 mm centerline bend radius. These are not actual cable specifications.
- Continuous straight USB approach considered: 20 mm.
- Nominal plug-to-plug surface clearance: 7.586031 mm; plug-to-opposite-MB clearance: 2.086031 mm; service sweep pair clearance: 5.986031 mm.
- Complete harness nominal bounding box with bank: 114.511 x 82.801 x 48.257 mm. This is not a precise dimension of the user's actual cables/electronics.

## What was actually verified

The published source reports 30 valid single positive-volume solids and closed positive STL meshes; STEP reimports checked. No nominal final printed-part/fit-envelope/service-volume intersections were recorded. Keeper insertion was checked by a continuous straight sweep of the exact prismatic keeper surfaces, not sparse sampled screenshots, and the required empty-surroundings sequence is specified above. Short camera wedges retain the original pin engagement zone and pull tab. Existing R03 reuse was compared against R04 geometry.

Known failure: exact continuous straight rear sweep of nominal CAM PCB intersects R04 carrier by 149.681432 mm3 per side, while final seated intersection is zero. R03 also showed a 26.821471 mm3 straight-sweep intersection despite user photos of its physical assembly. This means straight rear insertion is not proven; it does not prove that all possible real assembly paths are impossible. No alternative tilt/flex path has been verified. Avoid absolute claims in either direction.

Detailed electronics use photo-derived component sizes and source mesh, not measurements or vendor-certified CAD. Photo resemblance, fully seated geometry and photorealistic renders are not substitutes for a physical fit test. The 25 original meshes retained in the detailed render (21 printed + two plugs + two cable envelopes) are unchanged, but small reconstructed components were not used as certified fit gauges.

The selected eleven-part high-quality replacement job was previously sliced and started once; print completion and actual assembly remain unconfirmed. No new printing should be triggered by producing this manual.

## Release and problem table content

- Pin will not slide: remove support/debris and check joint alignment; do not hammer or use the wedge to drag the joint into alignment.
- Short wedge binds: verify correct 20/30 ID, clean slot and seated pin; no twist or excessive force.
- Yoke rocks or contacts lens/flex: stop; check actual sensor height and contact pads; do not tighten by forcing the wedge.
- USB shell contacts opposite board: stop; actual plug size may exceed the assumed envelope; try/check correct cable geometry, do not bend socket.
- Cable trapped when closing cradle: reopen and reroute before relocking.
- Feed cuts out with movement: inspect seating and cable strain with frame open; do not accept as finished.
- PCB cannot enter/extract freely: unresolved assembly path; stop and revise/check geometry.

Appropriate status: comprehensive manual content for the current digital prototype, with a specific unverified PCB insertion gate. Inappropriate status: physically validated final assembly instructions or printer-certified ready production.

## Audit sources

- README.md
- source/parameters.json
- source/build_harness.py, especially key(), wedge(), lockpair(), keeper channels/sweep, sensor yoke contacts
- checks/geometry-checks.json
- checks/reuse-checks.json
- checks/independent-review.json
- checks/manual-insertion-review.json
- manual-r05/source/build_manual.py and scene-manifest.json
- presentation/electronics/assembly-verification.json and README.md
