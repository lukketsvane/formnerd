import numpy as np
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.TopAbs import TopAbs_REVERSED
from OCP.BRepLib import BRepLib_ToolTriangulatedShape


def mesh_shape(shape, lin=0.003, ang=0.06):
    BRepMesh_IncrementalMesh(shape.wrapped, lin, False, ang, True)


def face_tris(f):
    loc = TopLoc_Location()
    tri = BRep_Tool.Triangulation_s(f.wrapped, loc)
    if tri is None:
        return None
    BRepLib_ToolTriangulatedShape.ComputeNormals_s(f.wrapped, tri)
    tr = loc.Transformation()
    nn = tri.NbNodes()
    v = np.empty((nn, 3)); n = np.empty((nn, 3))
    for i in range(1, nn + 1):
        v[i - 1] = tri.Node(i).Transformed(tr).Coord()
        n[i - 1] = tri.Normal(i).Transformed(tr).Coord()
    t = np.array([tri.Triangle(i).Get() for i in range(1, tri.NbTriangles() + 1)]) - 1
    if f.wrapped.Orientation() == TopAbs_REVERSED:
        t = t[:, ::-1]
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    fn = np.cross(b - a, c - a)
    if np.sum(fn * n[t[:, 0]]) < 0:
        n = -n
    return v, t, n


def merge(chunks):
    V, F, N = [], [], []
    off = 0
    for v, t, n in chunks:
        V.append(v); F.append(t + off); N.append(n); off += len(v)
    if not V:
        return None
    return np.vstack(V).astype(np.float32), np.vstack(F).astype(np.int32), np.vstack(N).astype(np.float32)
