import sys, time, json, os
import numpy as np
from build123d import (Solid, Face, Wire, Edge, Vector, Plane, Location, Compound, GeomType, SlotOverall, extrude, Axis, Color,
                       export_step, export_stl, export_gltf)
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.OCP.collections import List_TopoDS_Shape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Shape

T0 = time.time()
D = '.'


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def valid(s):
    return BRepCheck_Analyzer(s.wrapped).IsValid()


def biggest(shape):
    sols = list(shape.solids()) if hasattr(shape, 'solids') else [shape]
    return max(sols, key=lambda q: q.volume)


def save(s, p):
    BRepTools.Write_s(s.wrapped, p)


def load(p):
    s = TopoDS_Shape(); BRepTools.Read_s(s, p, BRep_Builder())
    return Solid(s)


def multi_cut(base, tools):
    a = List_TopoDS_Shape(); a.Append(base.wrapped)
    t = List_TopoDS_Shape()
    for s in tools:
        t.Append(s.wrapped)
    op = BRepAlgoAPI_Cut(); op.SetArguments(a); op.SetTools(t); op.SetRunParallel(True); op.SetUseOBB(True); op.SetFuzzyValue(1e-5)
    op.Build()
    if not op.IsDone():
        raise RuntimeError('cut failed')
    return biggest(Compound(op.Shape()))


def V(r, z):
    return Vector(r, 0, z)


def revolve_profile(items):
    pts = [items[0][1]]
    edges = []
    for it in items[1:]:
        if it[0] == 'L':
            edges.append(Edge.make_line(V(*pts[-1]), V(*it[1]))); pts.append(it[1])
        else:
            edges.append(Edge.make_three_point_arc(V(*pts[-1]), V(*it[1]), V(*it[2]))); pts.append(it[2])
    edges.append(Edge.make_line(V(*pts[-1]), V(*pts[0])))
    face = Face(Wire(edges))
    return Solid.revolve(face, 360, Axis.Z)


def smooth_field(seed, amp):
    rng = np.random.default_rng(seed)
    k = rng.normal(size=(7, 4)); ph = rng.uniform(0, 2 * np.pi, size=(7, 4))

    def f(th, z, H):
        t = np.radians(th)
        v = 0.0
        for i in range(1, 6):
            for j in range(0, 3):
                v = v + amp * k[i, j] / i * np.cos(i * t + ph[i, j]) * np.cos(j * np.pi * z / H + ph[i, j + 1])
        return v
    return f


def entropy(p, th, z, field):
    seam = p['SEAM']
    tw = (np.asarray(th) - seam) % 360.0 + seam - 360.0
    zn = (np.asarray(z) - p['Z_LO']) / (p['Z_HI'] - p['Z_LO'])
    t = (tw - (p['TH_A'] - p['SLANT'] * (zn - 0.5))) / p['SPAN']
    t = t + field(th, z, p['HR'])
    e = np.clip(t, 0.0, 1.0)
    return e * e * (3 - 2 * e) if p.get('E_SMOOTH', 1) else e


def ring_solid(p):
    R, HR = p['R'], p['HR']
    r_in = p['RC'] + p['GAP']
    zf = HR - p['REC']
    cb, co, ci = p['CH_BOT'], p['CH_TOP_O'], p['CH_TOP_I']
    it = [('L', (0.0, 0.0)), ('L', (R - cb, 0.0)), ('L', (R, cb)), ('L', (R, HR - co)), ('L', (R - co, HR))]
    if ci > 0:
        it += [('L', (r_in + ci, HR)), ('L', (r_in, HR - ci))]
    else:
        it += [('L', (r_in, HR))]
    it += [('L', (r_in, zf)), ('L', (0.0, zf))]
    ring = revolve_profile(it)
    dd = min(p['BORE_DEPTH'], zf - 0.8)
    hole = Solid.make_cylinder(p['BORE_R'], dd + 0.01, Plane(origin=(0, 0, -0.01)))
    flat = Solid.make_box(10, 10, dd + 0.2, Plane(origin=(p['BORE_FLAT'], -5, -0.1)))
    ring = biggest(ring.cut(hole.cut(flat)))
    return ring


