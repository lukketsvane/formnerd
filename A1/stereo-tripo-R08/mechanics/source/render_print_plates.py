from pathlib import Path
import vtk, trimesh
R=Path(__file__).resolve().parents[1]
for filename in sorted((R/'print').glob('*.3mf')):
 loaded=trimesh.load(filename,force='scene')
 combined=loaded.to_geometry()
 temp=R/'review'/('_'+filename.stem+'.stl');combined.export(temp)
 reader=vtk.vtkSTLReader();reader.SetFileName(str(temp));reader.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(reader.GetOutputPort())
 actor=vtk.vtkActor();actor.SetMapper(mapper)
 actor.GetProperty().SetColor(.49,.51,.54);actor.GetProperty().SetAmbient(.62);actor.GetProperty().SetDiffuse(.35);actor.GetProperty().SetSpecular(.12)
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1);ren.AddActor(actor)
 l=vtk.vtkLight();l.SetPosition(100,-150,350);l.SetIntensity(.95);ren.AddLight(l)
 b=actor.GetBounds();mx=(b[0]+b[1])/2;my=(b[2]+b[3])/2
 cam=vtk.vtkCamera();cam.SetPosition(mx,my,480);cam.SetFocalPoint(mx,my,0);cam.SetViewUp(0,1,0);cam.ParallelProjectionOn();cam.SetParallelScale(max(65,(b[3]-b[2])/2+25,(b[1]-b[0])/2+18));ren.SetActiveCamera(cam)
 win=vtk.vtkRenderWindow();win.SetSize(1500,1100);win.SetOffScreenRendering(1);win.AddRenderer(ren);win.Render()
 f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.SetInputBufferTypeToRGB();f.ReadFrontBufferOff();f.Update()
 path=R/'review'/('08_print_'+filename.stem+'.png')
 wr=vtk.vtkPNGWriter();wr.SetFileName(str(path));wr.SetInputConnection(f.GetOutputPort());wr.Write();win.Finalize()
 print(path.name)