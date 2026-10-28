import json
from pathlib import Path
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parent
q=np.load(ROOT/"R10_voxel_check.npz")
pitch=float(q["pitch"])
origin=q["origin"]
hardware=q["hardware"]
holder=q["holder"]
report={}
for part in ["P01_R10_Tripo_front_shell","P02_R10_Tripo_rear_shell"]:
    variants={}
    for suffix in ["","_SMOOTH_18","_SMOOTH_55"]:
        fn=ROOT/"parts"/(part+suffix+".stl")
        mesh=trimesh.load(fn,force="mesh")
        vol=mesh.voxelized(pitch).fill()
        indices=np.rint((vol.points-origin)/pitch).astype(np.int32)
        inside=((indices>=0)&(indices<np.array(hardware.shape))).all(axis=1)
        indices=indices[inside]
        overlap_hw=int(hardware[indices[:,0],indices[:,1],indices[:,2]].sum())
        overlap_holder=int(holder[indices[:,0],indices[:,1],indices[:,2]].sum())
        variants[suffix or "raw"]={"watertight":bool(mesh.is_watertight),"volume_mm3":round(mesh.volume,2),"voxels":len(indices),"hardware_overlap_voxels":overlap_hw,"holder_overlap_voxels":overlap_holder}
        print("QA",part,suffix,variants[suffix or "raw"],flush=True)
    report[part]=variants
(ROOT/"qa"/"finish_clearance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
