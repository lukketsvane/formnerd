import hashlib
import json
import sys

import numpy as np
import trimesh
from scipy import sparse
from scipy.sparse import csgraph


def face_edge_components(m):
    inc = sparse.coo_matrix((np.ones(len(m.edges_unique_inverse)), (m.edges_unique_inverse, np.repeat(np.arange(len(m.faces)), 3))))
    return int(csgraph.connected_components(inc.T @ inc, directed=False)[0])


def topology(m):
    edges = np.sort(m.edges, axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    return {
        "vertices": len(m.vertices),
        "faces": len(m.faces),
        "watertight_trimesh": bool(m.is_watertight),
        "winding_consistent": bool(m.is_winding_consistent),
        "boundary_edges": int((counts == 1).sum()),
        "nonmanifold_edges_more_than_two_faces": int((counts > 2).sum()),
        "connected_components": face_edge_components(m),
    }


def qa(path):
    data = open(path, "rb").read()
    m = trimesh.load(path, force="mesh", process=False)
    welded = m.copy()
    welded.merge_vertices(merge_tex=True, merge_norm=True)
    ext = m.extents
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "file_size_bytes": len(data),
        "extents_xyz_model_units": [float(x) for x in ext],
        "raw_indexed_topology": topology(m),
        "exact_position_welded_analysis_only": topology(welded),
    }


if __name__ == "__main__":
    print(json.dumps({p: qa(p) for p in sys.argv[1:]}, indent=2))
