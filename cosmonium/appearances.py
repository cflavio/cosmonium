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

from panda3d.core import  Material, TextureStage, Texture, GeomNode, InternalName
from panda3d.core import TransparencyAttrib

from .textures import TextureBase, WrapperTexture, SurfaceTexture, TransparentTexture, EmissionTexture, NormalMapTexture, SpecularMapTexture, BumpMapTexture, OcclusionMapTexture
from .textures import AutoTextureSource
from .utils import TransparencyBlend
from .dircontext import defaultDirContext
from .parameters import ParametersGroup, AutoUserParameter

from . import settings

class TexturesBlock(object):
    def __init__(self):
        self.albedo = None
        self.normal = None
        self.bump = None
        self.specular = None
        self.occlusion = None
        self.emission = None
        self.albedo_alpha_specular = False
        self.textures = []
        self.textures_map = {}
        self.nb_textures = 0

    def set_target(self, panda, input_name=None):
        if input_name is None:
            for texture in self.textures:
                texture.set_target(panda)
        else:
            for texture in self.textures:
                texture_input_name = input_name + '_' + texture.category
                texture.set_target(panda, texture_input_name)

    def set_albedo(self, albedo):
        self.albedo = albedo
        self.textures.append(albedo)
        self.nb_textures += 1
        self.textures_map[albedo.category] = albedo

    def set_transparent_albedo(self, albedo):
        self.albedo = albedo
        self.textures.append(albedo)
        self.nb_textures += 1
        self.textures_map[albedo.category] = albedo

    def set_emission(self, emission):
        self.emission = emission
        self.textures.append(emission)
        self.nb_textures += 1
        self.textures_map[emission.category] = emission

    def set_normal(self, normal):
        self.normal = normal
        self.textures.append(normal)
        self.nb_textures += 1
        self.textures_map[normal.category] = normal

    def set_specular(self, specular):
        self.specular = specular
        self.textures.append(specular)
        self.nb_textures += 1
        self.textures_map[specular.category] = specular

    def set_occlusion(self, occlusion):
        self.occlusion = occlusion
        self.textures.append(occlusion)
        self.nb_textures += 1
        self.textures_map[occlusion.category] = occlusion

    def set_bump(self, bump, bump_height):
        self.bump = bump
        self.bump_height = bump_height
        self.textures.append(bump)
        self.nb_textures += 1
        self.textures_map[bump.category] = bump

class AppearanceBase:
    def __init__(self):
        self.tex_transform = False
        self.nb_textures = 0
        self.texture_index = 0
        self.normal_map_index = 0
        self.bump_map_index = 0
        self.specular_map_index = 0
        self.emission_texture_index = 0
        self.gloss_map_texture_index = 0
        self.occlusion_map_index = 0
        self.texture = None
        self.normal_map = None
        self.bump_map = None
        self.specular_map = None
        self.emission_texture = None
        self.gloss_map = None
        self.occlusion_map = None
        self.has_specular_mask = False
        self.has_occlusion_channel = False
        self.normal_map_tangent_space = False
        self.generate_binormal = False
        self.specularColor = None
        self.transparency = False
        self.transparency_level = 0.0
        self.transparency_blend = TransparencyBlend.TB_None
        self.alpha_mask = False
        self.has_vertex_color = False
        self.has_attribute_color = False
        self.has_material = False
        self.roughness = 0.0
        self.nightscale = None
        self.backlit = None
        self.shadow_normal_bias = 0.5
        self.shadow_slope_bias = 0.5
        self.shadow_depth_bias = 0.1
        self.attribution = None

    def bake(self):
        pass

    def apply_textures(self, patch):
        pass

    def apply_patch(self, patch, owner):
        pass

    def apply(self, shape, owner):
        pass

    def update_lod(self, shape, apparent_radius, distance_to_obs, pixel_size):
        pass

    def get_recommended_shape(self):
        return None

    def get_user_parameters(self):
        group = ParametersGroup("Appearance")
        parameters = []
        parameters.append(AutoUserParameter('Shadow normal bias', 'shadow_normal_bias', self, AutoUserParameter.TYPE_FLOAT, [0, 2]))
        parameters.append(AutoUserParameter('Shadow slope bias', 'shadow_slope_bias', self, AutoUserParameter.TYPE_FLOAT, [0, 2]))
        parameters.append(AutoUserParameter('Shadow depth bias', 'shadow_depth_bias', self, AutoUserParameter.TYPE_FLOAT, [0, 2]))
        group.add_parameter(ParametersGroup("Shadows", parameters))
        return group

