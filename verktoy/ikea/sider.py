"""Portrait page composition, kept separate from the geometry renderer.

Coordinates and all type/line sizes are PDF points. A page reserves its title,
instructions and acceptance check before allocating the illustration area.
"""
import math
import numpy as np
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics


class Sider:
    def _header(self, side, section, number=None):
        d, m = self.dok, self.stil["margin"]
        w = d.W - 2 * m
        d.tekst(section.upper(), m, d.H - m - 8, 8, True)
        title = side.get("title", section)
        x = m if number is None else m + 65
        y = d.H - m - 43
        if number is not None:
            d.tekst(f"{number:02d}", m, y - 2, 34, True)
        size = 25 if number is None else 20
        lines = simpleSplit(title, "MB", size, d.W - m - x)
        for line in lines:
            d.tekst(line, x, y, size, True)
            y -= size * 1.15
        y -= 7
        if side.get("intro"):
            y = d.avsnitt(side["intro"], m, y, w, 10.5)
        return y - 16

    def _endmatter(self, side):
        """Return the figure-area floor after laying out fixed bottom notes."""
        d, m = self.dok, self.stil["margin"]
        entries = [(key, side.get(key)) for key in ("warning", "note", "alternative", "check") if side.get(key)]
        if not entries:
            return 76
        width = d.W - 2 * m - 64
        prepared = [(key, simpleSplit(value, "M", 10, width)) for key, value in entries]
        height = sum(max(14, 13.5 * len(lines)) + 12 for _, lines in prepared)
        y = 71 + height
        d.c.setStrokeGray(.74)
        d.c.setLineWidth(.4)
        d.c.line(m, y + 15, d.W - m, y + 15)
        top = y + 32
        for key, lines in prepared:
            label = {"warning": "MERK", "note": "TIPS", "alternative": "EC11", "check": "KONTROLL"}[key]
            d.tekst(label, m, y, 7.5, True)
            for line in lines:
                d.tekst(line, m + 64, y, 10)
                y -= 13.5
            y -= 12
        return top

    def _partsrow(self, entries, top):
        if not entries:
            return top
        d, m = self.dok, self.stil["margin"]
        x, y = m, top - 4
        for name, quantity in entries:
            part = self.del_(name)
            text = f"{self.ident(name)}  ×{quantity}  {part.get('short_name', part.get('name', name))}"
            tw = pdfmetrics.stringWidth(text, "M", 9)
            if x + tw > d.W - m and x > m:
                x, y = m, y - 18
            d.tekst(text, x, y, 9)
            x += tw + 22
        d.c.setStrokeGray(.8)
        d.c.setLineWidth(.4)
        d.c.line(m, y - 11, d.W - m, y - 11)
        return y - 28

    def cover(self, side):
        d, m = self.dok, self.stil["margin"]
        meta = self.spec.get("meta", {})
        d.tekst(side.get("eyebrow", "FORMNERD / KAMERAPROTOTYPE"), m, d.H - m - 8, 8, True)
        d.tekst(side.get("title", "ENTROPI"), m, d.H - m - 69, 48, True)
        d.tekst(meta.get("subtitle", "Monteringsrettleiing"), m, d.H - m - 97, 15)
        box = (m - 6, 202, d.W - 2 * m + 12, 412)
        fig = {**side, "labels": False}
        self.scenefigur(fig, box, side)
        d.c.setLineWidth(.6)
        d.c.setStrokeGray(0)
        d.c.line(m, 164, m + 40, 164)
        copy = side.get("intro", "Frå lause delar til samla kamera.")
        d.avsnitt(copy, m, 142, d.W - 2 * m, 11)
        if side.get("note"):
            d.avsnitt(side["note"], m, 97, d.W - 2 * m, 9)
        if side.get("status"):
            d.tekst(side["status"], m, 79, 8)
        self.opp = np.asarray(self.view(side.get("view", self.std))["up"], float)
        d.ny_side("Framside")

    def _catalogue(self, side, hardware=False):
        d, m = self.dok, self.stil["margin"]
        names = side.get("parts") or [k for k, p in self.spec["parts"].items()
                                      if (p.get("kind") == "hardware") == hardware and not p.get("hidden")]
        top = self._header(side, "Førebuing")
        bottom = self._endmatter(side)
        cols = side.get("cols", 3 if hardware else 2)
        rows = math.ceil(len(names) / cols)
        cw = (d.W - 2 * m) / cols
        ch = (top - bottom) / rows
        for i, name in enumerate(names):
            x, y = m + (i % cols) * cw, top - (i // cols) * ch
            p = self.del_(name)
            d.tekst(self.ident(name), x + 1, y - 11, 10, True)
            d.tekst(f"×{p.get('qty', 1)}", x + cw - 10, y - 11, 10, juster="r")
            # Independent scales keep small hardware legible. The page states
            # that these inventory views are not dimensional drawings.
            iw, ih = cw - 30, max(30, ch - 76)
            d.bilete(self.mini(name, (iw, ih)), (x + 10, y - ch + 49, iw, ih))
            ty = y - ch + 33
            ty = d.avsnitt(p.get("name", name), x + 1, ty, cw - 18, 9.5, True)
            if p.get("detail"):
                d.avsnitt(p["detail"], x + 1, ty - 1, cw - 18, 8)
            if i // cols < rows - 1:
                d.c.setStrokeGray(.86)
                d.c.setLineWidth(.35)
                d.c.line(x, y - ch + 1, x + cw - 14, y - ch + 1)
        d.ny_side(side.get("title", "Komponentar" if hardware else "Prenta delar"))

    def inventory(self, side):
        self._catalogue(side)

    def hardware(self, side):
        self._catalogue(side, hardware=True)

    def exploded(self, side):
        d, m = self.dok, self.stil["margin"]
        top = self._header(side, "Oversikt")
        bottom = self._endmatter(side)
        scene = [{**s, "role": "exploded"} if "explode" in s else s for s in side["scene"]]
        box = (m + 20, bottom + 6, d.W - 2 * m - 40, top - bottom - 18)
        v = side.get("view", self.std)
        F = self.figur(scene, v, box[2:], zoom=side.get("zoom", 1.05))
        to_pdf, frame = d.bilete(F["im"], box, maske=F["maske"])
        for a, b in side.get("guides", []):
            d.stipla(to_pdf(F["P3"](a)), to_pdf(F["P3"](b)))
        mid = np.array([frame[0] + frame[2] / 2, frame[1] + frame[3] / 2])
        seen = set()
        for i, name in enumerate(F["delnamn"]):
            if name in seen or self.del_(name).get("hidden"):
                continue
            seen.add(name)
            centre = to_pdf(F["P3"](self.delar.senter[name] + F["flytt"][i]))
            q = self.punkt(F, i, centre - mid)
            if q is not None:
                target = to_pdf(q)
                offset = side.get("label_offsets", {}).get(name)
                d.leiar(self.ident(name), target,
                        target + np.asarray(offset) if offset is not None else None,
                        foretrekk=centre - mid)
        self.opp = np.asarray(self.view(v)["up"], float)
        self.rapport.append({"side": d.n + 1, "type": "exploded", **F["info"]})
        d.ny_side(side.get("title", "Slik heng delane saman"))

    def step(self, side):
        d, m = self.dok, self.stil["margin"]
        self.steg += 1
        number = side.get("n", self.steg)
        figs = side["figures"]
        top = self._header(side, "Montering", number)
        consumed = side.get("hardware")
        if consumed is None:
            # A repeated before/after view is not an extra physical part.
            counts = {}
            for f in figs:
                local = {}
                for s in f["scene"]:
                    if s.get("role") == "new" and self.del_(s["part"]).get("kind") == "hardware":
                        local[s["part"]] = local.get(s["part"], 0) + len(s.get("at") or [0])
                for k, v in local.items():
                    counts[k] = max(counts.get(k, 0), v)
            consumed = list(counts.items())
        for k, v in consumed:
            self.brukt[k] = self.brukt.get(k, 0) + v
        visible_parts = side.get("parts_used")
        if visible_parts is None:
            new_parts = {}
            for f in figs:
                for s in f["scene"]:
                    if s.get("role") == "new" and not self.del_(s["part"]).get("hidden"):
                        new_parts[s["part"]] = max(new_parts.get(s["part"], 0), len(s.get("at") or [0]))
            visible_parts = list(new_parts.items())
        top = self._partsrow(visible_parts, top)
        bottom = self._endmatter(side)
        if side.get("diagram"):
            height = side["diagram"].get("height", 164)
            self.diagram(side["diagram"], (m, bottom, d.W - 2 * m, height))
            bottom += height + 18
        gap = 30
        n = len(figs)
        flow = side.get("flow", "down")
        infos = []
        self.vist = set()  # labels are local to the operation, never global.
        if flow == "detail":
            if n != 2 or not {"centre", "span"} <= set(figs[1]):
                raise ValueError("flow: detail krev hovudfigur og éi sentrert detaljvising")
            detail = {**figs[1], "r": 71, "pos": [d.W-m-76, bottom+82]}
            main = {**figs[0], "detail": detail}
            box = (m+7, bottom+174, d.W-2*m-14, top-bottom-174)
            _, info = self.scenefigur(main, box, side)
            infos.append(info)
            y = bottom + 136
            if figs[0].get("caption"):
                y = d.avsnitt(figs[0]["caption"], m+7, y, d.W-2*m-182, 9.5) - 18
            d.tekst("DETALJ", m+7, y, 8, True)
            d.avsnitt(figs[1].get("caption", ""), m+7, y-18, d.W-2*m-182, 10)
            figs = []
        for i, fig in enumerate(figs):
            caption_lines = simpleSplit(fig.get("caption", ""), "M", 9, (d.W - 2*m) if flow == "down" else (d.W - 2*m-gap)/n)
            cap_height = len(caption_lines) * 12 + (8 if caption_lines else 0)
            if flow == "down":
                height = (top - bottom - gap * (n - 1)) / n
                box = (m + 7, top - (i + 1) * height - i * gap + cap_height, d.W - 2 * m - 14, height - cap_height)
            else:
                width = (d.W - 2 * m - gap * (n - 1)) / n
                box = (m + i * (width + gap), bottom + cap_height, width, top - bottom - cap_height)
            if box[3] < 75:
                raise ValueError(f"Side {d.n+1}: for lite rom for figur; flytt innhald til ny side")
            frame, info = self.scenefigur(fig, box, side)
            infos.append(info)
            cy = box[1] - 18
            for line in caption_lines:
                d.tekst(line, box[0], cy, 9)
                cy -= 12
            if i < n - 1 and side.get("connector", False):
                px, py = (box[0] + box[2] / 2, box[1] - cap_height - gap / 2) if flow == "down" else (box[0] + box[2] + gap / 2, (bottom + top) / 2)
                d.hol_pil(px, py, "ned" if flow == "down" else "hogre", .7)
        final_figs = side["figures"]
        self.opp = np.asarray(self.view(final_figs[-1].get("view", side.get("view", self.std)))["up"], float)
        self.rapport.append({"side": d.n + 1, "steg": number, "action": side.get("action", "assembly"),
                             "nye_delar": sum(s.get("role") == "new" for f in final_figs for s in f["scene"]), "figurar": infos})
        d.ny_side(f"{number:02d} {side.get('title', '')}")

    def diagram(self, diagram, box):
        """Exact, vector schematics; no generated imagery for wiring/polarity."""
        d, c = self.dok, self.dok.c
        x, y, w, h = box
        kind = diagram.get("type")
        c.setLineWidth(.8)
        c.setStrokeGray(.78)
        c.line(x, y + h, x + w, y + h)
        if kind == "shutter_wiring":
            d.tekst("KOPLINGSPRINSIPP", x, y + h - 19, 8, True)
            bx, by, bw, bh = x + 3, y + 24, 142, 82
            c.setStrokeGray(0)
            c.roundRect(bx, by, bw, bh, 3, stroke=1, fill=0)
            d.tekst("ESP32-CAM", bx + 14, by + 61, 10, True)
            for label, dy in (("IO13", 37), ("GND", 17)):
                d.tekst(label, bx + 14, by + dy - 3, 9)
                c.circle(bx + bw, by + dy, 2, fill=0, stroke=1)
            sx, sy = x + w - 115, by + 27
            c.setLineWidth(1.1)
            c.line(bx + bw + 2, by + 37, sx, by + 37)
            c.line(sx, by + 37, sx, sy + 29)
            c.line(bx + bw + 2, by + 17, sx + 48, by + 17)
            c.line(sx + 48, by + 17, sx + 48, sy + 29)
            c.circle(sx, sy + 29, 2.4, stroke=1, fill=0)
            c.circle(sx + 48, sy + 29, 2.4, stroke=1, fill=0)
            c.line(sx + 2, sy + 31, sx + 39, sy + 45)
            d.tekst("Brytar · normalt open", sx - 16, by - 1, 9)
            d.tekst("To kontaktgrupper", sx - 16, by - 15, 8)
            d.tekst("2 isolerte leidningar", bx + bw + 24, by + 61, 9)
        elif kind == "magnet_pair":
            d.tekst("MERK DEN FRIE FLATA", x, y + h - 20, 8, True)
            mx, my = x + 72, y + 29
            for yy, grey in ((my, .93), (my + 51, .83)):
                c.setFillGray(grey)
                c.setStrokeGray(0)
                c.rect(mx, yy, 86, 20, fill=1, stroke=1)
                c.ellipse(mx, yy + 12, mx + 86, yy + 29, fill=1, stroke=1)
            c.setFillGray(0)
            c.ellipse(mx + 35, my + 68, mx + 51, my + 75, fill=1, stroke=0)
            d.stipla((mx + 43, my + 50), (mx + 43, my + 33))
            d.tekst("Laus motmagnet", mx + 121, my + 65, 10, True)
            d.tekst("Merk flata som vender frå botnskalet.", mx + 121, my + 49, 9)
            d.tekst("Magnet limt i botnskalet", mx + 121, my + 6, 10)
            c.setLineWidth(.6)
            c.line(mx + 54, my + 72, mx + 112, my + 72)
        elif kind == "switch_contacts":
            d.tekst("FINN KONTAKTGRUPPENE MED MULTIMETER", x, y + h - 20, 8, True)
            for i, (title, closed, result) in enumerate((
                    ("SLEPPT KNAPP", False, "Ingen samband mellom A og B"),
                    ("TRYKT INN", True, "Samband mellom A og B"))):
                left = x + i * (w/2 + 8)
                middle = left + w/4 - 8
                cy = y + 77
                d.tekst(title, left, y + h - 46, 9, True)
                c.setLineWidth(1)
                c.setStrokeGray(0)
                c.setFillGray(1)
                for px, name in ((middle-52, "A"), (middle+52, "B")):
                    c.circle(px, cy, 15, stroke=1, fill=0)
                    d.tekst(name, px, cy-4, 12, True, "c")
                c.line(middle-37, cy, middle-18, cy)
                c.line(middle+18, cy, middle+37, cy)
                c.circle(middle-18, cy, 2, stroke=1, fill=0)
                c.circle(middle+18, cy, 2, stroke=1, fill=0)
                c.line(middle-16, cy + (0 if closed else 2), middle+16, cy + (0 if closed else 20))
                d.avsnitt(result, left, y+37, w/2-18, 9)
            d.tekst("Prinsipp, ikkje beinplassering. IO13 til éi gruppe; GND til den andre.", x, y+6, 8.5)
        else:
            raise ValueError(f"Ukjent diagramtype: {kind}")

    def warnings(self, side):
        d, m = self.dok, self.stil["margin"]
        top = self._header(side, "Kontroll og vedlikehald")
        if side.get("scene"):
            self.scenefigur({**side, "labels": False}, (m, top - 245, d.W - 2*m, 225), side)
            top -= 265
        y = top - 10
        for i, item in enumerate(side["items"], 1):
            text = item.get("text", "") if isinstance(item, dict) else item
            d.tekst(f"{i:02d}", m, y, 10, True)
            y = d.avsnitt(text, m + 31, y, d.W - 2*m - 31, 10.5) - 19
        if side.get("sources"):
            y -= 12
            d.tekst("GRUNNLAG", m, y, 8, True)
            y -= 17
            for source in side["sources"]:
                if isinstance(source, dict):
                    label, url = source["label"], source.get("url")
                    if source.get("text"):
                        label += " · " + source["text"]
                else:
                    label, url = source, None
                lines = simpleSplit(label, "M", 8, d.W - 2*m)
                start = y
                for line in lines:
                    d.tekst(line, m, y, 8)
                    y -= 11
                if url:
                    d.c.linkURL(url, (m, y+8, d.W-m, start+8), relative=0)
                y -= 5
        d.ny_side(side.get("title", "Sluttkontroll"))
