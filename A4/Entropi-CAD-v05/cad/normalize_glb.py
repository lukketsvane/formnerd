import copy
import json
from pathlib import Path
import struct
import sys
import numpy as np

def remove_collapsed_triangles(document, binary):
    types = {5121: np.dtype('u1'), 5123: np.dtype('<u2'), 5125: np.dtype('<u4'), 5126: np.dtype('<f4')}
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
    def accessor(index):
        entry = document['accessors'][index]
        view = document['bufferViews'][entry['bufferView']]
        dtype = types[entry['componentType']]
        width = widths[entry['type']]
        offset = view.get('byteOffset', 0) + entry.get('byteOffset', 0)
        stride = view.get('byteStride', width * dtype.itemsize)
        return np.ndarray((entry['count'], width), dtype=dtype, buffer=binary, offset=offset, strides=(stride, dtype.itemsize))
    removed = 0
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            if primitive.get('mode', 4) != 4:
                raise ValueError('Expected triangle mesh')
            indices = accessor(primitive['indices'])
            triangles = indices.copy().reshape(-1, 3)
            points = accessor(primitive['attributes']['POSITION'])[triangles]
            collapsed = np.all(points[:, 0] == points[:, 1], axis=1) | np.all(points[:, 0] == points[:, 2], axis=1) | np.all(points[:, 1] == points[:, 2], axis=1)
            if collapsed.any():
                kept = triangles[~collapsed].reshape(-1, 1)
                indices[:len(kept)] = kept
                indices[len(kept):] = 0
                entry = document['accessors'][primitive['indices']]
                entry['count'] = len(kept)
                entry['min'] = [int(kept.min())]
                entry['max'] = [int(kept.max())]
                removed += int(collapsed.sum())
    previous = document.setdefault('extras', {}).get('removed_float32_collapsed_triangles', 0)
    document['extras']['removed_float32_collapsed_triangles'] = previous + removed

def normalize_glb(path):
    path = Path(path)
    data = path.read_bytes()
    size, kind = struct.unpack_from("<II",data,12)
    document = json.loads(data[20:20+size])
    remainder = bytearray(data[20+size:])
    binary_size, binary_kind = struct.unpack_from('<II', remainder)
    if binary_kind != 0x004e4942:
        raise ValueError('Expected GLB binary chunk')
    remove_collapsed_triangles(document, memoryview(remainder)[8:8+binary_size])
    for scene in document["scenes"]:
        for node in scene["nodes"]:
            document["nodes"][node]["scale"] = [0.001,0.001,0.001]
    cmf_path = path.parent / "cad/cmf_materials.json"
    if cmf_path.exists():
        cmf = json.loads(cmf_path.read_text())
        for material in document.get("materials",[]):
            material.setdefault("pbrMetallicRoughness",{}).update(cmf["default"])
        for node in document.get("nodes",[]):
            name = node.get("name")
            if name in cmf["parts"] and "mesh" in node:
                for primitive in document["meshes"][node["mesh"]]["primitives"]:
                    material = copy.deepcopy(document["materials"][primitive["material"]])
                    material["name"] = name + "_CMF"
                    material["pbrMetallicRoughness"].update(cmf["parts"][name])
                    primitive["material"] = len(document["materials"])
                    document["materials"].append(material)
    payload = json.dumps(document,separators=(",",":")).encode()
    payload += b" "*((-len(payload))%4)
    temporary = path.with_suffix('.write.glb')
    temporary.write_bytes(struct.pack("<4sII",b"glTF",2,20+len(payload)+len(remainder))+struct.pack("<II",len(payload),kind)+payload+remainder)
    temporary.replace(path)

if __name__ == "__main__":
    normalize_glb(sys.argv[1])
