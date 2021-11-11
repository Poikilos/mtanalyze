'''
Minetest
Copyright (C) 2010-2013 "celeron55" Perttu Ahola <celeron55@gmail.com>,
2021 "Poikilos" Jake Gustafson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


This file is based on
<https://github.com/minetest/minetest/blob/master/src/settings.h>
2021-11-11

C++ to Python issues:
- Name was a reference in Settings methods (impact unknown: review
  changes to the name param).

C++ to Python changes:
(this list isn't comprehensive)
- The SettingEntries type is replaced with a dict of SettingsEntry
  objects.
'''

# Old C++ imports (delete each from comment whenever replaced by Python)
'''
#include "irrlichttypes_bloated.h"
#include "util/string.h"
#include "util/basic_macros.h"

struct NoiseParams;

// Global objects
extern Settings *g_settings; // Same as Settings::getLayer(SL_GLOBAL);
extern std::string g_settings_path;

'''

from enum import Enum

U32_MAX = 0xFFFFFFFF


def is_yes(s):
    if s.lower() == "y":
        return True
    if s.lower() == "yes":
        return True
    return False


class ValueType(Enum):
    VALUETYPE_STRING = 0
    VALUETYPE_FLAG = 1  # Doesn't take any arguments


class SettingsParseEvent(Enum):
    SPE_NONE = 0
    SPE_INVALID = 1
    SPE_COMMENT = 2
    SPE_KVPAIR = 3
    SPE_END = 4
    SPE_GROUP = 5
    SPE_MULTILINE = 6


class SettingsLayer(Enum):
    '''
    Describe global setting layers.

    SL_GLOBAL -- where settings are stored
    '''
    SL_DEFAULTS = 0
    SL_GAME = 1
    SL_GLOBAL = 2
    SL_TOTAL_COUNT = 3


class SettingsHierarchy:
    '''
    This class is friends with Settings.

    Private members:
    _layers -- a list of Settings references
    '''
    def __init__(self, fallback=None):
        self._layers = None

    def __copy__(self):
        raise RuntimeError("Copying this object is not a proper usage.")
        # return None

    def __deepcopy__(self):
        raise RuntimeError("Copying this object is not a proper usage.")
        # return None

    def _getParent(self, layer):
        '''
        Get the parent Settings object using a layer number.
        '''

    def _onLayerCreated(layer, _settings):
        pass

    def _onLayerRemoved(layer):
        pass


class ValueSpec:
    '''
    Private members:
    _type -- a ValueType object
    _help -- a string (C++ type: const char*)
    '''
    def __init__(self, a_type, a_help=None):
        '''
        type -- type: ValueType
        a_help --
        '''
        if not isinstance(a_type, ValueType):
            raise TypeError("a_type must be a ValueType")
        self._type = a_type
        self._help = a_help


class SettingsEntry:
    def __init__(self, value=None, group=None):
        '''
        group -- type: Settings
        '''
        if (value is not None) and (group is not None):
            if not isinstance(group, str):
                raise TypeError("group must be a string but"
                                "is type {}".format(type(value)))
            raise ValueError("Only a value or group can be specified,"
                             " but group was {} and value was {}"
                             .format(group, value))
        if group is not None:
            if not isinstance(group, Settings):
                raise TypeError("group must be a settings object but"
                                "is type {}".format(type(group)))
            self.group = group
            self.is_group = True
        elif value is not None:
            self.value = value
            self.group = None
            self.is_group = False
        else:
            self.value = ""
            self.group = None
            self.is_group = False


SettingEntries = {}


