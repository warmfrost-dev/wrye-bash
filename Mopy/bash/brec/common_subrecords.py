# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2020 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================
"""Builds on the basic elements defined in base_elements.py to provide
definitions for some commonly needed subrecords."""

from __future__ import division, print_function
import struct
from collections import defaultdict
from itertools import product

from .advanced_elements import AttrValDecider, MelArray, MelTruncatedStruct, \
    MelUnion, PartialLoadDecider
from .basic_elements import MelBase, MelFid, MelGroup, MelGroups, MelLString, \
    MelNull, MelSequential, MelString, MelStruct, MelUInt32, MelOptStruct
from .utils_constants import _int_unpacker, FID, null1, null2, null3, null4
from ..bolt import Flags, encode, struct_pack, struct_unpack

#------------------------------------------------------------------------------
def mel_cdta_unpackers(sizes_list, pad=u'I'): ##: see if MelUnion can't do this better
    """Return compiled structure objects for each combination of size and
    condition value (?).

    :rtype: dict[unicode, struct.Struct]"""
    sizes_list = sorted(sizes_list)
    _formats = {u'11': u'II', u'10': u'Ii', u'01': u'iI', u'00': u'ii'}
    _formats = {u'%s%d' % (k, s): u'%s%s' % (
        f, u''.join([pad] * ((s - sizes_list[0]) // 4))) for (k, f), s in
                product(_formats.items(), sizes_list)}
    _formats = {k: struct.Struct(v) for (k, v) in _formats.items()}
    return _formats

#------------------------------------------------------------------------------
class MelBounds(MelGroup):
    """Wrapper around MelGroup for the common task of defining OBND - Object
    Bounds. Uses MelGroup to avoid merging them when importing."""
    def __init__(self):
        MelGroup.__init__(self, 'bounds',
            MelStruct('OBND', '=6h', 'boundX1', 'boundY1', 'boundZ1',
                      'boundX2', 'boundY2', 'boundZ2')
        )

#------------------------------------------------------------------------------
class MelCtda(MelUnion):
    """Handles a condition. The difficulty here is that the type of its
    parameters depends on its function index. We handle it by building what
    amounts to a decision tree using MelUnions."""
    # 0 = Unknown/Ignored, 1 = Int, 2 = FormID, 3 = Float
    _param_types = {0: u'4s', 1: u'i', 2: u'I', 3: u'f'}
    # This technically a lot more complex (the highest three bits also encode
    # the comparison operator), but we only care about use_global, so we can
    # treat the rest as unknown flags and just carry them forward
    _ctda_type_flags = Flags(0, Flags.getNames(
        u'do_or', u'use_aliases', u'use_global', u'use_packa_data',
        u'swap_subject_and_target'))

    def __init__(self, ctda_sub_sig=b'CTDA', suffix_fmt=u'',
                 suffix_elements=[], old_suffix_fmts=set()):
        """Creates a new MelCtda instance with the specified properties.

        :param ctda_sub_sig: The signature of this subrecord. Probably
            b'CTDA'.
        :param suffix_fmt: The struct format string to use, starting after the
            first two parameters.
        :param suffix_elements: The struct elements to use, starting after the
            first two parameters.
        :param old_suffix_fmts: A set of old versions to pass to
            MelTruncatedStruct. Must conform to the same syntax as suffix_fmt.
            May be empty.
        :type old_versions: set[unicode]"""
        from .. import bush
        super(MelCtda, self).__init__({
            # Build a (potentially truncated) struct for each function index
            func_index: self._build_struct(func_data, ctda_sub_sig, suffix_fmt,
                                           suffix_elements, old_suffix_fmts)
            for func_index, func_data
            in bush.game.condition_function_data.iteritems()
        }, decider=PartialLoadDecider(
            # Skip everything up to the function index in one go, we'll be
            # discarding this once we rewind anyways.
            loader=MelStruct(ctda_sub_sig, u'8sH', u'ctda_ignored', u'ifunc'),
            decider=AttrValDecider(u'ifunc'),
        ))

    # Helper methods - Note that we skip func_data[0]; the first element is
    # the function name, which is only needed for puny human brains
    def _build_struct(self, func_data, ctda_sub_sig, suffix_fmt,
                      suffix_elements, old_suffix_fmts):
        """Builds up a struct from the specified jungle of parameters. Mostly
        inherited from __init__, see there for docs."""
        # The '4s' here can actually be a float or a FormID. We do *not* want
        # to handle this via MelUnion, because the deep nesting is going to
        # cause exponential growth and bring PBash down to a crawl.
        prefix_fmt = u'B3s4sH2s' + (u'%s' * len(func_data[1:]))
        prefix_elements = [(self._ctda_type_flags, u'operFlag'),
                           (u'unused1', null3), u'compValue',
                           u'ifunc', (u'unused2', null2)]
        # Builds an argument tuple to use for formatting the struct format
        # string from above plus the suffix we got passed in
        fmt_list = tuple([self._param_types[func_param]
                          for func_param in func_data[1:]])
        full_old_versions = {(prefix_fmt + f) % fmt_list
                             for f in old_suffix_fmts}
        shared_params = ([ctda_sub_sig, (prefix_fmt + suffix_fmt) % fmt_list] +
                         self._build_params(func_data, prefix_elements,
                                            suffix_elements))
        # Only use MelTruncatedStruct if we have old versions, save the
        # overhead otherwise
        if old_suffix_fmts:
            return MelTruncatedStruct(*shared_params,
                                      old_versions=full_old_versions)
        return MelStruct(*shared_params)

    def _build_params(self, func_data, prefix_elements, suffix_elements):
        """Builds a list of struct elements to pass to MelTruncatedStruct."""
        # First, build up a list of the parameter elemnts to use
        func_elements = [
            (FID, u'param%u' % i) if func_param == 2 else u'param%u' % i
            for i, func_param in enumerate(func_data[1:], start=1)]
        # Then, combine the suffix, parameter and suffix elements
        return prefix_elements + func_elements + suffix_elements

    # Nesting workarounds -----------------------------------------------------
    # To avoid having to test MelUnions too deply - hurts performance even
    # further (see below) plus grows exponentially
    def loadData(self, record, ins, sub_type, size_, readId):
        super(MelCtda, self).loadData(record, ins, sub_type, size_, readId)
        # See _build_struct comments above for an explanation of this
        record.compValue = struct_unpack(u'fI'[record.operFlag.use_global],
                                         record.compValue)[0]

    def mapFids(self, record, function, save=False):
        super(MelCtda, self).mapFids(record, function, save)
        if record.operFlag.use_global:
            new_comp_val = function(record.compValue)
            if save: record.compValue = new_comp_val

    def dumpData(self, record, out):
        # See _build_struct comments above for an explanation of this
        record.compValue = struct_pack(u'fI'[record.operFlag.use_global],
                                       record.compValue)
        super(MelCtda, self).dumpData(record, out)

    # Some small speed hacks --------------------------------------------------
    # To avoid having to ask 100s of unions to each set their defaults,
    # declare they have fids, etc. Wastes a *lot* of time.
    def hasFids(self, formElements):
        self.fid_elements = self.element_mapping.values()
        formElements.add(self)

    def getLoaders(self, loaders):
        loaders[next(self.element_mapping.itervalues()).subType] = self

    def getSlotsUsed(self):
        return (self.decider_result_attr,) + next(
            self.element_mapping.itervalues()).getSlotsUsed()

    def setDefault(self, record):
        next(self.element_mapping.itervalues()).setDefault(record)

class MelCtdaFo3(MelCtda):
    """Version of MelCtda that handles the additional complexities that were
    introduced for in FO3 (and present in all games after that):

    1. The 'reference' element is a FormID if runOn is 2, otherwise it is an
    unused uint32. Except for the FNV functions IsFacingUp and IsLeftUp, where
    it is never a FormID. Yup.
    2. The 'GetVATSValue' function is horrible. The type of its second
    parameter depends on the value of the first one. And of course it can be a
    FormID."""
    # Maps param #1 value to the struct format string to use for GetVATSValue's
    # param #2 - missing means unknown/unused, aka 4s
    # Note 18, 19 and 20 were introduced in Skyrim, but since they are not used
    # in FO3 it's no problem to just keep them here
    _vats_param2_fmt = defaultdict(lambda: u'4s', {
        0: u'I', 1: u'I', 2: u'I', 3: u'I', 5: u'i', 6: u'I', 9: u'I',
        10: u'I', 15: u'I', 18: u'I', 19: u'I', 20: u'I'})
    # The param #1 values that indicate param #2 is a FormID
    _vats_param2_fid = {0, 1, 2, 3, 9, 10}

    def __init__(self, suffix_fmt=u'', suffix_elements=[],
                 old_suffix_fmts=set()):
        super(MelCtdaFo3, self).__init__(suffix_fmt=suffix_fmt,
                                         suffix_elements=suffix_elements,
                                         old_suffix_fmts=old_suffix_fmts)
        from .. import bush
        self._getvatsvalue_ifunc = bush.game.getvatsvalue_index
        self._ignore_ifuncs = ({106, 285} if bush.game.fsName == u'FalloutNV'
                               else set()) # 106 == IsFacingUp, 285 == IsLeftUp

    def loadData(self, record, ins, sub_type, size_, readId):
        super(MelCtdaFo3, self).loadData(record, ins, sub_type, size_, readId)
        if record.ifunc == self._getvatsvalue_ifunc:
            record.param2 = struct_unpack(self._vats_param2_fmt[record.param1],
                                          record.param2)[0]

    def mapFids(self, record, function, save=False):
        super(MelCtdaFo3, self).mapFids(record, function, save)
        if record.runOn == 2 and record.ifunc not in self._ignore_ifuncs:
            new_reference = function(record.reference)
            if save: record.reference = new_reference
        if (record.ifunc == self._getvatsvalue_ifunc and
                record.param1 in self._vats_param2_fid):
            new_param2 = function(record.param2)
            if save: record.param2 = new_param2

    def dumpData(self, record, out):
        if record.ifunc == self._getvatsvalue_ifunc:
            record.param2 = struct_pack(self._vats_param2_fmt[record.param1],
                                        record.param2)
        super(MelCtdaFo3, self).dumpData(record, out)

#------------------------------------------------------------------------------
class MelReferences(MelGroups):
    """Handles mixed sets of SCRO and SCRV for scripts, quests, etc."""
    def __init__(self):
        MelGroups.__init__(self, 'references', MelUnion({
            'SCRO': MelFid('SCRO', 'reference'),
            'SCRV': MelUInt32('SCRV', 'reference'),
        }))

#------------------------------------------------------------------------------
class MelCoordinates(MelTruncatedStruct):
    """Skip dump if we're in an interior."""
    def dumpData(self, record, out):
        if not record.flags.isInterior:
            MelTruncatedStruct.dumpData(self, record, out)

#------------------------------------------------------------------------------
class MelColorInterpolator(MelArray):
    """Wrapper around MelArray that defines a time interpolator - an array
    of five floats, where each entry in the array describes a point on a curve,
    with 'time' as the X axis and 'red', 'green', 'blue' and 'alpha' as the Y
    axis."""
    def __init__(self, sub_type, attr):
        MelArray.__init__(self, attr,
            MelStruct(sub_type, '5f', 'time', 'red', 'green', 'blue', 'alpha'),
        )

#------------------------------------------------------------------------------
# xEdit calls this 'time interpolator', but that name doesn't really make sense
# Both this class and the color interpolator above interpolate over time
class MelValueInterpolator(MelArray):
    """Wrapper around MelArray that defines a value interpolator - an array
    of two floats, where each entry in the array describes a point on a curve,
    with 'time' as the X axis and 'value' as the Y axis."""
    def __init__(self, sub_type, attr):
        MelArray.__init__(self, attr,
            MelStruct(sub_type, '2f', 'time', 'value'),
        )

#------------------------------------------------------------------------------
class MelEdid(MelString):
    """Handles an Editor ID (EDID) subrecord."""
    def __init__(self):
        MelString.__init__(self, 'EDID', 'eid')

#------------------------------------------------------------------------------
class MelFull(MelLString):
    """Handles a name (FULL) subrecord."""
    def __init__(self):
        MelLString.__init__(self, 'FULL', 'full')

#------------------------------------------------------------------------------
class MelIcons(MelSequential):
    """Handles icon subrecords. Defaults to ICON and MICO, with attribute names
    'iconPath' and 'smallIconPath', since that's most common."""
    def __init__(self, icon_attr='iconPath', mico_attr='smallIconPath',
                 icon_sig='ICON', mico_sig='MICO'):
        """Creates a new MelIcons with the specified attributes.

        :param icon_attr: The attribute to use for the ICON subrecord. If
            falsy, this means 'do not include an ICON subrecord'.
        :param mico_attr: The attribute to use for the MICO subrecord. If
            falsy, this means 'do not include a MICO subrecord'."""
        final_elements = []
        if icon_attr: final_elements += [MelString(icon_sig, icon_attr)]
        if mico_attr: final_elements += [MelString(mico_sig, mico_attr)]
        MelSequential.__init__(self, *final_elements)

class MelIcons2(MelIcons):
    """Handles ICO2 and MIC2 subrecords. Defaults to attribute names
    'femaleIconPath' and 'femaleSmallIconPath', since that's most common."""
    def __init__(self, ico2_attr='femaleIconPath',
                 mic2_attr='femaleSmallIconPath'):
        MelIcons.__init__(self, icon_attr=ico2_attr, mico_attr=mic2_attr,
                          icon_sig='ICO2', mico_sig='MIC2')

class MelIcon(MelIcons):
    """Handles a standalone ICON subrecord, i.e. without any MICO subrecord."""
    def __init__(self, icon_attr='iconPath'):
        MelIcons.__init__(self, icon_attr=icon_attr, mico_attr='')

class MelIco2(MelIcons2):
    """Handles a standalone ICO2 subrecord, i.e. without any MIC2 subrecord."""
    def __init__(self, ico2_attr):
        MelIcons2.__init__(self, ico2_attr=ico2_attr, mic2_attr='')

#------------------------------------------------------------------------------
class MelWthrColors(MelStruct):
    """Used in WTHR for PNAM and NAM0 for all games but FNV."""
    def __init__(self, wthr_sub_sig):
        MelStruct.__init__(
            self, wthr_sub_sig, '3Bs3Bs3Bs3Bs', 'riseRed', 'riseGreen',
            'riseBlue', ('unused1', null1), 'dayRed', 'dayGreen',
            'dayBlue', ('unused2', null1), 'setRed', 'setGreen', 'setBlue',
            ('unused3', null1), 'nightRed', 'nightGreen', 'nightBlue',
            ('unused4', null1))

#------------------------------------------------------------------------------
# Oblivion and Fallout --------------------------------------------------------
#------------------------------------------------------------------------------
class MelRaceParts(MelNull):
    """Handles a subrecord array, where each subrecord is introduced by an
    INDX subrecord, which determines the meaning of the subrecord. The
    resulting attributes are set directly on the record.
    :type _indx_to_loader: dict[int, MelBase]"""
    def __init__(self, indx_to_attr, group_loaders):
        """Creates a new MelRaceParts element with the specified INDX mapping
        and group loaders.

        :param indx_to_attr: A mapping from the INDX values to the final
            record attributes that will be used for the subsequent
            subrecords.
        :type indx_to_attr: dict[int, str]
        :param group_loaders: A callable that takes the INDX value and
            returns an iterable with one or more MelBase-derived subrecord
            loaders. These will be loaded and dumped directly after each
            INDX."""
        self._last_indx = None # used during loading
        self._indx_to_attr = indx_to_attr
        # Create loaders for use at runtime
        self._indx_to_loader = {
            part_indx: MelGroup(part_attr, *group_loaders(part_indx))
            for part_indx, part_attr in indx_to_attr.iteritems()
        }
        self._possible_sigs = {s for element
                               in self._indx_to_loader.itervalues()
                               for s in element.signatures}

    def getLoaders(self, loaders):
        temp_loaders = {}
        for element in self._indx_to_loader.itervalues():
            element.getLoaders(temp_loaders)
        for signature in temp_loaders.keys():
            loaders[signature] = self

    def getSlotsUsed(self):
        return self._indx_to_attr.values()

    def setDefault(self, record):
        for element in self._indx_to_loader.itervalues():
            element.setDefault(record)

    def loadData(self, record, ins, sub_type, size_, readId,
                 __unpacker=_int_unpacker):
        if sub_type == 'INDX':
            self._last_indx, = ins.unpack(__unpacker, size_, readId)
        else:
            self._indx_to_loader[self._last_indx].loadData(
                record, ins, sub_type, size_, readId)

    def dumpData(self, record, out):
        for part_indx, part_attr in self._indx_to_attr.iteritems():
            if hasattr(record, part_attr): # only dump present parts
                out.packSub('INDX', '=I', part_indx)
                self._indx_to_loader[part_indx].dumpData(record, out)

    @property
    def signatures(self):
        return self._possible_sigs

#------------------------------------------------------------------------------
class MelRaceVoices(MelStruct):
    """Set voices to zero, if equal race fid. If both are zero, then skip
    dumping."""
    def dumpData(self, record, out):
        if record.maleVoice == record.fid: record.maleVoice = 0
        if record.femaleVoice == record.fid: record.femaleVoice = 0
        if (record.maleVoice, record.femaleVoice) != (0, 0):
            MelStruct.dumpData(self, record, out)

#------------------------------------------------------------------------------
class MelScriptVars(MelGroups):
    """Handles SLSD and SCVR combos defining script variables."""
    _var_flags = Flags(0, Flags.getNames('is_long_or_short'))

    def __init__(self):
        MelGroups.__init__(self, 'script_vars',
            MelStruct('SLSD', 'I12sB7s', 'var_index',
                      ('unused1', null4 + null4 + null4),
                      (self._var_flags, 'var_flags', 0),
                      ('unused2', null4 + null3)),
            MelString('SCVR', 'var_name'),
        )

#------------------------------------------------------------------------------
# Skyrim and Fallout ----------------------------------------------------------
#------------------------------------------------------------------------------
class MelMODS(MelBase):
    """MODS/MO2S/etc/DMDS subrecord"""
    def hasFids(self,formElements):
        formElements.add(self)

    def setDefault(self,record):
        record.__setattr__(self.attr,None)

    def loadData(self, record, ins, sub_type, size_, readId,
                 __unpacker=_int_unpacker):
        insUnpack = ins.unpack
        insRead32 = ins.readString32
        count, = insUnpack(__unpacker, 4, readId)
        data = []
        dataAppend = data.append
        for x in xrange(count):
            string = insRead32(readId)
            fid = ins.unpackRef()
            index, = insUnpack(__unpacker, 4, readId)
            dataAppend((string,fid,index))
        record.__setattr__(self.attr,data)

    def dumpData(self,record,out):
        data = record.__getattribute__(self.attr)
        if data is not None:
            data = record.__getattribute__(self.attr)
            outData = struct_pack('I', len(data))
            for (string,fid,index) in data:
                outData += struct_pack('I', len(string))
                outData += encode(string)
                outData += struct_pack('=2I', fid, index)
            out.packSub(self.subType,outData)

    def mapFids(self,record,function,save=False):
        attr = self.attr
        data = record.__getattribute__(attr)
        if data is not None:
            data = [(string,function(fid),index) for (string,fid,index) in record.__getattribute__(attr)]
            if save: record.__setattr__(attr,data)

#------------------------------------------------------------------------------
class MelRegnEntrySubrecord(MelUnion):
    """Wrapper around MelUnion to correctly read/write REGN entry data.
    Skips loading and dumping if entryType != entry_type_val.

    entry_type_val meanings:
      - 2: Objects
      - 3: Weather
      - 4: Map
      - 5: Land
      - 6: Grass
      - 7: Sound
      - 8: Imposter (FNV only)"""
    def __init__(self, entry_type_val, element):
        """:type entry_type_val: int"""
        MelUnion.__init__(self, {
            entry_type_val: element,
        }, decider=AttrValDecider('entryType'),
            fallback=MelNull('NULL')) # ignore

#------------------------------------------------------------------------------
class MelRef3D(MelStruct):
    """3D position and rotation for a reference record (REFR, ACHR, etc.)."""
    def __init__(self):
        super(MelRef3D, self).__init__(
            b'DATA', u'6f', u'ref_pos_x', u'ref_pos_y', u'ref_pos_z',
            u'ref_rot_x', u'ref_rot_y', u'ref_rot_z'),


#------------------------------------------------------------------------------
class MelXlod(MelOptStruct):
    """Distant LOD Data."""
    def __init__(self):
        super(MelXlod, self).__init__(b'XLOD', u'3f', u'lod1', u'lod2',
                                      u'lod3')
