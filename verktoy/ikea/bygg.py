import hashlib
import json
import math
import os
import shutil
import subprocess
import sys

import manifold3d
import numpy as np
import trimesh
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from scipy import ndimage
from kontur import konturlag
from sider import Sider

HER = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PX = 2400
SK = 1
STIL = {"line_pt": 0.75, "seam_pt": 0.50, "feature_pt": 0.42, "valley_pt": 0.28,
        "ghost_line": 0.65, "crease": 38.0, "depth_eps": 0.004, "min_px": 30,
        "new_fill": [236, 236, 236], "ghost_grey": 170, "margin": 45.35}
TYPAR = ("cover", "inventory", "hardware", "exploded", "step", "warnings")
ROLLER = ("context", "new", "ghost", "exploded")
_SHA = {}
BRUKT = set()


def innhald(f):
    if f not in _SHA:
        _SHA[f] = hashlib.sha256(open(f, "rb").read()).hexdigest()
    return _SHA[f]


def kutt(m, cut):
    n = np.asarray(cut[:3], float)
    n /= np.linalg.norm(n)
    mf = manifold3d.Manifold(manifold3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    if mf.status() == manifold3d.Error.NoError:
        r = mf.trim_by_plane(n, float(cut[3])).to_mesh()
        return trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts)
    return m.slice_plane(n * float(cut[3]), n)


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
                cy = pr["cylinder"]
                if cy.get("inner_r"):
                    sections = cy.get("sections", 48)
                    if sections < 12:
                        outer = trimesh.creation.cylinder(radius=cy["r"], height=cy["h"], sections=sections)
                        bore = trimesh.creation.cylinder(radius=cy["inner_r"], height=cy["h"] + 2, sections=48)
                        m = trimesh.boolean.difference([outer, bore], engine="manifold")
                    else:
                        m = trimesh.creation.annulus(r_min=cy["inner_r"], r_max=cy["r"], height=cy["h"], sections=sections)
                else:
                    m = trimesh.creation.cylinder(radius=cy["r"], height=cy["h"], sections=cy.get("sections", 48))
            elif "box" in pr:
                m = trimesh.creation.box(extents=pr["box"])
            else:
                raise ValueError(f"ukjend primitiv i {namn}")
            if pr.get("axis"):
                m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], pr["axis"]))
            if pr.get("rotation"):
                angles = np.radians(pr["rotation"])
                m.apply_transform(trimesh.transformations.euler_matrix(*angles, axes="sxyz"))
        else:
            filer = p["mesh"] if isinstance(p["mesh"], list) else [p["mesh"]]
            m = trimesh.util.concatenate([trimesh.load(os.path.join(self.rot, f), force="mesh") for f in filer])
        if "offset" in p:
            m.apply_translation(p["offset"])
        return m

    def get(self, namn, cut=None):
        nøkkel = namn if cut is None else f"{namn}@{hashlib.sha256(json.dumps(cut).encode()).hexdigest()[:8]}"
        if nøkkel not in self.glb:
            m = self.mesh(namn)
            if namn not in self.senter:
                self.senter[namn], self.storleik[namn], self.grenser[namn] = m.bounds.mean(0), float(np.linalg.norm(m.extents)), m.bounds.copy()
            data = (kutt(m, cut) if cut is not None else m).export(file_type="glb")
            sti = f"{self.work}/{nøkkel}.glb"
            if not (os.path.exists(sti) and open(sti, "rb").read() == data):
                open(sti, "wb").write(data)
            self.glb[nøkkel] = sti
        return self.glb[nøkkel]


