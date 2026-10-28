from pathlib import Path
import numpy as np,trimesh
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData,vtkCellArray
from vtkmodules.vtkRenderingCore import vtkActor,vtkPolyDataMapper,vtkRenderer,vtkRenderWindow,vtkWindowToImageFilter
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLRenderWindow
from vtkmodules.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray

ROOT=Path(__file__).resolve().parent
def act(mesh,colour):
    mesh=mesh.copy()
    pts=vtkPoints();pts.SetData(numpy_to_vtk(np.asarray(mesh.vertices,dtype=np.float32),deep=True))
    tri=np.asarray(mesh.faces,dtype=np.int64)
    ff=np.column_stack([np.full(len(tri),3,dtype=np.int64),tri]).ravel()
    cells=vtkCellArray();cells.SetCells(len(tri),numpy_to_vtkIdTypeArray(ff,deep=True))
    poly=vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
    normal=vtkPolyDataNormals();normal.SetInputData(poly);normal.SetSplitting(False);normal.Update()
    mapper=vtkPolyDataMapper();mapper.SetInputConnection(normal.GetOutputPort())
    a=vtkActor();a.SetMapper(mapper);p=a.GetProperty()
    p.SetColor(*colour);p.SetAmbient(.35);p.SetDiffuse(.62);p.SetSpecular(.14)
    return a
for no in ["00_R10_fit_tests_P1S","01_R10_Tripo_shells_P1S","02_R10_mechanics_P1S"]:
    file=ROOT/"print"/(no+".3mf")
    scene=trimesh.load(file,force="scene")
    renderer=vtkRenderer();renderer.SetBackground(1,1,1)
    win=vtkRenderWindow();win.AddRenderer(renderer);win.SetSize(1300,1300);win.SetOffScreenRendering(1);win.SetMultiSamples(4)
    for index,mesh in enumerate(scene.dump(concatenate=False)):
        renderer.AddActor(act(mesh,(.62,.64,.66) if index%2 else(.38,.40,.43)))
    camera=renderer.GetActiveCamera();camera.ParallelProjectionOn();camera.SetPosition(128,128,450);camera.SetFocalPoint(128,128,0);camera.SetViewUp(0,1,0);camera.SetParallelScale(134)
    renderer.ResetCameraClippingRange();win.Render()
    cap=vtkWindowToImageFilter();cap.SetInput(win);cap.SetInputBufferTypeToRGB();cap.ReadFrontBufferOff();cap.Update()
    out=ROOT/"review"/(no+"_layout.png")
    writer=vtkPNGWriter();writer.SetInputConnection(cap.GetOutputPort());writer.SetFileName(str(out));writer.Write()
    print("PLATE_IMAGE",out.name,out.stat().st_size,flush=True)
    win.Finalize()
