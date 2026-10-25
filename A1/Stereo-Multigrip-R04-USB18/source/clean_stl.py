"""Drop triangles collapsed by binary STL float32 conversion; surface is unchanged."""
from pathlib import Path
import struct,sys

def clean_stl(path):
    path=Path(path);data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*n
    keep=[]
    for i in range(n):
        record=data[84+50*i:84+50*(i+1)]
        a=struct.unpack('<12fH',record)
        if len({tuple(a[k:k+3]) for k in (3,6,9)})==3:keep.append(record)
    if len(keep)!=n:path.write_bytes(data[:80]+struct.pack('<I',len(keep))+b''.join(keep))
    return n-len(keep)

if __name__=='__main__':
    print({'zero_area_triangles_removed':sum(clean_stl(p) for p in sys.argv[1:])})
