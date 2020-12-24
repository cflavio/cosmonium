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

from __future__ import print_function
from __future__ import absolute_import

from panda3d.core import LPoint3d, LQuaternion, LColor, LVector3, LVector3d
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomVertexRewriter, InternalName
from panda3d.core import Geom, GeomNode, GeomLines
from panda3d.core import NodePath

from .foundation import VisibleObject, ObjectLabel, LabelledObject
from .astro.orbits import FixedOrbit, InfinitePosition
from .astro import units
from .bodyclass import bodyClasses
from .shaders import BasicShader, FlatLightingModel, LargeObjectVertexControl
from .appearances import ModelAppearance
from .mesh import load_panda_model
from .utils import srgb_to_linear
from . import settings

from math import sin, cos, atan2, pi

class AnnotationLabel(ObjectLabel):
    def update_instance(self, camera_pos, camera_rot):
        position = self.parent.project(0, self.context.observer.camera_global_pos, self.context.observer.infinity)
        if position != None:
            self.instance.setPos(*position)
            scale = abs(self.context.observer.pixel_size * self.parent.get_label_size() * self.context.observer.infinity)
        else:
            scale = 0.0
        if scale < 1e-7:
            print("Label too far", self.get_name())
            scale = 1e-7
        self.instance.setScale(scale)
        self.look_at.set_pos(LVector3(*(camera_rot.xform(LVector3d.forward()))))
        self.label_instance.look_at(self.look_at, LVector3(), LVector3(*(camera_rot.xform(LVector3d.up()))))

class BackgroundLabel(AnnotationLabel):
    def create_instance(self):
        AnnotationLabel.create_instance(self)
        self.instance.setBin('background', self.parent.background_level)

class Orbit(VisibleObject):
    ignore_light = True
    default_shown = False
    selected_color = LColor(1.0, 0.0, 0.0, 1.0)
    appearance = None
    shader = None

    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-orbit')
        self.body = body
        self.owner = body
        self.nbOfPoints = 360
        self.orbit = self.find_orbit(self.body)
        self.color = None
        self.fade = 0.0
        if not self.orbit:
            print("No orbit for", self.get_name())
            self.visible = False

    def get_oid_color(self):
        if self.body is not None:
            return self.body.oid_color
        else:
            return LColor()

    @classmethod
    def create_shader(cls):
        cls.appearance = ModelAppearance(attribute_color=True)
        if settings.use_inv_scaling:
            vertex_control = LargeObjectVertexControl()
        else:
            vertex_control = None
        cls.shader = BasicShader(lighting_model=FlatLightingModel(), vertex_control=vertex_control)

    def check_settings(self):
        if self.body.body_class is None:
            print("No class for", self.body.get_name())
            return
        self.set_shown(settings.show_orbits and bodyClasses.get_show_orbit(self.body.body_class))

    def find_orbit(self, body):
        if body != None:
            if not isinstance(body.orbit, FixedOrbit):
                return body.orbit
            else:
                return None, None
        else:
            return None, None

    def set_selected(self, selected):
        if selected:
            self.color = self.selected_color
        else:
            self.color = self.parent.get_orbit_color()
        if self.instance:
            self.instance.setColor(srgb_to_linear(self.color * self.fade))

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        delta = self.body.parent.get_local_position()
        if self.orbit.is_periodic():
            epoch = self.context.time.time_full - self.orbit.period / 2
            step = self.orbit.period / (self.nbOfPoints - 1)
        else:
            #TODO: Properly calculate orbit start and end time
            epoch = self.orbit.get_time_of_perihelion() - self.orbit.period * 5.0
            step = self.orbit.period * 10.0 / (self.nbOfPoints - 1)
        for i in range(self.nbOfPoints):
            time = epoch + step * i
            pos = self.orbit.get_position_at(time) - delta
            self.vertexWriter.addData3f(*pos)
        self.lines = GeomLines(Geom.UHStatic)
        for i in range(self.nbOfPoints-1):
            self.lines.addVertex(i)
            self.lines.addVertex(i+1)
        if self.orbit.is_periodic() and self.orbit.is_closed():
            self.lines.addVertex(self.nbOfPoints-1)
            self.lines.addVertex(0)
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode(self.body.get_ascii_name() + '-orbit')
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.orbit_thickness)
        self.instance.setCollideMask(GeomNode.getDefaultCollideMask())
        self.instance.node().setPythonTag('owner', self)
        self.instance.reparentTo(self.context.annotation)
        if self.color is None:
            self.color = self.parent.get_orbit_color()
        self.instance.setColor(srgb_to_linear(self.color * self.fade))
        self.instance_ready = True
        if self.shader is None:
            self.create_shader()
        self.shader.apply(self, self.appearance)
        self.shader.update(self, self.appearance)

    def update_geom(self):
        geom = self.node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vwriter = GeomVertexRewriter(vdata, InternalName.get_vertex())
        #TODO: refactor with above code !!!
        delta = self.body.parent.get_local_position()
        if self.orbit.is_periodic():
            epoch = self.context.time.time_full - self.orbit.period
            step = self.orbit.period / (self.nbOfPoints - 1)
        else:
            #TODO: Properly calculate orbit start and end time
            epoch = self.orbit.get_time_of_perihelion() - self.orbit.period * 5.0
            step = self.orbit.period * 10.0 / (self.nbOfPoints - 1)
        for i in range(self.nbOfPoints):
            time = epoch + step * i
            pos = self.orbit.get_position_at(time) - delta
            vwriter.setData3f(*pos)

    def check_visibility(self, pixel_size):
        if self.parent.parent.visible and self.parent.shown and self.orbit:
            distance_to_obs = self.parent.distance_to_obs
            if distance_to_obs > 0.0:
                size = self.orbit.get_apparent_radius() / (distance_to_obs * pixel_size)
            else:
                size = 0.0
            self.visible = size > settings.orbit_fade
            self.fade = min(1.0, max(0.0, (size - settings.orbit_fade) / settings.orbit_fade))
            if self.color is not None and self.instance is not None:
                self.instance.setColor(srgb_to_linear(self.color * self.fade))
        else:
            self.visible = False

    def update_instance(self, camera_pos, camera_rot):
        if self.instance:
            self.place_instance_params(self.instance,
                                       self.body.parent.scene_position,
                                       self.body.parent.scene_scale_factor,
                                       LQuaternion())
            self.shader.update(self, self.appearance)

    def update_user_parameters(self):
        if self.instance is not None:
            self.update_geom()

