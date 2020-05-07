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
#  Mopy/bash/games.py copyright (C) 2016 Utumno: Original design
#
# =============================================================================

"""Game class implementing load order handling - **only** imported in
load_order.py."""
##: multiple backups? fixes can happen in rapid succession, so preserving
# several older files in a directory would be useful (maybe limit to some
# number, e.g. 5 older versions)

__author__ = u'Utumno'

import errno
import re
import time
from collections import defaultdict, OrderedDict
# Local
from . import bass, bolt, env, exception
from .ini_files import get_ini_type_and_encoding
from .localize import format_date

def _write_plugins_txt_(path, lord, active, _star):
    try:
        with path.open('wb') as out:
            __write_plugins(out, lord, active, _star)
    except IOError:
        env.clear_read_only(path)
        with path.open('wb') as out:
            __write_plugins(out, lord, active, _star)

def __write_plugins(out, lord, active, _star):
    def asterisk(active_set=frozenset(active)):
        return '*' if _star and (mod in active_set) else ''
    for mod in (_star and lord) or active:
        # Ok, this seems to work for Oblivion, but not Skyrim
        # Skyrim seems to refuse to have any non-cp1252 named file in
        # plugins.txt.  Even activating through the SkyrimLauncher
        # doesn't work.
        try:
            out.write(asterisk() + bolt.encode(mod.s, firstEncoding='cp1252'))
            out.write('\r\n')
        except UnicodeEncodeError:
            bolt.deprint(mod.s + u' failed to properly encode and was not '
                                 u'included in plugins.txt')

_re_plugins_txt_comment = re.compile(u'^#.*', re.U)
def _parse_plugins_txt_(path, mod_infos, _star):
    """Parse loadorder.txt and plugins.txt files with or without stars.

    Return two lists which are identical except when _star is True, whereupon
    the second list is the load order while the first the active plugins. In
    all other cases use the first list, which is either the list of active
    mods (when parsing plugins.txt) or the load order (when parsing
    loadorder.txt)
    :type path: bolt.Path
    :type mod_infos: bosh.ModInfos
    :type _star: bool
    :rtype: (list[bolt.Path], list[bolt.Path])
    """
    with path.open('r') as ins:
        #--Load Files
        active, modnames = [], []
        for line in ins:
            # Oblivion/Skyrim saves the plugins.txt file in cp1252 format
            # It wont accept filenames in any other encoding
            modname = _re_plugins_txt_comment.sub('', line).strip()
            if not modname: continue
            # use raw strings below
            is_active_ = not _star or modname.startswith('*')
            if _star and is_active_: modname = modname[1:]
            try:
                test = bolt.decode(modname, encoding='cp1252')
            except UnicodeError:
                bolt.deprint(u'%r failed to properly decode' % modname)
                continue
            if bolt.GPath(test) not in mod_infos:
                # The automatic encoding detector could have returned
                # an encoding it actually wasn't.  Luckily, we
                # have a way to double check: modInfos.data
                for encoding in bolt.encodingOrder:
                    try:
                        test2 = unicode(modname, encoding)
                        if bolt.GPath(test2) not in mod_infos:
                            continue
                        modname = bolt.GPath(test2)
                        break
                    except UnicodeError:
                        pass
                else:
                    modname = bolt.GPath(test)
            else:
                modname = bolt.GPath(test)
            modnames.append(modname)
            if is_active_: active.append(modname)
    return active, modnames

class FixInfo(object):
    """Encapsulate info on load order and active lists fixups."""
    def __init__(self):
        self.lo_removed = set()
        self.lo_added = set()
        self.lo_duplicates = set()
        self.lo_reordered = ([], [])
        # active mods corrections
        self.act_removed = set()
        self.act_added = set()
        self.act_duplicates = set()
        self.act_reordered = ()
        self.act_order_differs_from_load_order = u''
        self.master_not_active = False
        self.missing_must_be_active = []
        self.selectedExtra = []
        self.act_header = u''

    def lo_changed(self):
        return bool(self.lo_removed or self.lo_added or self.lo_duplicates or
                    any(self.lo_reordered))

    def act_changed(self):
        return bool(
            self.act_removed or self.act_added or self.act_duplicates or
            self.act_reordered or self.act_order_differs_from_load_order or
            self.master_not_active or self.missing_must_be_active)

    def lo_deprint(self):
        self.warn_lo()
        self.warn_active()

    def warn_lo(self):
        if not self.lo_changed(): return
        added = _pl(self.lo_added) or u'None'
        removed = _pl(self.lo_removed) or u'None'
        duplicates = (u'lo_duplicates(%s), ' % _pl(self.lo_duplicates)) \
            if self.lo_duplicates else u''
        reordered = u'(No)' if not any(self.lo_reordered) else _pl(
            self.lo_reordered[0], u'from:\n', joint=u'\n') + _pl(
            self.lo_reordered[1], u'\nto:\n', joint=u'\n')
        msg = u'Fixed Load Order: added(%s), removed(%s), %sreordered %s' % (
            added, removed, duplicates, reordered)
        bolt.deprint(msg)

    def warn_active(self):
        if not self.act_header: return
        msg = self.act_header
        if self.act_removed:
            msg += u'Active list contains mods not present in Data/ ' \
                   u'directory, invalid and/or corrupted: '
            msg += _pl(self.act_removed) + u'\n'
        if self.master_not_active:
            msg += u'%s not present in active mods\n' % self.master_not_active
        for path in self.missing_must_be_active:
            msg += (u'%s not present in active list while present in Data '
                    u'folder' % path) + u'\n'
        msg += self.act_order_differs_from_load_order
        if self.selectedExtra:
            msg += u'Active list contains more than 255 espms' \
                   u' - the following plugins will be deactivated: '
            msg += _pl(self.selectedExtra)
        if self.act_duplicates:
            msg += u'Removed duplicate entries from active list : '
            msg += _pl(self.act_duplicates)
        if len(self.act_reordered) == 2: # from, to
            msg += u'Reordered active plugins with fixed order '
            msg += _pl(self.act_reordered[0], u'from:\n', joint=u'\n')
            msg += _pl(self.act_reordered[1], u'\nto:\n', joint=u'\n')
        bolt.deprint(msg)

