import json
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, '/tmp/entropi-mesh-deps')
import numpy as np
import trimesh
import manifold3d as md
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent if (ROOT.parent / 'mesh/03-quick-capped.glb').exists() else ROOT.parent / 'Entropi-Tripo-Selected'
SOURCE = SOURCE_ROOT / 'mesh/03-quick-capped.glb'
scene = trimesh.load(SOURCE, force='scene', process=False)
solids = []
report = {}
for name in sorted(scene.graph.nodes_geometry):
    transform, geometry = scene.graph[name]
    native = scene.geometry[geometry]
    vertices = trimesh.transform_points(native.vertices, transform)[:, [2, 0, 1]] * 140.0
    unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
    faces = inverse[np.asarray(native.faces)]
    solid = md.Manifold(md.Mesh64(np.ascontiguousarray(unique, dtype=np.float64), np.ascontiguousarray(faces, dtype=np.uint64)))
    report[str(name)] = {'status': str(solid.status()), 'triangles': solid.num_tri()}
    print(name, report[str(name)], flush=True)
    if solid.status() != md.Error.NoError:
        raise ValueError(report[str(name)])
    solids.append(solid)
outer = md.Manifold.batch_boolean(solids, md.OpType.Add)
mesh = outer.to_mesh64()
np.savez_compressed(ROOT / 'cad/source-union.npz', vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)
vertices, inverse = np.unique(mesh.vert_properties[:, :3], axis=0, return_inverse=True)
faces = inverse[mesh.tri_verts]
graph = coo_matrix((np.ones(faces.size, dtype=bool), (faces.ravel(), faces[:, [1, 2, 0]].ravel())), shape=(len(vertices), len(vertices))).tocsr()
count, labels = connected_components(graph, directed=False)
face_labels = labels[faces[:, 0]]
triangles = vertices[faces]
volumes = np.bincount(face_labels, weights=np.einsum('ij,ij->i', triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])) / 6, minlength=count)
largest = int(np.argmax(volumes))
removed = float(np.abs(np.delete(volumes, largest)).sum())
if removed > 0.01:
    raise ValueError(('Non-numerical source components', removed))
selected = faces[face_labels == largest]
used = np.unique(selected)
mapping = np.full(len(vertices), -1, dtype=np.int64)
mapping[used] = np.arange(len(used))
np.savez_compressed(ROOT / 'cad/source-largest.npz', vertices=vertices[used], faces=mapping[selected])
report['union'] = {'status': str(outer.status()), 'triangles': outer.num_tri(), 'surface_components_before_numerical_cleanup': count, 'volume_mm3': outer.volume(), 'sum_absolute_removed_signed_volume_mm3': removed, 'maximum_permitted_removal_mm3': 0.01}
report['source_sha256'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
(ROOT / 'verification/source-union.json').write_text(json.dumps(report, indent=2) + '\n')
print(report['union'], flush=True)
