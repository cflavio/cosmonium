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

from ..astro.frame import J2000EclipticReferenceFrame, J2000HeliocentricEclipticReferenceFrame
from ..astro.frame import J2000EquatorialReferenceFrame, J2000HeliocentricEquatorialReferenceFrame
from ..astro.frame import EquatorialReferenceFrame, SynchroneReferenceFrame
from ..astro.frame import SurfaceReferenceFrame, CelestialReferenceFrame
from ..astro.frame import BodyReferenceFrame
from ..astro.frame import frames_db

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .utilsparser import AngleUnitsYamlParser

class FrameYamlParser(YamlModuleParser):
    @classmethod
    def decode_j2000_ecliptic(cls, data, parent):
        body = data.get('center', parent)
        return J2000EclipticReferenceFrame(body)

    @classmethod
    def decode_j2000_equatorial(cls, data, parent):
        body = data.get('center', parent)
        return J2000EquatorialReferenceFrame(body)

    @classmethod
    def decode_equatorial(cls, data, parent):
        body = data.get('center', parent)
        ra = data.get("ra", 0.0)
        de = data.get("de", 0.0)
        node = data.get("longitude", 0.0)
        return CelestialReferenceFrame(body, right_asc=ra, declination=de, longitude_at_node=node)

    @classmethod
    def decode_mean_equatorial(cls, data, parent):
        body = data.get('center', parent)
        return EquatorialReferenceFrame(body)

    @classmethod
    def decode_surface_frame(self, data, parent):
        long = data.get('long', 0.0)
        long_units = AngleUnitsYamlParser.decode(data.get('long-units', 'Deg'))
        lat = data.get('lat', 0.0)
        lat_units = AngleUnitsYamlParser.decode(data.get('lat-units', 'Deg'))
        return SurfaceReferenceFrame(parent, long * long_units, lat * lat_units)

    @classmethod
    def decode(self, data, parent=None):
        if data is None: return J2000EclipticReferenceFrame(parent)
        (object_type, parameters) = self.get_type_and_data(data)
        object_type = object_type.lower()
        if object_type == 'j2000ecliptic':
            return self.decode_j2000_ecliptic(parameters, parent)
        elif object_type == 'j2000equatorial':
            return self.decode_j2000_equatorial(parameters, parent )
        elif object_type == 'j2000heliocentricecliptic':
            return J2000HeliocentricEclipticReferenceFrame()
        elif object_type == 'j2000heliocentricequatorial':
            return J2000HeliocentricEquatorialReferenceFrame()
        elif object_type == 'fixed':
            return SynchroneReferenceFrame()
        elif object_type == 'surface':
            return self.decode_surface_frame(parameters, parent)
        elif object_type == 'equatorial':
            return self.decode_equatorial(parameters, parent)
        elif object_type == 'mean-equatorial':
            return self.decode_mean_equatorial(parameters, parent)
        else:
            frame = frames_db.get(object_type)
            #TODO: this should not be done arbitrarily
            if isinstance(frame, BodyReferenceFrame):
                frame.set_body(parent)
            return frame

class NamedFrameYamlParser(YamlModuleParser):
    @classmethod
    def decode(self, data, parent=None):
        name = data.get('name')
        if name is None: return None
        frame = FrameYamlParser.decode(data, None)
        frames_db.register_frame(name, frame)
        return None

ObjectYamlParser.register_object_parser('frame', NamedFrameYamlParser())