class Game(object):

    allow_deactivate_master = False
    must_be_active_if_present = ()
    max_espms = 255
    max_esls = 0
    # If set to False, indicates that this game has no plugins.txt. Currently
    # only allows swap() to be a sentinel method for multiple inheritance,
    # everything else has to be handled through overrides
    # TODO(inf) Refactor  Game to use this value and raise AbstractExceptions
    #  when it's False
    has_plugins_txt = True
    _star = False # whether plugins.txt uses a star to denote an active plugin

    def __init__(self, mod_infos, plugins_txt_path):
        super(Game, self).__init__()
        self.plugins_txt_path = plugins_txt_path # type: bolt.Path
        self.mod_infos = mod_infos # this is bosh.ModInfos, must be up to date
        self.master_path = mod_infos.masterName # type: bolt.Path
        self.mtime_plugins_txt = 0
        self.size_plugins_txt = 0

    def _plugins_txt_modified(self):
        exists = self.plugins_txt_path.exists()
        if not exists and self.mtime_plugins_txt: return True # deleted !
        return exists and ((self.size_plugins_txt, self.mtime_plugins_txt) !=
                           self.plugins_txt_path.size_mtime())

    # API ---------------------------------------------------------------------
    def get_load_order(self, cached_load_order, cached_active_ordered,
                       fix_lo=None):
        """Get and validate current load order and active plugins information.

        Meant to fetch at once both load order and active plugins
        information as validation usually depends on both. If the load order
        read is invalid (messed up loadorder.txt, game's master redated out
        of order, etc) it will attempt fixing and saving them before returning.
        The caller is responsible for passing a valid cached value in. If you
        pass a cached value for either parameter this value will be returned
        unchanged, possibly validating the other one based on stale data.
        NOTE: modInfos must exist and be up to date for validation.
        :type cached_load_order: tuple[bolt.Path]
        :type cached_active_ordered: tuple[bolt.Path]
        :rtype: (tuple[bolt.Path], tuple[bolt.Path])
        """
        if cached_load_order is not None and cached_active_ordered is not None:
            return cached_load_order, cached_active_ordered # NOOP
        lo, active = self._cached_or_fetch(cached_load_order,
                                           cached_active_ordered)
        # for timestamps we use modInfos so we should not get an invalid
        # load order (except redated master). For text based games however
        # the fetched order could be in whatever state, so get this fixed
        if cached_load_order is None: ##: if not should we assert is valid ?
            self._fix_load_order(lo, fix_lo=fix_lo)
        # having a valid load order we may fix active too if we fetched them
        fixed_active = cached_active_ordered is None and \
          self._fix_active_plugins(active, lo, on_disc=True, fix_active=fix_lo)
        self._save_fixed_load_order(fix_lo, fixed_active, lo, active)
        return tuple(lo), tuple(active)

    def _cached_or_fetch(self, cached_load_order, cached_active):
        # we need to override this bit for fallout4 to parse the file once
        if cached_active is None: # first get active plugins
            cached_active = self._fetch_active_plugins()
        # we need active plugins fetched to check for desync in load order
        if cached_load_order is None:
            cached_load_order = self._fetch_load_order(cached_load_order,
                                                       cached_active)
        return list(cached_load_order), list(cached_active)

    def _save_fixed_load_order(self, fix_lo, fixed_active, lo, active):
        if fix_lo.lo_changed():
            self._backup_load_order()
            self._persist_load_order(lo, None) # active is not used here

    def set_load_order(self, lord, active, previous_lord=None,
                       previous_active=None, dry_run=False, fix_lo=None):
        assert lord is not None or active is not None, \
            'load order or active must be not None'
        if lord is not None: self._fix_load_order(lord, fix_lo=fix_lo)
        if (previous_lord is None or previous_lord != lord) and active is None:
            # changing load order - must test if active plugins must change too
            assert previous_active is not None, \
                'you must pass info on active when setting load order'
            if previous_lord is not None:
                prev = set(previous_lord)
                new = set(lord)
                deleted = prev - new
                common = prev & new
                reordered = any(x != y for x, y in
                                zip((x for x in previous_lord if x in common),
                                    (x for x in lord if x in common)))
                test_active = self._must_update_active(deleted, reordered)
            else:
                test_active = True
            if test_active: active = list(previous_active)
        if active is not None:
            assert lord is not None or previous_lord is not None, \
                'you need to pass a load order in to set active plugins'
            # a load order is needed for all games to validate active against
            test = lord if lord is not None else previous_lord
            self._fix_active_plugins(active, test, on_disc=False,
                                     fix_active=fix_lo)
        lord = lord if lord is not None else previous_lord
        active = active if active is not None else previous_active
        assert lord is not None and active is not None, \
            'returned load order and active must be not None'
        if not dry_run: # else just return the (possibly fixed) lists
            self._persist_if_changed(active, lord, previous_active,
                                     previous_lord)
        return lord, active # return what was set or was previously set

    @property
    def pinned_mods(self): return {self.master_path}

    # Conflicts - only for timestamp games
    def has_load_order_conflict(self, mod_name): return False
    def has_load_order_conflict_active(self, mod_name, active): return False
    # force installation last - only for timestamp games
    def get_free_time(self, start_time, default_time='+1', end_time=None):
        raise exception.AbstractError

    @classmethod
    def _must_update_active(cls, deleted, reordered):
        raise exception.AbstractError

    def active_changed(self): return self._plugins_txt_modified()

    def load_order_changed(self): return True # timestamps, just calculate it

    # Swap plugins and loadorder txt
    def swap(self, old_path, new_path):
        """Save current plugins into oldPath directory and load plugins from
        newPath directory (if present)."""
        # If this game has no plugins.txt, don't try to swap it
        if not self.__class__.has_plugins_txt: return
        # Save plugins.txt inside the old (saves) directory
        if self.plugins_txt_path.exists():
            self.plugins_txt_path.copyTo(old_path.join(u'plugins.txt'))
        # Move the new plugins.txt here for use
        move = new_path.join(u'plugins.txt')
        if move.exists():
            move.copyTo(self.plugins_txt_path)
            self.plugins_txt_path.mtime = time.time() # copy will not change mtime, bad

    def in_master_block(self, minf): # minf is a master or mod info
        """Return true for files that load in the masters' block."""
        return minf.has_esm_flag()

    # ABSTRACT ----------------------------------------------------------------
    def _backup_active_plugins(self):
        """This method should make a backup of whatever file is storing the
        active plugins list."""
        raise exception.AbstractError

    def _backup_load_order(self):
        """This method should make a backup of whatever file is storing the
        load order plugins list."""
        raise exception.AbstractError

    def _fetch_load_order(self, cached_load_order, cached_active):
        """:type cached_load_order: tuple[bolt.Path] | None
        :type cached_active: tuple[bolt.Path]"""
        raise exception.AbstractError

    def _fetch_active_plugins(self): # no override for AsteriskGame
        """:rtype: list[bolt.Path]"""
        raise exception.AbstractError

    def _persist_load_order(self, lord, active):
        """Persist the fixed lord to disk - will break conflicts for
        timestamp games."""
        raise exception.AbstractError

    def _persist_active_plugins(self, active, lord):
        raise exception.AbstractError

    def _persist_if_changed(self, active, lord, previous_active,
                            previous_lord):
        # Override for fallout4 to write the file once and oblivion to save
        # active only if needed. Both active and lord must not be None.
        raise exception.AbstractError

    # MODFILES PARSING --------------------------------------------------------
    def _parse_modfile(self, path):
        """:rtype: (list[bolt.Path], list[bolt.Path])"""
        if not path.exists(): return [], []
        #--Read file
        acti, _lo = _parse_plugins_txt_(path, self.mod_infos, _star=self._star)
        return acti, _lo

    def _write_modfile(self, path, lord, active):
        _write_plugins_txt_(path, lord, active, _star=self._star)

    # PLUGINS TXT -------------------------------------------------------------
    def _parse_plugins_txt(self):
        """:rtype: (list[bolt.Path], list[bolt.Path])"""
        if not self.plugins_txt_path.exists(): return [], []
        #--Read file
        acti, _lo = self._parse_modfile(self.plugins_txt_path)
        self.__update_plugins_txt_cache_info()
        return acti, _lo

    def _write_plugins_txt(self, lord, active):
        self._write_modfile(self.plugins_txt_path, lord, active)
        self.__update_plugins_txt_cache_info()

    def __update_plugins_txt_cache_info(self):
        self.size_plugins_txt, self.mtime_plugins_txt = \
            self.plugins_txt_path.size_mtime()

    # VALIDATION --------------------------------------------------------------
    def _fix_load_order(self, lord, fix_lo):
        """Fix inconsistencies between given loadorder and actually installed
        mod files as well as impossible load orders. We need a refreshed
        bosh.modInfos reflecting the contents of Data/.

        Called in get_load_order() to fix a newly fetched LO and in
        set_load_order() to check if a load order passed in is valid. Needs
        rethinking as save load and active should be an atomic operation -
        leads to hacks (like the _selected parameter).
        :type lord: list[bolt.Path]
        """
        if fix_lo is None: fix_lo = FixInfo() # discard fix info
        old_lord = lord[:]
        # game's master might be out of place (if using timestamps for load
        # ordering or a manually edited loadorder.txt) so move it up
        master_name = self.master_path
        master_dex = 0
        # Tracks if fix_lo.lo_reordered needs updating
        lo_order_changed = any(fix_lo.lo_reordered)
        try:
            master_dex = lord.index(master_name)
        except ValueError:
            if not master_name in self.mod_infos:
                raise exception.BoltError(
                    u'%s is missing or corrupted' % master_name)
            fix_lo.lo_added = {master_name}
        if master_dex > 0:
            bolt.deprint(
                u'%s has index %d (must be 0)' % (master_name, master_dex))
            lord.remove(master_name)
            lord.insert(0, master_name)
            lo_order_changed = True
        # below do not apply to timestamp method (on getting it)
        loadorder_set = set(lord)
        mods_set = set(self.mod_infos.keys())
        fix_lo.lo_removed = loadorder_set - mods_set # may remove corrupted mods
        # present in text file, we are supposed to take care of that
        fix_lo.lo_added |= mods_set - loadorder_set
        # Remove non existent plugins from load order
        lord[:] = [x for x in lord if x not in fix_lo.lo_removed]
        # See if any esm files are loaded below an esp and reorder as necessary
        ol = lord[:]
        lord.sort(key=lambda m: not self.in_master_block(self.mod_infos[m]))
        lo_order_changed |= ol != lord
        # Append new plugins to load order
        index_first_esp = self._index_of_first_esp(lord)
        for mod in fix_lo.lo_added:
            if self.in_master_block(self.mod_infos[mod]):
                if not mod == master_name:
                    lord.insert(index_first_esp, mod)
                else:
                    lord.insert(0, master_name)
                    bolt.deprint(u'%s inserted to Load order' % master_name)
                index_first_esp += 1
            else: lord.append(mod)
        # end textfile get
        fix_lo.lo_duplicates = self._check_for_duplicates(lord)
        lo_order_changed |= self._order_fixed(lord)
        if lo_order_changed:
            fix_lo.lo_reordered = old_lord, lord

    def _fix_active_plugins(self, acti, lord, on_disc, fix_active):
        # filter plugins not present in modInfos - this will disable
        # corrupted too! Preserve acti order
        quiet = fix_active is None
        if quiet: fix_active = FixInfo() # discard fix info
        # Throw out files that aren't on disk as well as .esu files, which must
        # never be active
        acti_filtered = [x for x in acti if x in self.mod_infos
                         and x.cext != u'.esu']
        fix_active.act_removed = set(acti) - set(acti_filtered)
        if fix_active.act_removed and not quiet:
            # take note as we may need to rewrite plugins txt
            self.mod_infos.selectedBad = fix_active.lo_removed
        if not self.allow_deactivate_master:
            if not self.master_path in acti_filtered:
                acti_filtered.insert(0, self.master_path)
                fix_active.master_not_active = self.master_path
        for path in self.must_be_active_if_present:
            if path in lord and not path in acti_filtered:
                fix_active.missing_must_be_active.append(path)
        # order - affects which mods are chopped off if > 255 (the ones that
        # load last) - won't trigger saving but for Skyrim
        fix_active.act_order_differs_from_load_order += \
            self._check_active_order(acti_filtered, lord)
        for path in fix_active.missing_must_be_active: # insert after the last master
            acti_filtered.insert(self._index_of_first_esp(acti_filtered), path)
        # Check for duplicates
        fix_active.act_duplicates = self._check_for_duplicates(acti_filtered)
        # check if we have more than 256 active mods
        drop_espms, drop_esls = self.check_active_limit(acti_filtered)
        disable = drop_espms | drop_esls
        # update acti in place - this must always be done, since acti may
        # contain files that are no longer on disk (i.e. not in acti_filtered)
        acti[:] = [x for x in acti_filtered if x not in disable]
        if disable: # chop off extra
            self.mod_infos.selectedExtra = fix_active.selectedExtra = [
                x for x in acti_filtered if x in disable]
        before_reorder = acti # with overflowed plugins removed
        if self._order_fixed(acti):
            fix_active.act_reordered = (before_reorder, acti)
        if fix_active.act_changed():
            if on_disc: # used when getting active and found invalid, fix 'em!
                # Notify user and backup previous plugins.txt
                fix_active.act_header = u'Invalid Plugin txt corrected:\n'
                self._backup_active_plugins()
                self._persist_active_plugins(acti, lord)
            else: # active list we passed in when setting load order is invalid
                fix_active.act_header = u'Invalid active plugins list corrected:\n'
            return True # changes, saved if loading plugins.txt
        return False # no changes, not saved

    def check_active_limit(self, acti_filtered):
        return set(acti_filtered[self.max_espms:]), set()

    def _order_fixed(self, lord): return False

    @staticmethod
    def _check_active_order(acti, lord):
        dex_dict = {mod: index for index, mod in enumerate(lord)}
        acti.sort(key=dex_dict.__getitem__)
        return u''

    # HELPERS -----------------------------------------------------------------
    def _index_of_first_esp(self, lord):
        index_of_first_esp = 0
        while index_of_first_esp < len(lord) and self.in_master_block(
            self.mod_infos[lord[index_of_first_esp]]):
            index_of_first_esp += 1
        return index_of_first_esp

    @staticmethod
    def _check_for_duplicates(plugins_list):
        """:type plugins_list: list[bolt.Path]"""
        mods, duplicates, j = set(), set(), 0
        for i, mod in enumerate(plugins_list[:]):
            if mod in mods:
                del plugins_list[i - j]
                j += 1
                duplicates.add(mod)
            else:
                mods.add(mod)
        return duplicates

    # INITIALIZATION ----------------------------------------------------------
    @classmethod
    def parse_ccc_file(cls): pass