def render(objekt, view, work, senter, span, boks, fargar=None):
    sc = {"storleik": PX, "retning": list(map(float, view["dir"])), "opp": list(map(float, view["up"])), "flat": True,
          "senter": [float(v) for v in senter], "span": float(span), "boks": [[float(v) for v in b] for b in boks],
          "objekt": [{"fil": f, "flytt": [float(v) for v in t], "farge": (fargar or [None] * len(objekt))[i] or "#c8cac8"} for i, (f, t) in enumerate(objekt)]}
    nøkkel = hashlib.sha256(json.dumps({**sc, "renderer": innhald(f"{HER}/strek.mjs"), "objekt": [[innhald(o["fil"]), o["flytt"], o["farge"]] for o in sc["objekt"]]}, sort_keys=True).encode()).hexdigest()[:16]
    BRUKT.add(nøkkel)
    mappe = f"{work}/r/{nøkkel}"
    if not os.path.exists(f"{mappe}/kamera.json"):
        os.makedirs(mappe, exist_ok=True)
        json.dump(sc, open(f"{mappe}/scene.json", "w"))
        r = subprocess.run([os.environ.get("CODEX_PRIMARY_RUNTIME_NODE", "node"), f"{HER}/strek.mjs", f"{mappe}/scene.json", mappe], capture_output=True, text=True, timeout=360)
        if r.returncode:
            raise RuntimeError(r.stderr[-2000:])
    return mappe, json.load(open(f"{mappe}/kamera.json"))


def kantar(mappe, stil, crease=None, min_px=None):
    """Compatibility helper; page composition uses the separate line layers."""
    layers = konturlag(mappe, stil, crease, min_px)
    return layers.edges, layers.depth, layers.ids


def tjukk(kant, px):
    return kant if px <= 1.5 else ndimage.distance_transform_edt(~kant) <= px / 2


