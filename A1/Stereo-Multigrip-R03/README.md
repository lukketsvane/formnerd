# Stereo Multigrip R03

Nominal-fit CAD prototype. Six main printed parts, twelve printed T-pins and twelve removable retaining wedges. No metal screws or threaded inserts are used by this revision.

The two complete camera/programmer stacks rotate together by 12 degrees about their individual lens axes. The optical centres remain 76.326 mm apart on the same horizontal line. This staggers the two inward-facing USB connectors. The 8 x 10 x 7 mm plug envelopes have zero nominal mutual overlap and zero overlap with the harness in the checked model. They are reference volumes, not measurements of the user's actual leads. Both camera images will share the same roll; orientation/calibration must accommodate it.

## Fit first

Print the four parts in `fit_coupon/` before the harness. Insert the tongue into the fork, slide the T-pin through, then seat the cross wedge by hand. The pin must slide without hammering; the retaining wedge should stay seated and remain removable by its pull tab. Do not force a tight key or substitute a screw into a slot. Adjust `key_height` or lateral `key_clearance` and regenerate if the coupon is too tight or loose. The body joints use the same profile.

Pins print flat with a coplanar head and shank. Wedges print on their broad flat side. Individual `PRINT_*.stl` files are centred on the bed at Z=0. Main-body orientations are supplied as geometry, not a checked or sliced printer job.

## Assembly order

1. Place each complete ESP32-CAM plus MB stack into its carrier pocket from the rear. The flexible camera ribbon and soldered pins must stay clear of every supporting ledge.
2. Fit the left and right rear MB keepers. Each has an upper and lower fork joint. Insert one T-pin per joint and secure its exposed tail using one retaining wedge.
3. Each sensor yoke includes four integral 0.5 mm corner contacts. They must land on the rigid sensor-module shoulders, clear of the lens barrel and ribbon. Fit each sensor yoke from the front onto its hard stops; lock its two fork joints using T-pins and wedges. The printed contacts have nominal zero-gap shoulder contact without designed compression. Never force a key to push down a sensor. If a contact bears on the lens/ribbon or prevents the yoke seating, stop and adjust the parameter or carefully fit the contact height before assembly. The nominal pin/slot height difference is 0.10 mm; actual print fit must be checked.
4. Place the power bank in the rear cradle. Use accurately fitted, non-conductive anti-rattle shims at the peripheral support ledges if required. Keep its broad faces uncompressed and its ports accessible.
5. Join the carrier to the cradle. Install the four main T-pins at the long-edge joints and retain each with a cross wedge.
6. Route the camera leads through the open middle and lower exit. The inward sockets require compact right-angle leads; check their actual moulded bodies before fitting. The ends of the power bank stay open for its charging/output leads. Optional cord-tie slots are in the perimeter; no tie is included or required to operate a lock.

For disassembly, pull the cross wedge first, then withdraw its T-pin. The T-pin provides the positive mechanical capture across the joint. Wedge seating relies on the tapered print fit and must be checked; this is not a certified vibration-resistant latch.

## Files and scope

- `STEP/Stereo-Multigrip-R03-assembly.step`: printed parts plus simplified hardware references.
- `STEP/Stereo-Multigrip-R03-harness-only.step`: thirty separately named printed solids.
- `STEP/USB-keepouts-reference.step`: adjustable plug and cable-route reference volumes.
- `STL/PRINT_*.stl`: the thirty printable parts; the other STL files are assembly/render references.
- `source/parameters.json` and `source/build_harness.py`: editable CadQuery model.
- `checks/geometry-checks.json`: validity, connectivity and intersection results for the generated nominal geometry.

Bank and ESP32-CAM dimensions originate from the supplied nominal 1:1 PDF. That PDF does not contain the MB programmer boards. MB dimensions, header height, sensor shoulders, plugs and sensor-contact height remain assumptions. The design is not physically fit-tested. Hardware references are not vendor production CAD. Larger programmer boards require a coordinated cage/keeper change; the script guards against silently increasing them beyond the current nests.

## Feltreparasjon for laus ramme (24.10.2026)

Om berre dei to store R03-rammedelane er printa, vil dei vere lause utan dei fire tverrpinnane og fire låsekilane. For å berge dei eksisterande printa: sjå [R03-REPAIR-LOCKS-R01](REPAIR-LOCKS-R01/README.md) med passformprøve, tre klemmande pinnevariantar, fire hovudlåsesett, dei mindre kamerafestene og 3MF-plater for P1S. Fysisk passform må verifiserast før montering av elektronikk.