class INIGame(Game):
    """Class for games which use an INI section to determine parts of the load
    order. May be used in multiple inheritance with other Game types, just be
    sure to put INIGame first.

    To use an INI section to specify active plugins, change ini_key_actives.
    To use an INI section to specify load order, change ini_key_lo. You can
    also specify both if the game uses an INI for everything.
    Format for them is (INI Name, section, entry format string).
    The entry format string receives a format argument, %(lo_idx)s, which
    corresponds to the load order position of the mod written as a value.
    For example, (u'test.ini', u'Mods', u'Mod%(lo_idx)s') would result in
    something like this:
        [Mods]
        Mod0=FirstMod.esp
        Mod1=SecondMod.esp"""
    # The INI keys, see class docstring for more info
    ini_key_actives = (u'', u'', u'')
    ini_key_lo = (u'', u'', u'')

    def __init__(self, mod_infos, plugins_txt_path=u''):
        """Creates a new INIGame instance. plugins_txt_path does not have to
        be specified if INIGame will manage active plugins."""
        super(INIGame, self).__init__(mod_infos, plugins_txt_path)
        self._handles_actives = self.__class__.ini_key_actives != (
            u'', u'', u'')
        self._handles_lo = self.__class__.ini_key_lo != (u'', u'', u'')
        if self._handles_actives:
            self._cached_ini_actives = self._mk_ini(
                self.ini_dir_actives.join(self.ini_key_actives[0]))
        if self._handles_lo:
            self._cached_ini_lo = self._mk_ini(
                self.ini_dir_lo.join(self.ini_key_lo[0]))

    # INI directories, override if needed
    @property
    def ini_dir_actives(self): # type: () -> bolt.Path
        """Returns the directory containing the actives INI. Defaults to the
        game path."""
        return bass.dirs[u'app']

    @property
    def ini_dir_lo(self): # type: () -> bolt.Path
        """Returns the directory containing the load order INI. Defaults to the
        game path."""
        return bass.dirs[u'app']

    # Utilities
    @staticmethod
    def _mk_ini(ini_fpath):
        """Creates a new IniFile from the specified bolt.Path object."""
        ini_type, ini_encoding = get_ini_type_and_encoding(ini_fpath)
        return ini_type(ini_fpath, ini_encoding)

    @staticmethod
    def _read_ini(cached_ini, ini_key):
        """Reads a section specified INI using the specified key and returns
        all its values, as bolt.Path objects. Handles missing INI file and an
        absent section gracefully.

        :type cached_ini: bosh.ini_files.IniFile
        :type ini_key: tuple[unicode, unicode, unicode]
        :rtype: list[bolt.Path]"""
        # Returned format is dict[CIstr, tuple[unicode, int]], we want the
        # unicode (i.e. the mod names)
        section_mapping = cached_ini.get_setting_values(ini_key[1], {})
        # Sort by line number, then convert the values to paths and return
        section_vals = sorted(section_mapping.items(), key=lambda t: t[1][1])
        return [bolt.GPath(x[1][0]) for x in section_vals]

    @staticmethod
    def _write_ini(cached_ini, ini_key, mod_list):
        """Writes out the specified INI using the specified key and mod list.

        :type cached_ini: bosh.ini_files.IniFile
        :type ini_key: tuple[unicode, unicode, unicode]
        :type mod_list: list[bolt.Path]"""
        # Remove any existing section - also prevents duplicate sections with
        # different case
        cached_ini.remove_section(ini_key[1])
        # Now, write out the changed values - no backup here
        section_contents = OrderedDict()
        for i, lo_mod in enumerate(mod_list):
            section_contents[ini_key[2] % {u'lo_idx': i}] = lo_mod.s
        cached_ini.saveSettings({ini_key[1]: section_contents})

    # Backups
    def _backup_active_plugins(self):
        if self._handles_actives:
            ini_path = self._cached_ini_actives.abs_path
            ini_path.copyTo(ini_path.backup)
        else: super(INIGame, self)._backup_active_plugins()

    def _backup_load_order(self):
        if self._handles_actives:
            ini_path = self._cached_ini_lo.abs_path
            ini_path.copyTo(ini_path.backup)
        else: super(INIGame, self)._backup_load_order()

    # Reading from INI
    def _fetch_active_plugins(self):
        if self._handles_actives:
            actives = self._read_ini(self._cached_ini_actives,
                                     self.__class__.ini_key_actives)
            return actives
        return super(INIGame, self)._fetch_active_plugins()

    def _fetch_load_order(self, cached_load_order, cached_active):
        if self._handles_lo:
            lo = self._read_ini(self._cached_ini_lo,
                                self.__class__.ini_key_lo)
            return lo
        return super(INIGame, self)._fetch_load_order(cached_load_order,
                                                      cached_active)

    # Writing changes to INI
    def _persist_if_changed(self, active, lord, previous_active,
                            previous_lord):
        if self._handles_actives:
            if previous_active is None or previous_active != active:
                self._persist_active_plugins(active, lord)
            # We've handled this, let the next one in line know
            previous_active = active
        if self._handles_lo:
            if previous_lord is None or previous_lord != lord:
                self._persist_load_order(lord, active)
            # Same idea as above
            previous_lord = lord
        # If we handled both, don't do anything. Otherwise, delegate persisting
        # to the next method in the MRO
        if previous_lord != lord or previous_active != active:
            super(INIGame, self)._persist_if_changed(
                active, lord, previous_active, previous_lord)

    def _persist_active_plugins(self, active, lord):
        if self._handles_actives:
            self._write_ini(self._cached_ini_actives,
                            self.__class__.ini_key_actives, active)
            self._cached_ini_actives.do_update()
        else:
            super(INIGame, self)._persist_active_plugins(active, lord)

    def _persist_load_order(self, lord, active):
        if self._handles_lo:
            self._write_ini(self._cached_ini_lo,
                            self.__class__.ini_key_lo, lord)
            self._cached_ini_lo.do_update()
        else:
            super(INIGame, self)._persist_load_order(lord, active)

    # Misc overrides
    @classmethod
    def _must_update_active(cls, deleted, reordered):
        # Can't use _handles_active here, need to duplicate the logic
        if cls.ini_key_actives != (u'', u'', u''):
            return True # Assume order is important for the INI
        return super(INIGame, cls)._must_update_active(deleted, reordered)

    def active_changed(self):
        if self._handles_actives:
            return self._cached_ini_actives.needs_update()
        return super(INIGame, self).active_changed()

    def load_order_changed(self):
        if self._handles_lo:
            return self._cached_ini_lo.needs_update()
        return super(INIGame, self).load_order_changed()

    def swap(self, old_path, new_path):
        def _do_swap(cached_ini, ini_key):
            # If there's no INI inside the old (saves) directory, copy it
            old_ini = old_path.join(ini_key[0])
            if not old_ini.isfile():
                cached_ini.abs_path.copyTo(old_ini)
            # Read from the new INI if it exists and write to our main INI
            move_ini = new_path.join(ini_key[0])
            if move_ini.isfile():
                self._write_ini(cached_ini, ini_key, self._read_ini(
                    self._mk_ini(move_ini), ini_key))
        if self._handles_actives:
            _do_swap(self._cached_ini_actives, self.ini_key_actives)
        if self._handles_lo:
            _do_swap(self._cached_ini_lo, self.ini_key_lo)
        super(INIGame, self).swap(old_path, new_path)

