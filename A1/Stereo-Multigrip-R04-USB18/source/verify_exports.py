"""Verify final binary print meshes and re-import STEP exports. Read-only CAD checks."""
from pathlib import Path
import json,struct,collections,hashlib,sys
import cadquery as cq

root=Path(__file__).resolve().parents[1]
result={'STL':{},'STEP':{}}
failures=[]
for p in sorted((root/'STL').glob('PRINT_*.stl'))+sorted((root/'fit_coupon').glob('TEST_*.stl')):
    data=p.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+n*50,(p.name,'not binary STL')
    edges=collections.Counter();badtri=0;volume=0
    for i in range(n):
        values=struct.unpack_from('<12fH',data,84+50*i)
        vertices=[tuple(round(x,5) for x in values[k:k+3]) for k in (3,6,9)]
        if len(set(vertices))<3:badtri+=1
        for a,b in ((vertices[0],vertices[1]),(vertices[1],vertices[2]),(vertices[2],vertices[0])):
            edges[tuple(sorted((a,b)))]+=1
        a,b,c=vertices
        volume+=sum(a[j]*(b[(j+1)%3]*c[(j+2)%3]-b[(j+2)%3]*c[(j+1)%3]) for j in range(3))/6
    bad=sum(n!=2 for n in edges.values())
    result['STL'][p.name]={'triangles':n,'boundary_or_nonmanifold_edges':bad,'degenerate_triangles':badtri,'volume_mm3':round(volume,5),'sha256':hashlib.sha256(data).hexdigest()}
    if bad or badtri or volume<=0:failures.append((p.name,bad,badtri,volume))
assert result['STL'],'No print meshes found'
step_files=sorted((root/'STEP').glob('*assembly.step'))+sorted((root/'STEP').glob('*harness-only.step'))
if '--mesh-only' in sys.argv:
    result['STEP']=json.loads((root/'checks'/'export-checks.json').read_text())['STEP']
    assert all(s['valid'] for s in result['STEP'].values())
    step_files=[]
for p in step_files:
    s=cq.importers.importStep(str(p)).val()
    result['STEP'][p.name]={'valid':s.isValid(),'solids':len(s.Solids())}
    if not s.isValid():failures.append((p.name,'invalid STEP'))
assert result['STEP'],'No assembly STEP found'
(root/'checks').mkdir(exist_ok=True)
(root/'checks'/'export-checks.json').write_text(json.dumps(result,indent=2))
assert not failures,failures
print(json.dumps({'meshes_passed':len(result['STL']),'STEP_passed':len(result['STEP'])}))
