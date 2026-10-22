import numpy as np, trimesh
from scipy import sparse
from scipy.spatial import cKDTree
from manifold3d import Manifold, OpType


def glatt_felt(tm, verdi, iterasjonar=80):
    """Jamnar eit skalarfelt over overflata til meshen (naboar i kantgrafen)."""
    e = tm.edges_unique
    n = len(tm.vertices)
    A = sparse.coo_matrix((np.ones(2 * len(e), np.float32), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    grad = np.asarray(A.sum(1)).ravel()
    grad[grad == 0] = 1
    x = verdi.astype(np.float32)
    for _ in range(iterasjonar):
        x = 0.5 * x + 0.5 * (A @ x) / grad
    return x


def isolinjer(tm, f, nivaa=0.5):
    """Marsjerande trekantar: polylinjer der feltet kryssar nivået."""
    F, V = tm.faces, tm.vertices
    s = f[F] - nivaa
    kryss = {}
    seg = []
    for fi in np.nonzero((s > 0).any(1) & (s <= 0).any(1))[0]:
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            sa, sb = s[fi, a], s[fi, b]
            if (sa > 0) != (sb > 0):
                ia, ib = F[fi, a], F[fi, b]
                k = (ia, ib) if ia < ib else (ib, ia)
                if k not in kryss:
                    t = sa / (sa - sb)
                    kryss[k] = V[ia] + t * (V[ib] - V[ia])
                pts.append(k)
        if len(pts) == 2:
            seg.append(pts)
    nabo = {}
    for i, (a, b) in enumerate(seg):
        nabo.setdefault(a, []).append(i)
        nabo.setdefault(b, []).append(i)
    brukt = np.zeros(len(seg), bool)
    linjer = []
    for start in range(len(seg)):
        if brukt[start]:
            continue
        kjede = list(seg[start])
        brukt[start] = True
        for ende in (1, 0):
            while True:
                k = kjede[-1] if ende else kjede[0]
                neste = [j for j in nabo.get(k, []) if not brukt[j]]
                if not neste:
                    break
                j = neste[0]
                brukt[j] = True
                a, b = seg[j]
                ny = b if a == k else a
                if ende:
                    kjede.append(ny)
                else:
                    kjede.insert(0, ny)
        linjer.append(np.array([kryss[k] for k in kjede]))
    return linjer


def forenkla(p, tol):
    if len(p) < 3:
        return p
    a, b = p[0], p[-1]
    d = b - a
    L = np.linalg.norm(d)
    if L < 1e-9:
        avst = np.linalg.norm(p - a, axis=1)
    else:
        u = d / L
        proj = (p - a) @ u
        avst = np.linalg.norm(p - a - np.outer(proj, u), axis=1)
    i = int(np.argmax(avst))
    if avst[i] <= tol:
        return np.array([a, b])
    v = forenkla(p[: i + 1], tol)
    h = forenkla(p[i:], tol)
    return np.vstack([v[:-1], h])


def lengd(p):
    return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())


def spor_langs(linjer, r, min_lengd=12.0, tol=0.2):
    """Union av kapslar langs polylinjene: eit spor med radius r i overflata."""
    kapslar = []
    behaldne = []
    for p in linjer:
        if lengd(p) < min_lengd:
            continue
        q = forenkla(p, tol)
        behaldne.append(q)
        for a, b in zip(q[:-1], q[1:]):
            kapslar.append(Manifold.batch_hull([Manifold.sphere(r, 10).translate(a.tolist()), Manifold.sphere(r, 10).translate(b.tolist())]))
    if not kapslar:
        return Manifold(), behaldne
    return Manifold.batch_boolean(kapslar, OpType.Add), behaldne


def tett(p, steg):
    """Legg inn punkt langs polylinja med høgst `steg` mellom dei."""
    ut = [p[0]]
    for a, b in zip(p[:-1], p[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / steg)))
        ut.extend(a + (b - a) * (np.arange(1, n + 1) / n)[:, None])
    return np.array(ut)


def regel(p, K, hx, hy):
    """Faste fargereglar frå geometrien. Gjev (mørk, lys) som maskar over punkta p."""
    S, D = K["skal"], K["detalj"]
    ay, az = K["akse"]["y"], K["akse"]["z"]
    ux, uy = K["utloysar"]["senter"]
    sk_, ok_r = D["skinne"], D["okularring"]
    oc = ok_r["senter"]
    r_l = np.hypot(p[:, 1] - ay, p[:, 2] - az)
    moerk = ((p[:, 0] < 17.5) & (p[:, 1] > 44) & (p[:, 1] < 86) & (p[:, 2] > 60)) \
        | ((np.hypot(p[:, 0] - hx, p[:, 1] - hy) < 15.8) & (p[:, 2] > 70)) \
        | ((np.hypot(p[:, 0] - ux, p[:, 1] - uy) < K["utloysar"]["brunn_r"] + 2.2) & (p[:, 2] > 56)) \
        | ((p[:, 2] < sk_["z_topp"] + 0.2) & (p[:, 0] > sk_["x"][0] - 0.5) & (p[:, 0] < sk_["x"][1] + 0.5) & (p[:, 1] > sk_["y"][0] - 0.5) & (p[:, 1] < sk_["y"][1] + 0.5)) \
        | ((p[:, 0] < 1.0) & (np.hypot(p[:, 1] - oc[0], p[:, 2] - oc[1]) < ok_r["r_ytre"] + 0.8)) \
        | ((np.abs(p[:, 0] - D["panel_linje"]["x"]) < D["panel_linje"]["breidd"] / 2 + 0.1) & (r_l < 33.0)) \
        | ((p[:, 0] > 66.0) & (r_l <= 26.9))
    lys = (p[:, 0] > D["panel_linje"]["x"] + D["panel_linje"]["breidd"] / 2) & (r_l < 33.0) & (r_l > 26.9)
    return moerk, lys


def saumsider(linjer, hud, klasse, steg, avstand):
    """Tette saumpunkt med sidevektor og klassen 2 mm ut på kvar side."""
    tre = cKDTree(hud.vertices)
    vn = np.asarray(hud.vertex_normals)
    P, S, L = [], [], []
    for p in linjer:
        q = tett(p, steg)
        if len(q) < 2:
            continue
        tan = np.gradient(q, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-9)
        n = vn[tre.query(q)[1]]
        side = np.cross(n, tan)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        lp = klasse[tre.query(q + avstand * side)[1]]
        lm = klasse[tre.query(q - avstand * side)[1]]
        P.append(q)
        S.append(side)
        L.append(np.c_[lp, lm])
    if not P:
        return np.zeros((0, 3)), np.zeros((0, 2), bool), np.zeros((0, 3))
    return np.vstack(P), np.vstack(L), np.vstack(S)


def fjern_oyar(hud, felt, nivaa=0.5, min_tal=350, rundar=2):
    """Flyttar små øyar av éin klasse over til naboklassen og jamnar feltet att."""
    from scipy.sparse.csgraph import connected_components
    e = hud.edges_unique
    n = len(hud.vertices)
    for _ in range(rundar):
        kl = felt > nivaa
        same = kl[e[:, 0]] == kl[e[:, 1]]
        A = sparse.coo_matrix((np.ones(same.sum()), (e[same, 0], e[same, 1])), shape=(n, n))
        _, lab = connected_components(A, directed=False)
        tal = np.bincount(lab)
        liten = tal[lab] < min_tal
        felt = felt.copy()
        felt[liten & kl] = nivaa - 0.25
        felt[liten & ~kl] = nivaa + 0.25
        felt = glatt_felt(hud, felt, 12)
    return felt
