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
"""Houses more complex building blocks for creating record definitions. The
split from basic_elements.py is somewhat arbitrary, but generally elements in
this file involve conditional loading and are much less commonly used. Relies
on some of the elements defined in basic_elements, e.g. MelBase, MelObject and
MelStruct."""

from __future__ import division, print_function

__author__ = u'Infernio'

import copy
import struct

from .basic_elements import MelBase, MelNull, MelObject, MelStruct
from .mod_io import ModWriter
from .. import exception
from ..bolt import sio, struct_pack

#------------------------------------------------------------------------------
class _MelDistributor(MelNull):
    """Implements a distributor that can handle duplicate record signatures.
    See the wiki page '[dev] Plugin Format: Distributors' for a detailed
    overview of this class and the semi-DSL it implements.

    :type _attr_to_loader: dict[str, MelBase]
    :type _sig_to_loader: dict[str, MelBase]
    :type _target_sigs: set[str]"""
    def __init__(self, distributor_config): # type: (dict) -> None
        # Maps attribute name to loader
        self._attr_to_loader = {}
        # Maps subrecord signature to loader
        self._sig_to_loader = {}
        # All signatures that this distributor targets
        self._target_sigs = set()
        self.distributor_config = distributor_config
        # Validate that the distributor config we were given has valid syntax
        # and resolve any shortcuts (e.g. the A|B syntax)
        self._pre_process()

    def _raise_syntax_error(self, error_msg):
        raise SyntaxError(u'Invalid distributor syntax: %s' % error_msg)

    ##: Needs to change to only accept unicode strings as attributes, but keep
    # accepting only bytestrings as signatures
    def _pre_process(self):
        """Ensures that the distributor config defined above has correct syntax
        and resolves shortcuts (e.g. A|B syntax)."""
        if type(self.distributor_config) != dict:
            self._raise_syntax_error(
                u'distributor_config must be a dict (actual type: %s)' %
                type(self.distributor_config))
        mappings_to_iterate = [self.distributor_config] # TODO(inf) Proper name for dicts / mappings (scopes?)
        while mappings_to_iterate:
            mapping = mappings_to_iterate.pop()
            for signature_str in mapping.keys():
                if type(signature_str) != str:
                    self._raise_syntax_error(
                        u'All keys must be signature strings (offending key: '
                        u'%r)' % signature_str)
                # Resolve 'A|B' syntax
                signatures = signature_str.split('|')
                resolved_entry = mapping[signature_str]
                if not resolved_entry:
                    self._raise_syntax_error(
                        u'Mapped values may not be empty (offending value: '
                        u'%s)' % resolved_entry)
                # Delete the 'A|B' entry, not needed anymore
                del mapping[signature_str]
                for signature in signatures:
                    if len(signature) != 4:
                        self._raise_syntax_error(
                            u'Signature strings must have length 4 (offending '
                            u'string: %s)' % signature)
                    if signature in mapping:
                        self._raise_syntax_error(
                            u'Duplicate signature string (offending string: '
                            u'%s)' % signature)
                    # For each option in A|B|..|Z, make a new entry
                    mapping[signature] = resolved_entry
                re_type = type(resolved_entry)
                if re_type == dict:
                    # If the signature maps to a dict, recurse into it
                    mappings_to_iterate.append(resolved_entry)
                elif re_type == tuple:
                    # TODO(inf) Proper name for tuple values
                    if (len(resolved_entry) != 2
                            or type(resolved_entry[0]) != str
                            or type(resolved_entry[1]) != dict):
                        self._raise_syntax_error(
                            u'Tuples used as values must always have two '
                            u'elements - an attribute string and a dict '
                            u'(offending tuple: %r)' % resolved_entry)
                    # If the signature maps to a tuple, recurse into the
                    # dict stored in its second element
                    mappings_to_iterate.append(resolved_entry[1])
                elif re_type == list:
                    # If the signature maps to a list, ensure that each entry
                    # is correct
                    for seq_entry in resolved_entry:
                        if type(seq_entry) == tuple:
                            # Ensure that the tuple is correctly formatted
                            if (len(seq_entry) != 2
                                    or type(seq_entry[0]) != str
                                    or type(seq_entry[1]) != str):
                                self._raise_syntax_error(
                                    u'Sequential tuples must always have two '
                                    u'elements, both of them strings '
                                    u'(offending sequential entry: %r)' %
                                    seq_entry)
                        elif type(seq_entry) != str:
                            self._raise_syntax_error(
                                u'Sequential entries must either be '
                                u'tuples or strings (actual type: %r)' %
                                type(seq_entry))
                elif re_type != str:
                    self._raise_syntax_error(
                        u'Only dicts, lists, strings and tuples may occur as '
                        u'values (offending type: %r)' % re_type)

    def getLoaders(self, loaders):
        # We need a copy of the unmodified signature-to-loader dictionary
        self._sig_to_loader = loaders.copy()
        # We need to recursively descend into the distributor config to find
        # all relevant subrecord types
        self._target_sigs = set()
        mappings_to_iterate = [self.distributor_config]
        while mappings_to_iterate:
            mapping = mappings_to_iterate.pop()
            # The keys are always subrecord signatures
            for signature in mapping.keys():
                # We will definitely need this signature
                self._target_sigs.add(signature)
                resolved_entry = mapping[signature]
                re_type = type(resolved_entry)
                if re_type == dict:
                    # If the signature maps to a dict, recurse into it
                    mappings_to_iterate.append(resolved_entry)
                elif re_type == tuple:
                    # If the signature maps to a tuple, recurse into the
                    # dict stored in its second element
                    mappings_to_iterate.append(resolved_entry[1])
                elif re_type == list:
                    # If the signature maps to a list, record the signatures of
                    # each entry (str or tuple[str, str])
                    self._target_sigs.update([t[0] if type(t) == tuple else t
                                              for t in resolved_entry])
                # If it's not a dict, list or tuple, then this is a leaf node,
                # which means we've already recorded its type
        # Register ourselves for every type in the hierarchy, overriding
        # previous loaders when doing so
        for subrecord_type in self._target_sigs:
            loaders[subrecord_type] = self

    def getSlotsUsed(self):
        # _loader_state is the current state of our descent into the
        # distributor config, this is a tuple of strings marking the
        # subrecords we've visited.
        # _seq_index is only used when processing a sequential and marks
        # the index where we left off in the last loadData
        return '_loader_state', '_seq_index'

    def setDefault(self, record):
        record._loader_state = ()
        record._seq_index = None

    def set_mel_set(self, mel_set):
        """Sets parent MelSet. We use this to collect the attribute names
        from each loader."""
        self.mel_set = mel_set
        for element in mel_set.elements:
            # Underscore means internal usage only - e.g. distributor state
            el_attrs = [s for s in element.getSlotsUsed()
                        if not s.startswith('_')]
            for el_attr in el_attrs:
                self._attr_to_loader[el_attr] = element

    def _accepts_signature(self, dist_specifier, signature):
        """Internal helper method that checks if the specified signature is
        handled by the specified distribution specifier."""
        to_check = (dist_specifier[0] if type(dist_specifier) == tuple
                    else dist_specifier)
        return to_check == signature

    def _distribute_load(self, dist_specifier, record, ins, size_, readId):
        """Internal helper method that distributes a loadData call to the
        element loader pointed at by the specified distribution specifier."""
        if type(dist_specifier) == tuple:
            signature = dist_specifier[0]
            target_loader = self._attr_to_loader[dist_specifier[1]]
        else:
            signature = dist_specifier
            target_loader = self._sig_to_loader[dist_specifier]
        target_loader.loadData(record, ins, signature, size_, readId)

    def _apply_mapping(self, mapped_el, record, ins, signature, size_, readId):
        """Internal helper method that applies a single mapping element
        (mapped_el). This implements the correct loader state manipulations for
        that element and also distributes the loadData call to the correct
        loader, as specified by the mapping element and the current
        signature."""
        el_type = type(mapped_el)
        if el_type == dict:
            # Simple Scopes -----------------------------------------------
            # A simple scope - add the signature to the load state and
            # distribute the load by signature. That way we will descend
            # into this scope on the next loadData call.
            record._loader_state += (signature,)
            self._distribute_load(signature, record, ins, size_, readId)
        elif el_type == tuple:
            # Mixed Scopes ------------------------------------------------
            # A mixed scope - implement it like a simple scope, but
            # distribute the load by attribute name.
            record._loader_state += (signature,)
            self._distribute_load((signature, mapped_el[0]), record, ins,
                                  size_, readId)
        elif el_type == list:
            # Sequences, Pt. 2 --------------------------------------------
            # A sequence - add the signature to the load state, set the
            # sequence index to 1, and distribute the load to the element
            # specified by the first sequence entry.
            record._loader_state += (signature,)
            record._seq_index = 1 # we'll load the first element right now
            self._distribute_load(mapped_el[0], record, ins, size_,
                                  readId)
        else: # el_type == str, verified in _pre_process
            # Targets -----------------------------------------------------
            # A target - don't add the signature to the load state and
            # distribute the load by attribute name.
            self._distribute_load((signature, mapped_el), record, ins,
                                  size_, readId)

    def loadData(self, record, ins, sub_type, size_, readId):
        loader_state = record._loader_state
        seq_index = record._seq_index
        # First, descend as far as possible into the mapping. However, also
        # build up a tracker we can use to backtrack later on.
        descent_tracker = []
        current_mapping = self.distributor_config
        # Scopes --------------------------------------------------------------
        for signature in loader_state:
            current_mapping = current_mapping[signature]
            if type(current_mapping) == tuple: # handle mixed scopes
                current_mapping = current_mapping[1]
            descent_tracker.append((signature, current_mapping))
        # Sequences -----------------------------------------------------------
        # Then, check if we're in the middle of a sequence. If so,
        # current_mapping will actually be a list, namely the sequence we're
        # iterating over.
        if seq_index is not None:
            dist_specifier = current_mapping[seq_index]
            if self._accepts_signature(dist_specifier, sub_type):
                # We're good to go, call the next loader in the sequence and
                # increment the sequence index
                self._distribute_load(dist_specifier, record, ins, size_,
                                      readId)
                record._seq_index += 1
                return
            # The sequence is either over or we prematurely hit a non-matching
            # type - either way, stop distributing loads to it.
            record._seq_index = None
        # Next, check if the current mapping depth contains a specifier that
        # accepts our signature. If so, use that one to track and distribute.
        # If not, we have to backtrack.
        while descent_tracker:
            prev_sig, prev_mapping = descent_tracker.pop()
            # For each previous layer, check if it contains a specifier that
            # accepts our signature and use it if so.
            if sub_type in prev_mapping:
                # Calculate the new loader state - contains signatures for all
                # remaining scopes we haven't backtracked through yet plus the
                # one we just backtrackd into
                record._loader_state = tuple([x[0] for x in descent_tracker] +
                                             [prev_sig])
                self._apply_mapping(prev_mapping[sub_type], record, ins,
                                    sub_type, size_, readId)
                return
        # We didn't find anything during backtracking, so it must be in the top
        # scope. Wipe the loader state first and then apply the mapping.
        record._loader_state = ()
        self._apply_mapping(self.distributor_config[sub_type], record, ins,
                            sub_type, size_, readId)

    @property
    def signatures(self):
        return self._target_sigs

