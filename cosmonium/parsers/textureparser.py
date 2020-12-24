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

from panda3d.core import LColor

from ..procedural.texturecontrol import HeightTextureControl, HeightTextureControlEntry, SimpleTextureControl,\
    SlopeTextureControl, SlopeTextureControlEntry,\
    BiomeControl, BiomeTextureControlEntry, HeightColorMap, ColormapLayer
from ..procedural.texturecontrol import MixTextureControl
from ..procedural.appearances import TexturesDictionary, TextureTilingMode
from ..procedural.shaders import TextureDictionaryDataSource
from ..astro import units

from ..textures import AutoTextureSource
from ..textures import TransparentTexture, SurfaceTexture,  EmissionTexture, NormalMapTexture, SpecularMapTexture, BumpMapTexture, OcclusionMapTexture
from ..appearances import TexturesBlock

from .utilsparser import DistanceUnitsYamlParser
from .yamlparser import YamlParser, YamlModuleParser

class HeightColorControlYamlParser(YamlParser):
    def __init__(self):
        YamlParser.__init__(self)
        self.colormap_id = 0
        self.percentage = False
        self.float_values = False
        self.height_scale = 0.0
        self.height_offset = 0.0

    def decode_height_layer(self, data):
        height = data.get("height", 0.0)
        if not self.percentage:
            height_units = DistanceUnitsYamlParser.decode(data.get("height-units"), units.m)
            height *= height_units
        bottom = data.get("bottom", None)
        top = data.get("top", [0, 0, 0])
        if bottom is not None:
            if not self.float_values:
                bottom = LColor(bottom[0] / 255.0, bottom[1] / 255.0, bottom[2] / 255.0, 1.0)
            else:
                bottom = LColor(bottom[0], bottom[1], bottom[2], 1.0)
        if not self.float_values:
            top = LColor(top[0] / 255.0, top[1] / 255.0, top[2] / 255.0, 1.0)
        else:
            top = LColor(top[0], top[1], top[2], 1.0)
        return ColormapLayer(height * self.height_scale - self.height_offset, bottom, top)

    def decode_height_control(self, data):
        self.colormap_id += 1
        entries = []
        for entry in data:
            entries.append(self.decode_height_layer(entry))
        return HeightColorMap('colormap_%d' % self.colormap_id, entries)

    def decode(self, data, heightmap, radius=1.0):
        entries = data.get('entries', [])
        self.percentage = data.get('percentage', False)
        self.float_values = data.get('float', False)
        if self.percentage:
            self.height_scale = 1.0 / (heightmap.max_height - heightmap.min_height) / radius
            self.height_offset = heightmap.min_height * self.height_scale
        else:
            self.height_scale = 1.0 / radius
            self.height_offset = 0.0
        return self.decode_height_control(entries)

class MixTextureControlYamlParser(YamlParser):
    def __init__(self):
        YamlParser.__init__(self)
        self.slope_id = 0
        self.height_id = 0
        self.height_scale = 0.0

    def decode_height_entry(self, data):
        entry = self.decode_entry(data.get('entry'))
        height = data.get("height", 0.0)
        height_units = DistanceUnitsYamlParser.decode(data.get("height-units"), units.m)
        height *= height_units
        blend = data.get("blend", 0.0)
        blend *= height_units
        return HeightTextureControlEntry(entry, height * self.height_scale, blend * self.height_scale)

    def decode_height_control(self, data):
        self.height_id += 1
        entries = []
        for entry in data:
            entries.append(self.decode_height_entry(entry))
        return HeightTextureControl('height_%d' % self.height_id, entries)

    def decode_slope_entry(self, data):
        entry = self.decode_entry(data.get('entry'))
        angle = data.get("angle", 0.0)
        blend = data.get("blend", 0.0)
        return SlopeTextureControlEntry(entry, angle, blend)

    def decode_slope_control(self, data):
        self.slope_id += 1
        entries = []
        for entry in data:
            entries.append(self.decode_slope_entry(entry))
        return SlopeTextureControl('slope_%d' % self.slope_id, entries)

    def decode_biome_entry(self, data):
        entry = self.decode_entry(data.get('entry'))
        value = data.get("value", 0.0)
        blend = data.get("blend", 1.0)
        return BiomeTextureControlEntry(entry, value, blend)

    def decode_biome_control(self, data):
        entries = []
        for entry in data:
            entries.append(self.decode_biome_entry(entry))
        return BiomeControl('dummy', 'biome', entries) #TODO: make biome source configurable

    def decode_entry(self, data):
        if isinstance(data, str):
            return SimpleTextureControl(data)
        else:
            entry_type = list(data)[0]
            entry = data[entry_type]
            if entry_type == 'height':
                return self.decode_height_control(entry)
            elif entry_type == 'slope':
                return self.decode_slope_control(entry)
            elif entry_type == 'biome':
                return self.decode_biome_control(entry)
            else:
                return None

    def decode(self, data, heightmap, radius=1.0):
        self.height_scale = 1.0 / radius
        entry = self.decode_entry(data)
        #TODO: get or generate name
        return MixTextureControl("control", entry)

