import json
from pathlib import Path
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]


def prism_x(x_start,x_end,y,z,width,height,radius):
    return cq.Workplane('XY').box(x_end-x_start,width,height).edges('|X').fillet(radius).translate(((x_start+x_end)/2,y,z)).val()


def main():
    P=json.loads((ROOT/'cad/parameters.json').read_text())
    manifest=json.loads((ROOT/'cad/assembly_manifest.json').read_text())
    parts=manifest['parts'] if isinstance(manifest,dict) else manifest
    tip=P['usb_plug_body_tip_x_assumed']
    travel=30.0
    y=P['usb_axis_y']
    housing=prism_x(tip-P['usb_plug_body_length_assumed']-travel,tip,y,37,P['usb_plug_body_width_assumed'],P['usb_plug_body_height_assumed'],1)
    nose=prism_x(tip-travel,tip+P['usb_plug_nose_length_assumed'],y,37,P['usb_plug_nose_width_assumed'],P['usb_plug_nose_height_assumed'],.7)
    rows=[]
    errors=[]
    for item in parts:
        shape=cq.importers.importStep(str(ROOT/Path(item['file']).with_suffix('.step'))).val()
        b=shape.BoundingBox()
        for label,gauge in [('housing',housing),('metal_nose',nose)]:
            g=gauge.BoundingBox()
            separated=any(min(a1,b1)-max(a0,b0)<=1e-7 for a0,a1,b0,b1 in ((b.xmin,b.xmax,g.xmin,g.xmax),(b.ymin,b.ymax,g.ymin,g.ymax),(b.zmin,b.zmax,g.zmin,g.zmax)))
            volume=0.0 if separated else float(sum(s.Volume() for s in shape.intersect(gauge).Solids()))
            row={'part':item['name'],'gauge':label,'swept_intersection_mm3':volume}
            rows.append(row)
            if volume>1e-4:
                errors.append(row)
            print(json.dumps(row),flush=True)
    report={'units':'mm','scope':'Exact continuous straight insertion envelope for an assumed USB plug housing and metal nose, tested against every printed assembly part. Actual cable, socket and electronics remain unmeasured.','housing_width_height_length_mm':[P['usb_plug_body_width_assumed'],P['usb_plug_body_height_assumed'],P['usb_plug_body_length_assumed']],'nose_width_height_length_mm':[P['usb_plug_nose_width_assumed'],P['usb_plug_nose_height_assumed'],P['usb_plug_nose_length_assumed']],'housing_tip_x_mm':tip,'insertion_direction':[1,0,0],'insertion_travel_mm':travel,'part_count':len(parts),'checks':rows,'errors':errors,'nominal_access_pass':not errors,'physical_connector_fit_verified':False}
    (ROOT/'cad/usb_access_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'nominal_access_pass':not errors,'checks':len(rows),'errors':errors}),flush=True)
    if errors:
        raise SystemExit(1)


if __name__=='__main__':
    main()
