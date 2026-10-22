"""Ytre form til Entropi som rein B-rep (build123d/OCCT). Ingen mesh-kjelde."""
import json, pathlib, time
from build123d import *

HER = pathlib.Path(__file__).resolve().parent
K = json.loads((HER / "delar_konfig.json").read_text())
F = K["form"]
T0 = time.time()


def tid(n):
    print(f"{n:<28}{time.time() - T0:7.1f} s", flush=True)


def omriss():
    b = F["kropp"]
    r = RectangleRounded(b["x"][1] - b["x"][0], b["y"][1] - b["y"][0], b["hjorne_r"]).moved(Pos((b["x"][0] + b["x"][1]) / 2, (b["y"][0] + b["y"][1]) / 2))
    for cx, cy, cr in b["bular"]:
        r = r + Pos(cx, cy) * Circle(cr)
    kon = [v for v in r.vertices() if v.Z == 0]
    return fillet(kon, b["konkav_r"])


def kropp_blokk(om):
    b = F["kropp"]
    k = extrude(om, b["topp_z"])
    k = fillet(k.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1], b["topp_fillet"])
    k = fillet(k.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[0], b["botn_fillet"])
    return k


def linsetonne():
    L = F["linse"]
    ay, az = K["akse"]["y"], K["akse"]["z"]
    c = Pos(L["x"][0], ay, az) * Rot(0, 90, 0) * Cone(L["r"][0], L["r"][1], L["x"][1] - L["x"][0], align=(Align.CENTER, Align.CENTER, Align.MIN))
    return fillet(c.edges().group_by(Axis.X)[-1], L["front_fillet"])


def royr(p, r):
    sti = Spline(*[tuple(q) for q in p])
    return sweep(Plane(origin=sti @ 0, z_dir=sti % 0) * Circle(r), sti, transition=Transition.ROUND)


def sokarblokk():
    b = F["sokar"]
    k = Box(b["x"][1] - b["x"][0], b["y"][1] - b["y"][0], b["z"][1] - b["z"][0], align=(Align.MIN, Align.MIN, Align.MIN)).moved(Pos(b["x"][0], b["y"][0], b["z"][0]))
    return fillet([e for e in k.edges() if e.center().Z > F["kropp"]["topp_z"] - 1], b["fillet"])


def syl(cx, cy, r, z0, z1):
    return Pos(cx, cy, z0) * Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def hjulboss():
    b = F["hjulboss"]
    c = syl(b["senter"][0], b["senter"][1], b["r"], b["z"][0], b["z"][1])
    return fillet(c.edges().group_by(Axis.Z)[-1], b["fillet"])


def knappboss():
    b = F["knappboss"]
    c = syl(K["utloysar"]["senter"][0], K["utloysar"]["senter"][1], b["r"], b["z"][0], b["z"][1])
    return fillet(c.edges().group_by(Axis.Z)[-1], b["fillet"])


def bygg_form():
    om = omriss()
    k = kropp_blokk(om)
    delar = {"linse": linsetonne(), "sokar": sokarblokk(), "hjulboss": hjulboss(), "knappboss": knappboss()}
    delar.update({p["namn"]: royr(p["punkt"], p["r"]) for p in F["royr"]})
    tid("delar")
    for n, d in delar.items():
        for_ = set(k.edges())
        k = k + d
        if n in F.get("fillet_overgang", []):
            nye = [e for e in k.edges() if e not in for_ and not any(e.is_same(b) for b in d.edges())]
            try:
                k = fillet(nye, F["overgang_fillet"])
            except Exception as ex:
                print("overgangsfillet feila for", n, ex)
    tid("union")
    return k, om, delar


if __name__ == "__main__":
    k, _, _ = bygg_form()
    print("gyldig", k.is_valid, "volum", round(k.volume / 1000, 1), "cm3", "flater", len(k.faces()))
    ut = HER.parent / "print" / "cad"
    ut.mkdir(exist_ok=True)
    export_stl(k, ut / "form.stl", tolerance=0.02, angular_tolerance=0.15)
    tid("stl")
