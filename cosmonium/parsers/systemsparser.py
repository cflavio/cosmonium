from __future__ import print_function
from __future__ import absolute_import

from ..systems import SimpleSystem, Barycenter
from ..catalogs import objectsDB

from .yamlparser import YamlModuleParser
from .objectparser import ObjectYamlParser
from .orbitsparser import OrbitYamlParser
from .rotationsparser import RotationYamlParser

class SystemYamlParser(YamlModuleParser):
    def decode(self, data):
        name = data.get('name')
        parent_name = data.get('parent')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        system = SimpleSystem(name, orbit=orbit, rotation=rotation)
        children = data.get('children', [])
        children = ObjectYamlParser.decode(children)
        for child in children:
            system.add_child_fast(child)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_fast(system)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return system

class BarycenterYamlParser(YamlModuleParser):
    def decode(self, data):
        name = data.get('name')
        parent_name = data.get('parent')
        orbit = OrbitYamlParser.decode(data.get('orbit'))
        rotation = RotationYamlParser.decode(data.get('rotation'))
        system = Barycenter(name, orbit=orbit, rotation=rotation)
        for child in data.get('children', []):
            if child is None: continue
            body = ObjectYamlParser.decode_object_dict(child)
            system.add_child_fast(body)
        if parent_name is not None:
            parent = objectsDB.get(parent_name)
            if parent is not None:
                parent.add_child_fast(system)
            else:
                print("ERROR: Parent '%s' of '%s' not found" % (parent_name, name))
            return None
        else:
            return system

ObjectYamlParser.register_object_parser('system', SystemYamlParser())
ObjectYamlParser.register_object_parser('barycenter', BarycenterYamlParser())