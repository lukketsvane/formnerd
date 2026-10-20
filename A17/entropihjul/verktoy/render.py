import bpy, numpy as np, sys, json, math, mathutils, os, tempfile

args = sys.argv[sys.argv.index('--') + 1:]
src, camf, outp = args[0], args[1], args[2]
C = json.loads(open(args[3]).read()) if args[3].endswith('.json') else json.loads(args[3])
if len(args) > 4:
    C.update(json.loads(args[4]))
cam = json.load(open(camf))['blender']
res = C.get('res', 1.0)
W, H = int(round(1448 * res)), int(round(1086 * res))
mode = C.get('mode', 'final')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = C.get('samples', 64)
sc.cycles.use_denoising = C.get('denoise', True) and mode == 'final'
sc.cycles.max_bounces = C.get('bounces', 10); sc.cycles.glossy_bounces = C.get('glossy', 8); sc.cycles.diffuse_bounces = 4
sc.cycles.adaptive_threshold = C.get('adapt', 0.01)
sc.cycles.sample_clamp_indirect = C.get('clamp', 0.0)
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'Raw' if mode in ('raw', 'id') else C.get('view', 'Standard')
if C.get('look'):
    sc.view_settings.look = C['look']
sc.view_settings.exposure = C.get('exposure', 0.0)
sc.render.film_transparent = True
if C.get('border'):
    bx0, by0, bx1, by1 = C['border']
    sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = bx0, bx1
    sc.render.border_min_y, sc.render.border_max_y = 1 - by1, 1 - by0
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.color_mode = 'RGBA'

M = C.get('mat', {})


def nodes(m):
    m.use_nodes = True
    return m.node_tree, m.node_tree.nodes['Principled BSDF'], m.node_tree.links


def obj_coord(nt):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    return tc.outputs['Object']