class TimestampGame(Game):
    """Oblivion and other games where load order is set using modification
    times.

    :type _mtime_mods: dict[int, set[bolt.Path]]
    """

    allow_deactivate_master = True
    _mtime_mods = defaultdict(set)
    _get_free_time_step = 1 # step by one second intervals

    @classmethod
    def _must_update_active(cls, deleted, reordered): return deleted

    def has_load_order_conflict(self, mod_name):
        mtime = self.mod_infos[mod_name].mtime
        return mtime in self._mtime_mods and len(self._mtime_mods[mtime]) > 1

    def has_load_order_conflict_active(self, mod_name, active):
        mtime = self.mod_infos[mod_name].mtime
        return self.has_load_order_conflict(mod_name) and bool(
            (self._mtime_mods[mtime] - {mod_name}) & active)

    def get_free_time(self, start_time, default_time='+1', end_time=None):
        all_mtimes = set(x.mtime for x in self.mod_infos.itervalues())
        end_time = end_time or (start_time + 1000) # 1000 (seconds) is an arbitrary limit
        while start_time < end_time:
            if not start_time in all_mtimes:
                return start_time
            start_time += self._get_free_time_step
        return default_time

    # Abstract overrides ------------------------------------------------------
    def __calculate_mtime_order(self, mods=None): # excludes corrupt mods
        if mods is None: mods = self.mod_infos.keys()
        mods = sorted(mods) # sort case insensitive (for time conflicts)
        mods.sort(key=lambda x: self.mod_infos[x].mtime)
        mods.sort(key=lambda x: not self.in_master_block(self.mod_infos[x]))
        return mods

    def _backup_active_plugins(self):
        self.plugins_txt_path.copyTo(self.plugins_txt_path.backup)

    def _backup_load_order(self):
        pass # timestamps, no file to backup

    def _fetch_load_order(self, cached_load_order, cached_active):
        self._rebuild_mtimes_cache() ##: will need that tweaked for lock load order
        return self.__calculate_mtime_order()

    def _fetch_active_plugins(self):
        active, _lo = self._parse_plugins_txt()
        return active

    def _persist_load_order(self, lord, active):
        assert set(self.mod_infos.keys()) == set(lord) # (lord must be valid)
        if len(lord) == 0: return
        current = self.__calculate_mtime_order()
        # break conflicts
        older = self.mod_infos[current[0]].mtime # initialize to game master
        for i, mod in enumerate(current[1:]):
            info = self.mod_infos[mod]
            if info.mtime == older: break
            older = info.mtime
        else: mod = i = None # define i to avoid warning below
        if mod is not None: # respace this and next mods in 60 sec intervals
            for mod in current[i + 1:]:
                info = self.mod_infos[mod]
                older += 60
                info.setmtime(older)
        restamp = []
        for ordered, mod in zip(lord, current):
            if ordered == mod: continue
            restamp.append((ordered, self.mod_infos[mod].mtime))
        for ordered, mtime in restamp:
            self.mod_infos[ordered].setmtime(mtime)
        # rebuild our cache
        self._rebuild_mtimes_cache()

    def _rebuild_mtimes_cache(self):
        self._mtime_mods.clear()
        for mod, info in self.mod_infos.iteritems():
            mtime = info.mtime
            self._mtime_mods[mtime] |= {mod}

    def _persist_active_plugins(self, active, lord):
        self._write_plugins_txt(active, active)

    def _persist_if_changed(self, active, lord, previous_active,
                            previous_lord):
        if previous_lord is None or previous_lord != lord:
            self._persist_load_order(lord, active)
        if previous_active is None or set(previous_active) != set(active):
            self._persist_active_plugins(active, lord)

    def _fix_load_order(self, lord, fix_lo):
        super(TimestampGame, self)._fix_load_order(lord, fix_lo)
        if fix_lo is not None and fix_lo.lo_added:
            # should not occur, except if undoing
            bolt.deprint(u'Incomplete load order passed in to set_load_order. '
                u'Missing: ' + u', '.join(x.s for x in fix_lo.lo_added))
            lord[:] = self.__calculate_mtime_order(mods=lord)

# TimestampGame overrides
class Morrowind(INIGame, TimestampGame):
    """Morrowind uses timestamps for specifying load order, but stores active
    plugins in Morrowind.ini."""
    has_plugins_txt = False
    ini_key_actives = (u'Morrowind.ini', u'Game Files', u'GameFile%(lo_idx)s')

    def in_master_block(self, minf):
        """For Morrowind, extension seems to be the only thing that matters."""
        return minf.get_extension() == u'.esm'

