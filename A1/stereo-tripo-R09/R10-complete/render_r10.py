import os
import numpy as np
import trimesh
from pathlib import Path
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkCellArray
from vtkmodules.vtkRenderingCore import vtkActor,vtkPolyDataMapper,vtkRenderer,vtkRenderWindow,vtkWindowToImageFilter
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLRenderWindow
from vtkmodules.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray

HERE=Path(__file__).resolve().parent
R09=HERE.parent
OUT=HERE/"review"
if os.environ.get("R10_SMOOTH"): OUT=OUT/("smooth_"+os.environ["R10_SMOOTH"])
OUT.mkdir(exist_ok=True)
mesh_paths={
 "front":HERE/"parts"/"P01_R10_Tripo_front_shell.stl",
 "rear":HERE/"parts"/"P02_R10_Tripo_rear_shell.stl",
 "lensL":HERE/"parts"/"P03_R10_lens_bezel_L.stl",
 "lensR":HERE/"parts"/"P03_R10_lens_bezel_R.stl",
 "button":HERE/"parts"/"P04_R10_trigger_cap.stl",
 "harness":R09/"harness"/"stl"/"H11_dual_ESP32CAM_MB_harness.stl",
 "batteryholder":HERE/"parts"/"H12_R10_centered_Linocell_U_cage.stl",
 "battery":R09/"harness"/"stl"/"HW01_Linocell_5000mAh.stl",
 "boardL":R09/"harness"/"stl"/"HW02_L_ESP32CAM_MB_stack.stl",
 "boardR":R09/"harness"/"stl"/"HW02_R_ESP32CAM_MB_stack.stl"
}
if os.environ.get("R10_SMOOTH"):
    for k in ("front","rear"):
        f=mesh_paths[k]
        mesh_paths[k]=f.with_name(f.stem+"_SMOOTH_"+os.environ["R10_SMOOTH"]+f.suffix)
M={k:trimesh.load(p,force="mesh") for k,p in mesh_paths.items()}
M["battery"].apply_translation([-20.5,0,0])
palette={
 "front":(.35,.36,.37),"rear":(.43,.44,.45),
 "lensL":(.10,.11,.12),"lensR":(.10,.11,.12),"button":(.12,.12,.13),
 "harness":(.66,.67,.68),"batteryholder":(.53,.55,.57),
 "battery":(.14,.145,.155),"boardL":(.12,.25,.29),"boardR":(.12,.25,.29)
}
def actor(mesh,color,opacity=1,delta=(0,0,0),wire=False):
    xyz=np.asarray(mesh.vertices,dtype=np.float32)+np.asarray(delta,dtype=np.float32)
    pts=vtkPoints()
    pts.SetData(numpy_to_vtk(xyz,deep=True))
    tri=np.asarray(mesh.faces,dtype=np.int64)
    arr=np.column_stack([np.full((len(tri),),3,dtype=np.int64),tri]).ravel()
    cells=vtkCellArray();cells.SetCells(len(tri),numpy_to_vtkIdTypeArray(arr,deep=True))
    data=vtkPolyData();data.SetPoints(pts);data.SetPolys(cells)
    normals=vtkPolyDataNormals()
    normals.SetInputData(data);normals.SetSplitting(False);normals.SetConsistency(True);normals.Update()
    mapper=vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
    a=vtkActor();a.SetMapper(mapper)
    pr=a.GetProperty()
    pr.SetColor(*color);pr.SetOpacity(opacity)
    pr.SetAmbient(.35);pr.SetDiffuse(.60);pr.SetSpecular(.23);pr.SetSpecularPower(45)
    if wire:pr.SetRepresentationToWireframe()
    return a

def render(filename, included, camera, target=(0,0,0), scale=104, colors=None, alphas=None, deltas=None):
    colors=colors or {};alphas=alphas or {};deltas=deltas or {}
    ren=vtkRenderer();ren.SetBackground(1,1,1)
    win=vtkRenderWindow();win.SetSize(1600,1050);win.SetOffScreenRendering(1);win.SetMultiSamples(8);win.AddRenderer(ren)
    for k in included:
        ren.AddActor(actor(M[k],colors.get(k,palette[k]),alphas.get(k,1),deltas.get(k,(0,0,0))))
    ca=ren.GetActiveCamera();ca.ParallelProjectionOn();ca.SetPosition(*camera);ca.SetFocalPoint(*target);ca.SetViewUp(0,1,0);ca.SetParallelScale(scale)
    ren.ResetCameraClippingRange();win.Render()
    grab=vtkWindowToImageFilter();grab.SetInput(win);grab.SetInputBufferTypeToRGB();grab.ReadFrontBufferOff();grab.Update()
    writer=vtkPNGWriter();writer.SetInputConnection(grab.GetOutputPort());writer.SetFileName(str(OUT/filename));writer.Write()
    print("RENDER",filename,(OUT/filename).stat().st_size,flush=True)
    win.Finalize()

outside=["front","rear","lensL","lensR","button"]
inside=["harness","batteryholder","battery","boardL","boardR"]
render("01_r10_exterior_hero.png",outside,(140,88,-196),scale=103)
render("02_r10_front_orthographic.png",outside,(0,0,-220),scale=90)
render("03_r10_rear_orthographic.png",outside,(10,8,225),scale=90)
render("04_r10_transparent_with_internals.png",outside+inside,(147,80,-192),scale=106,alphas={"front":.18,"rear":.23,"lensL":.78,"lensR":.78,"button":.9})
render("05_r10_rear_open_hardware.png",["front","lensL","lensR","button"]+inside,(147,85,210),scale=105,alphas={"front":.48})
render("06_r10_exploded.png",outside+inside,(163,103,-235),target=(0,0,13),scale=150,
       deltas={"front":(0,0,-20),"lensL":(0,0,-34),"lensR":(0,0,-34),"button":(0,0,0),
               "harness":(0,0,0),"boardL":(0,0,14),"boardR":(0,0,14),
               "batteryholder":(0,0,32),"battery":(0,0,52),"rear":(0,0,75)})
render("07_r10_right_usb_wall.png",outside,(230,15,20),scale=60)
render("08_r10_battery_fit_closeup.png",["harness","batteryholder","battery","boardL","boardR"],(100,75,165),scale=79)
