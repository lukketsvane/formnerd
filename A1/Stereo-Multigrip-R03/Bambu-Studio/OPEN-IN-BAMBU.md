# Bambu Studio handoff

The `.3mf` files in this folder are **unsliced model layouts**, not G-code or verified machine jobs. They contain only printed parts, in millimetres, arranged inside a 256 × 256 plate with clear margins and gaps. They intentionally do not guess the nozzle, loaded filament, temperatures or the printer's current state.

Open the lock-fit test file first in Bambu Studio. Select the actual P1S printer, nozzle, build plate and loaded filament. Slice and inspect the layer preview before printing. Check the fit of the printed pin, clevis and wedge before committing to the complete harness.

The full-layout file contains the harness and all required printed locking pieces, with their supplied print orientation. Check support generation, especially under carrier overhangs and clevis shelves. No modelled electronics, reference pads or metal fasteners belong on the print plate.

This project was not opened in Bambu Studio or sent to a printer in the authoring session: neither application control nor a P1S connection was available. No print has been started.

The dimensions of the MB programmer stacks, sensor contact shoulders and actual cable plugs still need checking against the physical parts. The two inward-facing micro-USB sockets make plug-body clearance especially important. Keep the sensor optics and orange ribbons unloaded when fitting the retainers.