class RotationAxis(VisibleObject):
    default_shown = False
    ignore_light = True
    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-axis')
        self.body = body

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        radius = 1.0
        top=LPoint3d(0, 0, radius * 1.25)
        north_pole=LPoint3d(0, 0, radius)
        south_pole=LPoint3d(0, 0, -radius)
        bottom=LPoint3d(0, 0, -radius * 1.25)
        self.vertexWriter.addData3f(*top)
        self.vertexWriter.addData3f(*north_pole)
        self.vertexWriter.addData3f(*south_pole)
        self.vertexWriter.addData3f(*bottom)
        self.lines = GeomLines(Geom.UHStatic)
        self.lines.addVertex(0)
        self.lines.addVertex(1)
        self.lines.addVertex(2)
        self.lines.addVertex(3)
        self.lines.closePrimitive()
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode(self.body.get_ascii_name() + '-axis')
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.axis_thickness)
        self.instance.setColor(srgb_to_linear(self.parent.get_orbit_color()))
        self.instance.reparentTo(self.context.annotation)

    def check_settings(self):
        self.set_shown(settings.show_rotation_axis)

    def check_visibility(self, pixel_size):
        if self.parent.shown:
            distance_to_obs = self.parent.distance_to_obs
            if distance_to_obs > 0.0:
                size = self.parent.get_apparent_radius() / (distance_to_obs * pixel_size)
            else:
                size = 0.0
            self.visible = size > settings.axis_fade
        else:
            self.visible = False

    def update_instance(self, camera_pos, camera_rot):
        if self.instance:
            self.place_instance(self.instance, self.parent)

    def get_scale(self):
        return self.body.surface.get_scale()

class ReferenceAxis(VisibleObject):
    default_shown = False
    ignore_light = True
    def __init__(self, body):
        VisibleObject.__init__(self, body.get_ascii_name() + '-axis')
        self.body = body
        self.model = "zup-axis"

    def check_settings(self):
        self.set_shown(settings.show_reference_axis)

    def create_instance(self):
        self.instance = load_panda_model(self.model)
        self.instance.reparentTo(self.context.annotation)
        return self.instance

    def check_visibility(self, pixel_size):
        self.visible = self.parent is not None and self.parent.shown and self.parent.visible and self.parent.resolved

    def update_instance(self, camera_pos, camera_rot):
        if self.instance:
            self.place_instance(self.instance, self.parent)

    def get_scale(self):
        return self.body.surface.get_scale() / 5.0

