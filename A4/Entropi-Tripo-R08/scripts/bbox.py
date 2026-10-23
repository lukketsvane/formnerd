import bpy, json
from mathutils import Vector
names=["REF_Linocell_94x62x15","REF_ESP32_CAM_1","REF_ESP32_CAM_2","P1_BATTERY_RING","P2_ESP32_BRACKET","P3_ESP32_BRACKET","A0_Tripo_quads_organic_front","tripo_part_1","tripo_part_2"]
for n in names:
 o=bpy.data.objects[n]
 pts=[o.matrix_world@Vector(c) for c in o.bound_box]
 a=[round(min(v[i] for v in pts),2) for i in range(3)]
 b=[round(max(v[i] for v in pts),2) for i in range(3)]
 print("AABB",n,json.dumps({"min":a,"max":b,"location":list(o.location),"dimensions":list(o.dimensions)}))
