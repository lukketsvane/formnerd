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
STIL = {"line": 3, "crease": 38.0, "depth_eps": 0.004, "min_px": 30, "new_fill": [236, 236, 236], "margin": 22,
        "steg_pt": 44, "mengd_pt": 13, "mengd_fyrst": False, "tittel_pt": 30, "tittel_feit": False, "sidetal_pt": 10,
        "del_pt": 13, "lett_pt": None, "ramme": True, "beslagkolonne": True, "kontur": 1.0, "svarting": 1.0}


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
    sil1 = np.zeros(fg.shape, bool)            # einsidig grunnlag (1 px), til odde strekbreidder
    inne1 = np.zeros(fg.shape, bool)
    for ax in (0, 1):
        for s in (1, -1):
            ks = idb != np.roll(idb, s, ax)
            begge = fg & np.roll(fg, s, ax)
            ki = begge & ((np.abs(z - np.roll(z, s, ax)) > stil["depth_eps"]) | ((nv * np.roll(nv, s, ax)).sum(-1) < kos))
            sil |= ks
            inne |= ki
            if s == 1:
                sil1 |= ks
                inne1 |= ki
    inne &= ~sil
    lab, k = ndimage.label(inne, structure=np.ones((3, 3)))
    if k:
        storleik = np.bincount(lab.ravel(), minlength=k + 1)
        eigar = np.zeros(k + 1, int)
        np.maximum.at(eigar, lab.ravel(), idb.ravel())
        inne &= storleik[lab] >= mp[eigar[lab]]
    tjukk = lambda m, it: ndimage.binary_dilation(m, iterations=it) if it > 0 else m
    if stil.get("breidd"):             # breidd i pikslar på det høgoppløyste rasteret: steg på éin piksel, ikkje to
        inne1 &= inne
        def brei(m2, m1, w):
            w = max(1, int(round(w)))
            return tjukk(m2, (w - 2) // 2) if w % 2 == 0 else tjukk(m1, (w - 1) // 2)
        kant = brei(inne, inne1, stil["breidd"]) | brei(sil, sil1, stil["breidd"] * stil.get("kontur", 1.0))
    else:
        n = int(stil["line"]) - 1      # iterations=0 i scipy dilaterer til heile biletet er fylt
        ns = max(n, int(round(stil["line"] * stil.get("kontur", 1.0))) - 1)      # omriss og delgrenser kan vere tjukkare enn indre kantar
        kant = tjukk(inne, n) | tjukk(sil, ns)
    ut = np.full(fg.shape + (3,), 255, np.uint8)
    for i, rgb in fyll.items():
        ut[idb == i] = rgb
    sv = float(stil.get("svarting", 1.0))
    if sv > 1.0:                       # nedskalert strek blir grå i kantane: skaler dekninga opp så streken står svart
        H, W = kant.shape[0] // skala * skala, kant.shape[1] // skala * skala
        dek = kant[:H, :W].reshape(H // skala, skala, W // skala, skala).mean((1, 3))
        dek = np.clip(dek * sv, 0, 1)[..., None]
        botn = np.asarray(Image.fromarray(ut).resize((W // skala, H // skala), Image.NEAREST)).astype(np.float32)
        return Image.fromarray((botn * (1 - dek)).round().astype(np.uint8)), skala
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

    def bilete(self, im, boks, crop=True, reg=True, fast=False):
        """fast: skala og plassering frå heile biletet (fast utsnitt), men berre innhaldet blir teikna."""
        cb = beskjer(im) if crop or fast else (0, 0, im.width, im.height)
        sub = im.crop(cb)
        x, y, w, h = boks
        s = min(w / im.width, h / im.height) if fast else min(w / sub.width, h / sub.height)
        dw, dh = sub.width * s, sub.height * s
        if fast:
            dx, dy = x + (w - im.width * s) / 2 + cb[0] * s, y + (h - im.height * s) / 2 + (im.height - cb[3]) * s
        else:
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
        c.setLineWidth(self.stil["lett_pt"] or 1.0)
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
        r = self.stil["del_pt"]
        self.sirkel(ident, x + r, y + 5, r, r if len(ident) < 3 else r * 10 / 13)
        tal = f"{mengd}x" if self.stil.get("mengd_fyrst") else f"x{mengd}"
        return 2 * r + 4 + (self.tekst(tal, x + 2 * r + 4, y, size) if mengd is not None else 0)

    def leiar(self, ident, mål, ved):
        a, p = np.asarray(ved, float), np.asarray(mål, float)
        d = p - a
        L = np.linalg.norm(d)
        c = self.c
        r = self.stil["del_pt"]
        if L > r + 3:
            c.setStrokeGray(0)
            c.setLineWidth(self.stil["lett_pt"] or .7)
            c.line(*(a + d / L * r), *p)
            c.setFillGray(0)
            c.circle(*p, 1.5, fill=1, stroke=0)
        self.sirkel(ident, *a, r, r if len(ident) < 3 else r * 10 / 13)

    def glas(self, p, s=1.0):
        """To korte skrå parallelle strekar: glas eller anna klar flate."""
        c = self.c
        c.setStrokeGray(0)
        c.setLineWidth(self.stil["lett_pt"] or .7)
        c.setLineCap(1)
        for dx, lengd in ((-3.0, 16.0), (3.0, 10.0)):
            c.line(p[0] + dx * s - lengd * s * .35, p[1] - lengd * s * .5, p[0] + dx * s + lengd * s * .35, p[1] + lengd * s * .5)
        c.setLineCap(0)

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
        elif kind == "klokke":
            cx, cy, r = x + 15 * s, y + 15 * s, 15 * s
            c.circle(cx, cy, r, stroke=1, fill=1)
            c.line(cx, cy, cx, cy + r * 0.62)
            c.line(cx, cy, cx + r * 0.45, cy)
        elif kind == "vater":
            c.roundRect(x, y + 8 * s, 44 * s, 13 * s, 2 * s, fill=1, stroke=1)
            c.roundRect(x + 14 * s, y + 11 * s, 16 * s, 7 * s, 3.5 * s, fill=1, stroke=1)
            c.setFillGray(0)
            c.circle(x + 22 * s, y + 14.5 * s, 2.2 * s, fill=1, stroke=0)
        elif kind == "spray":
            c.roundRect(x + 2 * s, y, 15 * s, 26 * s, 2 * s, fill=1, stroke=1)
            c.rect(x + 6 * s, y + 26 * s, 7 * s, 5 * s, fill=1, stroke=1)
            c.setFillGray(0)
            for dx, dy in ((20, 31), (25, 34), (25, 28), (30, 37), (30, 31), (30, 25)):
                c.circle(x + dx * s, y + dy * s, 1.2 * s, fill=1, stroke=0)
        elif kind == "lodd":
            c.roundRect(x, y + 10 * s, 20 * s, 8 * s, 3 * s, fill=1, stroke=1)      # handtak
            c.line(x + 20 * s, y + 14 * s, x + 31 * s, y + 14 * s)                     # skaft
            c.line(x + 31 * s, y + 14 * s, x + 37 * s, y + 7 * s)                      # spiss
            c.line(x, y + 14 * s, x - 5 * s, y + 5 * s)                               # leidning

    def ny_side(self, tittel, botn=True):
        m = self.stil["margin"]
        c = self.c
        if self.stil["ramme"]:
            c.setStrokeGray(0)
            c.setLineWidth(1.2)
            c.rect(m, m + 14, self.W - 2 * m, self.H - 2 * m - 14, fill=0, stroke=1)
        self.n += 1
        if botn and self.stil.get("sidetal_ytre"):               # sidetal i ytre hjørne, dokumentkode berre på partalssider
            par_ = self.n % 2 == 0
            self.tekst(str(self.n), m + 8 if par_ else self.W - m - 8, m - 2, self.stil["sidetal_pt"], juster="l" if par_ else "r", reg=False)
            if self.meta.get("footer") and par_:
                self.tekst(self.meta["footer"], self.W - m - 8, m - 2, 5.5, juster="r", reg=False)
        elif botn:
            self.tekst(str(self.n), self.W / 2, m - 2, self.stil["sidetal_pt"], juster="c", reg=False)
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
        p = self.del_(self.del_(namn).get("counts_as", namn))
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

    def figur(self, scene, view, senter=None, span=None, zoom=1.05, boks=None, krop=True):
        """Med style.line_pt og ein boks blir strekbreidda vald slik at streken blir om lag line_pt i ferdig storleik."""
        res = self._figur(scene, view, senter, span, zoom, self.stil)
        if self.stil.get("line_pt") and boks is not None:
            cb = beskjer(res[0]) if krop else (0, 0, res[0].width, res[0].height)
            s = min(boks[2] / max(1, cb[2] - cb[0]), boks[3] / max(1, cb[3] - cb[1]))    # pt per piksel
            w = max(1, int(round(2 * self.stil["line_pt"] / s)))                         # høgoppløyste pikslar, to per piksel i biletet
            res = self._figur(scene, view, senter, span, zoom, {**self.stil, "breidd": w})
            res[5]["strek_pt"] = round(w * s / 2, 2)
        return res

    def _figur(self, scene, view, senter, span, zoom, stilen):
        obj, roller, delnamn, bev = self.objekt(scene)
        if senter is None:
            hjørne = np.array([self.delar.grenser[n] + t for (_, t), n in zip(obj, delnamn)]).reshape(-1, 3)
            lo, hi = hjørne.min(0), hjørne.max(0)
            senter, span = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2 * zoom
        synleg = [i for i, r in enumerate(roller) if r != "ghost"]
        spøkje = [i for i, r in enumerate(roller) if r == "ghost"]
        def pass_(idx, stil):
            mappe, cam = render([obj[i] for i in idx], self.view(view), self.work, senter, span)
            fyll = {k + 1: tuple(self.stil["new_fill"]) for k, i in enumerate(idx) if roller[i] == "new" and self.del_(delnamn[i]).get("fill", True)}
            crease = {k + 1: self.del_(delnamn[i])["crease"] for k, i in enumerate(idx) if "crease" in self.del_(delnamn[i])}
            min_px = {k + 1: self.del_(delnamn[i])["min_px"] for k, i in enumerate(idx) if "min_px" in self.del_(delnamn[i])}
            im, sk = linjer(mappe, fyll, stil, crease, min_px)
            return im, sk, cam, mappe
        im, sk, cam, mappe = pass_(synleg, stilen)
        if spøkje:
            gim, _, _, _ = pass_(spøkje, {**stilen, "line": max(1, stilen["line"] - 1)})
            a, g = np.asarray(im).copy(), np.asarray(gim.convert("L"))
            kvit = (a == 255).all(-1) & (g < 128)
            a[kvit] = self.stil.get("ghost_grey", 150)
            im = Image.fromarray(a)
        mørk = float((np.asarray(im.convert("L")) < 200).mean())
        return im, projektor(cam, sk), bev, roller, delnamn, {"mappe": mappe, "mørk_del": round(mørk, 4)}

    def mini(self, namn, boks=None):
        """Med style.line_pt og boks (breidd, høgd i pt) blir streken om lag line_pt også i miniatyrane."""
        nøkkel = (namn, None if boks is None else tuple(round(v, 1) for v in boks))
        if nøkkel not in self.miniar:
            p = self.del_(namn)
            self.delar.get(namn)
            mappe, cam = render([(self.delar.glb[namn], (0, 0, 0))], self.view(p.get("thumb_view", "iso")), self.work)
            arg = ({1: p["crease"]} if "crease" in p else None, {1: p["min_px"]} if "min_px" in p else None)
            im, _ = linjer(mappe, {}, {**self.stil, "line": 6}, *arg)
            if self.stil.get("line_pt") and boks:
                cb = beskjer(im, 10)
                w = max(1, int(round(2 * self.stil["line_pt"] / min(boks[0] / (cb[2] - cb[0]), boks[1] / (cb[3] - cb[1])))))
                im, _ = linjer(mappe, {}, {**self.stil, "breidd": w}, *arg)
            self.miniar[nøkkel] = im.crop(beskjer(im, 10))
        return self.miniar[nøkkel]

    def scenefigur(self, fig, boks, side):
        d = self.dok
        fast = fig.get("centre") is not None                     # fast utsnitt: ingen autobeskjering, så skalaen blir lik i sekvensen
        im, P3, bev, roller, delnamn, info = self.figur(fig["scene"], fig.get("view", side.get("view", "iso")), fig.get("centre"), fig.get("span"),
                                                        zoom=fig.get("zoom", 1.05), boks=boks, krop=not fast)
        tilpdf, ramme = d.bilete(im, boks, fast=fast)
        P = lambda w: tilpdf(P3(w))
        grupper = {}
        for namn, frå, til, stil, flytt in bev:
            a, b = P(frå), P(til)
            hw = self.del_(namn).get("kind") == "hardware"
            if (stil or ("dashed" if hw else "arrow")) == "dashed":
                d.stipla(a, b)
            elif stil != "none":
                d.pil(a + (b - a) * 0.15, b - (b - a) * 0.15)
            lo, hi = self.delar.grenser[namn]
            hjørne = np.array([P(np.array([x, y, z]) + flytt) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            grupper.setdefault(namn, []).append((hjørne, flytt))
        utan = {s["part"] for s in fig["scene"] if s.get("label") is False}
        skuv = {s["part"]: np.array(s["label_offset"], float) for s in fig["scene"] if s.get("label_offset")}
        midt_f = np.array([ramme[0] + ramme[2] / 2, ramme[1] + ramme[3] / 2])
        for namn, liste in grupper.items():
            if fig.get("labels", True) is False or namn in utan:
                continue
            hjørnelister = [q for q, _ in liste]
            h, fl = max(liste, key=lambda t: t[0][:, 1].max())
            høgre, midt = h[:, 0].max(), (h[:, 1].min() + h[:, 1].max()) / 2
            if self.del_(namn).get("kind") == "hardware":
                mp = self.stil["mengd_pt"]
                o = skuv.get(namn, np.zeros(2))
                if self.stil["mengd_fyrst"]:
                    w = d.tekst(f"{len(hjørnelister)}x", høgre + 8 + o[0], midt - mp * .3 + o[1], mp, reg=False)
                    d.tekst(self.ident(namn), høgre + 12 + w + o[0], midt - mp * .3 + o[1], self.stil["del_pt"], reg=False)
                else:
                    d.tekst(f"{self.ident(namn)}x{len(hjørnelister)}", høgre + 8 + o[0], midt - 4 + o[1], mp, reg=False)
            else:                                                # leiaren peikar på midten av delen der han er teikna, ringen står utanfor
                mål = P(self.delar.senter[namn] + fl)
                ut = mål - midt_f
                ut = ut / np.linalg.norm(ut) if np.linalg.norm(ut) > 1 else np.array([0.8, 0.6])
                d.leiar(self.ident(namn), mål, mål + ut * 44 + skuv.get(namn, np.zeros(2)))
        for co in fig.get("callouts", []):
            t = P(co["point"])
            d.leiar(self.ident(co["part"]), t, t + np.array(co.get("offset", [40, 30])))
        for a, b in fig.get("arrows", []):
            d.pil(P(a), P(b))
        for t in fig.get("texts", []):                           # mål og korte merke i figuren, t.d. «242 mm»
            q = P(t["point"]) + np.array(t.get("offset", [0, 0]), float)
            d.tekst(t["text"], q[0], q[1], t.get("size", self.stil["mengd_pt"]), reg=False)
        for g in fig.get("glas", []):
            d.glas(P(g))
        for det in ([fig["detail"]] if isinstance(fig.get("detail"), dict) else fig.get("detail") or []):
            self.boble(fig, det, P, boks, side)
        if fig.get("multiplier") and fig.get("multiplier_text", True):
            d.tekst(fig["multiplier"], ramme[0] + ramme[2] - 4, ramme[1] + 6, 40, juster="r", reg=False)
        info["figur_pt"] = [round(v, 1) for v in ramme]
        return ramme, info

    def boble(self, fig, det, P, boks, side):
        d = self.dok
        r = det.get("r", 62)
        im, _, _, _, _, _ = self.figur(det.get("scene", fig["scene"]), fig.get("view", side.get("view", "iso")), det["centre"], det["span"],
                                       boks=(0, 0, 2 * r, 2 * r), krop=False)
        x, y, w, h = boks
        pos = det.get("pos", "right")
        cx, cy = (x + pos[0] * w, y + pos[1] * h) if isinstance(pos, list) else \
            {"right": (x + w - r - 4, y + r + 4), "left": (x + r + 4, y + r + 4), "topright": (x + w - r - 4, y + h - r - 4)}[pos]
        src = P(det["centre"])
        c = d.c
        c.setStrokeGray(0)
        c.setLineWidth(self.stil["lett_pt"] or .9)
        v = src - np.array([cx, cy])
        if np.linalg.norm(v) > r + 4:                           # kile: to liner frå staden til ringen
            a0 = math.atan2(v[1], v[0])
            for da in (-0.5, 0.5):
                c.line(*src, cx + r * math.cos(a0 + da), cy + r * math.sin(a0 + da))
        c.saveState()
        p = c.beginPath()
        p.circle(cx, cy, r)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillGray(1)
        c.rect(cx - r, cy - r, 2 * r, 2 * r, fill=1, stroke=0)
        d.bilete(im, (cx - r, cy - r, 2 * r, 2 * r), crop=False, reg=False)
        c.restoreState()
        c.setLineWidth(self.stil.get("boble_pt", 1.6))
        c.circle(cx, cy, r, stroke=1, fill=0)
        if det.get("label"):
            d.tekst(det["label"], cx, cy - r - 16, 12, True, "c")
        if det.get("qty"):                                       # mengda bryt ringen oppe til venstre, slik IKEA set henne
            mp = self.stil["mengd_pt"]
            bw = pdfmetrics.stringWidth(det["qty"], "M", mp) + (pdfmetrics.stringWidth(det["letter"], "M", self.stil["del_pt"]) + 5 if det.get("letter") else 0)
            qx, qy = cx - r * .72 - bw * .55, cy + r * .72 - mp * .2
            c.setFillGray(1)
            c.rect(qx - 3, qy - 3, bw + 6, mp + 3, fill=1, stroke=0)
            tw = d.tekst(det["qty"], qx, qy, mp, reg=False)
            if det.get("letter"):
                d.tekst(det["letter"], qx + tw + 4, qy, self.stil["del_pt"], reg=False)

    def cover(self, side):
        d = self.dok
        m = self.stil["margin"]
        tp = self.stil["tittel_pt"]
        ekstra = max(0.0, tp - 30) * .75
        d.tekst(side.get("title", "MONTERINGSRETTLEIING"), m + 30, d.H - m - 70 - ekstra, tp, self.stil["tittel_feit"])
        if self.spec.get("meta", {}).get("subtitle"):
            d.tekst(self.spec["meta"]["subtitle"], m + 32, d.H - m - 96 - ekstra, 12)
        inn = side.get("inset_pt", 40)
        boks = (m + inn, m + 60, d.W - 2 * m - 2 * inn, d.H - 2 * m - 220 - ekstra)
        im, P3, *_ = self.figur(side["scene"], side.get("view", "iso"), zoom=1.0, boks=boks)
        tilpdf, _ = d.bilete(im, boks)
        for g in side.get("glas", []):
            d.glas(tilpdf(P3(g)))
        d.ny_side("Framside", botn=not self.stil.get("sidetal_ytre"))

    def inventory(self, side):
        d = self.dok
        m = self.stil["margin"]
        namn = side.get("parts") or [k for k, p in self.spec["parts"].items() if p.get("kind") != "hardware"]
        self.rutenett(namn, side.get("cols"), lambda k, x, y, cw: d.merke(self.ident(k), self.del_(k).get("qty", 1), x, y),
                      proporsjonal=side.get("proportional", False))
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
            midtstilt = side.get("centred", False)               # IKEA-oppsett: figur i midten, mengd under, bokstav lita ved sida, ingen liner
            if i % cols == 0 and not midtstilt:
                d.c.setStrokeGray(0)
                d.c.setLineWidth(1)
                d.c.line(x0, y - rh + 6, x1, y - rh + 6)
            x = x0 + (i % cols) * cw
            f = min(1.0, max(0.3, math.sqrt(self.delar.storleik[k] / størst))) if side.get("proportional", True) else 1.0
            q = self.del_(k).get('qty', 1)
            mengd = f"{q}x" if self.stil["mengd_fyrst"] else f"x{q}"
            if midtstilt:
                iw, ih = (cw - 36) * f, (rh - 50) * f
                base = y - rh + 10
                _, (bx, by, bw, bh) = d.bilete(self.mini(k, (iw, ih)), (x + (cw - iw) / 2, base + 26, iw, rh - 50))
                d.tekst(mengd, x + cw / 2, base, self.stil["mengd_pt"], juster="c")
                d.tekst(self.ident(k), bx + bw + 5, by + bh / 2 - 3, self.stil["del_pt"], reg=False)
                continue
            d.tekst(self.ident(k), x + 8, y - 28, 22)
            iw, ih = (cw - 20) * f, (rh - 80) * f
            base = y - rh + 22
            d.bilete(self.mini(k, (iw, ih)), (x + 8, base + 24, iw, ih))
            d.tekst(mengd, x + 8, base, 18)
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
            d.bilete(self.mini(k, (bw, bh)), (bx, by, bw, bh))
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

    def steps(self, side):
        """To steg på éi side, over kvarandre. `split` er delen av høgda det øvste får (standard 0,5)."""
        d = self.dok
        m = self.stil["margin"]
        a, b = side["steps"]
        midt = m + (d.H - 2 * m) * (1 - side.get("split", 0.5))
        titlar = [self.step(a, band=(d.H - m, midt - 30), ny=False), self.step(b, band=(midt - 4, m), ny=False)]
        d.ny_side(" · ".join(t for t in titlar if t))

    def step(self, side, band=None, ny=True):
        d = self.dok
        m = self.stil["margin"]
        T, B = band or (d.H - m, m)
        utan = side.get("n") is False          # side utan stegnummer: port, kontroll, bakside
        if not utan:
            self.steg += 1
        nr = None if utan else side.get("n", self.steg)
        sp = self.stil["steg_pt"]
        tx = m + 16
        if nr is not None:
            d.tekst(str(nr), m + 16, T - 56, sp, True)
            tx += sp * 0.62 * len(str(nr)) + 20
        for k in side.get("icons", []):
            d.ikon(k, tx, T - 60, 0.9)
            tx += 44 if k != "vater" else 56
        if side.get("icon_text"):                                # kort tal ved piktogramma, t.d. «24 h»
            d.tekst(side["icon_text"], tx - 6, T - 52, self.stil["mengd_pt"], reg=False)
        beslag = side.get("hardware")
        if beslag is None:
            tel = {}
            for fig in side["figures"]:
                for s in fig["scene"]:
                    if s.get("role") == "new" and self.del_(s["part"]).get("kind") == "hardware":
                        k = self.del_(s["part"]).get("counts_as", s["part"])
                        tel[k] = tel.get(k, 0) + len(s.get("at") or [0]) * int(str(fig.get("multiplier", "x1")).lstrip("x") or 1)
            beslag = [[k, v] for k, v in tel.items()]
        for k, v in beslag:
            self.brukt[k] = self.brukt.get(k, 0) + v
        høgre = d.W - m - 10
        if beslag and self.stil["beslagkolonne"]:
            sb = 108
            høgre = d.W - m - sb - 8
            y = T - 8
            for k, v in beslag:
                bh = 96
                d.c.setStrokeGray(0)
                d.c.setLineWidth(1)
                d.c.rect(d.W - m - sb, y - bh, sb, bh, fill=0, stroke=1)
                d.tekst(self.ident(k), d.W - m - sb + 6, y - 18, 15)
                d.bilete(self.mini(k, (sb - 28, bh - 44)), (d.W - m - sb + 14, y - bh + 22, sb - 28, bh - 44))
                d.tekst(f"x{v}", d.W - m - 8, y - bh + 8, 13, juster="r")
                y -= bh
        figs = side["figures"]
        botn = B + (60 if band is None else 34) + 22 * sum(1 for k in ("note", "warning") if side.get(k))
        topp = T - (80 if band is None else 64)
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
            if i < n - 1 and side.get("flow_arrow", True):
                if flyt == "down":
                    d.hol_pil(boks[0] + boks[2] / 2, boks[1] - gap / 2, "ned")
                else:
                    d.hol_pil(boks[0] + boks[2] + gap / 2, boks[1] + boks[3] / 2, "hogre")
        y = B + (46 if band is None else 34)
        if side.get("warning"):
            d.ikon("atvaring", m + 16, y - 6, 0.75)
            d.tekst(side["warning"], m + 46, y, 11, True)
            y += 22
        if side.get("note"):
            d.tekst(side["note"], m + 16, y, 11)
        nye = sum(1 for f in figs for s in f["scene"] if s.get("role") == "new")
        self.rapport.append({"side": d.n + 1, "steg": nr, **({} if utan else {"nye_delar": nye}), "figurar": info_figs})
        tittel = side.get("title", "") if utan else f"{nr} {side.get('title', '')}"
        if ny:
            d.ny_side(tittel)
        return tittel

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
        for f in os.listdir(f"{self.ut}/sider"):                 # sider frå ei lengre, eldre utgåve skal ikkje bli liggjande
            if f.startswith("side-") and f.endswith(".png"):
                os.remove(f"{self.ut}/sider/{f}")
        subprocess.run(["pdftoppm", "-r", "110", "-png", pdf, f"{self.ut}/sider/side"], check=True)
        for f in os.listdir(f"{self.ut}/sider"):                 # pdftoppm skalerer kvitt i store bilete ned til 254: gjer det kvitt att
            if f.endswith(".png"):
                Image.open(f"{self.ut}/sider/{f}").convert("RGB").point(lambda v: 255 if v >= 250 else v).save(f"{self.ut}/sider/{f}")
        bom = {k: {"i_steg": self.brukt.get(k, 0), "i_delliste": p.get("qty", 1)} for k, p in self.spec["parts"].items() if p.get("kind") == "hardware" and "counts_as" not in p}
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
