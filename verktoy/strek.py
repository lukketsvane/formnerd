import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HER = os.path.dirname(os.path.abspath(__file__))
THREE = os.environ.get("THREE_DIR", os.path.join(HER, "node_modules", "three"))


def les_rgba(sti):
    return np.asarray(Image.open(sti).convert("RGBA")).astype(np.float32)


def strek(mappe, utheva=(), grå=(), linje=2, skala=2):
    n = les_rgba(f"{mappe}/normal.png")
    dj = les_rgba(f"{mappe}/djupn.png")
    idb = les_rgba(f"{mappe}/id.png")[..., 0].round().astype(int)
    fg = idb > 0
    z = dj[..., 0] / 255 + dj[..., 1] / 255 / 255
    nv = n[..., :3] / 127.5 - 1
    nv /= np.linalg.norm(nv, axis=-1, keepdims=True) + 1e-9
    kant = np.zeros(fg.shape, bool)
    for ax in (0, 1):
        for s in (1, -1):
            idn = np.roll(idb, s, ax)
            kant |= idb != idn
            zn = np.roll(z, s, ax)
            kant |= fg & (np.roll(fg, s, ax)) & (np.abs(z - zn) > 0.004)
            nn = np.roll(nv, s, ax)
            kant |= fg & np.roll(fg, s, ax) & ((nv * nn).sum(-1) < np.cos(np.radians(38)))
    kant = ndimage.binary_dilation(kant, iterations=max(0, linje - 1))
    ut = np.full(fg.shape + (3,), 255, np.float32)
    for i in grå:
        ut[idb == i] = (226, 226, 226)
    for i in utheva:
        ut[idb == i] = (205, 215, 225)
    ut[kant] = 20
    im = Image.fromarray(ut.astype(np.uint8))
    return im.resize((im.width // skala, im.height // skala), Image.LANCZOS)


def render(scene, mappe):
    os.makedirs(mappe, exist_ok=True)
    sti = f"{mappe}/scene.json"
    json.dump(scene, open(sti, "w"))
    subprocess.run(["node", os.path.join(HER, "strek.mjs"), sti, mappe], check=True, env={**os.environ, "THREE_DIR": THREE})
    return json.load(open(f"{mappe}/ankre.json"))


if __name__ == "__main__":
    scene = json.load(open(sys.argv[1]))
    ankre = render(scene, sys.argv[2])
    strek(sys.argv[2]).save(f"{sys.argv[2]}/strek.png")