def ao_tint(nt, b, L, q, col):
    if q.get('ao_dist', 0) <= 0:
        b.inputs['Base Color'].default_value = (*col, 1)
        return
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.samples = q.get('ao_samples', 16); ao.inputs['Distance'].default_value = q['ao_dist']
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = q.get('ao_pow', 1.5)
    L.new(ao.outputs['AO'], pw.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = q.get('ao_min', 0.25); mr.inputs['To Max'].default_value = 1.0
    L.new(pw.outputs[0], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['A'].default_value = (*col, 1)
    cc = nt.nodes.new('ShaderNodeCombineColor')
    for i in range(3):
        L.new(mr.outputs['Result'], cc.inputs[i])
    L.new(cc.outputs[0], mx.inputs['B'])
    L.new(mx.outputs['Result'], b.inputs['Base Color'])


def mat_blast(name, q):
    m = bpy.data.materials.new(name); nt, b, L = nodes(m)
    ao_tint(nt, b, L, q, q.get('col', [0.9, 0.9, 0.89])); b.inputs['Metallic'].default_value = 1.0
    oc = obj_coord(nt)
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = q.get('grain', 14.0); n1.inputs['Detail'].default_value = 6.0; n1.inputs['Roughness'].default_value = 0.6
    L.new(oc, n1.inputs['Vector'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = q.get('grain', 14.0) * 0.08; n2.inputs['Detail'].default_value = 2.0
    L.new(oc, n2.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); r0 = q.get('rough', 0.45); rv = q.get('rvar', 0.05)
    mr.inputs['To Min'].default_value = r0 - rv; mr.inputs['To Max'].default_value = r0 + rv
    L.new(n2.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], b.inputs['Roughness'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = q.get('bump', 0.25); bp.inputs['Distance'].default_value = q.get('bdist', 0.003)
    L.new(n1.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    if q.get('bevel', 0) > 0:
        bv = nt.nodes.new('ShaderNodeBevel'); bv.samples = q.get('bevel_samples', 8); bv.inputs['Radius'].default_value = q['bevel']
        L.new(bv.outputs['Normal'], bp.inputs['Normal'])
    return m


def tangent_vec(nt, kind):
    L = nt.links
    if kind == 'z':
        cx = nt.nodes.new('ShaderNodeCombineXYZ'); cx.inputs[2].default_value = 1.0
        return cx.outputs[0]
    oc = obj_coord(nt)
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(oc, sx.inputs[0])
    cx = nt.nodes.new('ShaderNodeCombineXYZ')
    if kind == 'radial':
        L.new(sx.outputs[0], cx.inputs[0]); L.new(sx.outputs[1], cx.inputs[1])
    else:
        ng = nt.nodes.new('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0
        L.new(sx.outputs[1], ng.inputs[0]); L.new(ng.outputs[0], cx.inputs[0]); L.new(sx.outputs[0], cx.inputs[1])
    nm = nt.nodes.new('ShaderNodeVectorMath'); nm.operation = 'NORMALIZE'; L.new(cx.outputs[0], nm.inputs[0])
    return nm.outputs[0]


def mat_aniso(name, q, tkind, rings):
    m = bpy.data.materials.new(name); nt, b, L = nodes(m)
    b.inputs['Base Color'].default_value = (*q.get('col', [0.92, 0.92, 0.91]), 1); b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = q.get('rough', 0.25)
    b.inputs['Anisotropic'].default_value = q.get('aniso', 0.85)
    b.inputs['Anisotropic Rotation'].default_value = q.get('arot', 0.0)
    L.new(tangent_vec(nt, tkind), b.inputs['Tangent'])
    if q.get('lines', 0.0) > 0:
        oc = obj_coord(nt)
        sx = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(oc, sx.inputs[0])
        if rings:
            r2 = nt.nodes.new('ShaderNodeVectorMath'); r2.operation = 'LENGTH'
            cx = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(sx.outputs[0], cx.inputs[0]); L.new(sx.outputs[1], cx.inputs[1])
            L.new(cx.outputs[0], r2.inputs[0]); coord = r2.outputs['Value']
        else:
            coord = sx.outputs[2]
        n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.noise_dimensions = '1D'
        n1.inputs['Scale'].default_value = q.get('lscale', 40.0); n1.inputs['Detail'].default_value = 8.0; n1.inputs['Roughness'].default_value = 0.7
        L.new(coord, n1.inputs['W'])
        n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 3.0
        L.new(oc, n2.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY'
        L.new(n1.outputs['Fac'], mx.inputs[0]); L.new(n2.outputs['Fac'], mx.inputs[1])
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = q['lines']; bp.inputs['Distance'].default_value = 0.002
        L.new(mx.outputs[0], bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_plain(name, col, rough, metal=0.0):
    m = bpy.data.materials.new(name); nt, b, L = nodes(m)
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m


def mat_emit(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1)
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], o.inputs[0])
    return m


IDC = {'blast': (1, 0, 0), 'polish': (0, 1, 0), 'spun': (0, 0, 1), 'brushz': (1, 1, 0), 'paint': (1, 0, 1), 'dark': (0, 1, 1)}
if mode == 'id':
    MAT = {k: mat_emit(k, v) for k, v in IDC.items()}
elif mode == 'clay':
    cm_ = mat_plain('clay', [0.7, 0.7, 0.7], 0.5)
    MAT = {k: cm_ for k in IDC}
else:
    MAT = {
        'blast': mat_blast('blast', M.get('blast', {})),
        'polish': mat_plain('polish', M.get('polish', {}).get('col', [0.93, 0.93, 0.92]), M.get('polish', {}).get('rough', 0.08), 1.0),
        'spun': mat_aniso('spun', M.get('spun', {}), M.get('spun', {}).get('tan', 'radial'), True),
        'brushz': mat_aniso('brushz', M.get('brushz', {}), M.get('brushz', {}).get('tan', 'z'), False),
        'paint': mat_plain('paint', [0.012, 0.012, 0.012], 0.45),
        'dark': mat_plain('dark', [0.02, 0.02, 0.02], 0.6),
    }
    if C.get('blast_as'):
        MAT['blast'] = MAT[C['blast_as']]


def add_mesh(name, v, f, n, m):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set('co', v.ravel())
    me.loops.add(f.size); me.loops.foreach_set('vertex_index', f.ravel())
    me.polygons.add(len(f)); me.polygons.foreach_set('loop_start', np.arange(0, f.size, 3))
    me.polygons.foreach_set('loop_total', np.full(len(f), 3))
    me.update(); me.validate()
    me.polygons.foreach_set('use_smooth', np.ones(len(f), bool))
    me.normals_split_custom_set_from_vertices([tuple(r) for r in n])
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); ob.data.materials.append(m)
    return ob


d = np.load(src, allow_pickle=True)
for nm in [str(s) for s in d['names']]:
    fin = nm.split('__')[1]
    add_mesh(nm, d[nm + '_v'], d[nm + '_f'], d[nm + '_n'], MAT.get(fin, MAT['blast']))


def write_hdr(path, img):
    h, w = img.shape[:2]
    v = img.max(axis=2)
    m_, e = np.frexp(v)
    s_ = np.where(v > 1e-32, m_ * 256.0 / np.maximum(v, 1e-32), 0.0)
    rgbe = np.zeros((h, w, 4), np.uint8)
    rgbe[..., :3] = np.clip(img * s_[..., None], 0, 255).astype(np.uint8)
    rgbe[..., 3] = np.where(v > 1e-32, e + 128, 0).astype(np.uint8)
    with open(path, 'wb') as fh:
        fh.write(b'#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n')
        fh.write(('-Y %d +X %d\n' % (h, w)).encode())
        fh.write(rgbe.tobytes())


world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
nt = world.node_tree; bg = nt.nodes['Background']; L = nt.links
if mode == 'id':
    bg.inputs['Strength'].default_value = 0.0
else:
    env = np.load(C['env']).astype(np.float32) * C.get('env_gain', 1.0)
    hdr = os.path.join(tempfile.gettempdir(), 'env_%d.hdr' % os.getpid())
    write_hdr(hdr, np.maximum(env[..., :3], 0))
    img = bpy.data.images.load(hdr); img.colorspace_settings.name = 'Non-Color'
    tc = nt.nodes.new('ShaderNodeTexCoord'); sx = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sx.inputs[0])

    def mth(op, a, b=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]
    u = mth('FRACT', mth('ADD', mth('DIVIDE', mth('ARCTAN2', sx.outputs[1], sx.outputs[0]), 2 * math.pi), 1.0))
    v = mth('ADD', mth('DIVIDE', mth('ARCSINE', sx.outputs[2]), math.pi), 0.5)
    cx = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(u, cx.inputs[0]); L.new(v, cx.inputs[1])
    it = nt.nodes.new('ShaderNodeTexImage'); it.image = img; it.interpolation = 'Linear'; it.extension = 'REPEAT'
    L.new(cx.outputs[0], it.inputs['Vector']); L.new(it.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    for i, lt in enumerate(C.get('lights', [])):
        l = bpy.data.lights.new(f'l{i}', 'AREA'); l.shape = 'RECTANGLE'; l.size = lt['sx']; l.size_y = lt['sy']
        l.energy = lt['rad'] * math.pi * lt['sx'] * lt['sy']
        o = bpy.data.objects.new(f'l{i}', l); sc.collection.objects.link(o)
        el, az = math.radians(lt['el']), math.radians(lt['az'])
        dv = mathutils.Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        o.location = dv * lt.get('dist', 300) + mathutils.Vector((0, 0, 4))
        o.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
        o.visible_camera = False

c = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', c); sc.collection.objects.link(co); sc.camera = co
c.lens = cam['lens']; c.sensor_width = 36; c.sensor_fit = 'HORIZONTAL'; c.clip_start = 1; c.clip_end = 5000
co.location = cam['loc']; co.rotation_euler = mathutils.Matrix(cam['rot']).to_euler()
if C.get('env_list') and mode != 'id':
    sc.render.use_persistent_data = True
    for k, ep in enumerate(C['env_list']):
        e2 = np.load(ep).astype(np.float32)
        h2 = os.path.join(tempfile.gettempdir(), 'envb_%d_%d.hdr' % (os.getpid(), k))
        write_hdr(h2, np.maximum(e2[..., :3], 0))
        img2 = bpy.data.images.load(h2, check_existing=False); img2.colorspace_settings.name = 'Non-Color'
        it.image = img2
        world.update_tag(); sc.update_tag()
        sc.render.filepath = os.path.join(outp, os.path.basename(ep).replace('.npy', '.png'))
        bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = outp
    bpy.ops.render.render(write_still=True)
