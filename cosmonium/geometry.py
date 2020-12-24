#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from panda3d.core import Geom, GeomNode, GeomPatches, GeomPoints, GeomVertexData, GeomVertexArrayFormat, InternalName,\
    LVector3d, GlobPattern, BoundingBox, LPoint3, BoundingSphere
from panda3d.core import GeomVertexFormat, GeomTriangles, GeomVertexWriter, ColorAttrib
from panda3d.core import NodePath, VBase3, Vec3, LPoint3d, LPoint2d, BitMask32, LVector3, LVector4i
from panda3d.egg import EggData, EggVertexPool, EggVertex, EggPolygon, loadEggData

from .pstats import named_pstat
from . import settings

from math import sin, cos, pi, atan2, sqrt, asin

def empty_node(prefix, color=False):
    path = NodePath(prefix + '_path')
    node = GeomNode(prefix + '_node')
    path.attachNewNode(node)
    if color:
        path.setAttrib(ColorAttrib.makeVertex())
    return (path, node)

def empty_geom(prefix, nb_data, nb_vertices, points=False, normal=True, texture=True, color=False, tanbin=False):
    array = GeomVertexArrayFormat()
    array.addColumn(InternalName.get_vertex(), 3, Geom.NTFloat32, Geom.CPoint)
    if color:
        array.addColumn(InternalName.get_color(), 4, Geom.NTFloat32, Geom.CColor)
    if texture:
        array.addColumn(InternalName.get_texcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
    if normal:
        array.addColumn(InternalName.get_normal(), 3, Geom.NTFloat32, Geom.CVector)
    if tanbin:
        array.addColumn(InternalName.get_tangent(), 3, Geom.NTFloat32, Geom.CVector)
        array.addColumn(InternalName.get_binormal(), 3, Geom.NTFloat32, Geom.CVector)
    format = GeomVertexFormat()
    format.addArray(array)
    format = GeomVertexFormat.registerFormat(format)
    gvd = GeomVertexData('gvd', format, Geom.UHStatic)
    if nb_data != 0:
        gvd.unclean_set_num_rows(nb_data)
    geom = Geom(gvd)
    gvw = GeomVertexWriter(gvd, InternalName.get_vertex())
    if color:
        gcw = GeomVertexWriter(gvd, InternalName.get_color())
    else:
        gcw = None
    if texture:
        gtw = GeomVertexWriter(gvd, InternalName.get_texcoord())
    else:
        gtw = None
    if normal:
        gnw = GeomVertexWriter(gvd, InternalName.get_normal())
    else:
        gnw = None
    if tanbin:
        gtanw = GeomVertexWriter(gvd, InternalName.get_tangent())
        gbiw = GeomVertexWriter(gvd, InternalName.get_binormal())
    else:
        gtanw = None
        gbiw = None
    if points:
        prim = GeomPoints(Geom.UHStatic)
    else:
        prim = GeomTriangles(Geom.UHStatic)
    if nb_vertices != 0:
        prim.reserve_num_vertices(nb_vertices)
    return (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom)

def BoundingBoxGeom(box):
    (path, node) = empty_node('bb')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('bb', 8, 12, normal=False, texture=False, tanbin=False)
    node.add_geom(geom)
    for i in range(8):
        gvw.set_data3(box.get_point(i))

    prim.add_vertices(0, 4, 5)
    prim.add_vertices(0, 5, 1)
    prim.add_vertices(4, 6, 7)
    prim.add_vertices(4, 7, 5)
    prim.add_vertices(6, 2, 3)
    prim.add_vertices(6, 3, 7)
    prim.add_vertices(2, 0, 1)
    prim.add_vertices(2, 1, 3)
    prim.add_vertices(1, 5, 7)
    prim.add_vertices(1, 7, 3)
    prim.add_vertices(2, 6, 4)
    prim.add_vertices(2, 4, 0)

    geom.add_primitive(prim)
    return path

def CubeGeom():
    (path, node) = empty_node('cube')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', 8, 12, normal=False, texture=False, tanbin=False)
    node.add_geom(geom)
    gvw.add_data3(-1, -1, -1)
    gvw.add_data3(-1, -1, 1)
    gvw.add_data3(-1, 1, -1)
    gvw.add_data3(-1, 1, 1)
    gvw.add_data3(1, -1, -1)
    gvw.add_data3(1, -1, 1)
    gvw.add_data3(1, 1, -1)
    gvw.add_data3(1, 1, 1)

    prim.add_vertices(0, 4, 5)
    prim.add_vertices(0, 5, 1)
    prim.add_vertices(4, 6, 7)
    prim.add_vertices(4, 7, 5)
    prim.add_vertices(6, 2, 3)
    prim.add_vertices(6, 3, 7)
    prim.add_vertices(2, 0, 1)
    prim.add_vertices(2, 1, 3)
    prim.add_vertices(1, 5, 7)
    prim.add_vertices(1, 7, 3)
    prim.add_vertices(2, 6, 4)
    prim.add_vertices(2, 4, 0)

    geom.add_primitive(prim)
    return path

def UVSphere(radius=1, rings=5, sectors=5, inv_texture_u=False, inv_texture_v=False):
    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('uv', rings * sectors, (rings - 1) * sectors, tanbin=True)
    node.add_geom(geom)

    R = 1./(rings-1)
    S = 1./(sectors-1)

    u = 1.0
    v = 1.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, radius)
    gnw.add_data3(0, 0, 1)
    gtanw.add_data3(0, 1, 0)
    gbiw.add_data3(1, 0, 0)
    for r in range(0, rings):
        for s in range(0, sectors):
            cos_s = cos(2*pi * s * S + pi)
            sin_s = sin(2*pi * s * S + pi)
            sin_r = sin(pi * r * R)
            cos_r = cos(pi * r * R)
            x = cos_s * sin_r
            y = sin_s * sin_r
            z = -cos_r
            u = s * S
            v = r * R
            if inv_texture_v:
                v = 1.0 - v
            if inv_texture_u:
                u = 1.0 - u
            gtw.add_data2(u, v)
            gvw.add_data3(x * radius, y * radius, z * radius)
            gnw.add_data3(x, y, z)
            #Derivation wrt s and normalization (sin_r is dropped)
            gtanw.add_data3(-sin_s, cos_s, 0) #-y, x, 0
            #Derivation wrt r
            binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)
            binormal.normalize()
            gbiw.add_data3d(binormal)
    u = 0.0
    v = 0.0
    if inv_texture_v:
        v = 1.0 - v
    if inv_texture_u:
        u = 1.0 - u
    gtw.add_data2(u, v)
    gvw.add_data3(0, 0, -radius)
    gnw.add_data3(0, 0, -1)
    gtanw.add_data3(1, 0, 0)
    gbiw.add_data3(0, 1, 0)

    for r in range(0, rings - 1):
        for s in range(0, sectors):
            if r == 0:
                prim.addVertices(r * sectors + (s+1), (r+1) * sectors + (s+1), (r+1) * sectors + s)
            elif r == rings - 1:
                prim.addVertices(r * sectors + (s+1), (r+1) * sectors + (s+1), (r+1) * sectors + s)
            else:
                prim.addVertices(r * sectors + s, r * sectors + (s+1), (r+1) * sectors + s)
                prim.addVertices(r * sectors + (s+1), (r+1) * sectors + (s+1), (r+1) * sectors + s)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