class TextfileGame(Game):

    def __init__(self, mod_infos, plugins_txt_path, loadorder_txt_path):
        super(TextfileGame, self).__init__(mod_infos, plugins_txt_path)
        self.loadorder_txt_path = loadorder_txt_path # type: bolt.Path
        self.mtime_loadorder_txt = 0
        self.size_loadorder_txt = 0

    @property
    def pinned_mods(self):
        return super(TextfileGame, self).pinned_mods | set(
            self.must_be_active_if_present)

    def load_order_changed(self):
        # if active changed externally refetch load order to check for desync
        return self.active_changed() or (self.loadorder_txt_path.exists() and (
            (self.size_loadorder_txt, self.mtime_loadorder_txt) !=
            self.loadorder_txt_path.size_mtime()))

    def __update_lo_cache_info(self):
        self.size_loadorder_txt, self.mtime_loadorder_txt = \
            self.loadorder_txt_path.size_mtime()

    @classmethod
    def _must_update_active(cls, deleted, reordered):
        return deleted or reordered

    def swap(self, old_path, new_path):
        super(TextfileGame, self).swap(old_path, new_path)
        # Save loadorder.txt inside the old (saves) directory
        if self.loadorder_txt_path.exists():
            self.loadorder_txt_path.copyTo(old_path.join(u'loadorder.txt'))
        # Move the new loadorder.txt here for use
        move = new_path.join(u'loadorder.txt')
        if move.exists():
            move.copyTo(self.loadorder_txt_path)
            self.loadorder_txt_path.mtime = time.time() # update mtime to trigger refresh

    # Abstract overrides ------------------------------------------------------
    def _backup_active_plugins(self):
        self.plugins_txt_path.copyTo(self.plugins_txt_path.backup)

    def _backup_load_order(self):
        self.loadorder_txt_path.copyTo(self.loadorder_txt_path.backup)

    def _fetch_load_order(self, cached_load_order, cached_active):
        """Read data from loadorder.txt file. If loadorder.txt does not
        exist create it and try reading plugins.txt so the load order of the
        user is preserved (note it will create the plugins.txt if not
        existing). Additional mods should be added by caller who should
        anyway call _fix_load_order. If cached_active is passed, the relative
        order of mods will be corrected to match their relative order in
        cached_active.
        :type cached_active: tuple[bolt.Path] | list[bolt.Path]"""
        if not self.loadorder_txt_path.exists():
            mods = cached_active or []
            if cached_active is not None and not self.plugins_txt_path.exists():
                self._write_plugins_txt(cached_active, cached_active)
                bolt.deprint(
                    u'Created %s based on cached info' % self.plugins_txt_path)
            elif cached_active is None and self.plugins_txt_path.exists():
                mods = self._fetch_active_plugins() # will add Skyrim.esm
            self._persist_load_order(mods, mods)
            bolt.deprint(u'Created %s' % self.loadorder_txt_path)
            return mods
        #--Read file
        _acti, lo = self._parse_modfile(self.loadorder_txt_path)
        # handle desync with plugins txt
        if cached_active is not None:
            cached_active_copy = cached_active[:]
            active_in_lo = [x for x in lo if x in set(cached_active)]
            w = dict((x, i) for i, x in enumerate(lo))
            while active_in_lo:
                for i, (ordered, current) in enumerate(
                        zip(cached_active_copy, active_in_lo)):
                    if ordered != current:
                        if ordered not in lo:
                            # Mod is in plugins.txt, but not in loadorder.txt;
                            # just drop it from the copy for now, we'll check
                            # if it's really missing in _fix_active_plugins
                            cached_active_copy.remove(ordered)
                            break
                        for j, x in enumerate(active_in_lo[i:]):
                            if x == ordered: break
                            # x should be above ordered
                            to = w[ordered] + 1 + j
                            # make room
                            w = dict((x, i if i < to else i + 1) for x, i in
                                     w.iteritems())
                            w[x] = to # bubble them up !
                        active_in_lo.remove(ordered)
                        cached_active_copy = cached_active_copy[i + 1:]
                        active_in_lo = active_in_lo[i:]
                        break
                else: break
            fetched_lo = lo[:]
            lo.sort(key=w.get)
            if lo != fetched_lo:
                # We fixed a desync, make a backup and write the load order
                self._backup_load_order()
                self._persist_load_order(lo, lo)
                bolt.deprint(u'Corrected %s (order of mods differed from '
                             u'their order in %s)' % (
                        self.loadorder_txt_path, self.plugins_txt_path))
        self.__update_lo_cache_info()
        return lo

    def _fetch_active_plugins(self):
        acti, _lo = self._parse_plugins_txt()
        if self.master_path in acti:
            acti.remove(self.master_path)
            self._write_plugins_txt(acti, acti)
            bolt.deprint(u'Removed %s from %s' % (
                self.master_path, self.plugins_txt_path))
        acti.insert(0, self.master_path)
        return acti

    def _persist_load_order(self, lord, active):
        _write_plugins_txt_(self.loadorder_txt_path, lord, lord, _star=False)
        self.__update_lo_cache_info()

    def _persist_active_plugins(self, active, lord): # must chop off Skyrim.esm
        self._write_plugins_txt(active[1:], active[1:])

    def _persist_if_changed(self, active, lord, previous_active,
                            previous_lord):
        if previous_lord is None or previous_lord != lord:
            self._persist_load_order(lord, active)
        if previous_active is None or previous_active != active:
            self._persist_active_plugins(active, lord)

    # Validation overrides ----------------------------------------------------
    @staticmethod
    def _check_active_order(acti, lord):
        dex_dict = {mod: index for index, mod in enumerate(lord)}
        old = acti[:]
        acti.sort(key=dex_dict.__getitem__) # all present in lord
        if acti != old: # active mods order that disagrees with lord ?
            return (u'Active list order of plugins (%s) differs from supplied '
                    u'load order (%s)') % (_pl(old), _pl(acti))
        return u''

class AsteriskGame(Game):

    max_espms = 254
    max_esls = 4096 # hard limit, game runs out of fds sooner, testing needed
    # Creation Club content file - if empty, indicates that this game has no CC
    _ccc_filename = u''
    # Hardcoded list used if the file specified above does not exist or could
    # not be read
    _ccc_fallback = ()
    _star = True

    @property
    def remove_from_plugins_txt(self): return set()

    @property
    def pinned_mods(self): return self.remove_from_plugins_txt

    def load_order_changed(self): return self._plugins_txt_modified()

    def in_master_block(self, minf,
                        __master_exts=frozenset((u'.esm', u'.esl'))):
        """For esl games .esm and .esl files are set the master flag in
        memory even if not set on the file on disk. For esps we must check
        for the flag explicitly."""
        return minf.get_extension() in __master_exts or minf.has_esm_flag()

    def _cached_or_fetch(self, cached_load_order, cached_active):
        # read the file once
        return self._fetch_load_order(cached_load_order, cached_active)

    @classmethod
    def _must_update_active(cls, deleted, reordered): return True

    # Abstract overrides ------------------------------------------------------
    def _backup_active_plugins(self):
        self.plugins_txt_path.copyTo(self.plugins_txt_path.backup)

    def _backup_load_order(self):
        self._backup_active_plugins() # same thing for asterisk games

    def _fetch_load_order(self, cached_load_order, cached_active):
        """Read data from plugins.txt file. If plugins.txt does not exist
        create it. Discards information read if cached is passed in."""
        exists = self.plugins_txt_path.exists()
        active, lo = self._parse_modfile(self.plugins_txt_path) # empty if not exists
        lo, active = (lo if cached_load_order is None else cached_load_order,
                      active if cached_active is None else cached_active)
        to_drop = []
        for rem in self.remove_from_plugins_txt:
            if rem in active or rem in lo:
                to_drop.append(rem)
        lo, active = self._readd_in_lists(lo, active)
        msg = u''
        if not exists:
            # Create it if it doesn't exist
            msg = u'Created %s'
        if to_drop:
            # If we need to drop some mods, then make a backup first
            self._backup_load_order()
            msg = (u'Removed ' + u' ,'.join(map(unicode, to_drop)) +
                   u' from %s')
        if not exists or to_drop:
            # In either case, write out the LO and deprint it
            self._persist_load_order(lo, active)
            bolt.deprint(msg % self.plugins_txt_path)
        return lo, active

    def _persist_load_order(self, lord, active):
        assert active # must at least contain the master esm for these games
        lord = [x for x in lord if x not in self.remove_from_plugins_txt]
        active = [x for x in active if x not in self.remove_from_plugins_txt]
        self._write_plugins_txt(lord, active)

    def _persist_active_plugins(self, active, lord):
        self._persist_load_order(lord, active)

    def _save_fixed_load_order(self, fix_lo, fixed_active, lo, active):
        if fixed_active: return # plugins.txt already saved
        if fix_lo.lo_changed():
            self._backup_load_order()
            self._persist_load_order(lo, active)

    def _persist_if_changed(self, active, lord, previous_active,
                            previous_lord):
        if (previous_lord is None or previous_lord != lord) or (
                previous_active is None or previous_active != active):
            self._persist_load_order(lord, active)

    # Validation overrides ----------------------------------------------------
    def _order_fixed(self, lord):
        lo = [x for x in lord if x not in self.remove_from_plugins_txt]
        add = self._fixed_order_plugins()
        if add + lo != lord:
            lord[:] = add + lo
            return True
        return False

    def check_active_limit(self, acti_filtered):
        acti_filtered_espm = []
        acti_filtered_esl = []
        for x in acti_filtered:
            (acti_filtered_esl if self.mod_infos[
                x].is_esl() else acti_filtered_espm).append(x)
        return set(acti_filtered_espm[self.max_espms:]) , set(
            acti_filtered_esl[self.max_esls:])

    # Asterisk game specific: plugins with fixed load order -------------------
    def _readd_in_lists(self, lo, active):
        # add the plugins that should not be in plugins.txt in the lists,
        # assuming they should also be active
        add = self._fixed_order_plugins()
        lo = [x for x in lo if x not in self.remove_from_plugins_txt]
        active = [x for x in active if x not in self.remove_from_plugins_txt]
        return add + lo, add + active

    def _fixed_order_plugins(self):
        """Return existing fixed plugins in their fixed load order."""
        add = [self.master_path]
        add.extend(
            x for x in self.must_be_active_if_present if x in self.mod_infos)
        return add

    @classmethod
    def parse_ccc_file(cls):
        if not cls._ccc_filename: return # Abort if this game has no CC
        _ccc_path = bass.dirs[u'app'].join(cls._ccc_filename)
        try:
            with open(_ccc_path.s, u'r') as ins:
                lines = (bolt.GPath(line.strip()) for line in ins.readlines())
                cls.must_be_active_if_present += tuple(lines)
        except (OSError, IOError) as e:
            if e.errno != errno.ENOENT:
                bolt.deprint(u'Failed to open %s' % _ccc_path, traceback=True)
            bolt.deprint(u'%s does not exist or could not be read, falling '
                         u'back to hardcoded CCC list' % cls._ccc_filename)
            cls.must_be_active_if_present += cls._ccc_fallback