def dish_profile(p, z1):
    RC, ch = p['RC'], p['CH_CAP']
    a = p['DISH_D'] / 2.0; dep = p['DISH_DEPTH']; rf = p['DISH_FIL']
    Rs = (a * a + dep * dep) / (2 * dep)
    zs = z1 - dep + Rs
    zfc = z1 - rf
    rfc = np.sqrt((Rs + rf) ** 2 - (zfc - zs) ** 2)
    u = np.array([rfc, zfc - zs]); u /= np.linalg.norm(u)
    ps = (u[0] * Rs, zs + u[1] * Rs)
    a0 = np.arctan2(-Rs, 0.0); a1 = np.arctan2(u[1], u[0]); am = 0.5 * (a0 + a1)
    pm = (Rs * np.cos(am), zs + Rs * np.sin(am))
    b0 = np.arctan2(ps[1] - zfc, ps[0] - rfc); b1 = np.pi / 2
    bm = 0.5 * (b0 + b1)
    fm = (rfc + rf * np.cos(bm), zfc + rf * np.sin(bm))
    return [('A', pm, ps), ('A', fm, (rfc, z1)), ('L', (RC - ch, z1)), ('L', (RC, z1 - ch))], (0.0, z1 - dep)


def cap_solid(p):
    HR = p['HR']
    z0 = HR - p['REC'] + p['CAP_CLEAR']
    z1 = HR + p['CAP_UP']
    RC, ch = p['RC'], p['CH_CAP']
    if p['CAP_MODE'] == 'dish_center':
        segs, start = dish_profile(p, z1)
        it = [('L', start)] + segs + [('L', (RC, z0)), ('L', (0.0, z0))]
    else:
        it = [('L', (0.0, z0)), ('L', (RC, z0)), ('L', (RC, z1 - ch)), ('L', (RC - ch, z1)), ('L', (0.0, z1))]
    cap = revolve_profile(it)
    if p['CAP_MODE'] == 'dish_offset':
        from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ
        from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
        a = p['DISH_D'] / 2; dep = p['DISH_DEPTH']; sy = p.get('DISH_SY', 1.0)
        Rs = (a * a + dep * dep) / (2 * dep)
        g = gp_GTrsf(); g.SetVectorialPart(gp_Mat(1, 0, 0, 0, sy, 0, 0, 0, 1)); g.SetTranslationPart(gp_XYZ(p['DISH_X'], p['DISH_Y'], z1 - dep + Rs))
        sph = Solid(BRepBuilderAPI_GTransform(Solid.make_sphere(Rs).rotate(Axis.X, 90).wrapped, g, True).Shape())
        cap = biggest(cap.cut(sph))
        rim = [e for e in cap.edges() if abs(e.center().Z - z1) < 1e-4 and e.length < 40 and abs(e.center().X - p['DISH_X']) < 1.0]
        if rim:
            try:
                cap = cap.fillet(p['DISH_FIL'], rim)
            except Exception as ex:
                log('dish fillet failed', ex)
    return cap, z1


def index_cut(p, target, z_top):
    mode = p['IDX_MODE']
    ang = np.radians(p['IDX_ANG'])
    if mode == 'line_cap':
        L = p['IDX_R1'] - p['IDX_R0']; rm = 0.5 * (p['IDX_R0'] + p['IDX_R1'])
        xd = (np.cos(ang), np.sin(ang), 0)
    else:
        L = p['IDX_LEN']; rm = p['IDX_RM']
        xd = (-np.sin(ang), np.cos(ang), 0)
    pl = Plane(origin=(rm * np.cos(ang), rm * np.sin(ang), z_top - p['IDX_D']), x_dir=xd, z_dir=(0, 0, 1))
    slot = pl * SlotOverall(L, p['IDX_W'])
    groove = extrude(slot, amount=2.0).solids()[0]
    out = biggest(target.cut(groove))
    paint = extrude(slot, amount=p['IDX_D'] - 0.03).solids()[0]
    return out, paint