def DisplacementUVSphere(radius, heightmap, scale, rings=5, sectors=5, inv_texture_u=False, inv_texture_v=True):
    data = EggData()
    pool = EggVertexPool('pool')
    vertices = []
    data.addChild(pool)
    R = 1./(rings)
    S = 1./(sectors)
    for r in range(0, rings + 1):
        for s in range(0, sectors + 1):
            cos_s = cos(2*pi * s * S + pi)
            sin_s = sin(2*pi * s * S + pi)
            sin_r = sin(pi * r * R)
            cos_r = cos(pi * r * R)
            x = cos_s * sin_r
            y = sin_s * sin_r
            z = cos_r
            vertex = EggVertex()
            u = s * S
            v = r * R
            height = radius + heightmap.get_height_uv(u, v) * scale
            vertex.setPos(LPoint3d(x * height, y * height, z * height))
            if inv_texture_v:
                v = 1.0 - v
            if inv_texture_u:
                u = 1.0 - u
            vertex.setUv(LPoint2d(u, v))
            pool.addVertex(vertex)
            vertices.append(vertex)

    index = 0
    for r in range(0, rings):
        for s in range(0, sectors):
            poly = EggPolygon()
            data.addChild(poly)
            poly.addVertex(vertices[index + sectors + 1])
            poly.addVertex(vertices[index])
            poly.addVertex(vertices[index + sectors])

            poly = EggPolygon()
            data.addChild(poly)
            poly.addVertex(vertices[index + sectors + 1])
            poly.addVertex(vertices[index + 1])
            poly.addVertex(vertices[index])
            index += 1
    data.removeUnusedVertices(True)
    data.recomputeVertexNormals(45)
    data.recomputeTangentBinormal(GlobPattern(""))
    node = loadEggData(data)
    path = NodePath(node)
    path.flattenStrong()
    return path

def UVPatchPoint(radius, r, s, x0, y0, x1, y1, offset=None):
    dx = x1 - x0
    dy = y1 - y0

    if offset is not None:
        normal = UVPatchNormal(x0, y0, x1, y1)

    cos_s = cos(2*pi * (x0 + s * dx) + pi)
    sin_s = sin(2*pi * (x0 + s * dx) + pi)
    sin_r = sin(pi * (y0 + r * dy))
    cos_r = cos(pi * (y0 + r * dy))
    x = cos_s * sin_r * radius
    y = sin_s * sin_r * radius
    z = -cos_r * radius

    if offset is not None:
        x = x - normal[0] * offset
        y = y - normal[1] * offset
        z = z - normal[2] * offset

    return LVector3d(x, y, z)

def UVPatchNormal(x0, y0, x1, y1):
    dx = x1 - x0
    dy = y1 - y0
    x = cos(2*pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2))
    y = sin(2*pi * (x0 + dx / 2) + pi) * sin(pi * (y0 + dy / 2))
    z = -cos(pi * (y0 + dy / 2))
    return LVector3d(x, y, z)

@named_pstat("geom")
def PyUVPatch(radius, rings, sectors, x0, y0, x1, y1, global_texture=False, inv_texture_u=False, inv_texture_v=False, has_offset=False, offset=None):
    r_sectors = sectors + 1
    r_rings = rings + 1

    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('uv', (r_rings * r_sectors), rings * sectors, tanbin=True)

    dx = x1 - x0
    dy = y1 - y0

    if offset is not None:
        normal = UVPatchNormal(x0, y0, x1, y1)
    
    for r in range(0, r_rings):
        for s in range(0, r_sectors):
            cos_s = cos(2*pi * (x0 + s * dx / sectors) + pi)
            sin_s = sin(2*pi * (x0 + s * dx / sectors) + pi)
            sin_r = sin(pi * (y0 + r * dy / rings))
            cos_r = cos(pi * (y0 + r * dy / rings))
            x = cos_s * sin_r
            y = sin_s * sin_r
            z = -cos_r
            if global_texture:
                gtw.add_data2((x0 + s * dx / sectors), (y0 + r * dy / rings))
            else:
                u = s / sectors
                v = r / rings
                if inv_texture_v:
                    v = 1.0 - v
                if inv_texture_u:
                    u = 1.0 - u
                gtw.add_data2(u, v)
            if offset is not None:
                gvw.add_data3(x * radius - normal[0] * offset,
                              y * radius - normal[1] * offset,
                              z * radius - normal[2] * offset)
            else:
                gvw.add_data3(x * radius, y * radius, z * radius)
            gnw.add_data3f(x, y, z)
            #Derivation wrt s and normalization (sin_r is dropped)
            gtanw.add_data3(-sin_s, cos_s, 0) #-y, x, 0
            #Derivation wrt r
            binormal = LVector3d(cos_s * cos_r, sin_s * cos_r, sin_r)
            binormal.normalize()
            gbiw.add_data3d(binormal)

    for r in range(0, r_rings - 1):
        for s in range(0, r_sectors - 1):