class Settings:
    '''

    Private members:
    _m_settings -- a SettingsEntries object
    _m_callbacks -- a dict of SettingsCallbackList objects where
                    SettingsCallbackList is merely a list of
                    (SettingsChangedCallback, reference to anything)
                    tuples and SettingsChangedCallback is a (name,
                    reference to data) tuple
    _m_end_tag -- a string
    _m_callback_mutex -- C++ type: mutable std::mutex
    _m_mutex -- C++ type: mutable std::mutex
    _m_hierarchy -- a SettingsHierarchy object
    _m_settingslayer -- an int
    _s_flags -- a dictionary of FlagDesc objects
    '''
    def __init__(self, end_tag="", h=None, settings_layer=None):
        '''
        end_tag -- type: str
        settings_layer -- type: int

        (This replaces both C++ overloads of the constructor).
        '''
        self._m_settings = None
        self._m_callbacks = None
        self._m_end_tag = None
        self._m_callback_mutex = None
        self._m_hierarchy = None
        self._m_settingslayer = -1
        self._s_flags = {}
        # end C++ defaults

        self._m_end_tag = end_tag

    def __add__(self, o1, o2):
        pass

    @staticmethod
    def createLayer(sl, end_tag=""):
        '''
        sl -- type: SettingsLayer
        end_tag -- type: str
        '''

    @staticmethod
    def getLayer(sl):
        '''
        sl -- type: SettingsLayer
        '''

    def readConfigFile(self, filename):
        pass

    def updateConfigFile(self, filename):
        pass

    def parseCommandLine(self, argv, allowed_options):
        '''
        allowed_options -- dictionary of ValueSpec
        '''

    def parseConfigLines(self, ins):
        '''
        ins -- input stream (iterator)
        '''

    def writeLines(self, outs, tab_depth=0):
        '''
        Write lines to the output stream outs.
        (This should not change the object).
        '''

    def getGroup(self, name, noEx=False):
        '''
        Get a named Settings object.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def get(self, name, noEx=False):
        '''
        Get a named string setting.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getBool(self, name, noEx=False):
        '''
        Get a named boolean setting.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getInt(self, name, noEx=False):
        '''
        Get a named setting int
        (This replaces the following C++ methods: getU16, getS16,
        getU32, getS32, getU64, getU32 and *NoEx versions of those.)

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getFloat(self, name, noEx=False):
        '''
        Get a named float setting.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getV2F(self, name, noEx=False):
        '''
        Get a named float vector setting as a tuple of length 2.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getV3F(self, name, noEx=False):
        '''
        Get a named float vector setting as a tuple of length 3.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getFlagStr(self, name, flagdesc, flagmask, noEx=False):
        '''
        Get an integer based on a named FlagDesc and flagmask int.

        Like other getters, but handling each flag individually:
        1) Read default flags (or 0).
        2) Override using user-defined flags.

        Keyword arguments:
        noEx -- If True, don't raise exceptions.
        '''

    def getFlag(self, name):
        '''

        This method should raise no exceptions (to match C++ version).
        '''

    def getNoiseParams(self, name, np):
        '''
        Get a named boolean based on the given NoiseParams np.
        '''

    def getNoiseParamsFromValue(self, name, np):
        '''
        Get a named boolean based on the given NoiseParams np.
        '''

    def getNoiseParamsFromGroup(self, name, np):
        '''
        Get a named boolean based on the given NoiseParams np.
        '''

    def getNames(self):
        '''
        Get a list of names of the settings.
        '''

    def exists(self, name):
        '''
        Check if the setting exists.
        '''

    def setEntry(self, name, entry, set_group):
        '''
        Sequential arguments:
        name -- name of the setting
        entry -- any type of entry
        set_group -- True or False to set the group.
        '''
        if not isinstance(set_group, bool):
            raise ValueError("set_group must be a boolean.")
        ok = False
        return ok

    def set(self, name, value):
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(value, str):
            raise TypeError("value must be a string.")
        ok = False
        return ok

    def setDefault(self, name, value, flags=None):
        '''
        Set the default value.

        (This replaces both the regular string value and overloaded
        FlagDesc value versions of the C++ method).
        '''
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(value, str):
            if not isinstance(value, FlagDesc):
                raise TypeError("value must be a string or FlagDesc.")

    def setGroup(self, name, group):
        pass

    def setBool(self, name, value):
        if not isinstance(value, bool):
            raise ValueError("value must be a boolean.")

    def setInt(self, name, value):
        '''
        (This replaces the following C++ methods: setU16, setS16,
        setU32, setS32, setU64, setU32.)
        '''
        if not isinstance(value, int):
            raise ValueError("value must be an int.")

    def setFloat(self, name, value):
        pass

    def setV2F(self, name, value):
        '''
        Set a named tuple of length 2.
        '''
        if len(value) != 2:
            raise ValueError("setV2F requires a vector of length 2"
                             " but len({}) is {}"
                             "".format(name, len(value)))

    def setV3F(self, name, value):
        '''
        Set a named tuple of length 3.
        '''
        if len(value) != 3:
            raise ValueError("setV2F requires a vector of length 2"
                             " but len({}) is {}"
                             "".format(name, len(value)))

    def setFlagStr(self, name, flags, flagdesc=None, flagmask=U32_MAX):
        '''
        Set a named flag using the given FlagDesc.

        Sequential arguments:
        name -- the setting name
        flags -- the bitmask as an integer

        Keyword arguments:
        flagdesc -- a FlagDesc object
        flagmask -- an override for the default bitmask
        '''

    def setNoiseParams(self, name, np):
        '''
        Set a named NoiseParams object.
        '''

    def remove(self, name):
        '''
        Remove a setting.
        '''

    def getFlagDescFallback(self, name):
        '''
        Get a named FlagDesc callback object.
        '''

    def registerChangedCallback(self, name, cbf, userdata=None):
        '''
        Register SettingsChangedCallback cbf.
        '''

    def deregisterChangedCallback(self, name, cbf, userdata=None):
        '''
        Deregister (unregister) SettingsChangedCallback cbf.
        '''

    def removeSecureSettings(self):
        pass

    def getLayer(self):
        return self.m_settingslayer

    def _parseConfigObject(self, line):
        '''
        return a name, value tuple from a line
        (formerly returned values via reference)
        '''

    def _updateConfigObject(self, ins, outs, tab_depth=0):
        ok = False
        return ok

    @staticmethod
    def _checkNameValid(name):
        return False

    @staticmethod
    def _checkValueValid(value):
        return False

    @staticmethod
    def _getMultiline(ins, num_lines=None):
        return ""

    def _printEntry(self, outs, name, entry, tab_depth=0):
        '''
        Sequential arguments:
        outs -- an output stream
        entry -- a SettingsEntry object
        '''

    def _getParent(self):
        '''
        Get the parent Settings object.
        '''

    def _getEntry(self, name):
        '''
        Get a named entry.
        '''

    def updateNoLock(self, other):
        '''
        Update using another Settings object.
        '''

    def clearNoLock(self):
        pass

    def clearDefaultsNoLock(self):
        pass

    def doCallbacks(name):
        pass