def base_solid(p):
    zt = -p['BASE_GAP']; zb = zt - p['BASE_H']; Rb = p['BASE_R']; c = p['BASE_CH']
    it = [('L', (p['BASE_RI'], zb)), ('L', (Rb - c, zb)), ('L', (Rb, zb + c)), ('L', (Rb, zt - c)), ('L', (Rb - c, zt)), ('L', (p['BASE_RI'], zt))]
    return revolve_profile(it)


def capsule(th_deg, za, zb, w, depth, R):
    hw = w / 2.0
    r = (hw * hw + depth * depth) / (2.0 * depth)
    c = R - depth + r
    th = np.radians(th_deg)
    x, y = c * np.cos(th), c * np.sin(th)
    zc0, zc1 = za + hw, zb - hw
    if zc1 - zc0 < 0.02:
        return Solid.make_sphere(r).moved(Location((x, y, 0.5 * (za + zb))))
    cyl = Solid.make_cylinder(r, zc1 - zc0, Plane(origin=(x, y, zc0)))
    s0 = Solid.make_sphere(r).moved(Location((x, y, zc0)))
    s1 = Solid.make_sphere(r).moved(Location((x, y, zc1)))
    return biggest(cyl.fuse(s0, s1).clean())


def dimple(th_deg, zm, dd, depth, R):
    hw = dd / 2.0
    r = (hw * hw + depth * depth) / (2.0 * depth)
    c = R - depth + r
    th = np.radians(th_deg)
    return Solid.make_sphere(r).moved(Location((c * np.cos(th), c * np.sin(th), zm)))


def notch(th_deg, zn, rn, dn, L, R):
    th = np.radians(th_deg)
    c = R + rn - dn
    t = np.array([-np.sin(th), np.cos(th), 0.0])
    ctr = np.array([c * np.cos(th), c * np.sin(th), zn])
    st = ctr - t * L / 2
    return Solid.make_cylinder(rn, L, Plane(origin=tuple(st), z_dir=tuple(t)))


