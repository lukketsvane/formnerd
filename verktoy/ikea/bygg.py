import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np
import trimesh
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from scipy import ndimage

HER = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PX = 2400
STIL = {"line": 3, "crease": 38.0, "depth_eps": 0.004, "min_px": 30, "new_fill": [236, 236, 236], "margin": 22}


class Delar:
    def __init__(self, spec, rot, work):
        self.spec, self.rot, self.work = spec, rot, work
        self.glb, self.senter, self.storleik, self.grenser = {}, {}, {}, {}
        os.makedirs(work, exist_ok=True)

    def mesh(self, namn):
        p = self.spec[namn]
        if "primitive" in p:
            pr = p["primitive"]
            if "cylinder" in pr:
                m = trimesh.creation.cylinder(radius=pr["cylinder"]["r"], height=pr["cylinder"]["h"], sections=48)
            elif "box" in pr:
                m = trimesh.creation.box(extents=pr["box"])
            else:
                raise ValueError(f"ukjend primitiv i {namn}")
            if pr.get("axis"):
                m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], pr["axis"]))
            return m
        filer = p["mesh"] if isinstance(p["mesh"], list) else [p["mesh"]]
        return trimesh.util.concatenate([trimesh.load(os.path.join(self.rot, f), force="mesh") for f in filer])

    def get(self, namn):
        if namn not in self.glb:
            m = self.mesh(namn)
            sti = f"{self.work}/{namn}.glb"
            m.export(sti)
            self.glb[namn], self.senter[namn], self.storleik[namn], self.grenser[namn] = sti, m.bounds.mean(0), float(np.linalg.norm(m.extents)), m.bounds.copy()
        return self.glb[namn]


def render(objekt, view, work, senter=None, span=None, zoom=1.05):
    sc = {"storleik": PX, "retning": list(map(float, view["dir"])), "opp": list(map(float, view["up"])), "zoom": zoom, "flat": True,
          "objekt": [{"fil": f, "flytt": [float(v) for v in t]} for f, t in objekt]}
    if senter is not None:
        sc["senter"], sc["span"] = [float(v) for v in senter], float(span)
    nøkkel = hashlib.sha256((json.dumps(sc, sort_keys=True) + "".join(str(os.path.getmtime(f)) for f, _ in objekt)).encode()).hexdigest()[:16]
    mappe = f"{work}/r/{nøkkel}"
    if not os.path.exists(f"{mappe}/kamera.json"):
        os.makedirs(mappe, exist_ok=True)
        json.dump(sc, open(f"{mappe}/scene.json", "w"))
        r = subprocess.run(["node", f"{HER}/strek.mjs", f"{mappe}/scene.json", mappe], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-2000:])
    return mappe, json.load(open(f"{mappe}/kamera.json"))