class Appearance(AppearanceBase):
    JOB_TEXTURE_LOAD = 0x0001
    def __init__(self,
                 emissionColor=None,
                 diffuseColor=None,
                 ambientColor=None,
                 specularColor=None,
                 shininess=1.0,
                 colorScale=None,
                 transparency=False,
                 transparency_level=0.0,
                 transparency_blend=TransparencyBlend.TB_Alpha,
                 texture=None,
                 normalMap=None,
                 specularMap=None,
                 bumpMap=None,
                 bump_height = 10.0,
                 emission_texture=None,
                 tint=None,
                 srgb=None):
        AppearanceBase.__init__(self)
        self.emissionColor = emissionColor
        self.diffuseColor = diffuseColor
        self.ambientColor = ambientColor
        self.specularColor = specularColor
        self.shininess = shininess
        self.colorScale = colorScale
        if srgb is None:
            srgb = settings.srgb
        self.srgb = srgb
        if texture is not None:
            self.set_texture(texture, tint, transparency, transparency_level, transparency_blend)
        if emission_texture is not None:
            self.set_emission_texture(emission_texture, tint)
        self.set_normal_map(normalMap)
        self.set_specular_map(specularMap)
        self.set_bump_map(bumpMap, bump_height)
        self.normal_map_tangent_space = True
        self.nb_textures_coord = 0
        self.tex_transform = True
        self.has_material = True

    def set_roughness(self, roughness):
        self.roughness = roughness

    def set_nightscale(self, nightscale):
        self.nightscale = nightscale

    def set_backlit(self, backlit):
        self.backlit = backlit

    def check_specular_mask(self):
        if self.texture is not None and self.specularColor is not None:
            self.texture.check_specular_mask = True

    def check_transparency(self):
        if self.texture is not None:
            self.texture.check_transparency = True

    def bake(self):
        self.material=Material()
        if self.emissionColor != None:
            self.material.setEmission(self.emissionColor)
        if self.diffuseColor != None:
            self.material.setDiffuse(self.diffuseColor)
        if self.ambientColor != None:
            self.material.setAmbient(self.ambientColor)
        if self.specularColor != None:
            self.material.setSpecular(self.specularColor)
        if self.shininess != None:
            self.material.setShininess(self.shininess)
        self.check_specular_mask()
        self.calc_indexes()

    def set_texture(self, texture, tint=None, transparency=False, transparency_level=0.0, transparency_blend=TransparencyBlend.TB_Alpha, offset=0, context=defaultDirContext):
        if texture is not None and not isinstance(texture, TextureBase):
            if transparency:
                texture = TransparentTexture(AutoTextureSource(texture, None, context), tint, level=transparency_level, blend=transparency_blend, srgb=self.srgb)
            else:
                texture = SurfaceTexture(AutoTextureSource(texture, None, context), tint, srgb=self.srgb)
            texture.set_offset(offset)
        self.texture = texture
        self.transparency = transparency
        self.transparency_level = transparency_level
        self.transparency_blend = transparency_blend
        self.tint = tint

    def set_emission_texture(self, emission_texture, tint=None, context=defaultDirContext):
        if emission_texture is not None and not isinstance(emission_texture, TextureBase):
            emission_texture = EmissionTexture(AutoTextureSource(emission_texture, None, context), tint, srgb=self.srgb)
        self.emission_texture = emission_texture

    def set_normal_map(self, normal_map, context=defaultDirContext):
        if normal_map is not None and not isinstance(normal_map, TextureBase):
            normal_map = NormalMapTexture(AutoTextureSource(normal_map, None, context))
        self.normal_map = normal_map

    def set_specular_map(self, specular_map, context=defaultDirContext):
        if specular_map is not None and not isinstance(specular_map, TextureBase):
            specular_map = SpecularMapTexture(AutoTextureSource(specular_map, None, context))
        self.specular_map = specular_map

    def set_bump_map(self, bump_map, bump_height, context=defaultDirContext):
        if bump_map is not None and not isinstance(bump_map, TextureBase):
            bump_map = BumpMapTexture(AutoTextureSource(bump_map, None, context))
        self.bump_map = bump_map
        self.bump_height = bump_height

    def set_occlusion_map(self, occlusion_map, context=defaultDirContext):
        if occlusion_map is not None and not isinstance(occlusion_map, TextureBase):
            occlusion_map = OcclusionMapTexture(AutoTextureSource(occlusion_map, None, context))
        self.occlusion_map = occlusion_map

    def calc_indexes(self):
        self.nb_textures = 0
        self.nb_textures_coord = 0
        if self.texture is not None:
            self.texture_index = self.nb_textures
            self.nb_textures += 1
        if self.normal_map is not None:
            self.normal_map_index = self.nb_textures
            self.nb_textures += 1
        if self.bump_map is not None:
            self.bump_map_index = self.nb_textures
            self.nb_textures += 1
        if self.specularColor is not None and self.specular_map is not None:
            self.specular_map_index = self.nb_textures
            self.nb_textures += 1
        if self.emission_texture is not None:
            self.emission_texture_index = self.nb_textures
            self.nb_textures += 1
        if self.occlusion_map is not None:
            self.occlusion_map_index = self.nb_textures
            self.nb_textures += 1
        if self.nb_textures > 0:
            self.nb_textures_coord = 1

    def get_recommended_shape(self):
        if self.texture is not None and self.texture.source is not None:
            return self.texture.source.get_recommended_shape()
        else:
            return None

    def texture_loaded_cb(self, texture, patch, owner):
        shape = owner.shape
        if self.texture is not None and self.texture.check_specular_mask:
            self.has_specular_mask = self.texture.has_specular_mask
            self.texture.check_specular_mask = False
        if shape.patchable:
            #print("CB", patch.str_id(), '-', patch.jobs_pending)
            owner.jobs_done_cb(patch)
        else:
            #print("CB", shape, '-', shape.jobs_pending)
            owner.jobs_done_cb(None)

    def load_textures(self, shape, owner):
        if self.texture:
            self.texture.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.normal_map:
            self.normal_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.bump_map:
            self.bump_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.specular_map:
            self.specular_map.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.emission_texture:
            self.emission_texture.load(shape, self.texture_loaded_cb, (shape, owner))
        if self.occlusion_map:
            self.occlusion_map.load(shape, self.texture_loaded_cb, (shape, owner))

    def apply_textures(self, patch):
        patch.instance.clearTexture()
        if self.texture:
            self.has_specular_mask = self.texture.has_specular_mask
            self.texture.apply(patch)
        if self.normal_map:
            self.normal_map.apply(patch)
        if self.bump_map:
            self.bump_map.apply(patch)
        if self.specularColor is not None and self.specular_map is not None:
            self.specular_map.apply(patch)
        if self.emission_texture:
            self.emission_texture.apply(patch)
        if self.occlusion_map:
            self.occlusion_map.apply(patch)

    def apply_patch(self, patch, owner):
        if (patch.jobs & Appearance.JOB_TEXTURE_LOAD) == 0:
            #print("APPLY", patch.str_id())
            if self.nb_textures > 0:
                patch.jobs |= Appearance.JOB_TEXTURE_LOAD
                patch.jobs_pending += self.nb_textures
                self.load_textures(patch, owner)

    def apply(self, shape, owner):
        #Override any material present on the shape (use ModelAppearance to keep it)
        shape.instance.setMaterial(self.material, 1)
        if self.colorScale is not None:
            shape.instance.set_color_scale(self.colorScale)
        if shape.patchable: return
        if (shape.jobs & Appearance.JOB_TEXTURE_LOAD) == 0:
            #print("APPLY", shape, self.nb_textures)
            if self.nb_textures > 0:
                shape.jobs |= Appearance.JOB_TEXTURE_LOAD
                shape.jobs_pending += self.nb_textures
                self.load_textures(shape, owner)