def layout_fd(p):
    R, N = p['R'], p['N']
    rng = np.random.default_rng(p['SEED'])
    field = smooth_field(p['SEED'] + 1, p['NOISE'])
    pitch = 360.0 / N
    zg = np.linspace(p['Z_LO'], p['Z_HI'], 400)
    flutes, cells = [], []
    W = p['W_FLUTE']
    for i in range(N):
        th = p['PHASE'] + i * pitch + rng.normal(0, 0.1)
        e = entropy(p, np.full_like(zg, th), zg, field)
        ok = e < p['E1']
        if ok.all():
            seg = [(p['Z_LO'], p['Z_HI'])]
        else:
            seg = []
            idx = np.where(np.diff(np.r_[0, ok.astype(int), 0]))[0].reshape(-1, 2)
            for a, b in idx:
                za, zb = zg[a], zg[min(b, len(zg) - 1)]
                if a == 0:
                    za = p['Z_LO']
                if b >= len(zg):
                    zb = p['Z_HI']
                emax = e[a:b].max() if b > a else 0
                if zb - za >= p['MIN_FLUTE'] * W:
                    if zb < p['Z_HI'] - 1e-6:
                        zb -= p['FLUTE_GAP']
                    if za > p['Z_LO'] + 1e-6:
                        za += p['FLUTE_GAP']
                    if zb - za >= W:
                        seg.append((za, zb))
        for za, zb in seg:
            em = float(np.interp(0.5 * (za + zb), zg, e))
            w = W * (1.0 - p['FLUTE_SHRINK'] * em)
            flutes.append(dict(kind='slot', th=th, za=za, zb=zb, w=w, depth=p['DEPTH_FLUTE'] * w, e=em))
    th0 = p['TH_A'] - p['SPAN'] * 0.6 - p['SLANT']
    th1 = p['SEAM'] - 0.5
    s_of = lambda th: np.radians(th) * R
    th_of = lambda s: np.degrees(s / R)
    hfun = lambda th, z: p['D_MAX'] - (p['D_MAX'] - p['D_MIN']) * np.clip((entropy(p, th, z, field) - p['E1']) / (1 - p['E1']), 0, 1) ** p['D_GAMMA']
    ths = np.linspace(th0, th1, 900); zs = np.linspace(p['Z_LO'], p['Z_HI'], 120)
    TT, ZZ = np.meshgrid(ths, zs, indexing='ij')
    E = entropy(p, TT, ZZ, field)
    Hh = hfun(TT, ZZ)
    dens = np.where(E >= p['E1'], 1.0 / (0.866 * Hh ** 2), 0.0)
    cellA = (s_of(ths[1]) - s_of(ths[0])) * (zs[1] - zs[0])
    npts = int(dens.sum() * cellA)
    prob = (dens / dens.sum()).ravel()
    pick = rng.choice(prob.size, size=npts, p=prob)
    pts = np.stack([s_of(TT.ravel()[pick]) + rng.uniform(-0.05, 0.05, npts), ZZ.ravel()[pick] + rng.uniform(-0.05, 0.05, npts)], 1)
    fl = np.array([[s_of(f['th']), f['za'] + f['w'] / 2, f['zb'] - f['w'] / 2, f['w']] for f in flutes])
    OV = p['OVERLAP']
    for itn in range(p['RELAX']):
        th_p = th_of(pts[:, 0])
        h = hfun(th_p, pts[:, 1])
        d = pts[:, None, :] - pts[None, :, :]
        dist = np.linalg.norm(d, axis=2) + 1e-9
        tgt = 0.5 * (h[:, None] + h[None, :])
        over = np.clip(tgt - dist, 0, None); np.fill_diagonal(over, 0)
        mv = (d / dist[..., None] * over[..., None]).sum(1) * 0.45
        dz = np.clip(pts[:, 1], fl[:, 1].min() if len(fl) else 0, None)
        if len(fl):
            dzc = np.clip(pts[:, 1][:, None], fl[None, :, 1], fl[None, :, 2])
            vx = pts[:, 0][:, None] - fl[None, :, 0]; vz = pts[:, 1][:, None] - dzc
            dd_ = np.sqrt(vx ** 2 + vz ** 2) + 1e-9
            need = 0.5 * (h[:, None] * OV + fl[None, :, 3]) * p['FLUTE_CLEAR']
            ov2 = np.clip(need - dd_, 0, None)
            mv[:, 0] += (vx / dd_ * ov2).sum(1); mv[:, 1] += (vz / dd_ * ov2).sum(1)
        pts += mv
        e_p = entropy(p, th_of(pts[:, 0]), pts[:, 1], field)
        pts[:, 0] += np.where(e_p < p['E1'], 0.08 * h, 0.0)
        hz = 0.5 * h * OV
        pts[:, 1] = np.clip(pts[:, 1], p['Z_LO'] + hz, p['Z_HI'] - hz)
        pts[:, 0] = np.clip(pts[:, 0], None, s_of(th1) - hz)
    th_p = th_of(pts[:, 0]); h = hfun(th_p, pts[:, 1])
    e_p = entropy(p, th_p, pts[:, 1], field)
    keep = e_p >= p['E1'] * 0.7
    for k in np.where(keep)[0]:
        dd = h[k] * OV * (1 + rng.normal(0, p['D_JIT']))
        cells.append(dict(kind='dimple', th=float(th_p[k]), z=float(pts[k, 1]), d=float(dd), depth=float(p['DEPTH_DIMPLE'] * dd), e=float(e_p[k])))
    return flutes + cells