#             if y0 == 0 and r == 0:
#                 #prim.addVertices((r+1) * r_sectors + (s+1), (r+1) * r_sectors + s, r * r_sectors + (s+1))
#             elif y1 == rings and r == r_rings - 1:
#                 #prim.addVertices((r+1) * r_sectors + (s+1), (r+1) * r_sectors + s, r * r_sectors + (s+1))
#             else:
#             if y0 >= 0.5:
                prim.addVertices(r * r_sectors + s, r * r_sectors + (s+1), (r+1) * r_sectors + s)
                prim.addVertices(r * r_sectors + (s+1), (r+1) * r_sectors + (s+1), (r+1) * r_sectors + s)
#             else:
#                 prim.addVertices((r + 1) * r_sectors + s, r * r_sectors + (s+1), r * r_sectors + s)
#                 prim.addVertices(r * r_sectors + (s+1), (r+1) * r_sectors + s, (r + 1) * r_sectors + (s+1))
    prim.closePrimitive()
    geom.addPrimitive(prim)
    node.add_geom(geom)
    return path

def halfSphereAABB(height, positive, offset):
    if positive:
        min_points = LPoint3(-1, 0 - offset, -1)
        max_points = LPoint3(1, 1 - offset, 1)
    else:
        min_points = LPoint3(-1, offset - 1, -1)
        max_points = LPoint3(1, offset, 1)
    return BoundingBox(min_points, max_points)

def UVPatchAABB(min_radius, max_radius, x0, y0, x1, y1, offset):
    points = []
    if min_radius != max_radius:
        radii = (min_radius, max_radius)
    else:
        radii = (min_radius,)
    for radius in radii:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                points.append(UVPatchPoint(radius, i, j, x0, y0, x1, y1, offset))
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box

def UVPatchedSphere(radius=1, rings=8, sectors=16, lod=2):
    #LOD = 1 : Two half sphere
    path = NodePath('uv')
    r_div = 1 << lod
    s_div = 2 << lod
    for sector in range(s_div):
        for ring in range(r_div):
            x0 = int(sector * sectors / s_div)
            y0 = int(ring * rings / r_div)
            x1 = int((sector + 1) * sectors / s_div)
            y1 = int((ring + 1) * rings / r_div)
            subpath = UVPatch(radius, rings, sectors, x0, y0, x1, y1)
            subpath.reparentTo(path)
    return path

def IcoSphere(radius=1, subdivisions=1):
    (path, node) = empty_node('ico')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('ico', 0, 0, tanbin=True)
    node.add_geom(geom)

    verts = []

    phi = .5 * (1. + sqrt(5.))
    invnorm = 1 / sqrt(phi * phi + 1)

    verts.append(Vec3(-1, phi, 0) * invnorm)  # 0
    verts.append(Vec3(1, phi, 0) * invnorm)  # 1
    verts.append(Vec3(0, 1, -phi) * invnorm)  # 2
    verts.append(Vec3(0, 1, phi) * invnorm)  # 3
    verts.append(Vec3(-phi, 0, -1) * invnorm)  # 4
    verts.append(Vec3(-phi, 0, 1) * invnorm)  # 5
    verts.append(Vec3(phi, 0, -1) * invnorm)  # 6
    verts.append(Vec3(phi, 0, 1) * invnorm)  # 7
    verts.append(Vec3(0, -1, -phi) * invnorm)  # 8
    verts.append(Vec3(0, -1, phi) * invnorm)  # 9
    verts.append(Vec3(-1, -phi, 0) * invnorm)  # 10
    verts.append(Vec3(1, -phi, 0) * invnorm)  # 11

    faces = [
        0, 1, 2,
        0, 3, 1,
        0, 4, 5,
        1, 7, 6,
        1, 6, 2,
        1, 3, 7,
        0, 2, 4,
        0, 5, 3,
        2, 6, 8,
        2, 8, 4,
        3, 5, 9,
        3, 9, 7,
        11, 6, 7,
        10, 5, 4,
        10, 4, 8,
        10, 9, 5,
        11, 8, 6,
        11, 7, 9,
        10, 8, 11,
        10, 11, 9
    ]

    size = 60

    # Step 2 : tessellate
    for subdivision in range(0, subdivisions):
        size *= 4;
        newFaces = []
        for i in range(0, int(size / 12)):
            i1 = faces[i * 3]
            i2 = faces[i * 3 + 1]
            i3 = faces[i * 3 + 2]
            i12 = len(verts)
            i23 = i12 + 1
            i13 = i12 + 2
            v1 = verts[i1]
            v2 = verts[i2]
            v3 = verts[i3]
            # make 1 vertice at the center of each edge and project it onto the sphere
            vt = v1 + v2
            vt.normalize()
            verts.append(vt)
            vt = v2 + v3
            vt.normalize()
            verts.append(vt)
            vt = v1 + v3
            vt.normalize()
            verts.append(vt)
            # now recreate indices
            newFaces.append(i1)
            newFaces.append(i12)
            newFaces.append(i13)
            newFaces.append(i2)
            newFaces.append(i23)
            newFaces.append(i12)
            newFaces.append(i3)
            newFaces.append(i13)
            newFaces.append(i23)
            newFaces.append(i12)
            newFaces.append(i23)
            newFaces.append(i13)
        faces = newFaces

    vertices = []
    texs = []
    norms = []
    for i in range(0, len(verts)):
        vert = verts[i]
        vertices.append(VBase3(vert * radius))
        norms.append(vert)
        #Calculate texture coords
        u = -((atan2(vert.x, vert.y)) / pi) / 2.0 + 0.5
        v = asin(vert.z) / pi + 0.5
        texs.append([u, v])
    indices = len(vertices)
    for i in range(0, int(len(faces) / 3)):
        i1 = faces[i * 3]
        i2 = faces[i * 3 + 1]
        i3 = faces[i * 3 + 2]
        u1 = texs[i2][0] - texs[i1][0]
        v1 = texs[i2][1] - texs[i1][1]
        u2 = texs[i3][0] - texs[i2][0]
        v2 = texs[i3][1] - texs[i2][1]
        if (u1*v2 - u2*v1) < 0:
            if texs[i1][0] < 0.5:
                vertices.append(vertices[i1])
                norms.append(norms[i1])
                texs.append([texs[i1][0]+1.0, texs[i1][1]])
                i1 = indices
                indices += 1
            if texs[i2][0] < 0.5:
                vertices.append(vertices[i2])
                norms.append(norms[i2])
                texs.append([texs[i2][0]+1.0, texs[i2][1]])
                i2 = indices
                indices += 1
            if texs[i3][0] < 0.5:
                vertices.append(vertices[i3])
                norms.append(norms[i3])
                texs.append([texs[i3][0]+1.0, texs[i3][1]])
                i3 = indices
                indices += 1
        faces[i * 3] = i1
        faces[i * 3 + 1] = i2
        faces[i * 3 + 2] = i3
    for i in range(0, len(vertices)):
        gvw.add_data3(vertices[i])
        gnw.add_data3(norms[i])
        gtw.add_data2(*texs[i])
    for i in range(0, int(len(faces) / 3)):
        i1 = faces[i * 3]
        i2 = faces[i * 3 + 1]
        i3 = faces[i * 3 + 2]
        prim.addVertices(i1, i2, i3)

    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

