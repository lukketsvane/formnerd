import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import marching_cubes

ROOT=Path(__file__).resolve().parent
q=np.load(ROOT/"R10_voxel_check.npz")
pitch=float(q["pitch"]);origin=q["origin"]
block=q["hardware"]|q["holder"]
sdf=distance_transform_edt(~block,sampling=pitch)
cutter=(sdf<=.82).astype(np.float32)
smoothed=gaussian_filter(np.pad(cutter,2),sigma=.45)
verts,faces,_,_=marching_cubes(smoothed,level=.5,spacing=(pitch,pitch,pitch))
verts+=origin-2*pitch
cutmesh=trimesh.Trimesh(vertices=verts,faces=faces,process=True)
cutmesh.fix_normals()
print("CUTTER",len(faces),"watertight",cutmesh.is_watertight,"bodies",len(cutmesh.split()),flush=True)
if not cutmesh.is_watertight:
    raise RuntimeError("Cutter not closed")
result={}
for name in ["P01_R10_Tripo_front_shell","P02_R10_Tripo_rear_shell"]:
    mesh=trimesh.load(ROOT/"parts"/(name+"_SMOOTH_55.stl"),force="mesh")
    print("START_BOOLEAN",name,len(mesh.faces),flush=True)
    clean=trimesh.boolean.difference([mesh,cutmesh],engine="manifold",check_volume=False)
    if clean is None or not clean.is_watertight or clean.volume<=1:
        raise RuntimeError("Clean shell failed")
    out=ROOT/"parts"/(name+"_SMOOTH_CLEAR.stl")
    clean.export(out)
    voxel=clean.voxelized(pitch).fill()
    idx=np.rint((voxel.points-origin)/pitch).astype(np.int32)
    idx=idx[((idx>=0)&(idx<np.array(block.shape))).all(axis=1)]
    hw=int(q["hardware"][idx[:,0],idx[:,1],idx[:,2]].sum())
    hold=int(q["holder"][idx[:,0],idx[:,1],idx[:,2]].sum())
    result[name]={"watertight":bool(clean.is_watertight),"faces":len(clean.faces),"volume_mm3":round(clean.volume,1),"hardware_collision_voxels":hw,"holder_collision_voxels":hold}
    print("CLEAR_SHELL",name,result[name],flush=True)
(ROOT/"qa"/"clearance_restoration.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