class TextureControlYamlParser(YamlModuleParser):
    def decode(self, data, appearance, heightmap, radius=1.0):
        if data is None: return None
        control_type = data.get('type', 'textures')
        if control_type == 'textures':
            control_parser = MixTextureControlYamlParser()
            control = control_parser.decode(data, heightmap, radius)
            appearance_source = TextureDictionaryDataSource(appearance)
        elif control_type == 'colormap':
            control_parser = HeightColorControlYamlParser()
            control = control_parser.decode(data, heightmap, radius)
            appearance_source = None
        else:
            print("Unknown control type '%s'" % control_type)
            control = None
            appearance_source = None
        return (control, appearance_source)

class TextureTilingYamlParser(YamlModuleParser):
    @classmethod
    def decode(cls, data):
        (object_type, object_data) = cls.get_type_and_data(data, 'default')
        if object_type == 'default':
            return TextureTilingMode.F_none
        elif object_type == 'hash':
            return TextureTilingMode.F_hash
        else:
            print("Unknown tiling type '%s'" % object_type)
            return TextureTilingMode.F_none

class TextureDictionaryYamlParser(YamlModuleParser):
    @classmethod
    def decode_texture_albedo(self, data, srgb):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            srgb = data.get('srgb', srgb)
            albedo = SurfaceTexture(texture_source, srgb)
        else:
            albedo = None
        return albedo

    @classmethod
    def decode_texture_normal(self, data):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            normal = NormalMapTexture(texture_source)
        else:
            normal = None
        return normal

    @classmethod
    def decode_texture_occlusion(self, data):
        if data is not None:
            if isinstance(data, str):
                texture_source = AutoTextureSource(data, context=YamlModuleParser.context)
                data = {}
            else:
                texture_source = AutoTextureSource(data.get('file'), context=YamlModuleParser.context)
            occlusion = OcclusionMapTexture(texture_source)
        else:
            occlusion = None
        return occlusion

    @classmethod
    def decode_textures_dictionary_entry(self, data, srgb):
        entry = TexturesBlock()
        if isinstance(data, str):
            albedo = self.decode_texture_albedo(data, srgb)
            entry.set_albedo(albedo)
        else:
            albedo = self.decode_texture_albedo(data.get('albedo'), srgb)
            if albedo is not None:
                entry.set_albedo(albedo)
            normal = self.decode_texture_normal(data.get('normal'))
            if normal is not None:
                entry.set_normal(normal)
            occlusion = self.decode_texture_occlusion(data.get('occlusion'))
            if occlusion is not None:
                entry.set_occlusion(occlusion)
        return entry

    @classmethod
    def decode_textures_dictionary(cls, data):
        entries = {}
        srgb = data.get('srgb')
        for (name, entry) in data.get('entries', {}).items():
            entries[name] = cls.decode_textures_dictionary_entry(entry, srgb)
        scale = data.get('scale')
        tiling = TextureTilingYamlParser.decode(data.get('tiling'))
        return TexturesDictionary(entries, scale, tiling, context=YamlModuleParser.context)

    @classmethod
    def decode(cls, data):
        entry_type = list(data)[0]
        entry = data[entry_type]
        if entry_type == 'textures':
            return cls.decode_textures_dictionary(entry)
        else:
            return None