# TextfileGame overrides
class Skyrim(TextfileGame):
    must_be_active_if_present = (bolt.GPath(u'Update.esm'),
                                 bolt.GPath(u'Dawnguard.esm'),
                                 bolt.GPath(u'Hearthfires.esm'),
                                 bolt.GPath(u'Dragonborn.esm'))

class Enderal(TextfileGame):
    must_be_active_if_present = (bolt.GPath(u'Update.esm'),
                                 bolt.GPath(u'Enderal - Forgotten '
                                            u'Stories.esm'))

# AsteriskGame overrides
class Fallout4(AsteriskGame):
    must_be_active_if_present = (bolt.GPath(u'DLCRobot.esm'),
                                 bolt.GPath(u'DLCworkshop01.esm'),
                                 bolt.GPath(u'DLCCoast.esm'),
                                 bolt.GPath(u'DLCWorkshop02.esm'),
                                 bolt.GPath(u'DLCWorkshop03.esm'),
                                 bolt.GPath(u'DLCNukaWorld.esm'),
                                 bolt.GPath(u'DLCUltraHighResolution.esm'),)
    _ccc_filename = u'Fallout4.ccc'
    _ccc_fallback = (
        # Up to date as of 2019/11/22
        bolt.GPath(u'ccBGSFO4001-PipBoy(Black).esl'),
        bolt.GPath(u'ccBGSFO4002-PipBoy(Blue).esl'),
        bolt.GPath(u'ccBGSFO4003-PipBoy(Camo01).esl'),
        bolt.GPath(u'ccBGSFO4004-PipBoy(Camo02).esl'),
        bolt.GPath(u'ccBGSFO4006-PipBoy(Chrome).esl'),
        bolt.GPath(u'ccBGSFO4012-PipBoy(Red).esl'),
        bolt.GPath(u'ccBGSFO4014-PipBoy(White).esl'),
        bolt.GPath(u'ccBGSFO4005-BlueCamo.esl'),
        bolt.GPath(u'ccBGSFO4016-Prey.esl'),
        bolt.GPath(u'ccBGSFO4018-GaussRiflePrototype.esl'),
        bolt.GPath(u'ccBGSFO4019-ChineseStealthArmor.esl'),
        bolt.GPath(u'ccBGSFO4020-PowerArmorSkin(Black).esl'),
        bolt.GPath(u'ccBGSFO4022-PowerArmorSkin(Camo01).esl'),
        bolt.GPath(u'ccBGSFO4023-PowerArmorSkin(Camo02).esl'),
        bolt.GPath(u'ccBGSFO4025-PowerArmorSkin(Chrome).esl'),
        bolt.GPath(u'ccBGSFO4033-PowerArmorSkinWhite.esl'),
        bolt.GPath(u'ccBGSFO4024-PACamo03.esl'),
        bolt.GPath(u'ccBGSFO4038-HorseArmor.esl'),
        bolt.GPath(u'ccBGSFO4041-DoomMarineArmor.esl'),
        bolt.GPath(u'ccBGSFO4042-BFG.esl'),
        bolt.GPath(u'ccBGSFO4044-HellfirePowerArmor.esl'),
        bolt.GPath(u'ccFSVFO4001-ModularMilitaryBackpack.esl'),
        bolt.GPath(u'ccFSVFO4002-MidCenturyModern.esl'),
        bolt.GPath(u'ccFRSFO4001-HandmadeShotgun.esl'),
        bolt.GPath(u'ccEEJFO4001-DecorationPack.esl'),
        bolt.GPath(u'ccRZRFO4001-TunnelSnakes.esm'),
        bolt.GPath(u'ccBGSFO4045-AdvArcCab.esl'),
        bolt.GPath(u'ccFSVFO4003-Slocum.esl'),
        bolt.GPath(u'ccGCAFO4001-FactionWS01Army.esl'),
        bolt.GPath(u'ccGCAFO4002-FactionWS02ACat.esl'),
        bolt.GPath(u'ccGCAFO4003-FactionWS03BOS.esl'),
        bolt.GPath(u'ccGCAFO4004-FactionWS04Gun.esl'),
        bolt.GPath(u'ccGCAFO4005-FactionWS05HRPink.esl'),
        bolt.GPath(u'ccGCAFO4006-FactionWS06HRShark.esl'),
        bolt.GPath(u'ccGCAFO4007-FactionWS07HRFlames.esl'),
        bolt.GPath(u'ccGCAFO4008-FactionWS08Inst.esl'),
        bolt.GPath(u'ccGCAFO4009-FactionWS09MM.esl'),
        bolt.GPath(u'ccGCAFO4010-FactionWS10RR.esl'),
        bolt.GPath(u'ccGCAFO4011-FactionWS11VT.esl'),
        bolt.GPath(u'ccGCAFO4012-FactionAS01ACat.esl'),
        bolt.GPath(u'ccGCAFO4013-FactionAS02BoS.esl'),
        bolt.GPath(u'ccGCAFO4014-FactionAS03Gun.esl'),
        bolt.GPath(u'ccGCAFO4015-FactionAS04HRPink.esl'),
        bolt.GPath(u'ccGCAFO4016-FactionAS05HRShark.esl'),
        bolt.GPath(u'ccGCAFO4017-FactionAS06Inst.esl'),
        bolt.GPath(u'ccGCAFO4018-FactionAS07MM.esl'),
        bolt.GPath(u'ccGCAFO4019-FactionAS08Nuk.esl'),
        bolt.GPath(u'ccGCAFO4020-FactionAS09RR.esl'),
        bolt.GPath(u'ccGCAFO4021-FactionAS10HRFlames.esl'),
        bolt.GPath(u'ccGCAFO4022-FactionAS11VT.esl'),
        bolt.GPath(u'ccGCAFO4023-FactionAS12Army.esl'),
        bolt.GPath(u'ccAWNFO4001-BrandedAttire.esl'),
        bolt.GPath(u'ccSWKFO4001-AstronautPowerArmor.esm'),
        bolt.GPath(u'ccSWKFO4002-PipNuka.esl'),
        bolt.GPath(u'ccSWKFO4003-PipQuan.esl'),
        bolt.GPath(u'ccBGSFO4050-DgBColl.esl'),
        bolt.GPath(u'ccBGSFO4051-DgBox.esl'),
        bolt.GPath(u'ccBGSFO4052-DgDal.esl'),
        bolt.GPath(u'ccBGSFO4053-DgGoldR.esl'),
        bolt.GPath(u'ccBGSFO4054-DgGreatD.esl'),
        bolt.GPath(u'ccBGSFO4055-DgHusk.esl'),
        bolt.GPath(u'ccBGSFO4056-DgLabB.esl'),
        bolt.GPath(u'ccBGSFO4057-DgLabY.esl'),
        bolt.GPath(u'ccBGSFO4058-DGLabC.esl'),
        bolt.GPath(u'ccBGSFO4059-DgPit.esl'),
        bolt.GPath(u'ccBGSFO4060-DgRot.esl'),
        bolt.GPath(u'ccBGSFO4061-DgShiInu.esl'),
        bolt.GPath(u'ccBGSFO4036-TrnsDg.esl'),
        bolt.GPath(u'ccRZRFO4004-PipInst.esl'),
        bolt.GPath(u'ccBGSFO4062-PipPat.esl'),
        bolt.GPath(u'ccRZRFO4003-PipOver.esl'),
        bolt.GPath(u'ccFRSFO4002-AntimaterielRifle.esl'),
        bolt.GPath(u'ccEEJFO4002-Nuka.esl'),
        bolt.GPath(u'ccYGPFO4001-PipCruiser.esl'),
        bolt.GPath(u'ccBGSFO4072-PipGrog.esl'),
        bolt.GPath(u'ccBGSFO4073-PipMMan.esl'),
        bolt.GPath(u'ccBGSFO4074-PipInspect.esl'),
        bolt.GPath(u'ccBGSFO4075-PipShroud.esl'),
        bolt.GPath(u'ccBGSFO4076-PipMystery.esl'),
        bolt.GPath(u'ccBGSFO4071-PipArc.esl'),
        bolt.GPath(u'ccBGSFO4079-PipVim.esl'),
        bolt.GPath(u'ccBGSFO4078-PipReily.esl'),
        bolt.GPath(u'ccBGSFO4077-PipRocket.esl'),
        bolt.GPath(u'ccBGSFO4070-PipAbra.esl'),
        bolt.GPath(u'ccBGSFO4008-PipGrn.esl'),
        bolt.GPath(u'ccBGSFO4015-PipYell.esl'),
        bolt.GPath(u'ccBGSFO4009-PipOran.esl'),
        bolt.GPath(u'ccBGSFO4011-PipPurp.esl'),
        bolt.GPath(u'ccBGSFO4021-PowerArmorSkinBlue.esl'),
        bolt.GPath(u'ccBGSFO4027-PowerArmorSkinGreen.esl'),
        bolt.GPath(u'ccBGSFO4034-PowerArmorSkinYellow.esl'),
        bolt.GPath(u'ccBGSFO4028-PowerArmorSkinOrange.esl'),
        bolt.GPath(u'ccBGSFO4031-PowerArmorSkinRed.esl'),
        bolt.GPath(u'ccBGSFO4030-PowerArmorSkinPurple.esl'),
        bolt.GPath(u'ccBGSFO4032-PowerArmorSkinTan.esl'),
        bolt.GPath(u'ccBGSFO4029-PowerArmorSkinPink.esl'),
        bolt.GPath(u'ccGRCFO4001-PipGreyTort.esl'),
        bolt.GPath(u'ccGRCFO4002-PipGreenVim.esl'),
        bolt.GPath(u'ccBGSFO4013-PipTan.esl'),
        bolt.GPath(u'ccBGSFO4010-PipPnk.esl'),
        bolt.GPath(u'ccSBJFO4001-SolarFlare.esl'),
        bolt.GPath(u'ccZSEF04001-BHouse.esm'),
        bolt.GPath(u'ccTOSFO4001-NeoSky.esm'),
        bolt.GPath(u'ccKGJFO4001-bastion.esl'),
        bolt.GPath(u'ccBGSFO4063-PAPat.esl'),
        bolt.GPath(u'ccQDRFO4001_PowerArmorAI.esl'),
        bolt.GPath(u'ccBGSFO4048-Dovah.esl'),
        bolt.GPath(u'ccBGSFO4101-AS_Shi.esl'),
        bolt.GPath(u'ccBGSFO4114-WS_Shi.esl'),
        bolt.GPath(u'ccBGSFO4115-X02.esl'),
        bolt.GPath(u'ccRZRFO4002-Disintegrate.esl'),
        bolt.GPath(u'ccBGSFO4116-HeavyFlamer.esl'),
        bolt.GPath(u'ccBGSFO4091-AS_Bats.esl'),
        bolt.GPath(u'ccBGSFO4092-AS_CamoBlue.esl'),
        bolt.GPath(u'ccBGSFO4093-AS_CamoGreen.esl'),
        bolt.GPath(u'ccBGSFO4094-AS_CamoTan.esl'),
        bolt.GPath(u'ccBGSFO4097-AS_Jack-oLantern.esl'),
        bolt.GPath(u'ccBGSFO4104-WS_Bats.esl'),
        bolt.GPath(u'ccBGSFO4105-WS_CamoBlue.esl'),
        bolt.GPath(u'ccBGSFO4106-WS_CamoGreen.esl'),
        bolt.GPath(u'ccBGSFO4107-WS_CamoTan.esl'),
        bolt.GPath(u'ccBGSFO4111-WS_Jack-oLantern.esl'),
        bolt.GPath(u'ccBGSFO4118-WS_TunnelSnakes.esl'),
        bolt.GPath(u'ccBGSFO4113-WS_ReillysRangers.esl'),
        bolt.GPath(u'ccBGSFO4112-WS_Pickman.esl'),
        bolt.GPath(u'ccBGSFO4110-WS_Enclave.esl'),
        bolt.GPath(u'ccBGSFO4108-WS_ChildrenOfAtom.esl'),
        bolt.GPath(u'ccBGSFO4103-AS_TunnelSnakes.esl'),
        bolt.GPath(u'ccBGSFO4099-AS_ReillysRangers.esl'),
        bolt.GPath(u'ccBGSFO4098-AS_Pickman.esl'),
        bolt.GPath(u'ccBGSFO4096-AS_Enclave.esl'),
        bolt.GPath(u'ccBGSFO4095-AS_ChildrenOfAtom.esl'),
        bolt.GPath(u'ccBGSFO4090-PipTribal.esl'),
        bolt.GPath(u'ccBGSFO4089-PipSynthwave.esl'),
        bolt.GPath(u'ccBGSFO4087-PipHaida.esl'),
        bolt.GPath(u'ccBGSFO4085-PipHawaii.esl'),
        bolt.GPath(u'ccBGSFO4084-PipRetro.esl'),
        bolt.GPath(u'ccBGSFO4083-PipArtDeco.esl'),
        bolt.GPath(u'ccBGSFO4082-PipPRC.esl'),
        bolt.GPath(u'ccBGSFO4081-PipPhenolResin.esl'),
        bolt.GPath(u'ccBGSFO4080-PipPop.esl'),
        bolt.GPath(u'ccBGSFO4035-Pint.esl'),
        bolt.GPath(u'ccBGSFO4086-PipAdventure.esl'),
        bolt.GPath(u'ccJVDFO4001-Holiday.esl'),
        bolt.GPath(u'ccBGSFO4047-QThund.esl'),
        bolt.GPath(u'ccFRSFO4003-CR75L.esl'),
        bolt.GPath(u'ccZSEFO4002-SManor.esm'),
        bolt.GPath(u'ccACXFO4001-VSuit.esl'),
        bolt.GPath(u'ccBGSFO4040-VRWorkshop01.esl'),
        bolt.GPath(u'ccFSVFO4005-VRDesertIsland.esl'),
        bolt.GPath(u'ccFSVFO4006-VRWasteland.esl'),
        bolt.GPath(u'ccSBJFO4002_ManwellRifle.esl'),
        bolt.GPath(u'ccTOSFO4002_NeonFlats.esm'),
        bolt.GPath(u'ccBGSFO4117-CapMerc.esl'),
        bolt.GPath(u'ccFSVFO4004-VRWorkshopGNRPlaza.esl'),
        bolt.GPath(u'ccBGSFO4046-TesCan.esl'),
        bolt.GPath(u'ccGCAFO4025-PAGunMM.esl'),
        bolt.GPath(u'ccCRSFO4001-PipCoA.esl'),
    )

    @property
    def remove_from_plugins_txt(self):
        return {bolt.GPath(u'Fallout4.esm')} | set(
            self.must_be_active_if_present)