def layout_gear(p):
    R, N = p['R'], p['NT']
    rng = np.random.default_rng(p['SEED'])
    field = smooth_field(p['SEED'] + 1, p['NOISE'])
    pitch = 360.0 / N
    out = []
    tops = []
    for i in range(N):
        th = p['PHASE'] + i * pitch
        e = float(entropy(p, th, p['Z_HI'], field))
        zt = p['GZ_TOP0'] + (p['GZ_TOP1'] - p['GZ_TOP0']) * e + rng.normal(0, p['GZ_JIT']) * e
        w = p['WG'] * (1 + rng.normal(0, p.get('WG_JIT', 0.0)) * e)
        tops.append(zt)
        out.append(dict(kind='groove', th=th + rng.normal(0, p.get('TH_JIT', 0.0)) * e, za=-3.0, zb=zt, w=w, depth=p['DG'], e=e))
    for i in range(N):
        tht = p['PHASE'] + (i + 0.5) * pitch
        e = float(entropy(p, tht, p['Z_HI'], field))
        if e < p['E1']:
            continue
        ztop = min(tops[i], tops[(i + 1) % N])
        if e < p['E2']:
            k = (e - p['E1']) / (p['E2'] - p['E1'])
            out.append(dict(kind='groove', th=tht, za=-3.0, zb=ztop - 0.15 * k, w=p['SPLIT_W'] * (0.6 + 0.4 * k), depth=p['DG'] * (0.45 + 0.55 * k), e=e))
            continue
        k = (e - p['E2']) / (1 - p['E2'])
        sp = p['NS0'] + (p['NS1'] - p['NS0']) * k
        z = p['NZ0'] + rng.uniform(0, sp)
        while z < ztop + sp * 0.2:
            rn = sp * p['NR'] * (1 + rng.normal(0, 0.1 * (0.5 + k)))
            dn = p['ND'] * (0.4 + 0.6 * k) * rng.uniform(0.6, 1.0)
            out.append(dict(kind='notch', th=tht + rng.normal(0, 0.6 * k), z=float(z), r=float(rn), depth=float(dn), L=float(np.radians(pitch) * R * p['NL']), e=e))
            z += sp * rng.uniform(0.9, 1.15 + 0.3 * k)
    return out


def tool_of(c, R):
    if c['kind'] in ('slot', 'groove'):
        return capsule(c['th'], c['za'], c['zb'], c['w'], c['depth'], R)
    if c['kind'] == 'dimple':
        return dimple(c['th'], c['z'], c['d'], c['depth'], R)
    return notch(c['th'], c['z'], c['r'], c['depth'], c['L'], R)


def build(p, pref):
    lay = {'fd': layout_fd, 'gear': layout_gear, 'none': lambda q: []}[p['KNURL']](p)
    kinds = {}
    for c in lay:
        kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
    log('layout', kinds)
    json.dump(lay, open(f'{pref}_layout.json', 'w'))
    ring = ring_solid(p)
    log('ring blank', valid(ring))
    tools = [(np.arctan2(np.sin(np.radians(c['th'])), np.cos(np.radians(c['th']))), tool_of(c, p['R'])) for c in lay]
    tools.sort(key=lambda q: q[0])
    log('tools', len(tools))
    nsec = p.get('NSEC', 12)
    for k in range(nsec):
        sub = [t for a, t in tools[k * len(tools) // nsec:(k + 1) * len(tools) // nsec]]
        if sub:
            prev = ring
            ring = multi_cut(prev, sub)
            if not valid(ring):
                from OCP.ShapeFix import ShapeFix_Shape
                fx = ShapeFix_Shape(ring.wrapped); fx.Perform()
                fixed = biggest(Compound(fx.Shape()))
                if valid(fixed):
                    ring = fixed
                    log('sector', k, 'fixed by ShapeFix')
                else:
                    log('sector', k, 'invalid, retry tools one by one')
                    ring = prev
                    for t in sub:
                        r2 = multi_cut(ring, [t])
                        if valid(r2):
                            ring = r2
                        else:
                            log('  dropped one tool')
    log('ring cut valid', valid(ring), 'faces', len(ring.faces()))
    cap, z1 = cap_solid(p)
    parts = {'ring': ring}
    if p['IDX_MODE'] == 'line_cap':
        cap, paint = index_cut(p, cap, z1)
    else:
        parts['ring'], paint = index_cut(p, parts['ring'], p['HR'])
    parts['cap'] = cap; parts['paint'] = paint
    if p.get('BASE'):
        parts['base'] = base_solid(p)
    for n, s in parts.items():
        log(n, 'valid', valid(s), 'vol', round(s.volume, 2))
        save(s, f'{pref}_{n}.brep')
    return parts


if __name__ == '__main__':
    cfg = json.load(open(sys.argv[1]))
    pref = sys.argv[2]
    over = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    p = dict(json.load(open(f'{D}/defaults.json'))); p.update(cfg); p.update(over)
    json.dump(p, open(f'{pref}_params.json', 'w'), indent=1)
    build(p, pref)
    log('done')
