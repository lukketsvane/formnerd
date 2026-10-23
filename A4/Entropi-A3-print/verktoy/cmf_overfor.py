import sys, json, pathlib, numpy as np, trimesh

HER = pathlib.Path(__file__).resolve().parent
A3 = HER.parent
UT = A3 / "print" / "cmf"
LYS, MOERK = np.array([150, 154, 154], np.uint8), np.array([62, 67, 69], np.uint8)
HEILT_MOERKE = ("utloysar", "usb-lokk", "hjulaksel")
DELAR = ("botn", "topp", "utloysar", "usb-lokk", "hjulaksel")


def moerk(p, K):
    p = np.atleast_2d(np.asarray(p, float))
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    H, U, D, A = K["form"]["hjulboss"], K["utloysar"], K["detalj"], K["akse"]
    sk, ok = D["skinne"], D["okularring"]
    r_l = np.hypot(y - A["y"], z - A["z"])
    over_saum = z > 58.5
    sokar = (x < 18.2) & over_saum
    hjul = (np.hypot(x - H["senter"][0], y - H["senter"][1]) < H["r"] + 0.3) & over_saum
    knapp = (np.hypot(x - U["senter"][0], y - U["senter"][1]) < K["form"]["knappboss"]["r"] + 0.3) & over_saum
    linse = (x > D["panel_linje"]["x"]) & (r_l < 31.5)
    skinne = (z < sk["z_topp"] + 0.2) & (x > sk["x"][0] - 0.5) & (x < sk["x"][1] + 0.5) & (y > sk["y"][0] - 0.5) & (y < sk["y"][1] + 0.5)
    okular = (x < 1.0) & (np.hypot(y - ok["senter"][0], z - ok["senter"][1]) < ok["r_ytre"] + 0.8)
    return sokar | hjul | knapp | linse | skinne | okular


def farg(namn, K):
    m = trimesh.load(A3 / "print" / "stl" / f"{namn}.stl", process=False)
    v = np.asarray(m.vertices)
    er_moerk = np.ones(len(v), bool) if namn in HEILT_MOERKE else moerk(v, K)
    farge = np.where(er_moerk[:, None], MOERK, LYS)
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[farge, np.full(len(v), 255, np.uint8)])
    m.export(UT / f"{namn}.ply")
    return len(v), int((~er_moerk).sum())


if __name__ == "__main__":
    UT.mkdir(parents=True, exist_ok=True)
    K = json.loads((HER / "delar_konfig.json").read_text())
    for namn in sys.argv[1:] or DELAR:
        n, lyse = farg(namn, K)
        print(namn, n, "lyse punkt:", lyse)