def strokedekning(kant, px):
    """Subpixel coverage preserves physical stroke widths in the printed PDF."""
    if not kant.any():
        return np.zeros(kant.shape, np.float32)
    distance = ndimage.distance_transform_edt(~kant).astype(np.float32)
    return np.clip((px + 1) / 2 - distance, 0, min(1, px))


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
        self.c.setAuthor(meta.get("author", "FormNerd"))
        self.c.setSubject(meta.get("description", "Monteringsrettleiing"))
        self.c.setCreator("FormNerd / verktoy/ikea")
        self.meta, self.stil, self.n = meta, stil, 0
        self.boksar, self.figurar, self.konfliktar = [], [], []

    def utanfor(self, x0, y0, x1, y1):
        m = self.stil["margin"]
        return x0 < m or y0 < m + 14 or x1 > self.W - m or y1 > self.H - m

    def kollisjonar(self, x0, y0, x1, y1):
        return [k for k, a0, b0, a1, b1 in self.boksar if min(a1, x1) - max(a0, x0) > 1 and min(b1, y1) - max(b0, y0) > 1]

    def dekning(self, x0, y0, x1, y1):
        treff = 0.0
        for dx, dy, dw, dh, mk in self.figurar:
            h, w = mk.shape
            ax0, ax1 = (int(np.clip((v - dx) / dw * w, 0, w)) for v in (x0, x1))
            ay0, ay1 = (int(np.clip((dy + dh - v) / dh * h, 0, h)) for v in (y1, y0))
            if ax1 > ax0 and ay1 > ay0:
                treff += mk[ay0:ay1, ax0:ax1].sum() * dw / w * dh / h
        return treff / max((x1 - x0) * (y1 - y0), 1e-6)

    def reg(self, kind, x0, y0, x1, y1, geometri=True):
        b = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        kva = self.kollisjonar(*b)
        if self.utanfor(*b):
            kva.append("utanfor ramma")
        if geometri and self.dekning(*b) > 0.2:
            kva.append("geometri")
        self.konfliktar += [{"side": self.n + 1, "a": kind, "b": k} for k in kva]
        self.boksar.append((kind, *b))

    def plasser(self, mål, w, h, foretrekk=(1.0, 0.6), avstand=(30, 42, 56, 72)):
        mål = np.asarray(mål, float)
        f = np.asarray(foretrekk, float) / (np.linalg.norm(foretrekk) + 1e-9)
        beste = None
        for L in avstand:
            for a in range(0, 360, 20):
                v = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
                p = mål + v * L
                b = (p[0] - w / 2, p[1] - h / 2, p[0] + w / 2, p[1] + h / 2)
                linje = np.mean([self.dekning(*(q - 2), *(q + 2)) for q in (mål + v * (L - max(w, h) / 2) * t for t in (0.5, 0.7, 0.9))])
                s = 6 * self.dekning(*b) + 3 * len(self.kollisjonar(*b)) + 50 * self.utanfor(*b) + 2 * linje + 0.25 * (1 - v @ f) + L / 300
                if beste is None or s < beste[0]:
                    beste = (s, p)
        return beste[1]

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

    def avsnitt(self, s, x, y, breidd, size=11, feit=False):
        for linje in simpleSplit(s, "MB" if feit else "M", size, breidd):
            self.tekst(linje, x, y, size, feit)
            y -= size * 1.35
        return y

    def bilete(self, im, boks, crop=True, reg=True, maske=None):
        cb = beskjer(im) if crop else (0, 0, im.width, im.height)
        sub = im.crop(cb)
        x, y, w, h = boks
        s = min(w / sub.width, h / sub.height)
        dw, dh = sub.width * s, sub.height * s
        dx, dy = x + (w - dw) / 2, y + (h - dh) / 2
        self.c.drawImage(ImageReader(sub), dx, dy, dw, dh)
        if reg:
            mk = np.asarray(sub.convert("L")) < 250
            if maske is not None:
                mk |= maske[cb[1]:cb[3], cb[0]:cb[2]]
            f = max(1, max(mk.shape) // 300)
            mk = mk[:mk.shape[0] // f * f, :mk.shape[1] // f * f].reshape(mk.shape[0] // f, f, mk.shape[1] // f, f).any((1, 3))
            self.figurar.append((dx, dy, dw, dh, mk))
        return (lambda px: np.array([dx + (px[0] - cb[0]) * s, dy + dh - (px[1] - cb[1]) * s])), (dx, dy, dw, dh)

    def pil(self, a, b, breidd=1.8, hovud=9):
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

    def leiar(self, ident, mål, ved=None, foretrekk=(1.0, 0.6)):
        p = np.asarray(mål, float)
        a = self.plasser(p, 28, 28, foretrekk) if ved is None else np.asarray(ved, float)
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
            p.arc(cx - r, cy - r, cx + r, cy + r, 40, 245)
            c.drawPath(p, stroke=1, fill=0)
            self.pil((cx + r * math.cos(math.radians(285)), cy + r * math.sin(math.radians(285))), (cx + r * math.cos(math.radians(330)), cy + r * math.sin(math.radians(330))), 1.6 * s, 8 * s)
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
        c.setStrokeGray(.78)
        c.setLineWidth(.4)
        c.line(m, 49, self.W - m, 49)
        self.n += 1
        total = self.meta.get("page_count", "")
        self.tekst(f"{self.n:02d} / {total:02d}" if isinstance(total, int) else str(self.n), self.W - m, 32, 8, juster="r", reg=False)
        if self.meta.get("footer"):
            self.tekst(self.meta["footer"], m, 32, 7.5, reg=False)
        c.bookmarkPage(f"p{self.n}")
        c.addOutlineEntry(tittel, f"p{self.n}", 0)
        c.showPage()
        self.boksar, self.figurar = [], []


def valider(spec):
    feil = []
    views, parts = spec.get("views") or {}, spec.get("parts") or {}
    if not views:
        feil.append("views manglar")
    def vector(value, where):
        try:
            a = np.asarray(value, float)
            if a.shape != (3,) or not np.isfinite(a).all():
                raise ValueError()
            return a
        except (ValueError, TypeError):
            feil.append(f"{where}: krev tre endelege tal")
            return None
    for key, v in views.items():
        direction, up = vector(v.get("dir"), f"view {key} dir"), vector(v.get("up"), f"view {key} up")
        if direction is not None and up is not None and np.linalg.norm(np.cross(direction, up)) < 1e-6:
            feil.append(f"view {key}: dir og up må vere ulike, ikkje-null retningar")
    sjå = lambda v, kvar: isinstance(v, str) and v not in views and feil.append(f"{kvar}: ukjend view «{v}»")

    def scene(sc, kvar):
        if not sc:
            feil.append(f"{kvar}: scene manglar")
        for s in sc or []:
            if s.get("part") not in parts:
                feil.append(f"{kvar}: ukjend del «{s.get('part')}»")
            if s.get("role", "context") not in ROLLER:
                feil.append(f"{kvar}: ukjend rolle «{s.get('role')}»")
    for namn, p in parts.items():
        if "mesh" not in p and "primitive" not in p:
            feil.append(f"del {namn}: manglar mesh eller primitive")
        if "offset" in p:
            vector(p["offset"], f"del {namn} offset")
        sjå(p.get("thumb_view"), f"del {namn}")
    for i, s in enumerate(spec.get("pages", []), 1):
        t, kvar = s.get("type"), f"side {i} ({s.get('type')})"
        if t not in TYPAR:
            feil.append(f"{kvar}: ukjend type, bruk {', '.join(TYPAR)}")
            continue
        sjå(s.get("view"), kvar)
        if t in ("cover", "exploded"):
            scene(s.get("scene"), kvar)
        if t == "exploded" and s.get("inset"):
            scene(s["inset"].get("scene"), kvar + " inset")
            sjå(s["inset"].get("view"), kvar + " inset")
        if t == "step":
            if not s.get("figures"):
                feil.append(f"{kvar}: figures manglar")
            for j, f in enumerate(s.get("figures") or [], 1):
                scene(f.get("scene"), f"{kvar} figur {j}")
                sjå(f.get("view"), f"{kvar} figur {j}")
                if "centre" in f:
                    vector(f["centre"], f"{kvar} figur {j} centre")
                    if not isinstance(f.get("span"), (int, float)) or f["span"] <= 0:
                        feil.append(f"{kvar} figur {j}: centre krev positiv span")
                if f.get("detail"):
                    scene(f["detail"].get("scene", f.get("scene")), f"{kvar} figur {j} detail")
                    if not {"centre", "span"} <= set(f["detail"]):
                        feil.append(f"{kvar} figur {j}: detail krev centre og span")
            if s.get("diagram", {}).get("type") not in (None, "magnet_pair", "shutter_wiring"):
                feil.append(f"{kvar}: ukjend diagramtype")
        if t == "warnings" and not s.get("items"):
            feil.append(f"{kvar}: items manglar")
        if t == "hardware" and not (s.get("parts") or any(p.get("kind") == "hardware" for p in parts.values())):
            feil.append(f"{kvar}: ingen beslag (kind: hardware)")
    if feil:
        raise SystemExit("Feil i spesifikasjonen:\n- " + "\n- ".join(feil))


class Byggjar(Sider):
    def __init__(self, spec, rot, ut):
        valider(spec)
        self.spec, self.rot, self.ut = spec, rot, ut
        self.stil = {**STIL, **spec.get("style", {})}
        self.std = "iso" if "iso" in spec["views"] else next(iter(spec["views"]))
        self.work = f"{ut}/_arbeid"
        self.delar = Delar(spec["parts"], rot, f"{self.work}/glb")
        self.dok = Dok(f"{ut}/rettleiing.pdf", {**spec.get("meta", {}), "page_count": len(spec["pages"])}, self.stil)
        self.miniar, self.steg, self.rapport, self.brukt, self.vist, self.opp = {}, 0, [], {}, set(), None

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
            glb = self.delar.get(item["part"], item.get("cut"))
            ex = np.array(item.get("explode", [0, 0, 0]), float)
            for at in item.get("at") or [[0, 0, 0]]:
                at = np.array(at, float)
                flytt = at + (ex if item.get("role") in ("new", "exploded") else 0)
                if item.get("role") == "new" and np.linalg.norm(ex) > 0:
                    c = self.delar.senter[item["part"]] + at
                    bevegelse.append((item["part"], c + ex, c, item.get("line"), flytt, len(obj)))
                obj.append((glb, flytt))
                roller.append(item.get("role", "context"))
                delnamn.append(item["part"])
        return obj, roller, delnamn, bevegelse

    def figur(self, scene, view, mål, senter=None, span=None, zoom=1.05, crop=True, shade=False):
        obj, roller, delnamn, bev = self.objekt(scene)
        hjørne = np.array([self.delar.grenser[n] + t for (_, t), n in zip(obj, delnamn)]).reshape(-1, 3)
        lo, hi = hjørne.min(0), hjørne.max(0)
        if senter is None:
            senter, span = (lo + hi) / 2, float(np.linalg.norm(hi - lo)) / 2 * zoom
        v = self.view(view)

        def pass_(idx):
            mappe, cam = render([obj[i] for i in idx], v, self.work, senter, span, (lo, hi), [self.del_(delnamn[i]).get("color") for i in idx])
            crease = {k + 1: self.del_(delnamn[i])["crease"] for k, i in enumerate(idx) if "crease" in self.del_(delnamn[i])}
            min_px = {k + 1: self.del_(delnamn[i])["min_px"] for k, i in enumerate(idx) if "min_px" in self.del_(delnamn[i])}
            organic = [k + 1 for k, i in enumerate(idx) if self.del_(delnamn[i]).get("organic")]
            layers = konturlag(mappe, self.stil, crease, min_px, organic_ids=organic)
            return layers, cam, mappe
        synleg = [i for i, r in enumerate(roller) if r != "ghost"]
        spøkje = [i for i, r in enumerate(roller) if r == "ghost"]
        lag, cam, mappe = pass_(synleg)
        kant, z, idb = lag.edges, lag.depth, lag.ids
        fg = idb > 0
        bw = bh = PX
        if crop and fg.any():
            ys, xs = np.nonzero(fg)
            bw, bh = xs.max() - xs.min() + 32 * SK, ys.max() - ys.min() + 32 * SK
        faktor = max(bw / mål[0], bh / mål[1])
        px = self.stil["line_pt"] * faktor
        ut = np.full(fg.shape + (3,), 255, np.uint8)
        for k, i in enumerate(synleg):
            if roller[i] == "new":
                ut[idb == k + 1] = self.stil["new_fill"]
        if spøkje:
            glag, _, _ = pass_(spøkje)
            gk, gz, gidb = glag.edges, glag.depth, glag.ids
            g = gk & (~fg | ((gidb > 0) & (gz <= z + self.stil["depth_eps"])))
            ut[tjukk(g, px * self.stil["ghost_line"])] = self.stil["ghost_grey"]
        coverage = np.zeros(fg.shape, np.float32)
        for mask, width in ((lag.valleys, "valley_pt"), (lag.features, "feature_pt"), (lag.seams, "seam_pt"), (lag.silhouette, "line_pt")):
            coverage = np.maximum(coverage, strokedekning(mask, self.stil[width] * faktor))
        ut = np.rint(ut * (1 - coverage[..., None])).astype(np.uint8)
        if shade:
            ut = np.asarray(Image.open(f"{mappe}/farge.png").convert("RGB"))
        im = Image.fromarray(ut).resize((PX // SK, PX // SK), Image.LANCZOS)
        mørk = float((np.asarray(im.convert("L")) < 200).mean())
        return {"im": im, "P3": projektor(cam, SK), "bev": bev, "flytt": [t for _, t in obj], "roller": roller, "delnamn": delnamn, "cam": cam, "idb": idb,
                "id_av": {i: k + 1 for k, i in enumerate(synleg)}, "maske": fg[::SK, ::SK],
                "info": {"mappe": mappe, "mørk_del": round(mørk, 4), "strek_px": round(float(px), 1)}}

    def mini(self, namn, mål):
        k = (namn, round(mål[0]), round(mål[1]))
        if k not in self.miniar:
            self.miniar[k] = self.figur([{"part": namn}], self.del_(namn).get("thumb_view", self.std), mål, zoom=1.0)["im"]
        return self.miniar[k]

    def punkt(self, F, i, retning=(1.0, 0.6)):
        k = F["id_av"].get(i)
        mk = F["idb"] == k if k else None
        if mk is None or not mk.any():
            return None
        ys, xs = np.nonzero(mk)
        y0, x0 = ys.min(), xs.min()
        sub = ndimage.binary_erosion(mk[y0:ys.max() + 1, x0:xs.max() + 1], iterations=6)
        if sub.any():
            ys, xs = np.nonzero(sub)
            ys, xs = ys + y0, xs + x0
        j = np.argmax(xs * retning[0] - ys * retning[1])
        return np.array([xs[j], ys[j]], float) / SK

    def spor(self, F, i, a, b):
        k = F["id_av"].get(i)
        t = np.linspace(0, 1, int(np.linalg.norm(b - a)) + 2)
        q = a + (b - a) * t[:, None]
        ids = F["idb"][np.clip(q[:, 1].round().astype(int), 0, PX - 1), np.clip(q[:, 0].round().astype(int), 0, PX - 1)]
        start = int(np.argmax(ids != k)) if k and ids[0] == k else 0
        andre = np.nonzero((ids[start:] != 0) & (ids[start:] != k))[0]
        return q[start], q[start + andre[0]] if len(andre) else q[-1], bool(len(andre))

    def scenefigur(self, fig, boks, side):
        d = self.dok
        crop = fig.get("crop", True)
        F = self.figur(fig["scene"], fig.get("view", side.get("view", self.std)), boks[2:], senter=fig.get("centre"), span=fig.get("span"), zoom=fig.get("zoom", 1.05), crop=crop, shade=fig.get("shade", False))
        tilpdf, ramme = d.bilete(F["im"], boks, crop=crop, maske=F["maske"])
        P = lambda w: tilpdf(F["P3"](w))
        R = lambda q: tilpdf(np.asarray(q) / SK)
        for namn, frå, til, line, flytt, i in F["bev"]:
            if line == "none":
                continue
            s, e, traff = self.spor(F, i, F["P3"](frå) * SK, F["P3"](til) * SK)
            a, b = R(s), R(e)
            if (line or ("dashed" if self.del_(namn).get("kind") == "hardware" else "arrow")) == "dashed":
                d.stipla(a, R(F["P3"](til) * SK))
            else:
                heil = R(F["P3"](til) * SK) - R(F["P3"](frå) * SK)
                u = heil / (np.linalg.norm(heil) + 1e-9)
                L = float((b - a) @ u) - (6 if traff else 0)
                if L < 20:
                    L = min(40.0, 0.6 * float(np.linalg.norm(heil)))
                d.pil(a + u * 4, a + u * L)
        if fig.get("detail"):
            self.boble(fig, fig["detail"], P, F, ramme, side)
        for co in fig.get("callouts", []):
            t = P(co["point"])
            d.leiar(self.ident(co["part"]), t, t + np.array(co["offset"]) if "offset" in co else None)
        for annotation in fig.get("annotations", []):
            target = P(annotation["point"])
            lines = simpleSplit(annotation["text"], "M", 9, annotation.get("width", 112))
            width = max(pdfmetrics.stringWidth(s, "M", 9) for s in lines)
            height = 12 * len(lines)
            pos = target + np.asarray(annotation["offset"]) if "offset" in annotation else d.plasser(target, width + 12, height + 10, (-1, 1), (60, 85, 110, 140))
            c = d.c
            c.setStrokeGray(0)
            c.setLineWidth(.6)
            c.line(*target, *pos)
            c.setFillGray(1)
            c.rect(pos[0] - width/2 - 4, pos[1] - height/2 - 3, width+8, height+6, fill=1, stroke=0)
            c.setFillGray(0)
            c.circle(*target, 1.5, fill=1, stroke=0)
            for j, line in enumerate(lines):
                d.tekst(line, pos[0], pos[1] + height/2 - 9 - j*12, 9, juster="c")
        if fig.get("labels", True) is not False:
            grupper = {}
            for namn, frå, til, line, flytt, i in F["bev"]:
                grupper.setdefault(namn, []).append((flytt, i))
            for namn, inst in grupper.items():
                if self.del_(namn).get("kind") == "hardware":
                    fl, i = max(inst, key=lambda q: P(self.delar.senter[namn] + q[0]) @ (0.3, 1))
                    q = self.punkt(F, i, (1, 0.3))
                    s = f"{self.ident(namn)}x{len(inst)}"
                    w = pdfmetrics.stringWidth(s, "M", 13)
                    p = d.plasser(tilpdf(q) if q is not None else P(self.delar.senter[namn] + fl), w + 4, 16, (1, 0.3), (w / 2 + 8, w / 2 + 18, w / 2 + 32))
                    d.tekst(s, p[0], p[1] - 4.5, 13, juster="c")
                else:
                    q = self.punkt(F, inst[0][1])
                    if q is not None:
                        d.leiar(self.ident(namn), tilpdf(q))
                self.vist.add(namn)
            for i, (namn, rolle) in enumerate(zip(F["delnamn"], F["roller"])):
                if namn in self.vist or rolle == "ghost":
                    continue
                q = self.punkt(F, i)
                if q is not None:
                    d.leiar(self.ident(namn), tilpdf(q))
                    self.vist.add(namn)
        for a, b in fig.get("arrows", []):
            d.pil(P(a), P(b))
        if fig.get("multiplier"):
            d.tekst(fig["multiplier"], ramme[0] + ramme[2] - 4, ramme[1] + 6, 40, juster="r")
        F["info"]["figur_pt"] = [round(v, 1) for v in ramme]
        return ramme, F["info"]

    def boble(self, fig, det, P, F, ramme, side):
        d = self.dok
        r = det.get("r", 62)
        src = P(det["centre"])
        rk = max(6.0, float(np.linalg.norm(P(np.array(det["centre"], float) + np.array(F["cam"]["hogre"]) * det["span"]) - src)))
        x, y, w, h = ramme
        kandidatar = {"right": (x + w - r, y + r), "left": (x + r, y + r), "topright": (x + w - r, y + h - r), "topleft": (x + r, y + h - r)}
        pos = det.get("pos", "auto")
        cx, cy = pos if isinstance(pos, list) else kandidatar[pos] if pos in kandidatar else min(kandidatar.values(), key=lambda q: d.dekning(q[0] - r, q[1] - r, q[0] + r, q[1] + r) + np.linalg.norm(np.array(q) - src) / 2000)
        im = self.figur(det.get("scene", fig["scene"]), det.get("view", fig.get("view", side.get("view", self.std))), (2 * r, 2 * r), det["centre"], det["span"], crop=False)["im"]
        c = d.c
        c.setStrokeGray(0)
        c.setLineWidth(.9)
        c.circle(*src, rk, stroke=1, fill=0)
        v = np.array([cx, cy]) - src
        if np.linalg.norm(v) > r + rk:
            v /= np.linalg.norm(v)
            c.line(*(src + v * rk), *(np.array([cx, cy]) - v * r))
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
        d.reg("boble", cx - r, cy - r, cx + r, cy + r, geometri=False)
        if det.get("label"):
            d.tekst(det["label"], cx, cy - r - 16, 12, True, "c")

    def bygg(self):
        for i, side in enumerate(self.spec["pages"], 1):
            print(f"Side {i}/{len(self.spec['pages'])}: {side.get('title', side['type'])}", flush=True)
            getattr(self, side["type"])(side)
        self.dok.c.save()
        pdf = f"{self.ut}/rettleiing.pdf"
        shutil.rmtree(f"{self.ut}/sider", ignore_errors=True)
        os.makedirs(f"{self.ut}/sider")
        subprocess.run(["pdftoppm", "-r", "110", "-png", pdf, f"{self.ut}/sider/side"], check=True)
        if os.path.isdir(f"{self.work}/r"):
            for k in set(os.listdir(f"{self.work}/r")) - BRUKT:
                shutil.rmtree(f"{self.work}/r/{k}")
        bom = {k: {"i_steg": self.brukt.get(k, 0), "i_delliste": p.get("qty", 1)} for k, p in self.spec["parts"].items() if p.get("kind") == "hardware"}
        åtvaringar = [f"{k}: {v['i_steg']} brukt i steg, {v['i_delliste']} i dellista" for k, v in bom.items() if v["i_steg"] != v["i_delliste"]]
        åtvaringar += [f"side {r['side']}: steget har ingen ny del" for r in self.rapport if r.get("nye_delar") == 0 and r.get("action") != "inspect"]
        åtvaringar += [f"side {r['side']}: tom figur" for r in self.rapport for f in r.get("figurar", [r]) if f.get("mørk_del", 1) < 0.002]
        åtvaringar += [f"side {k['side']}: {k['a']} overlappar {k['b']}" for k in self.dok.konfliktar]
        sources = {}
        for part in self.spec["parts"].values():
            mesh = part.get("mesh", [])
            for file in [mesh] if isinstance(mesh, str) else mesh:
                sources[file] = innhald(os.path.join(self.rot, file))
        json.dump({"pdf": pdf, "sha256": hashlib.sha256(open(pdf, "rb").read()).hexdigest(), "sider": self.dok.n,
                   "spec_sha256": hashlib.sha256(json.dumps(self.spec, sort_keys=True).encode()).hexdigest(),
                   "source_commit": self.spec.get("meta", {}).get("source_commit"), "mesh_sha256": sources,
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