class ModelAppearance(AppearanceBase):
    def __init__(self, srgb=None, vertex_color=True, attribute_color=False, material=False, occlusion_channel=False):
        AppearanceBase.__init__(self)
        self.tex_transform = False
        if srgb is None:
            srgb = settings.srgb
        self.srgb = srgb
        #TODO: Should be inferred from model
        self.has_vertex_color = vertex_color
        self.has_attribute_color = attribute_color
        self.has_material = material
        self.has_occlusion_channel = occlusion_channel
        self.offsets = None
        #TODO: This should be factored out...
        self.normal_map_tangent_space = True
        self.nb_textures_coord = 0

    def scan_model(self, instance):
        stages = instance.findAllTextureStages()
        stages.sort()
        #TODO: We assume all the geom have the same texture stage (which is obviously wrong)
        #Should be done like transparency for all the geoms and create a shader per geom...
        has_surface = False
        has_normal = False
        has_glow = False
        has_gloss = False
        for stage in stages:
            tex = instance.find_texture(stage)
            if tex:
                mode = stage.get_mode()
                #print("FOUND STAGE", stage.name, stage.sort, mode, tex)
                if mode in (TextureStage.M_modulate, TextureStage.M_modulate_glow, TextureStage.M_modulate_gloss):
                    if not has_surface:
                        self.texture = WrapperTexture(tex)
                        self.texture_index = self.nb_textures
                        self.has_specular_mask = mode == TextureStage.M_modulate_gloss
                        if self.srgb:
                            tex_format = tex.getFormat()
                            if tex_format == Texture.F_rgb:
                                tex.set_format(Texture.F_srgb)
                            elif tex_format == Texture.F_rgba:
                                tex.set_format(Texture.F_srgb_alpha)
                        self.nb_textures += 1
                        has_surface = True
                        #print("SURFACE", self.texture_index, self.texture)
                elif mode in (TextureStage.M_normal, TextureStage.M_normal_height, TextureStage.M_normal_gloss):
                    if not has_normal:
                        self.normal_map = WrapperTexture(tex)
                        self.normal_map_index = self.nb_textures
                        self.nb_textures += 1
                        has_normal = True
                        #print("NORMAL", self.normal_map_index, self.normal_map)
                elif mode in (TextureStage.M_glow, ):
                    if not has_glow:
                        self.emission_texture = WrapperTexture(tex)
                        self.emission_texture_index = self.nb_textures
                        self.nb_textures += 1
                        has_glow = True
                        #print("GLOW", self.emission_texture_index, self.emission_texture)
                elif mode in (TextureStage.M_gloss, ):
                    if not has_gloss:
                        self.gloss_map = WrapperTexture(tex)
                        self.gloss_map_texture_index = self.nb_textures
                        self.nb_textures += 1
                        has_gloss = True
                        #print("GLOSS", self.gloss_map_texture_index, self.gloss_map)
                else:
                    print("Unsupported mode %d" % mode)
        transparency_mode = TransparencyAttrib.M_none
        for np in instance.find_all_matches('**'):
            if np.has_transparency():
                if transparency_mode != TransparencyAttrib.M_none:
                    print("Overriding transparency config")
                transparency_mode = np.get_transparency()
            node = np.node()
            attrib = node.get_attrib(TransparencyAttrib)
            if attrib is not None:
                transparency_mode = attrib.get_mode()
            if isinstance(node, GeomNode):
                for geom in node.get_geoms():
                    vdata = geom.getVertexData()
                    has_tangent= vdata.has_column(InternalName.get_tangent())
                    has_binormal = vdata.has_column(InternalName.get_binormal())
                    self.generate_binormal =  has_tangent and not has_binormal
                for state in node.get_geom_states():
                    attrib = state.get_attrib(TransparencyAttrib)
                    if attrib is not None:
                        transparency_mode = attrib.get_mode()
        if transparency_mode == TransparencyAttrib.M_none:
            self.transparency = False
            self.transparency_blend = TransparencyBlend.TB_None
        elif transparency_mode == TransparencyAttrib.M_alpha:
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_Alpha
        elif transparency_mode == TransparencyAttrib.M_premultiplied_alpha:
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_PremultipliedAlpha
        elif transparency_mode == TransparencyAttrib.M_binary:
            self.transparency = True
            self.transparency_level = 0.5
            self.transparency_blend = TransparencyBlend.TB_None
        else:
            print("Unsupported transparency mode", transparency_mode)
            #Activate transparency anyway
            self.transparency = True
            self.transparency_level = 0.0
            self.transparency_blend = TransparencyBlend.TB_Alpha
        self.nb_textures_coord = 1

    def apply(self, shape, owner):
        self.scan_model(shape.instance)
