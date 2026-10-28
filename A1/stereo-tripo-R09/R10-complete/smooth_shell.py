from pathlib import Path
import trimesh
import time
ROOT=Path(__file__).resolve().parent
for iteration in (18,55):
    for n in ("P01_R10_Tripo_front_shell","P02_R10_Tripo_rear_shell"):
        path=ROOT/"parts"/(n+".stl")
        m=trimesh.load(path,force="mesh")
        trimesh.smoothing.filter_taubin(m,lamb=.50,nu=-.53,iterations=iteration)
        dst=ROOT/"parts"/(n+f"_SMOOTH_{iteration}.stl")
        m.export(dst)
        print("SMOOTH",iteration,n,"watertight",m.is_watertight,"volume",round(m.volume,2),flush=True)