class PyTesselationInfo():
    def __init__(self, inner, outer):
        self.inner = inner
        self.outer = outer
        self.ratio = [inner // x if inner >= x else 1 for x in outer]

def make_config(inner, outer):
    nb_vertices = inner + 1
    if outer is None:
        outer = [inner, inner, inner, inner]
    ratio = [inner // x if inner >= x else 1 for x in outer]
    return (nb_vertices, inner, outer, ratio)

def make_square_primitives(prim, inner, nb_vertices):
    for x in range(0, inner):
        for y in range(0, inner):
            v = nb_vertices * y + x
            prim.addVertices(v, v + nb_vertices, v + 1)
            prim.addVertices(v + 1, v + nb_vertices, v + nb_vertices + 1)

def make_adapted_square_primitives(prim, inner, nb_vertices, ratio):
    for x in range(0, inner):
        for y in range(0, inner):
#     for x in (0, 1, 2, inner - 3, inner - 2, inner - 1): #range(0, inner):
#         for y in (0, 1, 2, inner - 3, inner - 2, inner - 1): #range(0, inner):
#    for x in (0, inner - 1): #range(0, inner):
#        for y in (0, inner - 1): #range(0, inner):
            if x == 0:
                if y == 0:
                    i = 0
                    v = nb_vertices * y + x
                    vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                    if (x % ratio[i]) == 0:
                        prim.addVertices(v, v + nb_vertices + ratio[i], v + ratio[i])
                    prim.addVertices(vp, v + nb_vertices, v + nb_vertices + 1)
                    i = 1
                    v = nb_vertices * y + x
                    vp = nb_vertices * (y // ratio[i]) * ratio[i] + x
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v, v + nb_vertices * ratio[i], v + 1)
                    prim.addVertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1)
                elif y == inner - 1:
                    i = 1
                    v = nb_vertices * y + x
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v, v + nb_vertices * ratio[i], v + 1)
                    i = 2
                    v = nb_vertices * y + x
                    vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                    prim.addVertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i])
                else:
                    i = 1
                    v = nb_vertices * y + x
                    vp = nb_vertices * (y // ratio[i]) * ratio[i] + x
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v, v + nb_vertices * ratio[i], v + 1)
                    prim.addVertices(v + 1, vp + nb_vertices * ratio[i], v + nb_vertices + 1)
            elif x == inner - 1:
                if y == 0:
                    i = 0
                    v = nb_vertices * y + x
                    vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                    if (x % ratio[i]) == 0:
                        prim.addVertices(v, v + nb_vertices + ratio[i], v + ratio[i])
                    prim.addVertices(vp, v + nb_vertices, v + nb_vertices + 1)
                    i = 3
                    v = nb_vertices * y + x
                    vp = nb_vertices * ((y // ratio[i]) * ratio[i]) + x
                    prim.addVertices(v, v + nb_vertices, vp + 1)
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1)
                elif y == inner - 1:
                    i = 2
                    v = nb_vertices * y + x
                    vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                    prim.addVertices(v, vp + nb_vertices, v + 1)
                    if (x % ratio[i]) == 0:
                        prim.addVertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i])
                    i = 3
                    v = nb_vertices * y + x
                    vp = nb_vertices * ((y // ratio[i]) * ratio[i]) + x
                    prim.addVertices(v, v + nb_vertices, vp + 1)
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1)
                else:
                    i = 3
                    v = nb_vertices * y + x
                    vp = nb_vertices * ((y // ratio[i]) * ratio[i]) + x
                    prim.addVertices(v, v + nb_vertices, vp + 1)
                    if (y % ratio[i]) == 0:
                        prim.addVertices(v + 1, v + nb_vertices * ratio[i], v + nb_vertices * ratio[i] + 1)
            elif y == 0:
                i = 0
                v = nb_vertices * y + x
                vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                if (x % ratio[i]) == 0:
                    prim.addVertices(v, v + nb_vertices + ratio[i], v + ratio[i])
                prim.addVertices(vp, v + nb_vertices, v + nb_vertices + 1)
            elif y == inner - 1:
                i = 2
                v = nb_vertices * y + x
                vp = nb_vertices * y + (x // ratio[i]) * ratio[i]
                prim.addVertices(v, vp + nb_vertices, v + 1)
                if (x % ratio[i]) == 0:
                    prim.addVertices(vp + ratio[i], v + nb_vertices, v + nb_vertices + ratio[i])
            else:
                v = nb_vertices * y + x
                prim.addVertices(v, v + nb_vertices, v + 1)
                prim.addVertices(v + 1, v + nb_vertices, v + nb_vertices + 1)

def make_adapted_square_primitives_skirt(prim, inner, nb_vertices, ratio):
    for a in range(0, 4):
        start = nb_vertices * nb_vertices + a * nb_vertices
        for b in range(0, inner):
            skirt = start + b
            if a == 0:
                i = 1
                x = 0
                y = b
            elif a == 1:
                i = 3
                x = inner - 1
                y = b
            elif a == 2:
                i = 0
                x = b
                y = 0
            elif a == 3:
                i = 2
                x = b
                y = inner - 1
            v = nb_vertices * x + y
            if a == 0:
                if (y % ratio[i]) == 0:
                    prim.addVertices(v, v + ratio[i], skirt)
                    prim.addVertices(skirt, v + ratio[i], skirt + ratio[i])
            elif a == 1:
                if (y % ratio[i]) == 0:
                    prim.addVertices(v + nb_vertices, skirt, v + nb_vertices + ratio[i])
                    prim.addVertices(v + nb_vertices + ratio[i], skirt, skirt + ratio[i])
            elif a == 2:
                if (x % ratio[i]) == 0:
                    prim.addVertices(v, skirt, v + nb_vertices * ratio[i])
                    prim.addVertices(v + nb_vertices * ratio[i], skirt, skirt + ratio[i])
            elif a == 3:
                if (x % ratio[i]) == 0:
                    prim.addVertices(skirt + ratio[i], v + 1, v + nb_vertices * ratio[i] + 1)
                    prim.addVertices(skirt, v + 1, skirt + ratio[i])

def make_primitives_skirt(prim, inner, nb_vertices):
    for a in range(0, 4):
        start = nb_vertices * nb_vertices + a * nb_vertices
        for b in range(0, inner):
            skirt = start + b
            if a == 0:
                x = 0
                y = b
            elif a == 1:
                x = inner - 1
                y = b
            elif a == 2:
                x = b
                y = 0
            elif a == 3:
                x = b
                y = inner - 1
            v = nb_vertices * x + y
            if a == 0:
                prim.addVertices(v, v + 1, skirt)
                prim.addVertices(skirt, v + 1, skirt + 1)
            elif a == 1:
                prim.addVertices(v + nb_vertices, skirt, v + nb_vertices + 1)
                prim.addVertices(v + nb_vertices + 1, skirt, skirt + 1)
            elif a == 2:
                prim.addVertices(v, skirt, v + nb_vertices)
                prim.addVertices(v + nb_vertices, skirt, skirt + 1)
            elif a == 3:
                prim.addVertices(skirt + 1, v + 1, v + nb_vertices + 1)
                prim.addVertices(skirt, v + 1, skirt + 1)

def Tile(size, inner, outer=None, inv_u=False, inv_v=False, swap_uv=False):
    (nb_vertices, inner, outer, ratio) = make_config(inner, outer)
    (path, node) = empty_node('uv')
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if settings.use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            u = float(i) / inner
            v = float(j) / inner

            x = u
            y = v

            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                gtw.add_data2(v, u)
            else:
                gtw.add_data2(u, v)
            gvw.add_data3(x * size, y * size, 0)
            gnw.add_data3(0, 0, 1.0)
            gtanw.add_data3(1, 0, 0)
            gbiw.add_data3(0, 1, 0)

    if settings.use_patch_skirts:
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i = 0
                    j = b
                elif a == 1:
                    i = inner
                    j = b
                elif a == 2:
                    i = b
                    j = 0
                elif a == 3:
                    i = b
                    j = inner
                u = float(i) / inner
                v = float(j) / inner

                x = u
                y = v

                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    gtw.add_data2(v, u)
                else:
                    gtw.add_data2(u, v)
                gvw.add_data3(x * size, y * size, -size)
                gnw.add_data3(0, 0, 1.0)
                gtanw.add_data3(1, 0, 0)
                gbiw.add_data3(0, 1, 0)

    if settings.use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, ratio)
        if settings.use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if settings.use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

def TileAABB(size=1.0, height=1.0):
    return BoundingBox(LPoint3(0, 0, -height ), LPoint3(size, size, height))

def Patch(size=1.0):
    (path, node) = empty_node('patch')
    form = GeomVertexFormat.getV3()
    vdata = GeomVertexData("vertices", form, Geom.UHStatic)

    vertexWriter = GeomVertexWriter(vdata, "vertex")
    vertexWriter.add_data3(0, 0, 0)
    vertexWriter.add_data3(size, 0, 0)
    vertexWriter.add_data3(size, size, 0)
    vertexWriter.add_data3(0, size, 0)
    patches = GeomPatches(4, Geom.UHStatic)

    patches.addConsecutiveVertices(0, 4) #South, west, north, east
    patches.closePrimitive()

    gm = Geom(vdata)
    gm.addPrimitive(patches)

    node.addGeom(gm)
    return path

def PatchAABB(size=1.0, min_height=-1.0, max_height=1.0):
    return BoundingBox(LPoint3(0, 0, min_height), LPoint3(size, size, max_height))

def convert_xy(x0, y0, x1, y1, x_inverted=False, y_inverted=False, xy_swap=False):
    if x_inverted:
        x0, x1 = 1 - x1, 1 - x0
    if y_inverted:
        y0, y1 = 1 - y1, 1 - y0
    if xy_swap:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    dx = float(x1 - x0)
    dy = float(y1 - y0)

    return (x0, y0, x1, y1, dx, dy)

def QuadPatch(x0, y0, x1, y1,
              x_inverted=False, y_inverted=False, xy_swap=False, offset=None):

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    if offset is None:
        offset = 1.0

    (path, node) = empty_node('patch')
    form = GeomVertexFormat.getV3()
    vdata = GeomVertexData("vertices", form, Geom.UHStatic)

    vertexWriter = GeomVertexWriter(vdata, "vertex")
    x0 = 2.0 * x0 - 1.0
    x1 = 2.0 * x1 - 1.0
    y0 = 2.0 * y0 - 1.0
    y1 = 2.0 * y1 - 1.0
    vertexWriter.add_data3(x0, y0, offset)
    vertexWriter.add_data3(x1, y0, offset)
    vertexWriter.add_data3(x1, y1, offset)
    vertexWriter.add_data3(x0, y1, offset)
    patches = GeomPatches(4, Geom.UHStatic)

    patches.addConsecutiveVertices(0, 4) #South, west, north, east
    patches.closePrimitive()

    gm = Geom(vdata)
    gm.addPrimitive(patches)

    node.addGeom(gm)
    return path

@named_pstat("geom")
def SquarePatch(height, inner, outer,
                x0, y0, x1, y1,
                inv_u=False, inv_v=False, swap_uv=False,
                x_inverted=False, y_inverted=False, xy_swap=False, offset=None):
    (nb_vertices, inner, outer, ratio) = make_config(inner, outer)

    (path, node) = empty_node('uv')
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_vertices * nb_vertices, inner * inner, tanbin=True)
    node.add_geom(geom)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    if offset is None:
        offset = height

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            x = x0 + i * dx / inner
            y = y0 + j * dy / inner

            x = 2.0 * x - 1.0
            y = 2.0 * y - 1.0

            u = float(i) / inner
            v = float(j) / inner

            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                gtw.add_data2(v, u)
            else:
                gtw.add_data2(u, v)
            gvw.add_data3(x * height, y * height, height)
            gnw.add_data3(0, 0, 1.0)
            gtanw.add_data3(1, 0, 0)
            gbiw.add_data3(0, 1, 0)

    make_adapted_square_primitives(prim, inner, nb_vertices, ratio)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

@named_pstat("geom")
def PySquaredDistanceSquarePatch(height, tesselation,
                x0, y0, x1, y1,
                inv_u=False, inv_v=False, swap_uv=False,
                x_inverted=False, y_inverted=False, xy_swap=False, has_offset=False, offset=None,
                use_patch_adaptation = True,
                use_patch_skirts = True):
    (path, node) = empty_node('uv')
    inner = tesselation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if offset is not None:
        normal = SquaredDistanceSquarePatchNormal(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            u = float(i) / inner
            v = float(j) / inner
            x = x0 + i * dx / inner
            y = y0 + j * dy / inner
            x = 2.0 * x - 1.0
            y = 2.0 * y - 1.0
            z = 1.0
            x2 = x * x
            y2 = y * y
            z2 = z * z
            xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
            yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
            zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                u, v = v, u
            gtw.add_data2(u, v)
            if offset is not None:
                gvw.add_data3(xp * height - normal[0] * offset,
                              yp * height - normal[1] * offset,
                              zp * height - normal[2] * offset)
            else:
                gvw.add_data3(xp * height, yp * height, zp * height)
            gnw.add_data3(xp, yp, zp)
            tan = LVector3d(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5))
            tan.normalize()
            bin = LVector3d(x * y * (z2 / 3.0 - 0.5), 1.0, y * z * (x2 / 3.0 - 0.5))
            bin.normalize()
            if inv_u: tan = -tan
            if inv_v: bin = -bin
            if swap_uv:
                tan, bin = bin, tan
            gtanw.add_data3d(tan)
            gbiw.add_data3d(bin)

    if use_patch_skirts:
        if offset is None:
            offset = 0
        offset = offset + sqrt(dx * dx + dy * dy) / inner
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i = 0
                    j = b
                elif a == 1:
                    i = inner
                    j = b
                elif a == 2:
                    i = b
                    j = 0
                elif a == 3:
                    i = b
                    j = inner
                u = float(i) / inner
                v = float(j) / inner
                x = x0 + i * dx / inner
                y = y0 + j * dy / inner
                x = 2.0 * x - 1.0
                y = 2.0 * y - 1.0
                z = 1.0
                x2 = x * x
                y2 = y * y
                z2 = z * z
                xp = x * sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
                yp = y * sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
                zp = z * sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    u, v = v, u
                gtw.add_data2(u, v)
                if offset is not None:
                    gvw.add_data3(xp * height - normal[0] * offset,
                                  yp * height - normal[1] * offset,
                                  zp * height - normal[2] * offset)
                else:
                    gvw.add_data3(xp * height, yp * height, zp * height)
                gnw.add_data3(xp, yp, zp)
                tan = LVector3d(1.0, x * y * (z2 / 3.0 - 0.5), x * z * (y2 / 3.0 - 0.5))
                tan.normalize()
                bin = LVector3d(x * y * (z2 / 3.0 - 0.5), 1.0, y * z * (x2 / 3.0 - 0.5))
                bin.normalize()
                if inv_u: tan = -tan
                if inv_v: bin = -bin
                if swap_uv:
                    tan, bin = bin, tan
                gtanw.add_data3d(tan)
                gbiw.add_data3d(bin)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tesselation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tesselation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

def SquaredDistanceSquarePatchPoint(radius,
                                    u, v,
                                    x0, y0, x1, y1,
                                    offset = None,
                                    x_inverted=False, y_inverted=False, xy_swap=False):

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    x = x0 + u * dx
    y = y0 + v * dy

    x = 2.0 * x - 1.0
    y = 2.0 * y - 1.0
    z = 1.0

    x2 = x * x
    y2 = y * y
    z2 = z * z

    x *= sqrt(1.0 - y2 * 0.5 - z2 * 0.5 + y2 * z2 / 3.0)
    y *= sqrt(1.0 - z2 * 0.5 - x2 * 0.5 + z2 * x2 / 3.0)
    z *= sqrt(1.0 - x2 * 0.5 - y2 * 0.5 + x2 * y2 / 3.0)
    vec = LVector3d(x, y, z)
    vec *= radius

    if offset is not None:
        normal = SquaredDistanceSquarePatchNormal(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)
        vec = vec - normal * offset

    return vec

def SquaredDistanceSquarePatchNormal(x0, y0, x1, y1,
                                     x_inverted=False, y_inverted=False, xy_swap=False):

    return SquaredDistanceSquarePatchPoint(1.0, 0.5, 0.5, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)

def SquaredDistanceSquarePatchAABB(min_radius, max_radius,
                                   x0, y0, x1, y1, offset=None,
                                   x_inverted=False, y_inverted=False, xy_swap=False):
    points = []
    if min_radius != max_radius:
        radii = (min_radius, max_radius)
    else:
        radii = (min_radius,)
    for radius in radii:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                points.append(SquaredDistanceSquarePatchPoint(radius, i, j, x0, y0, x1, y1, offset, x_inverted, y_inverted, xy_swap))
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box

@named_pstat("geom")
def PyNormalizedSquarePatch(height, tesselation,
                          x0, y0, x1, y1,
                          inv_u=False, inv_v=False, swap_uv=False,
                          x_inverted=False, y_inverted=False, xy_swap=False, has_offset=False, offset=None,
                          use_patch_adaptation = True,
                          use_patch_skirts = True):
    (path, node) = empty_node('uv')
    inner = tesselation.inner
    nb_vertices = inner + 1
    nb_points = nb_vertices * nb_vertices
    nb_primitives = inner * inner
    if use_patch_skirts:
        nb_points += nb_vertices * 4
        nb_primitives += inner * 4
    (gvw, gcw, gtw, gnw, gtanw, gbiw, prim, geom) = empty_geom('cube', nb_points, nb_primitives, tanbin=True)
    node.add_geom(geom)

    if has_offset:
        normal = NormalizedSquarePatchNormal(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    for i in range(0, nb_vertices):
        for j in range(0, nb_vertices):
            x = x0 + i * dx / inner
            y = y0 + j * dy / inner
            x = 2.0 * x - 1.0
            y = 2.0 * y - 1.0
            vec = LVector3d(x, y, 1.0)
            vec.normalize()
            u = float(i) / inner
            v = float(j) / inner
            if inv_u:
                u = 1.0 - u
            if inv_v:
                v = 1.0 - v
            if swap_uv:
                u, v = v, u
            gtw.add_data2(u, v)
            nvec = vec
            vec = vec * height
            if offset is not None:
                vec = vec - normal * offset
            gvw.add_data3d(vec)
            gnw.add_data3d(nvec)
            tan = LVector3d(1.0 + y*y, -x*y, -x)
            tan.normalize()
            bin = LVector3d(x * y, 1.0 + x*x, -y)
            bin.normalize()
            if inv_u: tan = -tan
            if inv_v: bin = -bin
            if swap_uv:
                tan, bin = bin, tan
            gtanw.add_data3d(tan)
            gbiw.add_data3d(bin)

    if use_patch_skirts:
        if offset is None:
            offset = 0
        offset = offset + sqrt(dx * dx + dy * dy) / inner
        for a in range(0, 4):
            for b in range(0, nb_vertices):
                if a == 0:
                    i = 0
                    j = b
                elif a == 1:
                    i = inner
                    j = b
                elif a == 2:
                    i = b
                    j = 0
                elif a == 3:
                    i = b
                    j = inner
                x = x0 + i * dx / inner
                y = y0 + j * dy / inner
                x = 2.0 * x - 1.0
                y = 2.0 * y - 1.0
                vec = LVector3d(x, y, 1.0)
                vec.normalize()
                u = float(i) / inner
                v = float(j) / inner
                if inv_u:
                    u = 1.0 - u
                if inv_v:
                    v = 1.0 - v
                if swap_uv:
                    u, v = v, u
                gtw.add_data2(u, v)
                nvec = vec
                vec = vec * height
                if has_offset:
                    vec = vec - normal * offset
                gvw.add_data3d(vec)
                gnw.add_data3d(nvec)
                tan = LVector3d(1.0 + y*y, -x*y, -x)
                tan.normalize()
                bin = LVector3d(x * y, 1.0 + x*x, -y)
                bin.normalize()
                if inv_u: tan = -tan
                if inv_v: bin = -bin
                if swap_uv:
                    tan, bin = bin, tan
                gtanw.add_data3d(tan)
                gbiw.add_data3d(bin)

    if use_patch_adaptation:
        make_adapted_square_primitives(prim, inner, nb_vertices, tesselation.ratio)
        if use_patch_skirts:
            make_adapted_square_primitives_skirt(prim, inner, nb_vertices, tesselation.ratio)
    else:
        make_square_primitives(prim, inner, nb_vertices)
        if use_patch_skirts:
            make_primitives_skirt(prim, inner, nb_vertices)
    prim.closePrimitive()
    geom.addPrimitive(prim)

    return path

def NormalizedSquarePatchPoint(radius,
                               u, v,
                               x0, y0, x1, y1,
                               offset = None,
                               x_inverted=False, y_inverted=False, xy_swap=False):
    if offset is not None:
        normal = NormalizedSquarePatchNormal(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    (x0, y0, x1, y1, dx, dy) = convert_xy(x0, y0, x1, y1, x_inverted, y_inverted, xy_swap)

    x = x0 + u * dx
    y = y0 + v * dy
    vec = LVector3d(2.0 * x - 1.0, 2.0 * y - 1.0, 1.0)
    vec.normalize()
    vec *= radius

    if offset is not None:
        vec = vec - normal * offset

    return vec

def NormalizedSquarePatchNormal(x0, y0, x1, y1,
                                x_inverted=False, y_inverted=False, xy_swap=False):
    return NormalizedSquarePatchPoint(1.0, 0.5, 0.5, x0, y0, x1, y1, None, x_inverted, y_inverted, xy_swap)

def NormalizedSquarePatchAABB(min_radius, max_radius,
                              x0, y0, x1, y1, offset=None,
                              x_inverted=False, y_inverted=False, xy_swap=False):
    points = []
    if min_radius != max_radius:
        radii = (min_radius, max_radius)
    else:
        radii = (min_radius,)
    for radius in radii:
        for i in (0.0, 0.5, 1.0):
            for j in (0.0, 0.5, 1.0):
                points.append(NormalizedSquarePatchPoint(radius, i, j, x0, y0, x1, y1, offset, x_inverted, y_inverted, xy_swap))
    x_min = min(p.get_x() for p in points)
    x_max = max(p.get_x() for p in points)
    y_min = min(p.get_y() for p in points)
    y_max = max(p.get_y() for p in points)
    z_min = min(p.get_z() for p in points)
    z_max = max(p.get_z() for p in points)
    box = BoundingBox(LPoint3(x_min, y_min, z_min), LPoint3(x_max, y_max, z_max))
    return box

@named_pstat("geom")
def RingFaceGeometry(up, inner_radius, outer_radius, nbOfPoints):
    format = GeomVertexFormat.getV3n3cpt2()
    vdata = GeomVertexData('ring', format, Geom.UHStatic)
    vdata.unclean_set_num_rows(nbOfPoints)
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    texcoord = GeomVertexWriter(vdata, 'texcoord')
    for i in range(nbOfPoints):
        angle = 2 * pi / nbOfPoints * i
        x = cos(angle)
        y = sin(angle)
        vertex.add_data3(outer_radius * x, outer_radius * y, 0)
        normal.add_data3(0, 0, up)
        color.add_data4(1, 1, 1, 1)
        texcoord.add_data2(1, 0)
        vertex.add_data3(inner_radius * x, inner_radius * y, 0)
        normal.add_data3(0, 0, up)
        color.add_data4(1, 1, 1, 1)
        texcoord.add_data2(0, 0)
    triangles = GeomTriangles(Geom.UHStatic)
    triangles.reserve_num_vertices(nbOfPoints - 1)
    for i in range(nbOfPoints-1):
        if up < 0:
            triangles.addVertex(i*2+0)
            triangles.addVertex(i*2+1)
            triangles.addVertex(i*2+2)
            triangles.closePrimitive()
            triangles.addVertex(i*2+2)
            triangles.addVertex(i*2+1)
            triangles.addVertex(i*2+3)
            triangles.closePrimitive()
        else:
            triangles.addVertex(i*2+2)
            triangles.addVertex(i*2+1)
            triangles.addVertex(i*2+0)
            triangles.closePrimitive()
            triangles.addVertex(i*2+3)
            triangles.addVertex(i*2+1)
            triangles.addVertex(i*2+2)
            triangles.closePrimitive()
    if up < 0:
        triangles.addVertex((nbOfPoints-1)*2+0)
        triangles.addVertex((nbOfPoints-1)*2+1)
        triangles.addVertex(0)
        triangles.closePrimitive()
        triangles.addVertex(0)
        triangles.addVertex((nbOfPoints-1)*2+1)
        triangles.addVertex(1)
        triangles.closePrimitive()
    else:
        triangles.addVertex(0)
        triangles.addVertex((nbOfPoints-1)*2+1)
        triangles.addVertex((nbOfPoints-1)*2+0)
        triangles.closePrimitive()
        triangles.addVertex(1)
        triangles.addVertex((nbOfPoints-1)*2+1)
        triangles.addVertex(0)
        triangles.closePrimitive()
    geom = Geom(vdata)
    geom.addPrimitive(triangles)
    return geom

UVPatch = PyUVPatch
SquaredDistanceSquarePatch = PySquaredDistanceSquarePatch
NormalizedSquarePatch = PyNormalizedSquarePatch
TesselationInfo = PyTesselationInfo

try:
    from cosmonium_engine import TesselationInfo as CTesselationInfo
    from cosmonium_engine import UVPatchGenerator, QCSPatchGenerator, ImprovedQCSPatchGenerator
    TesselationInfo = CTesselationInfo
    uv_patch_generator = UVPatchGenerator()
    UVPatch = uv_patch_generator.make
    qcs_patch_generator = QCSPatchGenerator()
    NormalizedSquarePatch = qcs_patch_generator.make
    improved_qcs_patch_generator = ImprovedQCSPatchGenerator()
    SquaredDistanceSquarePatch = improved_qcs_patch_generator.make
except ImportError as e:
    print("WARNING: Could not load geometry C implementation, fallback on python implementation")
    print("\t", e)
