import json
import sys

import manifold3d as mf
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

PITCH = 0.25


def last_ytre(sti, breidd):
    m = trimesh.load(sti, force="mesh")
    m.merge_vertices(merge_tex=True, merge_norm=True)
    m.apply_translation(-m.bounds[0])
    m.apply_scale(breidd / m.extents[2])
    return m


def til_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def til_tm(M):
    g = M.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)


def fyll(m, pitch=PITCH, kant=4):
    lo = m.bounds[0] - kant * pitch
    n = np.ceil((m.bounds[1] - lo) / pitch).astype(int) + kant
    v, f = m.vertices, m.faces
    t = (v[f] - lo) / pitch + np.array([0.0, 0.0137, 0.0071])
    ylo, yhi = np.ceil(t[:, :, 1].min(1)).astype(int), np.floor(t[:, :, 1].max(1)).astype(int)
    zlo, zhi = np.ceil(t[:, :, 2].min(1)).astype(int), np.floor(t[:, :, 2].max(1)).astype(int)
    cy, cz = np.clip(yhi - ylo + 1, 0, None), np.clip(zhi - zlo + 1, 0, None)
    k = np.repeat(np.arange(len(f)), cy * cz)
    i = np.arange((cy * cz).sum()) - np.repeat(np.cumsum(cy * cz) - cy * cz, cy * cz)
    yy = ylo[k] + i // np.maximum(cz[k], 1)
    zz = zlo[k] + i % np.maximum(cz[k], 1)
    a, b, c = t[k, 0], t[k, 1], t[k, 2]
    d = (b[:, 1] - c[:, 1]) * (a[:, 2] - c[:, 2]) + (c[:, 2] - b[:, 2]) * (a[:, 1] - c[:, 1])
    ok = np.abs(d) > 1e-12
    d = np.where(ok, d, 1)
    w1 = ((b[:, 1] - c[:, 1]) * (zz - c[:, 2]) + (c[:, 2] - b[:, 2]) * (yy - c[:, 1])) / d
    w2 = ((c[:, 1] - a[:, 1]) * (zz - c[:, 2]) + (a[:, 2] - c[:, 2]) * (yy - c[:, 1])) / d
    inne = ok & (w1 >= 0) & (w2 >= 0) & (1 - w1 - w2 >= 0)
    x = w1 * a[:, 0] + w2 * b[:, 0] + (1 - w1 - w2) * c[:, 0]
    veksl = np.zeros((n[1], n[2], n[0]), np.int32)
    np.add.at(veksl, (yy[inne], zz[inne], np.clip(np.ceil(x[inne]).astype(int), 0, n[0] - 1)), 1)
    occ = (np.cumsum(veksl, axis=2) % 2).astype(bool)
    occ[veksl.sum(2) % 2 == 1] = False
    return occ.transpose(2, 0, 1), lo


def avstand(occ, pitch=PITCH):
    inn = ndimage.distance_transform_edt(occ) * pitch - pitch / 2
    ut = ndimage.distance_transform_edt(~occ) * pitch - pitch / 2
    return np.where(occ, inn, -ut).astype(np.float32)


def nivaa(d, lo, niva, pitch=PITCH):
    v, f, _, _ = measure.marching_cubes(d, level=niva, spacing=(pitch,) * 3)
    m = trimesh.Trimesh(v + lo, f[:, ::-1], process=True)
    if m.volume < 0:
        m.invert()
    return til_mf(m)


def boks(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return mf.Manifold.cube(hi - lo).translate(lo)


def sylinder(senter, r, lengd, akse):
    c = mf.Manifold.cylinder(lengd, r, r, 96)
    if akse == "x":
        c = c.rotate((0, 90, 0))
    elif akse == "y":
        c = c.rotate((-90, 0, 0))
    return c.translate(np.asarray(senter, float) - np.array({"x": (lengd / 2, 0, 0), "y": (0, lengd / 2, 0), "z": (0, 0, lengd / 2)}[akse]))


STOR = 1000.0


def halvrom_x(a, b):
    return boks((a, -STOR, -STOR), (b, STOR, STOR))
