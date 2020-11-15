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

from ..systems import SimpleSystem, Barycenter
from ..bodies import Star

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser
from .utilsparser import check_parent

class SystemYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        star_system = data.get('star-system', False)
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None: return None
        orbit = OrbitYamlParser.decode(data.get('orbit'), None, parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), None, parent)
        system = SimpleSystem(translated_names, source_names, star_system=star_system, orbit=orbit, rotation=rotation)
        children = data.get('children', [])
        children = ObjectYamlParser.decode(children, system)
        for child in children:
            if isinstance(child, Star):
                system.add_child_star_fast(child)
            else:
                system.add_child_fast(child)
            system.add_child_fast(child)
        if explicit_parent:
            parent.add_child_fast(system)
            return None
        else:
            return system

class BarycenterYamlParser(YamlModuleParser):
    def decode(self, data, parent=None):
        name = data.get('name')
        (translated_names, source_names) = self.translate_names(name)
        parent_name = data.get('parent')
        parent, explicit_parent = check_parent(name, parent, parent_name)
        if parent is None: return None
        orbit = OrbitYamlParser.decode(data.get('orbit'), None, parent)
        rotation = RotationYamlParser.decode(data.get('rotation'), None, parent)
        system = Barycenter(translated_names, source_names, orbit=orbit, rotation=rotation)
        children = data.get('children', [])
        children = ObjectYamlParser.decode(children, system)
        for child in children:
            system.add_child_fast(child)
        if explicit_parent:
            parent.add_child_fast(system)
            return None
        else:
            return system

ObjectYamlParser.register_object_parser('system', SystemYamlParser())
ObjectYamlParser.register_object_parser('barycenter', BarycenterYamlParser())
