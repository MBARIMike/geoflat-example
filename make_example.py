#!/usr/bin/env python3
"""Make the files of the example: terrain.glb, terrain_ifs.x3d and viewpoints.json.

A 210 m by 210 m patch of hills (relief about 25 m) in a plane tangent to the WGS 84 ellipsoid at the GeoOrigin. The vertices and normals are
in ECEF axes, with the ECEF position of the GeoOrigin taken off the vertices, so that they are relative to the GeoOrigin as the GLBs of
MB-System mbmesh and mbgrd2gltf are. No other dependencies than the standard library.
"""
import json
import math
import struct

LAT, LON, ALT = 36.637514, -122.399356, 0.0   # the GeoOrigin
N = 61                                          # nodes along a side
STEP = 3.5                                      # meters between nodes

A = 6378137.0
F = 1 / 298.257223563
E2 = F * (2 - F)


def ecef(lat, lon, h):
    la, lo = math.radians(lat), math.radians(lon)
    n = A / math.sqrt(1 - E2 * math.sin(la) ** 2)
    return ((n + h) * math.cos(la) * math.cos(lo), (n + h) * math.cos(la) * math.sin(lo), (n * (1 - E2) + h) * math.sin(la))


def enu_axes(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    east = (-math.sin(lo), math.cos(lo), 0.0)
    north = (-math.sin(la) * math.cos(lo), -math.sin(la) * math.sin(lo), math.cos(la))
    up = (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
    return east, north, up


def comb(a, u, b, v, c, w):
    return tuple(a * u[i] + b * v[i] + c * w[i] for i in range(3))


def height(e, n):
    return 12 * math.sin(e / 22.0) * math.cos(n / 31.0) + 8 * math.sin((e + n) / 17.0) + 5 * math.cos(n / 9.0)


EAST, NORTH, UP = enu_axes(LAT, LON)
positions, normals = [], []
half = (N - 1) * STEP / 2
for j in range(N):
    for i in range(N):
        e, n = -half + i * STEP, -half + j * STEP
        positions.append(comb(e, EAST, n, NORTH, height(e, n), UP))
        d = 0.01
        dhde = (height(e + d, n) - height(e - d, n)) / (2 * d)
        dhdn = (height(e, n + d) - height(e, n - d)) / (2 * d)
        length = math.sqrt(dhde ** 2 + dhdn ** 2 + 1)
        normals.append(comb(-dhde / length, EAST, -dhdn / length, NORTH, 1 / length, UP))
triangles = []
for j in range(N - 1):
    for i in range(N - 1):
        a, b, c, d = j * N + i, j * N + i + 1, (j + 1) * N + i, (j + 1) * N + i + 1
        triangles += [(a, b, d), (a, d, c)]   # counterclockwise seen from above

# ---- GLB
pos_bytes = b''.join(struct.pack('<3f', *p) for p in positions)
nor_bytes = b''.join(struct.pack('<3f', *p) for p in normals)
idx_bytes = b''.join(struct.pack('<3I', *t) for t in triangles)
blob = pos_bytes + nor_bytes + idx_bytes
mins = [min(p[k] for p in positions) for k in range(3)]
maxs = [max(p[k] for p in positions) for k in range(3)]
gltf = {
    'asset': {'version': '2.0', 'generator': 'make_example.py'},
    'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0}],
    'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1}, 'indices': 2, 'material': 0}]}],
    'materials': [{'name': 'terrain', 'pbrMetallicRoughness': {'baseColorFactor': [0.55, 0.65, 0.8, 1.0], 'metallicFactor': 0.0, 'roughnessFactor': 0.65}}],
    'accessors': [
        {'bufferView': 0, 'componentType': 5126, 'count': len(positions), 'type': 'VEC3', 'min': mins, 'max': maxs},
        {'bufferView': 1, 'componentType': 5126, 'count': len(normals), 'type': 'VEC3'},
        {'bufferView': 2, 'componentType': 5125, 'count': len(triangles) * 3, 'type': 'SCALAR'}],
    'bufferViews': [
        {'buffer': 0, 'byteOffset': 0, 'byteLength': len(pos_bytes), 'target': 34962},
        {'buffer': 0, 'byteOffset': len(pos_bytes), 'byteLength': len(nor_bytes), 'target': 34962},
        {'buffer': 0, 'byteOffset': len(pos_bytes) + len(nor_bytes), 'byteLength': len(idx_bytes), 'target': 34963}],
    'buffers': [{'byteLength': len(blob)}],
}
js = json.dumps(gltf, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
blob += b'\0' * (-len(blob) % 4)
total = 12 + 8 + len(js) + 8 + len(blob)
with open('terrain.glb', 'wb') as f:
    f.write(struct.pack('<4sII', b'glTF', 2, total))
    f.write(struct.pack('<I4s', len(js), b'JSON') + js)
    f.write(struct.pack('<I4s', len(blob), b'BIN\0') + blob)

# ---- the same mesh as X3D nodes, for a page that does not use glTF
with open('terrain_ifs.x3d', 'w') as f:
    f.write('<Shape>\n  <Appearance><Material diffuseColor="0.55 0.65 0.8" specularColor="0 0 0"></Material></Appearance>\n')
    f.write('  <IndexedFaceSet solid="false" coordIndex="' + ' '.join('%d %d %d -1' % t for t in triangles) + '">\n')
    f.write('    <Coordinate point="' + ' '.join('%.4f %.4f %.4f' % p for p in positions) + '"></Coordinate>\n')
    f.write('    <Normal vector="' + ' '.join('%.5f %.5f %.5f' % p for p in normals) + '"></Normal>\n')
    f.write('  </IndexedFaceSet>\n</Shape>\n')


# ---- viewpoints: the same camera as a Viewpoint (model coordinates) and as a GeoViewpoint
def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def axis_angle(m):
    angle = math.acos(max(-1.0, min(1.0, (m[0][0] + m[1][1] + m[2][2] - 1) / 2)))
    if angle < 1e-9:
        return [0, 0, 1, 0]
    s = 2 * math.sin(angle)
    ax = [(m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s]
    return ax + [angle]


SOUTH = tuple(-c for c in NORTH)
basis = [[EAST[r], UP[r], SOUTH[r]] for r in range(3)]   # columns: east, up, south (the frame of a GeoViewpoint)


def rot_x(t):
    return [[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]]


views = {}
for name, tilt, back, high in (('DOWN', -math.pi / 2, 0.0, 260.0), ('OBLIQUE', -math.pi / 4, 220.0, 220.0)):
    local_pos = comb(-back, NORTH, high, UP, 0, UP)
    # a point 'back' meters south of the origin and 'high' meters above it, in geodetic terms
    geo_h = ALT + high
    dlat = -back / 111000.0
    views[name] = {
        'local': {'position': [round(c, 3) for c in local_pos], 'orientation': [round(c, 6) for c in axis_angle(matmul(basis, rot_x(tilt)))]},
        'geo': {'position': [LAT + dlat, LON, geo_h], 'orientation': [round(c, 6) for c in axis_angle(rot_x(tilt))]},
    }
views['origin'] = {'geo': [LAT, LON, ALT], 'ecef': [round(c, 3) for c in ecef(LAT, LON, ALT)]}
with open('viewpoints.json', 'w') as f:
    json.dump(views, f, indent=1)
print(json.dumps(views, indent=1))
print('terrain.glb', total, 'bytes;', len(positions), 'vertices,', len(triangles), 'triangles')
