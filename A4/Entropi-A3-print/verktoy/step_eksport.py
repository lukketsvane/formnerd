"""Skriv STEP frå dei lagra B-rep-ane (print/cad/*.brep) slik at OCCT-skrivaren får med alle flatene.

Forskyvingskurvene (Geom_OffsetCurve) som 2D-offseten til delingsfasen etterlèt, blir ikkje skrivne av STEP-skrivaren;
dei blir konverterte til B-splinar først, så SameParameter og ShapeFix. Resultatet blir lese inn att og kontrollert."""
import sys, pathlib
from build123d import Solid, import_brep, import_step, export_step
from OCP.ShapeCustom import ShapeCustom, ShapeCustom_RestrictionParameters
from OCP.GeomAbs import GeomAbs_Shape
from OCP.BRepLib import BRepLib
from OCP.TopExp import TopExp
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
from OCP.collections import IndexedDataMap_TopoDS_Shape_List_TopoDS_Shape_TopTools_ShapeMapHasher as IDM

HER = pathlib.Path(__file__).resolve().parent
UT = HER.parent / "print"


def steptrygg(solid, tol=1e-4):
    p = ShapeCustom_RestrictionParameters()
    p.ConvertOffsetCurv3d = True
    p.ConvertOffsetCurv2d = True
    p.ConvertOffsetSurf = True
    for namn in ("ConvertExtrusionSurf", "ConvertRevolutionSurf", "ConvertPlane", "ConvertBezierSurf", "ConvertCurve3d", "ConvertCurve2d", "ConvertConicalSurf", "ConvertCylindricalSurf", "ConvertSphericalSurf", "ConvertToroidalSurf"):
        setattr(p, namn, False)
    ny = Solid(ShapeCustom.BSplineRestriction_s(solid.wrapped, tol, tol / 100, 14, 2000, GeomAbs_Shape.GeomAbs_C2, GeomAbs_Shape.GeomAbs_C2, True, False, p))
    BRepLib.SameParameter_s(ny.wrapped, tol, True)
    return ny.fix()


def frie_kantar(shape):
    mp = IDM()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, mp)
    return sum(1 for i in range(1, mp.Extent() + 1) if mp.FindFromIndex(i).Extent() == 1)


def skriv(solid, fil):
    export_step(steptrygg(solid), fil)
    inn = import_step(fil)
    sol = inn.solids()
    return len(sol), len(inn.faces()), frie_kantar(inn), (sol[0].is_valid if sol else False)


if __name__ == "__main__":
    for n in sys.argv[1:] or ("botn", "topp"):
        m = import_brep(UT / "cad" / f"{n}.brep")
        r = skriv(m.solids()[0], UT / "step" / f"{n}.step")
        print(f"{n:<10} STEP lesen att: solidar {r[0]} flater {r[1]} frie kantar {r[2]} gyldig {r[3]}")
