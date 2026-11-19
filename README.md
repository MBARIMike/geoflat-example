# GeoViewpoint: the headlight gives no shading

A 210 m by 210 m patch of hills (about 25 m of relief) with normals, shown
from the same camera as a `Viewpoint` and as a `GeoViewpoint` with a
`GeoOrigin`. The vertices are relative to the GeoOrigin (ECEF meters minus its
ECEF position), as in the GLBs that MB-System mbmesh and mbgrd2gltf write.

- `index.html`        the page, with a button for each view
- `terrain.glb`       the mesh as glTF 2.0 with POSITION, NORMAL and a
                      metallic 0, roughness 0.65 material
- `terrain_ifs.x3d`   the same mesh as `IndexedFaceSet`, `Coordinate`, `Normal`
                      and a `Material`
- `make_example.py`   makes the two files and the camera numbers (standard
                      library only)

## Run

Put a build of x3dom master (`x3dom-full.js`, `x3dom.css`) in this directory,
then:

    python3 -m http.server 8000

and open http://127.0.0.1:8000/index.html . The buttons bind the camera:
"Viewpoint (model coordinates)" and "GeoViewpoint (with GeoOrigin)", each
looking straight down or at 45 degrees. The links at the top choose the
model (`?model=glb` or `?model=ifs`) and `&light=1` switches the headlight
off and adds one `DirectionalLight`.

## Expected and observed

Expected: the relief is shaded the same with the `GeoViewpoint` as with the
`Viewpoint`, since the camera, the mesh and the normals are the same.

Observed with x3dom 1.8.4-dev build 7527 (2026-10-15, revision a1e12d27), in
headless Chrome 157 with SwiftShader (software GL):

| model | `Viewpoint` | `GeoViewpoint` | `GeoViewpoint`, headlight off, one `DirectionalLight` |
|---|---|---|---|
| glTF with NORMAL | shaded | flat light blue | shaded, as the `Viewpoint` |
| `IndexedFaceSet` with `Normal` | shaded | black | shaded, as the `Viewpoint` |

See `screenshots/`. The 45 degree `GeoViewpoint` is flat too (screenshot 6),
so tilting the camera does not bring the shading back.

So the mesh, the normals and the materials are fine in a `GeoViewpoint`
view, since an explicit light shades them. It is the headlight, the default
of `NavigationInfo`, that does not light the surface when the viewpoint is
a `GeoViewpoint`: the surface gets no diffuse term (black with the Phong
material of `IndexedFaceSet`) or only the constant term (flat with the
physically based material of glTF).

Not tried: another position than latitude 36.6, longitude -122.4, height 0,
a `GeoViewpoint` without a `GeoOrigin`, and a browser with a GPU. The same
flat look was seen in a browser on real data (a seafloor mesh below the
ellipsoid), so it does not depend on the height or on software GL.

Where it may come from (not checked): the headlight is added in the shader
code with the direction (0, 0, -1) and is the only light that depends on the
viewpoint, so the matrix that a `GeoViewpoint` gives may not be the one that
this direction is meant to go with.