#------------------------------------------------------------------------------
class MelArray(MelBase):
    """Represents a single subrecord that consists of multiple fixed-size
    components. Note that only elements that properly implement static_size
    and fulfill len(self.signatures) == 1, i.e. ones that have a static size
    and resolve to only a single signature, can be used."""
    def __init__(self, array_attr, element, prelude=None):
        """Creates a new MelArray with the specified attribute and element.

        :param array_attr: The attribute name to give the entire array.
        :type array_attr: str
        :param element: The element that each entry in this array will be
            loaded and dumped by.
        :type element: MelBase
        :param prelude: An optional element that will be loaded and dumped once
            before the repeating element.
        :type prelude: MelBase"""
        try:
            self._element_size = element.static_size
        except exception.AbstractError:
            raise SyntaxError(u'MelArray may only be used with elements that '
                              u'have a static size')
        if len(element.signatures) != 1:
            raise SyntaxError(u'MelArray may only be used with elements that '
                              u'resolve to exactly one signature')
        # Use this instead of element.subType to support e.g. unions
        MelBase.__init__(self, next(iter(element.signatures)), array_attr)
        self._element = element
        # Underscore means internal usage only - e.g. distributor state
        self._element_attrs = [s for s in element.getSlotsUsed()
                              if not s.startswith('_')]
        if prelude and prelude.subType != element.subType:
            raise SyntaxError(u'MelArray preludes must have the same '
                              u'signature as the main element')
        self._prelude = prelude
        try:
            self._prelude_size = prelude.static_size if prelude else 0
        except exception.AbstractError:
            raise SyntaxError(u'MelArray preludes must have a static size')

    class _DirectModWriter(ModWriter):
        """ModWriter that does not write out any subrecord headers."""
        def packSub(self, sub_rec_type, data, *values):
            if data is None: return
            if values: data = struct_pack(data, *values)
            self.out.write(data)

        def packSub0(self, sub_rec_type, data):
            self.out.write(data)
            self.out.write(b'\x00')

        def packRef(self, sub_rec_type, fid):
            if fid is not None: self.pack(u'I', fid)

    def getSlotsUsed(self):
        slots_ret = self._prelude.getSlotsUsed() if self._prelude else ()
        return super(MelArray, self).getSlotsUsed() + slots_ret

    def hasFids(self, formElements):
        temp_elements = set()
        if self._prelude:
            self._prelude.hasFids(temp_elements)
        self._element.hasFids(temp_elements)
        if temp_elements: formElements.add(self)

    def setDefault(self, record):
        if self._prelude:
            self._prelude.setDefault(record)
        setattr(record, self.attr, [])

    def mapFids(self,record,function,save=False):
        if self._prelude:
            self._prelude.mapFids(record, function, save)
        array_val = getattr(record, self.attr)
        if array_val:
            map_entry = self._element.mapFids
            for arr_entry in array_val:
                map_entry(arr_entry, function, save)

    def loadData(self, record, ins, sub_type, size_, readId):
        append_entry = getattr(record, self.attr).append
        entry_slots = self._element_attrs
        entry_size = self._element_size
        load_entry = self._element.loadData
        if self._prelude:
            self._prelude.loadData(record, ins, sub_type, self._prelude_size,
                                   readId)
            size_ -= self._prelude_size
        for x in xrange(size_ // entry_size):
            arr_entry = MelObject()
            append_entry(arr_entry)
            arr_entry.__slots__ = entry_slots
            load_entry(arr_entry, ins, sub_type, entry_size, readId)

    def dumpData(self, record, out):
        array_data = self._collect_array_data(record)
        if array_data: out.packSub(self.subType, array_data)

    def _collect_array_data(self, record):
        """Collects the actual data that will be dumped out."""
        array_data = MelArray._DirectModWriter(sio())
        if self._prelude:
            self._prelude.dumpData(record, array_data)
        array_val = getattr(record, self.attr)
        if not array_val: return b'' # don't dump out empty arrays
        dump_entry = self._element.dumpData
        for arr_entry in array_val:
            dump_entry(arr_entry, array_data)
        return array_data.getvalue()

#------------------------------------------------------------------------------
class MelTruncatedStruct(MelStruct):
    """Works like a MelStruct, but automatically upgrades certain older,
    truncated struct formats."""
    def __init__(self, sub_sig, sub_fmt, *elements, **kwargs):
        """Creates a new MelTruncatedStruct with the specified parameters.

        :param sub_sig: The subrecord signature of this struct.
        :param sub_fmt: The format of this struct.
        :param elements: The element syntax of this struct. Passed to
            MelStruct.parseElements, see that method for syntax explanations.
        :param kwargs: Must contain an old_versions keyword argument, which
            specifies the older formats that are supported by this struct. The
            keyword argument is_optional can be supplied, which determines
            whether or not this struct should behave like MelOptStruct. May
            also contain any keyword arguments that MelStruct supports."""
        try:
            old_versions = kwargs.pop('old_versions')
        except KeyError:
            raise SyntaxError(u'MelTruncatedStruct requires an old_versions '
                              u'keyword argument')
        if type(old_versions) != set:
            raise SyntaxError(u'MelTruncatedStruct: old_versions must be a '
                              u'set')
        self._is_optional = kwargs.pop('is_optional', False)
        MelStruct.__init__(self, sub_sig, sub_fmt, *elements)
        self._all_unpackers = {
            struct.calcsize(alt_fmt): struct.Struct(alt_fmt).unpack for
            alt_fmt in old_versions}
        self._all_unpackers[struct.calcsize(sub_fmt)] = struct.Struct(
            sub_fmt).unpack

    def loadData(self, record, ins, sub_type, size_, readId):
        # Try retrieving the format - if not possible, wrap the error to make
        # it more informative
        try:
            target_unpacker = self._all_unpackers[size_]
        except KeyError:
            raise exception.ModSizeError(
                ins.inName, readId, tuple(self._all_unpackers.keys()), size_)
        # Actually unpack the struct and pad it with defaults if it's an older,
        # truncated version
        unpacked_val = ins.unpack(target_unpacker, size_, readId)
        unpacked_val = self._pre_process_unpacked(unpacked_val)
        # Apply any actions and then set the attributes according to the values
        # we just unpacked
        setter = record.__setattr__
        for attr, value, action in zip(self.attrs, unpacked_val, self.actions):
            if callable(action): value = action(value)
            setter(attr, value)

    def _pre_process_unpacked(self, unpacked_val):
        """You may override this if you need to change the unpacked value in
        any way before it is used to assign attributes. By default, this
        performs the actual upgrading by appending default values to
        unpacked_val."""
        return unpacked_val + self.defaults[len(unpacked_val):]

    def dumpData(self, record, out):
        if self._is_optional:
            # If this struct is optional, compare the current values to the
            # defaults and skip the dump conditionally - basically the same
            # thing MelOptStruct does
            record_get_attr = record.__getattribute__
            for attr, default in zip(self.attrs, self.defaults):
                curr_val = record_get_attr(attr)
                if curr_val is not None and curr_val != default:
                    break
            else:
                return
        MelStruct.dumpData(self, record, out)

    @property
    def static_size(self):
        # We behave just like a regular struct if we don't have any old formats
        if len(self._all_unpackers) != 1:
            raise exception.AbstractError()
        return super(MelTruncatedStruct, self).static_size

#------------------------------------------------------------------------------
# Unions and Deciders
class ADecider(object):
    """A decider returns one of several possible values when called, based on
    parameters such as the record instance, sub type, or record size. See
    MelUnion's docstring for more information."""
    # Set this to True if your decider can handle a decide_dump call -
    # otherwise, the result of decide_load will be stored and reused during
    # dumpData, if that is possible. If not (e.g. for a newly created record),
    # then the union will pick some element in its dict - no guarantees made.
    can_decide_at_dump = False

    def decide_load(self, record, ins, sub_type, rec_size):
        """Called during loadData.

        :param record: The record instance we're assigning attributes to.
        :param ins: The ModReader instance used to read the record.
        :type ins: ModReader
        :param sub_type: The four-character subrecord signature.
        :type sub_type: str
        :param rec_size: The total size of the subrecord.
        :type rec_size: int
        :return: Any value this decider deems fitting for the parameters it is
            given."""
        raise exception.AbstractError()

    def decide_dump(self, record):
        """Called during dumpData.

        :param record: The record instance we're reading attributes from.
        :return: Any value this decider deems fitting for the parameters it is
            given."""
        if self.__class__.can_decide_at_dump:
            raise exception.AbstractError()

class ACommonDecider(ADecider):
    """Abstract class for deciders that can decide at both load and dump-time,
    based only on the record. Provides a single method, _decide_common, that
    the subclass has to implement."""
    can_decide_at_dump = True

    def decide_load(self, record, ins, sub_type, rec_size):
        return self._decide_common(record)

    def decide_dump(self, record):
        return self._decide_common(record)

    def _decide_common(self, record):
        """Performs the actual decisions for both loading and dumping."""
        raise exception.AbstractError()

class AttrExistsDecider(ACommonDecider):
    """Decider that returns True if an attribute with the specified name is
    present on the record."""
    def __init__(self, target_attr):
        """Creates a new AttrExistsDecider with the specified attribute.

        :param target_attr: The name of the attribute to check.
        :type target_attr: str"""
        self.target_attr = target_attr

    def _decide_common(self, record):
        return hasattr(record, self.target_attr)

class AttrValDecider(ACommonDecider):
    """Decider that returns an attribute value (may optionally apply a function
    to it first)."""
    # Internal sentinel value used for the assign_missing argument
    _assign_missing_sentinel = object()

    def __init__(self, target_attr, transformer=None,
                 assign_missing=_assign_missing_sentinel):
        """Creates a new AttrValDecider with the specified attribute and
        optional arguments.

        :param target_attr: The name of the attribute to return the value
            for.
        :type target_attr: str
        :param transformer: A function that takes a single argument, the value
            read from target_attr, and returns some other value. Can be used to
            e.g. return only the first character of an eid.
        :param assign_missing: Normally, an AttributeError is raised if the
            record does not have target_attr. If this is anything other than
            the sentinel value, an error will not be raised and this will be
            returned instead."""
        self.target_attr = target_attr
        self.transformer = transformer
        self.assign_missing = assign_missing

    def _decide_common(self, record):
        if self.assign_missing is not self._assign_missing_sentinel:
            # We have a valid assign_missing, default to it
            ret_val = getattr(record, self.target_attr, self.assign_missing)
        else:
            # Raises an AttributeError if target_attr is missing
            ret_val = getattr(record, self.target_attr)
        if self.transformer:
            ret_val = self.transformer(ret_val)
        return ret_val

class FlagDecider(ACommonDecider):
    """Decider that checks if certain flags are set."""
    def __init__(self, flags_attr, *required_flags):
        """Creates a new FlagDecider with the specified flag attribute and
        required flag names.

        :param flags_attr: The attribute that stores the flag value.
        :param required_flags: The names of all flags that have to be set."""
        self._flags_attr = flags_attr
        self._required_flags = required_flags

    def _decide_common(self, record):
        flags_val = getattr(record, self._flags_attr)
        check_flag = flags_val.__getattr__
        return all(check_flag(flag_name) for flag_name in self._required_flags)

class GameDecider(ACommonDecider):
    """Decider that returns the name of the currently managed game."""
    def __init__(self):
        from .. import bush
        self.game_fsName = bush.game.fsName

    def _decide_common(self, record):
        return self.game_fsName

class PartialLoadDecider(ADecider):
    """Partially loads a subrecord using a given loader, then rewinds the
    input stream and delegates to a given decider. Can decide at dump-time
    iff the given decider can as well."""
    def __init__(self, loader, decider):
        """Constructs a new PartialLoadDecider with the specified loader and
        decider.

        :param loader: The MelBase instance to use for loading. Must have a
            static size.
        :type loader: MelBase
        :param decider: The decider to use after loading.
        :type decider: ADecider"""
        self._loader = loader
        self._load_size = loader.static_size
        self._decider = decider
        # This works because MelUnion._get_element_from_record does not use
        # self.__class__ to access can_decide_at_dump
        self.can_decide_at_dump = decider.can_decide_at_dump

    def decide_load(self, record, ins, sub_type, rec_size):
        starting_pos = ins.tell()
        # Make a deep copy so that no modifications from this decision will
        # make it to the actual record
        target = copy.deepcopy(record)
        self._loader.loadData(target, ins, sub_type, self._load_size,
                             'DECIDER.' + sub_type)
        ins.seek(starting_pos)
        # Use the modified record here to make the temporary changes visible to
        # the delegate decider
        return self._decider.decide_load(target, ins, sub_type, rec_size)

    def decide_dump(self, record):
        if not self.can_decide_at_dump:
            raise exception.AbstractError()
        # We can simply delegate here without doing anything else, since the
        # record has to have been loaded since then
        return self._decider.decide_dump(record)

class SaveDecider(ADecider):
    """Decider that returns True if the input file is a save."""
    def __init__(self):
        from .. import bush
        self._save_ext = bush.game.Ess.ext

    def decide_load(self, record, ins, sub_type, rec_size):
        return ins.inName.cext == self._save_ext

class SignatureDecider(ADecider):
    """Very simple decider that just returns the subrecord type (aka
    signature). This is the default decider used by MelUnion."""
    def decide_load(self, record, ins, sub_type, rec_size):
        return sub_type

class SizeDecider(ADecider):
    """Decider that returns the size of the target subrecord."""
    def decide_load(self, record, ins, sub_type, rec_size):
        return rec_size

class MelUnion(MelBase):
    """Resolves to one of several record elements based on an ADecider.
    Defaults to a SignatureDecider.

    The decider is queried for a value, which is then used to perform a lookup
    in the element_mapping dict passed in. For example, consider this MelUnion,
    which showcases all features:
        MelUnion({
            'b': MelStruct('DATA', 'I', 'value'),
            'f': MelStruct('DATA', 'f', 'value'),
            's': MelLString('DATA', 'value'),
        }, decider=AttrValDecider(
            'eid', lambda eid: eid[0] if eid else 'i'),
            fallback=MelStruct('DATA', 'i', 'value')
        ),
    When a DATA subrecord is encountered, the union is asked to load it. It
    queries its decider, which in this case reads the 'eid' attribute (i.e. the
    EDID subrecord) and returns the first character of that attribute's value,
    defaulting to 'i' if it's empty. The union then looks up the returned value
    in its mapping. If it finds it (e.g. if it's 'b'), then it will delegate
    loading to the MelBase-derived object mapped to that value. Otherwise, it
    will check if a fallback element is available. If it is, then that one is
    used. Otherwise, an ArgumentError is raised.

    When dumping and mapping fids, a similar process occurs. The decider is
    asked if it is capable of deciding with the (more limited) information
    available at this time. If it can, it is queried and the result is once
    again used to look up in the mapping. If, however, the decider can't decide
    at this time, the union looks if this is a newly created record or one that
    has been read. In the former case, it just picks an arbitrary element to
    dump out. In the latter case, it reuses the previous decider result to look
    up the mapping.

    Note: This class does not (and likely won't ever be able to) support
    getDefaulters / getDefault."""
    # Incremented every time we construct a MelUnion - ensures we always make
    # unique attributes on the records
    _union_index = 0

    def __init__(self, element_mapping, decider=SignatureDecider(),
                 fallback=None):
        """Creates a new MelUnion with the specified element mapping and
        optional parameters. See the class docstring for extensive information
        on MelUnion usage.

        :param element_mapping: The element mapping.
        :type element_mapping: dict[object, MelBase]
        :param decider: An ADecider instance to use. Defaults to
            SignatureDecider.
        :type decider: ADecider
        :param fallback: The fallback element to use. Defaults to None, which
            will raise an error if the decider returns an unknown value.
        :type fallback: MelBase"""
        self.element_mapping = element_mapping
        self.fid_elements = set()
        if not isinstance(decider, ADecider):
            raise exception.ArgumentError(u'decider must be an ADecider')
        self.decider = decider
        self.decider_result_attr = u'_union_type_%u' % MelUnion._union_index
        MelUnion._union_index += 1
        self.fallback = fallback
        self._possible_sigs = {s for element
                               in self.element_mapping.itervalues()
                               for s in element.signatures}
        if self.fallback:
            self._possible_sigs.update(self.fallback.signatures)

    def _get_element(self, decider_ret):
        """Retrieves the fitting element from element_mapping for the
        specified decider result.

        :param decider_ret: The result of the decide_* method that was
            invoked.
        :return: The matching record element to use."""
        element = self.element_mapping.get(decider_ret, self.fallback)
        if not element:
            raise exception.ArgumentError(
                u'Specified element mapping did not handle a decider return '
                u'value (%r) and there is no fallback' % decider_ret)
        return element

    def _get_element_from_record(self, record):
        """Retrieves the fitting element based on the specified record instance
        only. Small wrapper around _get_element to share code between dumpData
        and mapFids.

        :param record: The record instance we're dealing with.
        :return: The matching record element to use."""
        if self.decider.can_decide_at_dump:
            # If the decider can decide at dump-time, let it
            return self._get_element(self.decider.decide_dump(record))
        elif not hasattr(record, self.decider_result_attr):
            # We're dealing with a record that was just created, but the
            # decider can't be used - default to some element
            return next(self.element_mapping.itervalues())
        else:
            # We can use the result we decided earlier
            return self._get_element(
                getattr(record, self.decider_result_attr))

    def getSlotsUsed(self):
        # We need to reserve every possible slot, since we can't know what
        # we'll resolve to yet. Use a set to avoid duplicates.
        slots_ret = {self.decider_result_attr}
        for element in self.element_mapping.itervalues():
            slots_ret.update(element.getSlotsUsed())
        if self.fallback: slots_ret.update(self.fallback.getSlotsUsed())
        return tuple(slots_ret)

    def getLoaders(self, loaders):
        # We need to collect all signatures and assign ourselves for them all
        # to handle unions with different signatures
        temp_loaders = {}
        for element in self.element_mapping.itervalues():
            element.getLoaders(temp_loaders)
        if self.fallback: self.fallback.getLoaders(temp_loaders)
        for signature in temp_loaders.keys():
            loaders[signature] = self

    def hasFids(self, formElements):
        # Ask each of our elements, and remember the ones where we'd have to
        # actually forward the mapFids call. We can't just blindly call
        # mapFids, since MelBase.mapFids is abstract.
        for element in self.element_mapping.itervalues():
            temp_elements = set()
            element.hasFids(temp_elements)
            if temp_elements:
                self.fid_elements.add(element)
        if self.fallback:
            temp_elements = set()
            self.fallback.hasFids(temp_elements)
            if temp_elements:
                self.fid_elements.add(self.fallback)
        if self.fid_elements: formElements.add(self)

    def setDefault(self, record):
        # Ask each element - but we *don't* want to set our _union_type
        # attributes here! If we did, then we'd have no way to distinguish
        # between a loaded and a freshly constructed record.
        for element in self.element_mapping.itervalues():
            element.setDefault(record)
        if self.fallback: self.fallback.setDefault(record)

    def mapFids(self, record, function, save=False):
        element = self._get_element_from_record(record)
        if element in self.fid_elements:
            element.mapFids(record, function, save)

    def loadData(self, record, ins, sub_type, size_, readId):
        # Ask the decider, and save the result for later - even if the decider
        # can decide at dump-time! Some deciders may want to have this as a
        # backup if they can't deliver a high-quality result.
        decider_ret = self.decider.decide_load(record, ins, sub_type, size_)
        setattr(record, self.decider_result_attr, decider_ret)
        self._get_element(decider_ret).loadData(record, ins, sub_type, size_,
                                                readId)

    def dumpData(self, record, out):
        self._get_element_from_record(record).dumpData(record, out)

    @property
    def signatures(self):
        return self._possible_sigs

    @property
    def static_size(self):
        all_elements = self.element_mapping.values() + (
            [self.fallback] if self.fallback else [])
        first_size = all_elements[0].static_size # pick arbitrary element size
        if any(element.static_size != first_size for element in all_elements):
            raise exception.AbstractError() # The sizes are not all identical
        return first_size