def linjer(mappe, fyll, stil, crease=None, min_px=None, skala=2):
    rd = lambda n: np.asarray(Image.open(f"{mappe}/{n}.png").convert("RGBA")).astype(np.float32)
    n, dj, idb = rd("normal"), rd("djupn"), rd("id")[..., 0].round().astype(int)
    fg = idb > 0
    z = dj[..., 0] / 255 + dj[..., 1] / 255 / 255
    nv = n[..., :3] / 127.5 - 1
    nv /= np.linalg.norm(nv, axis=-1, keepdims=True) + 1e-9
    ant = idb.max() + 1
    cr = np.full(ant, stil["crease"])
    mp = np.full(ant, stil["min_px"])
    for i, v in (crease or {}).items():
        cr[i] = v
    for i, v in (min_px or {}).items():
        mp[i] = v
    kos = np.cos(np.radians(cr))[idb]
    sil = np.zeros(fg.shape, bool)
    inne = np.zeros(fg.shape, bool)
    for ax in (0, 1):
        for s in (1, -1):
            sil |= idb != np.roll(idb, s, ax)
            begge = fg & np.roll(fg, s, ax)
            inne |= begge & (np.abs(z - np.roll(z, s, ax)) > stil["depth_eps"])
            inne |= begge & ((nv * np.roll(nv, s, ax)).sum(-1) < kos)
    inne &= ~sil
    lab, k = ndimage.label(inne, structure=np.ones((3, 3)))
    if k:
        storleik = np.bincount(lab.ravel(), minlength=k + 1)
        eigar = np.zeros(k + 1, int)
        np.maximum.at(eigar, lab.ravel(), idb.ravel())
        inne &= storleik[lab] >= mp[eigar[lab]]
    kant = ndimage.binary_dilation(sil | inne, iterations=max(0, stil["line"] - 1))
    ut = np.full(fg.shape + (3,), 255, np.uint8)
    for i, rgb in fyll.items():
        ut[idb == i] = rgb
    ut[kant] = 0
    im = Image.fromarray(ut)
    return im.resize((im.width // skala, im.height // skala), Image.LANCZOS), skala


def projektor(cam, skala):
    c, r, S = np.array(cam["senter"]), cam["r"], cam["storleik"]
    h, o = np.array(cam["hogre"]), np.array(cam["opp"])
    return lambda p: np.array([(((np.asarray(p, float) - c) @ h) / r + 1) / 2 * S / skala, (1 - ((np.asarray(p, float) - c) @ o) / r) / 2 * S / skala])


def beskjer(im, marg=16):
    a = np.asarray(im.convert("L")) < 200
    ys, xs = np.nonzero(a)
    if not len(xs):
        return (0, 0, im.width, im.height)
    return (max(0, xs.min() - marg), max(0, ys.min() - marg), min(im.width, xs.max() + marg), min(im.height, ys.max() + marg))


class Dok:
    def __init__(self, sti, meta, stil):
        pdfmetrics.registerFont(TTFont("M", FONT))
        pdfmetrics.registerFont(TTFont("MB", FONTB))
        self.W, self.H = A4 if meta.get("orientation", "portrait") == "portrait" else landscape(A4)
        self.c = canvas.Canvas(sti, pagesize=(self.W, self.H), pageCompression=1)
        self.c.setTitle(meta.get("title", ""))
        self.meta, self.stil, self.n = meta, stil, 0
        self.boksar, self.konfliktar = [], []

    def reg(self, kind, x0, y0, x1, y1):
        b = (kind, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        for k, a0, b0, a1, b1 in self.boksar:
            if "tekst" in (k, kind) and min(a1, b[3]) - max(a0, b[1]) > 1 and min(b1, b[4]) - max(b0, b[2]) > 1:
                self.konfliktar.append({"side": self.n + 1, "a": k, "b": kind})
        self.boksar.append(b)

    def tekst(self, s, x, y, size=11, feit=False, juster="l", reg=True):
        c = self.c
        c.setFillGray(0)
        f = "MB" if feit else "M"
        c.setFont(f, size)
        w = pdfmetrics.stringWidth(s, f, size)
        x0 = {"l": x, "r": x - w, "c": x - w / 2}[juster]
        c.drawString(x0, y, s)
        if reg:
            self.reg("tekst", x0, y - size * 0.22, x0 + w, y + size * 0.78)
        return w

    def bilete(self, im, boks, crop=True, reg=True):
        cb = beskjer(im) if crop else (0, 0, im.width, im.height)
        sub = im.crop(cb)
        x, y, w, h = boks
        s = min(w / sub.width, h / sub.height)
        dw, dh = sub.width * s, sub.height * s
        dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
        self.c.drawImage(ImageReader(sub), dx, dy, dw, dh)
        if reg:
            self.reg("figur", dx, dy, dx + dw, dy + dh)
        return (lambda px: np.array([dx + (px[0] - cb[0]) * s, dy + dh - (px[1] - cb[1]) * s])), (dx, dy, dw, dh)

    def pil(self, a, b, breidd=2.4, hovud=11):
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = b - a
        L = np.linalg.norm(d)
        if L < 8:
            return False
        u = d / L
        nn = np.array([-u[1], u[0]])
        base = b - u * hovud
        c = self.c
        c.setLineCap(0)
        for lw, g in ((breidd + 4, 1), (breidd, 0)):
            c.setStrokeGray(g)
            c.setLineWidth(lw)
            c.line(*a, *base)
        for vekst, g in ((2.2, 1), (0, 0)):
            c.setFillGray(g)
            p = c.beginPath()
            p.moveTo(*(b + u * vekst))
            p.lineTo(*(base + nn * (hovud * .5 + vekst) - u * vekst))
            p.lineTo(*(base - nn * (hovud * .5 + vekst) - u * vekst))
            p.close()
            c.drawPath(p, fill=1, stroke=0)
        return True

    def stipla(self, a, b):
        c = self.c
        c.setStrokeGray(0)
        c.setLineWidth(1.0)
        c.setDash(4, 3)
        c.line(*a, *b)
        c.setDash()

    def hol_pil(self, x, y, retning="ned", s=1.0):
        c = self.c
        c.setStrokeGray(0)
        c.setFillGray(1)
        c.setLineWidth(1.3)
        c.setLineJoin(0)
        pts = [(-6, 10), (6, 10), (6, 0), (12, 0), (0, -12), (-12, 0), (-6, 0)]
        if retning == "hogre":
            pts = [(-y_, x_) for x_, y_ in pts]
        p = c.beginPath()
        p.moveTo(x + pts[0][0] * s, y + pts[0][1] * s)
        for px, py in pts[1:]:
            p.lineTo(x + px * s, y + py * s)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    def sirkel(self, s, x, y, r=12, size=12):
        c = self.c
        c.setFillGray(1)
        c.setStrokeGray(0)
        c.setLineWidth(1.1)
        c.circle(x, y, r, fill=1, stroke=1)
        self.tekst(s, x, y - size * .36, size, juster="c", reg=False)
        self.reg("merke", x - r, y - r, x + r, y + r)

    def merke(self, ident, mengd, x, y, size=16):
        self.sirkel(ident, x + 13, y + 5, 13, 13 if len(ident) < 3 else 10)
        return 30 + (self.tekst(f"x{mengd}", x + 30, y, size) if mengd is not None else 0)

    def leiar(self, ident, mål, ved):
        a, p = np.asarray(ved, float), np.asarray(mål, float)
        d = p - a
        L = np.linalg.norm(d)
        c = self.c
        if L > 16:
            c.setStrokeGray(0)
            c.setLineWidth(.7)
            c.line(*(a + d / L * 13), *p)
            c.setFillGray(0)
            c.circle(*p, 1.5, fill=1, stroke=0)
        self.sirkel(ident, *a, 13, 13 if len(ident) < 3 else 10)

    def ikon(self, kind, x, y, s=1.0):
        c = self.c
        c.setStrokeGray(0)
        c.setLineWidth(1.6 * s)
        c.setFillGray(1)
        if kind == "lim":
            c.roundRect(x, y, 14 * s, 26 * s, 3 * s, fill=1, stroke=1)
            p = c.beginPath()
            p.moveTo(x + 3 * s, y + 26 * s); p.lineTo(x + 7 * s, y + 35 * s); p.lineTo(x + 11 * s, y + 26 * s); p.close()
            c.drawPath(p, fill=1, stroke=1)
            c.setFillGray(0)
            c.circle(x + 7 * s, y + 40 * s, 1.8 * s, fill=1, stroke=0)
        elif kind == "snu":
            cx, cy, r = x + 18 * s, y + 18 * s, 15 * s
            p = c.beginPath()
            p.arc(cx - r, cy - r, cx + r, cy + r, 40, 280)
            c.drawPath(p, stroke=1, fill=0)
            self.pil((cx + r * math.cos(math.radians(305)), cy + r * math.sin(math.radians(305))), (cx + r * math.cos(math.radians(330)), cy + r * math.sin(math.radians(330))), 1.6 * s, 8 * s)
        elif kind == "atvaring":
            p = c.beginPath()
            p.moveTo(x, y); p.lineTo(x + 30 * s, y); p.lineTo(x + 15 * s, y + 26 * s); p.close()
            c.setLineJoin(1)
            c.drawPath(p, fill=1, stroke=1)
            self.tekst("!", x + 15 * s, y + 5 * s, 15 * s, True, "c", reg=False)
        elif kind == "ok":
            c.circle(x + 15 * s, y + 15 * s, 15 * s, stroke=1, fill=1)
            c.setLineWidth(2.4 * s)
            c.line(x + 8 * s, y + 15 * s, x + 13 * s, y + 9 * s)
            c.line(x + 13 * s, y + 9 * s, x + 23 * s, y + 22 * s)
        elif kind == "klikk":
            self.tekst("klikk!", x, y + 8 * s, 13 * s, True, reg=False)

    def ny_side(self, tittel):
        m = self.stil["margin"]
        c = self.c
        c.setStrokeGray(0)
        c.setLineWidth(1.2)
        c.rect(m, m + 14, self.W - 2 * m, self.H - 2 * m - 14, fill=0, stroke=1)
        self.n += 1
        self.tekst(str(self.n), self.W / 2, m - 2, 10, juster="c", reg=False)
        if self.meta.get("footer"):
            self.tekst(self.meta["footer"], self.W - m, m - 2, 7, juster="r", reg=False)
        c.bookmarkPage(f"p{self.n}")
        c.addOutlineEntry(tittel, f"p{self.n}", 0)
        c.showPage()
        self.boksar = []


class Byggjar:
    def __init__(self, spec, rot, ut):
        self.spec, self.rot, self.ut = spec, rot, ut
        self.stil = {**STIL, **spec.get("style", {})}
        self.work = f"{ut}/_arbeid"
        self.delar = Delar(spec["parts"], rot, f"{self.work}/glb")
        self.dok = Dok(f"{ut}/rettleiing.pdf", spec.get("meta", {}), self.stil)
        self.miniar, self.steg, self.rapport, self.brukt = {}, 0, [], {}

    def view(self, v):
        return self.spec["views"][v] if isinstance(v, str) else v

    def del_(self, namn):
        return self.spec["parts"][namn]

    def ident(self, namn):
        p = self.del_(namn)
        return p.get("letter") or str(p.get("id", namn))

    def objekt(self, scene):
        obj, roller, delnamn, bevegelse = [], [], [], []
        for item in scene:
            glb = self.delar.get(item["part"])
            ex = np.array(item.get("explode", [0, 0, 0]), float)
            for at in item.get("at") or [[0, 0, 0]]:
                at = np.array(at, float)
                flytt = at + (ex if item.get("role") in ("new", "exploded") else 0)
                obj.append((glb, flytt))
                roller.append(item.get("role", "context"))
                delnamn.append(item["part"])
                if item.get("role") == "new" and np.linalg.norm(ex) > 0:
                    c = self.delar.senter[item["part"]] + at
                    bevegelse.append((item["part"], c + ex, c, item.get("line"), flytt))
        return obj, roller, delnamn, bevegelse

    def figur(self, scene, view, senter=None, span=None, zoom=1.05):
        obj, roller, delnamn, bev = self.objekt(scene)
        if senter is None:
            hjørne = np.array([self.delar.grenser[n] + t for (_, t), n in zip(obj, delnamn)]).reshape(-1, 3)
            lo, hi = hjørne.min(0), hjørne.max(0)
            senter, span = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2 * zoom
        synleg = [i for i, r in enumerate(roller) if r != "ghost"]
        spøkje = [i for i, r in enumerate(roller) if r == "ghost"]
        def pass_(idx, stil):
            mappe, cam = render([obj[i] for i in idx], self.view(view), self.work, senter, span)
            fyll = {k + 1: tuple(self.stil["new_fill"]) for k, i in enumerate(idx) if roller[i] == "new"}
            crease = {k + 1: self.del_(delnamn[i])["crease"] for k, i in enumerate(idx) if "crease" in self.del_(delnamn[i])}
            min_px = {k + 1: self.del_(delnamn[i])["min_px"] for k, i in enumerate(idx) if "min_px" in self.del_(delnamn[i])}
            im, sk = linjer(mappe, fyll, stil, crease, min_px)
            return im, sk, cam, mappe
        im, sk, cam, mappe = pass_(synleg, self.stil)
        if spøkje:
            gim, _, _, _ = pass_(spøkje, {**self.stil, "line": max(1, self.stil["line"] - 1)})
            a, g = np.asarray(im).copy(), np.asarray(gim.convert("L"))
            kvit = (a == 255).all(-1) & (g < 128)
            a[kvit] = self.stil.get("ghost_grey", 150)
            im = Image.fromarray(a)
        mørk = float((np.asarray(im.convert("L")) < 200).mean())
        return im, projektor(cam, sk), bev, roller, delnamn, {"mappe": mappe, "mørk_del": round(mørk, 4)}

    def mini(self, namn):
        if namn not in self.miniar:
            p = self.del_(namn)
            self.delar.get(namn)
            mappe, cam = render([(self.delar.glb[namn], (0, 0, 0))], self.view(p.get("thumb_view", "iso")), self.work)
            im, _ = linjer(mappe, {}, {**self.stil, "line": 6}, {1: p["crease"]} if "crease" in p else None, {1: p["min_px"]} if "min_px" in p else None)
            self.miniar[namn] = im.crop(beskjer(im, 10))
        return self.miniar[namn]

    def scenefigur(self, fig, boks, side):
        d = self.dok
        im, P3, bev, roller, delnamn, info = self.figur(fig["scene"], fig.get("view", side.get("view", "iso")), zoom=fig.get("zoom", 1.05))
        tilpdf, ramme = d.bilete(im, boks)
        P = lambda w: tilpdf(P3(w))
        grupper = {}
        for namn, frå, til, stil, flytt in bev:
            a, b = P(frå), P(til)
            hw = self.del_(namn).get("kind") == "hardware"
            if (stil or ("dashed" if hw else "arrow")) == "dashed":
                d.stipla(a, b)
            else:
                d.pil(a + (b - a) * 0.15, b - (b - a) * 0.15)
            lo, hi = self.delar.grenser[namn]
            hjørne = np.array([P(np.array([x, y, z]) + flytt) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            grupper.setdefault(namn, []).append(hjørne)
        for namn, hjørnelister in grupper.items():
            if fig.get("labels", True) is False:
                continue
            h = max(hjørnelister, key=lambda q: q[:, 1].max())
            høgre, midt = h[:, 0].max(), (h[:, 1].min() + h[:, 1].max()) / 2
            if self.del_(namn).get("kind") == "hardware":
                d.tekst(f"{self.ident(namn)}x{len(hjørnelister)}", høgre + 8, midt - 4, 13, reg=False)
            else:
                d.leiar(self.ident(namn), np.array([høgre - 4, midt]), np.array([høgre + 30, midt + 16]))
        for co in fig.get("callouts", []):
            t = P(co["point"])
            d.leiar(self.ident(co["part"]), t, t + np.array(co.get("offset", [40, 30])))
        for a, b in fig.get("arrows", []):
            d.pil(P(a), P(b))
        if fig.get("detail"):
            self.boble(fig, fig["detail"], P, boks, side)
        if fig.get("multiplier"):
            d.tekst(fig["multiplier"], ramme[0] + ramme[2] - 4, ramme[1] + 6, 40, juster="r", reg=False)
        info["figur_pt"] = [round(v, 1) for v in ramme]
        return ramme, info

    def boble(self, fig, det, P, boks, side):
        d = self.dok
        im, _, _, _, _, _ = self.figur(det.get("scene", fig["scene"]), fig.get("view", side.get("view", "iso")), det["centre"], det["span"])
        r = det.get("r", 62)
        x, y, w, h = boks
        cx, cy = {"right": (x + w - r - 4, y + r + 4), "left": (x + r + 4, y + r + 4), "topright": (x + w - r - 4, y + h - r - 4)}[det.get("pos", "right")]
        src = P(det["centre"])
        c = d.c
        c.setStrokeGray(0)
        c.setLineWidth(.9)
        c.circle(*src, 12, stroke=1, fill=0)
        v = np.array([cx, cy]) - src
        v /= np.linalg.norm(v) + 1e-9
        c.line(*(src + v * 12), *(np.array([cx, cy]) - v * r))
        c.saveState()
        p = c.beginPath()
        p.circle(cx, cy, r)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillGray(1)
        c.rect(cx - r, cy - r, 2 * r, 2 * r, fill=1, stroke=0)
        d.bilete(im, (cx - r, cy - r, 2 * r, 2 * r), crop=False, reg=False)
        c.restoreState()
        c.setLineWidth(1.6)
        c.circle(cx, cy, r, stroke=1, fill=0)
        if det.get("label"):
            d.tekst(det["label"], cx, cy - r - 16, 12, True, "c")

    def cover(self, side):
        d = self.dok
        m = self.stil["margin"]
        d.tekst(side.get("title", "MONTERINGSRETTLEIING"), m + 30, d.H - m - 70, 30)
        if self.spec.get("meta", {}).get("subtitle"):
            d.tekst(self.spec["meta"]["subtitle"], m + 32, d.H - m - 96, 12)
        im, *_ = self.figur(side["scene"], side.get("view", "iso"), zoom=1.0)
        d.bilete(im, (m + 40, m + 60, d.W - 2 * m - 80, d.H - 2 * m - 220))
        d.ny_side("Framside")

    def inventory(self, side):
        d = self.dok
        m = self.stil["margin"]
        namn = side.get("parts") or [k for k, p in self.spec["parts"].items() if p.get("kind") != "hardware"]
        self.rutenett(namn, side.get("cols"), lambda k, x, y, cw: d.merke(self.ident(k), self.del_(k).get("qty", 1), x, y))
        d.ny_side(side.get("title", "Delar"))

    def hardware(self, side):
        d = self.dok
        m = self.stil["margin"]
        namn = side.get("parts") or [k for k, p in self.spec["parts"].items() if p.get("kind") == "hardware"]
        for k in namn:
            self.delar.get(k)
        størst = max(self.delar.storleik[k] for k in namn)
        cols = side.get("cols") or min(max(len(namn), 3), 5)
        x0, x1 = m + 24, d.W - m - 24
        cw = (x1 - x0) / cols
        rh = side.get("row_height", 170)
        y = d.H - m - 30
        for i, k in enumerate(namn):
            if i and i % cols == 0:
                y -= rh
            if i % cols == 0:
                d.c.setStrokeGray(0)
                d.c.setLineWidth(1)
                d.c.line(x0, y - rh + 6, x1, y - rh + 6)
            x = x0 + (i % cols) * cw
            d.tekst(self.ident(k), x + 8, y - 28, 22)
            f = min(1.0, max(0.3, math.sqrt(self.delar.storleik[k] / størst))) if side.get("proportional", True) else 1.0
            iw, ih = (cw - 20) * f, (rh - 80) * f
            base = y - rh + 22
            d.bilete(self.mini(k), (x + 8, base + 24, iw, ih))
            d.tekst(f"x{self.del_(k).get('qty', 1)}", x + 8, base, 18)
        d.ny_side(side.get("title", "Beslag"))

    def rutenett(self, namn, cols, topp, under=None, linjer=False, proporsjonal=False):
        d = self.dok
        m = self.stil["margin"]
        cols = cols or (2 if len(namn) <= 4 else 3 if len(namn) <= 9 else 4)
        x0, x1 = m + 24, d.W - m - 24
        cw = (x1 - x0) / cols
        rader = math.ceil(len(namn) / cols)
        ch = min(cw * 1.05 + (40 if under else 20), (d.H - 2 * m - 90) / rader)
        y = d.H - m - 40
        for i, k in enumerate(namn):
            if i and i % cols == 0:
                y -= ch
                if linjer:
                    d.c.setStrokeGray(0)
                    d.c.setLineWidth(1)
                    d.c.line(x0, y + 4, x1, y + 4)
            x = x0 + (i % cols) * cw
            topp(k, x + 4, y - 26, cw)
            bx, by, bw, bh = x + 8, y - ch + (34 if under else 12), cw - 16, ch - (70 if under else 46)
            if proporsjonal:
                for n_ in namn:
                    self.delar.get(n_)
                f = min(1.0, max(0.3, math.sqrt(self.delar.storleik[k] / max(self.delar.storleik[n_] for n_ in namn))))
                bx, by, bw, bh = bx, by, bw * f, bh * f
            d.bilete(self.mini(k), (bx, by, bw, bh))
            if under:
                under(k, x + 4, y - ch + 12, cw)
        if linjer:
            d.c.line(x0, y - ch + 4, x1, y - ch + 4)

    def exploded(self, side):
        d = self.dok
        m = self.stil["margin"]
        boks = (m + 30, m + 40, d.W - 2 * m - 60, d.H - 2 * m - 100)
        scene = [{**s, "role": "exploded"} if "explode" in s else s for s in side["scene"]]
        im, P3, bev, roller, delnamn, info = self.figur(scene, side.get("view", "iso"), zoom=side.get("zoom", 1.0))
        tilpdf, ramme = d.bilete(im, boks)
        midt = np.array([ramme[0] + ramme[2] / 2, ramme[1] + ramme[3] / 2])
        sett = set()
        for s in side["scene"]:
            for at in s.get("at") or [[0, 0, 0]]:
                if s["part"] in sett and not side.get("all_instances"):
                    continue
                sett.add(s["part"])
                p = tilpdf(P3(self.delar.senter[s["part"]] + np.array(at, float) + np.array(s.get("explode", [0, 0, 0]), float)))
                v = p - midt
                v = v / (np.linalg.norm(v) + 1e-9)
                d.leiar(self.ident(s["part"]), p, p + v * 34)
        if side.get("inset"):
            ins = side["inset"]
            bw, bh = 170, 150
            bx, by = ramme[0] + ramme[2] - bw, m + 40
            d.c.setLineWidth(1.1)
            d.c.rect(bx, by, bw, bh, fill=0, stroke=1)
            im2, *_ = self.figur(ins["scene"], ins.get("view", side.get("view", "iso")))
            d.bilete(im2, (bx + 8, by + 26, bw - 16, bh - 34))
            if ins.get("multiplier"):
                d.tekst(ins["multiplier"], bx + bw / 2, by + 8, 16, True, "c")
        self.rapport.append({"side": d.n + 1, "type": "exploded", **info})
        d.ny_side(side.get("title", "Oversikt"))

    def step(self, side):
        d = self.dok
        m = self.stil["margin"]
        self.steg += 1
        nr = side.get("n", self.steg)
        d.tekst(str(nr), m + 16, d.H - m - 56, 44, True)
        tx = m + 16 + 44 * 0.62 * len(str(nr)) + 20
        for k in side.get("icons", []):
            d.ikon(k, tx, d.H - m - 60, 0.9)
            tx += 44
        beslag = side.get("hardware")
        if beslag is None:
            tel = {}
            for fig in side["figures"]:
                for s in fig["scene"]:
                    if s.get("role") == "new" and self.del_(s["part"]).get("kind") == "hardware":
                        tel[s["part"]] = tel.get(s["part"], 0) + len(s.get("at") or [0]) * int(str(fig.get("multiplier", "x1")).lstrip("x") or 1)
            beslag = [[k, v] for k, v in tel.items()]
        for k, v in beslag:
            self.brukt[k] = self.brukt.get(k, 0) + v
        høgre = d.W - m - 10
        if beslag:
            sb = 108
            høgre = d.W - m - sb - 8
            y = d.H - m - 8
            for k, v in beslag:
                bh = 96
                d.c.setStrokeGray(0)
                d.c.setLineWidth(1)
                d.c.rect(d.W - m - sb, y - bh, sb, bh, fill=0, stroke=1)
                d.tekst(self.ident(k), d.W - m - sb + 6, y - 18, 15)
                d.bilete(self.mini(k), (d.W - m - sb + 14, y - bh + 22, sb - 28, bh - 44))
                d.tekst(f"x{v}", d.W - m - 8, y - bh + 8, 13, juster="r")
                y -= bh
        figs = side["figures"]
        botn = m + 60 + 22 * sum(1 for k in ("note", "warning") if side.get(k))
        topp = d.H - m - 80
        flyt = side.get("flow", "down")
        n = len(figs)
        gap = 30
        info_figs = []
        for i, fig in enumerate(figs):
            if flyt == "down":
                fh = (topp - botn - gap * (n - 1)) / n
                boks = (m + 14, topp - (i + 1) * fh - i * gap, høgre - m - 20, fh)
            else:
                fw = (høgre - m - 20 - gap * (n - 1)) / n
                boks = (m + 14 + i * (fw + gap), botn, fw, topp - botn)
            ramme, info = self.scenefigur(fig, boks, side)
            info_figs.append(info)
            if i < n - 1:
                if flyt == "down":
                    d.hol_pil(boks[0] + boks[2] / 2, boks[1] - gap / 2, "ned")
                else:
                    d.hol_pil(boks[0] + boks[2] + gap / 2, boks[1] + boks[3] / 2, "hogre")
        y = m + 46
        if side.get("warning"):
            d.ikon("atvaring", m + 16, y - 6, 0.75)
            d.tekst(side["warning"], m + 46, y, 11, True)
            y += 22
        if side.get("note"):
            d.tekst(side["note"], m + 16, y, 11)
        nye = sum(1 for f in figs for s in f["scene"] if s.get("role") == "new")
        self.rapport.append({"side": d.n + 1, "steg": nr, "nye_delar": nye, "figurar": info_figs})
        d.ny_side(f"{nr} {side.get('title', '')}")

    def warnings(self, side):
        d = self.dok
        m = self.stil["margin"]
        y = d.H - m - 50
        for t in side["items"]:
            d.ikon("atvaring", m + 16, y - 6, 0.7)
            d.tekst(t, m + 46, y, 11)
            y -= 30
        x = m + 16
        for k in side.get("icons", []):
            d.ikon(k, x, y - 60, 1.4)
            x += 80
        d.ny_side(side.get("title", "Åtvaringar"))

    def bygg(self):
        for side in self.spec["pages"]:
            getattr(self, side["type"])(side)
        self.dok.c.save()
        pdf = f"{self.ut}/rettleiing.pdf"
        os.makedirs(f"{self.ut}/sider", exist_ok=True)
        subprocess.run(["pdftoppm", "-r", "110", "-png", pdf, f"{self.ut}/sider/side"], check=True)
        bom = {k: {"i_steg": self.brukt.get(k, 0), "i_delliste": p.get("qty", 1)} for k, p in self.spec["parts"].items() if p.get("kind") == "hardware"}
        åtvaringar = [f"{k}: {v['i_steg']} brukt i steg, {v['i_delliste']} i dellista" for k, v in bom.items() if v["i_steg"] != v["i_delliste"]]
        åtvaringar += [f"side {r['side']}: steget har ingen ny del" for r in self.rapport if r.get("nye_delar") == 0]
        åtvaringar += [f"side {r['side']}: tom figur" for r in self.rapport for f in r.get("figurar", [r]) if f.get("mørk_del", 1) < 0.002]
        åtvaringar += [f"side {k['side']}: {k['a']} overlappar {k['b']}" for k in self.dok.konfliktar]
        json.dump({"pdf": pdf, "sha256": hashlib.sha256(open(pdf, "rb").read()).hexdigest(), "sider": self.dok.n,
                   "beslag": bom, "steg": self.rapport, "åtvaringar": åtvaringar}, open(f"{self.ut}/rapport.json", "w"), indent=1, ensure_ascii=False, default=str)
        sider = sorted(f for f in os.listdir(f"{self.ut}/sider") if f.endswith(".png"))
        ims = [Image.open(f"{self.ut}/sider/{f}").convert("RGB") for f in sider]
        if ims:
            w, h = ims[0].size
            k = min(len(ims), 4)
            ark = Image.new("RGB", (w * k, h * math.ceil(len(ims) / k)), "white")
            for i, im in enumerate(ims):
                ark.paste(im, ((i % k) * w, (i // k) * h))
            ark.thumbnail((2400, 2400))
            ark.save(f"{self.ut}/kontaktark.png")
        print(pdf, self.dok.n, "sider")
        for å in åtvaringar:
            print("ÅTVARING:", å)
        return åtvaringar


if __name__ == "__main__":
    spec_sti = sys.argv[1]
    spec = json.load(open(spec_sti))
    ut = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(spec_sti), "ut")
    os.makedirs(ut, exist_ok=True)
    Byggjar(spec, os.path.dirname(os.path.abspath(spec_sti)), ut).bygg()