class Grid(VisibleObject):
    ignore_light = True
    default_shown = False
    def __init__(self, name, orientation, color):
        VisibleObject.__init__(self, name)
        self.visible = True
        self.nbOfPoints = 360
        self.nbOfRings = 17
        self.nbOfSectors = 24
        self.points_to_remove = (self.nbOfPoints // (self.nbOfRings + 1)) // 2
        self.orientation = orientation
        self.color = color
        self.settings_attr = 'show_' + name.lower() + '_grid'

    def check_settings(self):
        show = getattr(settings, self.settings_attr)
        if show is not None:
            self.set_shown(show)

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        for r in range(1, self.nbOfRings + 1):
            for i in range(self.nbOfPoints):
                angle = 2 * pi / self.nbOfPoints * i
                x = cos(angle) * sin( pi * r / (self.nbOfRings + 1) )
                y = sin(angle) * sin( pi * r / (self.nbOfRings + 1) )
                z = sin( -pi / 2 + pi * r / (self.nbOfRings + 1) )

                self.vertexWriter.addData3f((self.context.observer.infinity * x, self.context.observer.infinity * y, self.context.observer.infinity * z))
                if r == self.nbOfRings / 2 + 1:
                    self.colorwriter.addData4(srgb_to_linear((self.color.x * 1.5, 0, 0, 1)))
                else:
                    self.colorwriter.addData4(srgb_to_linear(self.color))
        for s in range(self.nbOfSectors):
            for i in range(self.points_to_remove, self.nbOfPoints // 2 - self.points_to_remove + 1):
                angle = 2 * pi / self.nbOfPoints * i
                x = cos(2*pi * s / self.nbOfSectors) * sin(angle)
                y = sin(2*pi * s / self.nbOfSectors) * sin(angle)
                z = cos(angle)

                self.vertexWriter.addData3f((self.context.observer.infinity * x , self.context.observer.infinity * y, self.context.observer.infinity * z))
                if s == 0:
                    self.colorwriter.addData4(srgb_to_linear((self.color.x * 1.5, 0, 0, 1)))
                else:
                    self.colorwriter.addData4(srgb_to_linear(self.color))
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for r in range(self.nbOfRings):
            for i in range(self.nbOfPoints-1):
                self.lines.addVertex(index)
                self.lines.addVertex(index+1)
                self.lines.closePrimitive()
                index += 1
            self.lines.addVertex(index)
            self.lines.addVertex(index - self.nbOfPoints + 1)
            self.lines.closePrimitive()
            index += 1
        for r in range(self.nbOfSectors):
            for i in range(self.nbOfPoints // 2 - self.points_to_remove * 2):
                self.lines.addVertex(index)
                self.lines.addVertex(index+1)
                self.lines.closePrimitive()
                index += 1
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("grid")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.grid_thickness)
        self.instance.reparentTo(self.context.annotation)
        self.instance.setQuat(LQuaternion(*self.orientation))

    def set_orientation(self, orientation):
        self.orientation = orientation
        if self.instance:
            self.instance.setQuat(LQuaternion(*self.orientation))

class Asterism(VisibleObject):
    def __init__(self, name):
        VisibleObject.__init__(self, name)
        self.visible = True
        self.color = bodyClasses.get_orbit_color('constellation')
        self.position = LPoint3d(0, 0, 0)
        self.segments = []
        self.position = None

    def check_settings(self):
        self.set_shown(settings.show_asterisms)

    def set_segments_list(self, segments):
        self.segments = segments
        ra_sin = 0
        ra_cos = 0
        decl = 0
        if len(self.segments) > 0 and len(self.segments[0]) > 0:
            for star in self.segments[0]:
                asc = star.orbit.get_right_asc()
                ra_sin += sin(asc)
                ra_cos += cos(asc)
                decl += star.orbit.get_declination()
            ra = atan2(ra_sin, ra_cos)
            decl /= len(self.segments[0])
            self.position = InfinitePosition(right_asc=ra, right_asc_unit=units.Rad, declination=decl, declination_unit=units.Rad)

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        #TODO: Ugly hack to calculate star position from the sun...
        old_cam_pos = self.context.observer.camera_global_pos
        self.context.observer.camera_global_pos = LPoint3d()
        center = LPoint3d()
        for segment in self.segments:
            if len(segment) < 2: continue
            for star in segment:
                #TODO: Temporary workaround to have star pos
                star.update(0, 0)
                star.update_obs(self.context.observer)
                position, distance, scale_factor = self.calc_scene_params(star.rel_position, star._position, star.distance_to_obs, star.vector_to_obs)
                self.vertexWriter.addData3f(*position)
                self.colorwriter.addData4(srgb_to_linear(self.color))
        self.context.observer.camera_global_pos = old_cam_pos
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for segment in self.segments:
            if len(segment) < 2: continue
            for i in range(len(segment)-1):
                self.lines.addVertex(index)
                self.lines.addVertex(index+1)
                self.lines.closePrimitive()
                index += 1
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("asterism")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.asterism_thickness)
        self.instance.reparentTo(self.context.annotation)
        self.instance.setBin('background', settings.asterisms_depth)
        self.instance.set_depth_write(False)

class NamedAsterism(LabelledObject):
    ignore_light = True
    default_shown = True
    background_level = settings.constellations_depth
    body_class = 'constellation'

    def __init__(self, name):
        LabelledObject.__init__(self, name)
        self.visible = True
        self.create_components()

    def create_label_instance(self):
        return BackgroundLabel(self.get_ascii_name() + '-label')

    def create_components(self):
        self.create_label()
        self.asterism = Asterism(self.get_name())
        self.add_component(self.asterism)

    def set_segments_list(self, segments):
        self.asterism.set_segments_list(segments)

    def project(self, time, center, distance):
        return self.asterism.position.project(time, center, distance)

    def get_label_text(self):
        return self.get_name()

    def get_label_color(self):
        return bodyClasses.get_label_color(self.body_class)
        
    def get_label_size(self):
        return settings.constellations_label_size
        
class Boundary(VisibleObject):
    ignore_light = True
    default_shown = True
    def __init__(self, name, points = [], color = None):
        VisibleObject.__init__(self, name)
        self.visible = True
        if color is None:
            color = bodyClasses.get_orbit_color('boundary')
        self.color = color
        self.points = points

    def check_settings(self):
        self.set_shown(settings.show_boundaries)

    def set_points_list(self, points):
        self.points = points

    def create_instance(self):
        self.vertexData = GeomVertexData('vertexData', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertexWriter = GeomVertexWriter(self.vertexData, 'vertex')
        self.colorwriter = GeomVertexWriter(self.vertexData, 'color')
        for point in self.points:
            position = point.project(0, self.context.observer.camera_global_pos, self.context.observer.infinity)
            self.vertexWriter.addData3f(*position)
            self.colorwriter.addData4(srgb_to_linear(self.color))
        self.lines = GeomLines(Geom.UHStatic)
        index = 0
        for i in range(len(self.points)-1):
            self.lines.addVertex(index)
            self.lines.addVertex(index+1)
            self.lines.closePrimitive()
            index += 1
        self.geom = Geom(self.vertexData)
        self.geom.addPrimitive(self.lines)
        self.node = GeomNode("boundary")
        self.node.addGeom(self.geom)
        self.instance = NodePath(self.node)
        self.instance.setRenderModeThickness(settings.boundary_thickness)
        self.instance.reparentTo(self.context.annotation)
        self.instance.setBin('background', settings.boundaries_depth)
        self.instance.set_depth_write(False)

class Constellation(LabelledObject):
    ignore_light = True
    default_shown = True
    background_level = settings.constellations_depth
    body_class = 'constellation'

    def __init__(self, name, center, boundary):
        LabelledObject.__init__(self, name)
        self.visible = True
        self.center = center
        self.boundary = boundary
        self.create_components()

    def create_label_instance(self):
        return BackgroundLabel(self.get_ascii_name() + '-label')

    def create_components(self):
        self.create_label()
        self.add_component(self.boundary)

    def project(self, time, center, distance):
        return self.center.project(time, center, distance)

    def get_label_text(self):
        return self.get_name()

    def get_label_color(self):
        return bodyClasses.get_label_color(self.body_class)

    def get_label_size(self):
        return settings.constellations_label_size
