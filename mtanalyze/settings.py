#!/usr/bin/env python
# mtanalyze: module for using minetest data
# Copyright (C) 2022 Jake Gustafson

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

# TODO: read settingtypes.txt files (and cache them):
'''
Read settingtypes.txt files where each non-commented line is formatted
like: `<source>name (Readable name) type type_args</source>`
(See minetest/builtin/settingtypes.txt).
Terms specific to this implementation:
- The "default_default" is a default that is set if no default is
  specified by the settingtypes.txt.
- "<type>,..." means more than one value separated by commas but no
  spaces (where type is string or some other type).
- "default", "min", and "max" always take the format of the
  setting_params key which can be found in setting_formats.
  - Any other param's value can be looked up in setting_formats
    directly.

For a more complete implementation of Minetest settings, see
<https://github.com/poikilos/voxboxor>
'''
setting_formats = {
    "possible_flags": "<string>,...",
    "values": "<string>,...",
    "noise_params_2d": "<offset>, <scale>, (<spreadX>, <spreadY>, <spreadZ>), <seed>, <octaves>, <persistence>, <lacunarity>[, <default flags>]",
    "v3f": "<float>,<float>,<float>",
}
setting_formats["noise_params_3d"] = setting_formats["noise_params_2d"]

setting_params = {
    "int": {
        'overloads': [['default'], ['default', 'min', 'max']],
    },
    "string": {
        'overloads': [['default']],
        'default_default': "",
    },
    "bool": {
        'overloads': [['default']],
    },
    "float": {
        'overloads': [['default'], ['default', 'min', 'max']],
    },
    "enum": {
        'overloads': [['default', 'values']],
    },
    "path": {
        'overloads': [['default']],
        'default_default': "",
    },
    "filepath": {
        'overloads': [['default']],
        'default_default': "",
    },
    "key": {
        'overloads': [['default']],
    },
    "flags": {
        'overloads': [['default', 'possible_flags']],
    },
    "noise_params_2d": {
        'overloads': [['default']],
    },
    "noise_params_3d": {
        'overloads': [['default']],
    },
    "v3f": {
        'overloads': [['default']],
    },
}
settingtypes = {}