class Fallout4VR(Fallout4):
    must_be_active_if_present = (bolt.GPath(u'Fallout4_VR.esm'),)
    _ccc_filename = u''

class SkyrimSE(AsteriskGame):
    must_be_active_if_present = (bolt.GPath(u'Update.esm'),
                                 bolt.GPath(u'Dawnguard.esm'),
                                 bolt.GPath(u'Hearthfires.esm'),
                                 bolt.GPath(u'Dragonborn.esm'),)
    _ccc_filename = u'Skyrim.ccc'
    _ccc_fallback = (
        # Up to date as of 2019/11/22
        bolt.GPath(u'ccBGSSSE002-ExoticArrows.esl'),
        bolt.GPath(u'ccBGSSSE003-Zombies.esl'),
        bolt.GPath(u'ccBGSSSE004-RuinsEdge.esl'),
        bolt.GPath(u'ccBGSSSE006-StendarsHammer.esl'),
        bolt.GPath(u'ccBGSSSE007-Chrysamere.esl'),
        bolt.GPath(u'ccBGSSSE010-PetDwarvenArmoredMudcrab.esl'),
        bolt.GPath(u'ccBGSSSE014-SpellPack01.esl'),
        bolt.GPath(u'ccBGSSSE019-StaffofSheogorath.esl'),
        bolt.GPath(u'ccBGSSSE020-GrayCowl.esl'),
        bolt.GPath(u'ccBGSSSE021-LordsMail.esl'),
        bolt.GPath(u'ccMTYSSE001-KnightsoftheNine.esl'),
        bolt.GPath(u'ccQDRSSE001-SurvivalMode.esl'),
        bolt.GPath(u'ccTWBSSE001-PuzzleDungeon.esm'),
        bolt.GPath(u'ccEEJSSE001-Hstead.esm'),
        bolt.GPath(u'ccQDRSSE002-Firewood.esl'),
        bolt.GPath(u'ccBGSSSE018-Shadowrend.esl'),
        bolt.GPath(u'ccBGSSSE035-PetNHound.esl'),
        bolt.GPath(u'ccFSVSSE001-Backpacks.esl'),
        bolt.GPath(u'ccEEJSSE002-Tower.esl'),
        bolt.GPath(u'ccEDHSSE001-NorJewel.esl'),
        bolt.GPath(u'ccVSVSSE002-Pets.esl'),
        bolt.GPath(u'ccBGSSSE037-Curios.esl'),
        bolt.GPath(u'ccBGSSSE034-MntUni.esl'),
        bolt.GPath(u'ccBGSSSE045-Hasedoki.esl'),
        bolt.GPath(u'ccBGSSSE008-Wraithguard.esl'),
        bolt.GPath(u'ccBGSSSE036-PetBWolf.esl'),
        bolt.GPath(u'ccFFBSSE001-ImperialDragon.esl'),
        bolt.GPath(u'ccMTYSSE002-VE.esl'),
        bolt.GPath(u'ccBGSSSE043-CrossElv.esl'),
        bolt.GPath(u'ccVSVSSE001-Winter.esl'),
        bolt.GPath(u'ccEEJSSE003-Hollow.esl'),
        bolt.GPath(u'ccBGSSSE016-Umbra.esm'),
        bolt.GPath(u'ccBGSSSE031-AdvCyrus.esm'),
        bolt.GPath(u'ccBGSSSE040-AdvObGobs.esl'),
        bolt.GPath(u'ccBGSSSE050-BA_Daedric.esl'),
        bolt.GPath(u'ccBGSSSE052-BA_Iron.esl'),
        bolt.GPath(u'ccBGSSSE054-BA_Orcish.esl'),
        bolt.GPath(u'ccBGSSSE058-BA_Steel.esl'),
        bolt.GPath(u'ccBGSSSE059-BA_Dragonplate.esl'),
        bolt.GPath(u'ccBGSSSE061-BA_Dwarven.esl'),
        bolt.GPath(u'ccPEWSSE002-ArmsOfChaos.esl'),
        bolt.GPath(u'ccBGSSSE041-NetchLeather.esl'),
        bolt.GPath(u'ccEDHSSE002-SplKntSet.esl'),
        bolt.GPath(u'ccBGSSSE064-BA_Elven.esl'),
        bolt.GPath(u'ccBGSSSE063-BA_Ebony.esl'),
        bolt.GPath(u'ccBGSSSE062-BA_DwarvenMail.esl'),
        bolt.GPath(u'ccBGSSSE060-BA_Dragonscale.esl'),
        bolt.GPath(u'ccBGSSSE056-BA_Silver.esl'),
        bolt.GPath(u'ccBGSSSE055-BA_OrcishScaled.esl'),
        bolt.GPath(u'ccBGSSSE053-BA_Leather.esl'),
        bolt.GPath(u'ccBGSSSE051-BA_DaedricMail.esl'),
        bolt.GPath(u'ccBGSSSE057-BA_Stalhrim.esl'),
        bolt.GPath(u'ccVSVSSE003-NecroArts.esl'),
        bolt.GPath(u'ccBGSSSE025-AdvDSGS.esm'),
        bolt.GPath(u'ccFFBSSE002-CrossbowPack.esl'),
        bolt.GPath(u'ccBGSSSE013-Dawnfang.esl'),
        bolt.GPath(u'ccRMSSSE001-NecroHouse.esl'),
        bolt.GPath(u'ccEEJSSE004-Hall.esl'),
    )

    @property
    def remove_from_plugins_txt(self):
        return {bolt.GPath(u'Skyrim.esm')} | set(
            self.must_be_active_if_present)

    __dlc_spacing = 60 # in seconds
    def _fixed_order_plugins(self):
        """Return the semi fixed plugins after pinning them in correct order by
        timestamping them."""
        # get existing
        add = [self.master_path]
        add.extend(
            x for x in self.must_be_active_if_present if x in self.mod_infos)
        # rewrite mtimes
        master_mtime = self.mod_infos[self.master_path].mtime
        update = bolt.GPath(u'Update.esm')
        for dlc in add[1:]:
            if dlc == update:
                master_mtime = self.mod_infos[update].mtime
            else:
                master_mtime += self.__dlc_spacing
                dlc_mtime = self.mod_infos[dlc].mtime
                if dlc_mtime != master_mtime:
                    self.mod_infos[dlc].setmtime(master_mtime)
                    bolt.deprint(u'Restamped %s  from %s to %s' % (
                        dlc, format_date(dlc_mtime),
                        format_date(master_mtime)))
        return add

    def _persist_load_order(self, lord, active):
        # Write the primary file, then make a copy for the CK to use (it looks
        # for plugins.txt in the wrong path, namely the game folder, not
        # AppData\Local - and then falls back to timestamps when it can't find
        # plugins.txt in the game folder)
        # Note that this is fixed in FO4, and seems to crash the Skyrim LE CK,
        # so we only do it for SSE
        super(SkyrimSE, self)._persist_load_order(lord, active)
        self.plugins_txt_path.copyTo(bass.dirs[u'app'].join(u'plugins.txt'))

