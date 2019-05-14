from __future__ import print_function

from ..patchedshapes import SquarePatchBase, NormalizedSquareShape
from .. import geometry

class SpaceEngineTextureSquarePatch(SquarePatchBase):
    xy_params = [
                 {'x_inverted':False, 'y_inverted':False, 'xy_swap':True}, #Right
                 {'x_inverted':True, 'y_inverted':True, 'xy_swap':True}, #left
                 {'x_inverted':False, 'y_inverted':True, 'xy_swap':False}, #Back
                 {'x_inverted':True, 'y_inverted':False, 'xy_swap':False}, #Face
                 {'x_inverted':True, 'y_inverted':False, 'xy_swap':False}, #Top
                 {'x_inverted':True, 'y_inverted':False, 'xy_swap':False} #bottom
             ]

    def __init__(self, *args, **kwargs):
        SquarePatchBase.__init__(self, *args, **kwargs)
        self.inv_u = self.xy_params[self.face]['x_inverted']
        self.inv_v = self.xy_params[self.face]['y_inverted']
        self.swap_uv = self.xy_params[self.face]['xy_swap']

    def face_normal(self, x, y):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchNormal(float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div)

    def create_bounding_volume(self, x, y, offset):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchAABB(self.geom_scale,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div,
                                                  offset=offset)

    def create_centre(self, x, y, offset):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatchPoint(self.geom_scale,
                                                  0.5, 0.5,
                                                  float(x) / self.div,
                                                  float(y) / self.div,
                                                  float(x + 1) / self.div,
                                                  float(y + 1) / self.div,
                                                  offset)

    def create_patch_instance(self, x, y):
        (x, y) = self.calc_xy(x, y)
        return geometry.NormalizedSquarePatch(self.geom_scale,
                                              self.density,
                                              float(x) / self.div,
                                              float(y) / self.div,
                                              float(x + 1) / self.div,
                                              float(y + 1) / self.div,
                                              offset=self.offset)

    def calc_xy(self, x, y):
        if self.xy_params[self.face]['xy_swap']:
            x, y = y, x
        if self.xy_params[self.face]['x_inverted']:
            x = self.div - x - 1
        if self.xy_params[self.face]['y_inverted']:
            y = self.div - y - 1
        return x, y

class SpaceEnginePatchedSquareShape(NormalizedSquareShape):
    def __init__(self, *args, **kwargs):
        NormalizedSquareShape.__init__(*args, **kwargs)
        self.face_unique = True

    def create_patch(self, parent, lod, face, x, y, average_height=1.0):
        density = self.lod_control.get_density_for(lod)
        patch = SpaceEngineTextureSquarePatch(face, x, y, parent, lod, density, self.radius, average_height, self.use_shader, self.use_tesselation)
        #TODO: Temporary or make right
        patch.owner = self
        return patch