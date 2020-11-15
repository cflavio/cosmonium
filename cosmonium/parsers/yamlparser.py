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

from ..dircontext import defaultDirContext, DirContext
from ..cache import create_path_for
from ..import settings

import os
import hashlib
import pickle
import io

import ruamel.yaml

def yaml_include(loader, node):
    print("Loading", node.value)
    filepath = node.value
    if filepath is not None:
        with io.open(filepath, encoding='utf8') as inputfile:
            data = yaml.load(inputfile)
            return data
    else:
        print("File", node.value, "not found")
        return None

#yaml.add_constructor("!include", yaml_include)

class YamlParser(object):
    def __init__(self):
        pass

    def decode(self, data):
        return None

    def encode(self, data):
        return None

    def parse(self, stream, stream_name=None):
        data = None
        try:
            yaml = ruamel.yaml.YAML(typ='safe')
            yaml.allow_duplicate_keys = True
            data = yaml.load(stream)
        except ruamel.yaml.YAMLError as e:
            if stream_name is not None:
                print("Syntax error in '%s' :" % stream_name, e)
            else:
                print("Syntax error : ", e)
        return data

    def store(self, data, stream):
        yaml = ruamel.yaml.YAML(typ='safe')
        yaml.default_flow_style = False
        yaml.dump(data, stream)

    def encode_and_store(self, filename):
        try:
            stream = open(filename, 'w')
            data = self.encode()
            self.store(data, stream)
            stream.close()
        except IOError as e:
            print("Could not write", filename, ':', e)
            return None

    def load_and_parse(self, filename):
        data = None
        try:
            text = open(filename).read()
            data = self.parse(text, filename)
            data = self.decode(data)
        except IOError as e:
            print("Could not read", filename, ':', e)
        return data

    @classmethod
    def get_type_and_data(cls, data, default=None, detect_trivial=True):
        if data is None:
            object_type = default
            object_data = {}
        elif isinstance(data, str):
            object_type = data
            object_data = {}
        else:
            if detect_trivial and len(data) == 1 and data.get('type') is None:
                object_type = list(data)[0]
                object_data = data[object_type]
            else:
                object_type = data.get('type', default)
                object_data = data
        return (object_type, object_data)

class YamlModuleParser(YamlParser):
    context = defaultDirContext
    translation = None
    app = None

    @classmethod
    def set_translation(cls, translation):
        YamlModuleParser.translation = translation

    @classmethod
    def translate_name(cls, name, context=None):
        if context is not None:
            return cls.translation.pgettext(context, name)
        else:
            return cls.translation.gettext(name)

    @classmethod
    def translate_names(cls, names, context=None):
        translated_names = []
        source_names = []
        if not isinstance(names, list):
            names = [names]
        if context is not None:
            for name in names:
                translated = cls.translation.pgettext(context, name)
                translated_names.append(translated)
                if translated != name:
                    source_names.append(name)
        else:
            for name in names:
                translated = cls.translation.gettext(name)
                translated_names.append(translated)
                if translated != name:
                    source_names.append(name)
        return (translated_names, source_names)

    def create_new_context(self, old_context, filepath):
        new_context = DirContext(old_context)
        path = os.path.dirname(filepath)
        new_context.add_all_path(path)
        for category in new_context.category_paths.keys():
            new_context.add_path(category, os.path.join(path, category))
        return new_context

    def load_from_cache(self, filename, filepath):
        data = None
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")
        if os.path.exists(cache_file):
            file_timestamp = os.path.getmtime(filepath)
            cache_timestamp = os.path.getmtime(cache_file)
            if cache_timestamp > file_timestamp:
                print("Loading %s (cached)" % filepath)
                base.splash.set_text("Loading %s (cached)" % filepath)
                try:
                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)
                except (IOError, ValueError) as e:
                    print("Could not read cache for", filename, cache_file, ':', e)
        return data

    def store_to_cache(self, data, filename, filepath):
        config_path = create_path_for('config')
        md5 = hashlib.md5(filepath.encode()).hexdigest()
        cache_file = os.path.join(config_path, md5 + ".dat")
        try:
            with open(cache_file, "wb") as f:
                print("Caching into", cache_file)
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        except IOError as e:
            print("Could not write cache for", filename, cache_file, ':', e)

    def load_and_parse(self, filename, parent=None, context=None):
        data = None
        if context is None:
            context = YamlModuleParser.context
        filepath = context.find_data(filename)
        if filepath is not None:
            saved_context = YamlModuleParser.context
            YamlModuleParser.context = self.create_new_context(context, filepath)
            if settings.cache_yaml:
                data = self.load_from_cache(filename, filepath)
            if data is None:
                print("Loading %s" % filepath)
                base.splash.set_text("Loading %s" % filepath)
                try:
                    text = io.open(filepath, encoding='utf8').read()
                    data = self.parse(text, filepath)
                except IOError as e:
                    print("Could not read", filename, filepath, ':', e)
                if settings.cache_yaml and data is not None:
                    self.store_to_cache(data, filename, filepath)
            if data is not None:
                if parent is not None:
                    data = self.decode(data, parent)
                else:
                    data =self.decode(data)
            YamlModuleParser.context = saved_context
        else:
            print("Could not find", filename)
        return data