class SkyrimVR(SkyrimSE):
    must_be_active_if_present = (bolt.GPath(u'Update.esm'),
                                 bolt.GPath(u'Dawnguard.esm'),
                                 bolt.GPath(u'Hearthfires.esm'),
                                 bolt.GPath(u'Dragonborn.esm'),
                                 bolt.GPath(u'SkyrimVR.esm'),)
    _ccc_filename = u''

# Game factory
def game_factory(game_fsName, mod_infos, plugins_txt_path,
                 loadorder_txt_path=None):
    if game_fsName == u'Skyrim':
        return Skyrim(mod_infos, plugins_txt_path, loadorder_txt_path)
    if game_fsName == u'Enderal':
        return Enderal(mod_infos, plugins_txt_path, loadorder_txt_path)
    elif game_fsName == u'Skyrim Special Edition':
        return SkyrimSE(mod_infos, plugins_txt_path)
    elif game_fsName == u'Skyrim VR':
        return SkyrimVR(mod_infos, plugins_txt_path)
    elif game_fsName == u'Fallout4':
        return Fallout4(mod_infos, plugins_txt_path)
    elif game_fsName == u'Fallout4VR':
        return Fallout4VR(mod_infos, plugins_txt_path)
    elif game_fsName == u'Morrowind':
        return Morrowind(mod_infos)
    else:
        return TimestampGame(mod_infos, plugins_txt_path)

# Print helpers
def _pl(it, legend=u'', joint=u', '):
    return legend + joint.join(u'%s' % x for x in it) # use Path.__unicode__
