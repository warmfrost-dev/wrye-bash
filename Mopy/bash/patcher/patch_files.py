# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash.  If not, see <https://www.gnu.org/licenses/>.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2020 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================
from __future__ import print_function
import time
from collections import defaultdict, Counter
from itertools import chain
from operator import attrgetter
from .. import bush # for game etc
from .. import bolt # for type hints
from ..balt import readme_url
from .. import load_order
from .. import bass
from ..brec import MreRecord, RecHeader
from ..bolt import GPath, SubProgress, deprint, Progress
from ..exception import BoltError, CancelError, ModError
from ..localize import format_date
from ..mod_files import ModFile, LoadFactory

# the currently executing patch set in _Mod_Patch_Update before showing the
# dialog - used in getAutoItems, to get mods loading before the patch
##: HACK ! replace with method param once gui_patchers are refactored
executing_patch = None # type: bolt.Path

class PatchFile(ModFile):
    """Base class of patch files. Wraps an executing bashed Patch."""

    def set_mergeable_mods(self, mergeMods):
        """Set `mergeSet` attribute to the srcs of MergePatchesPatcher. Update
        allMods and allSet to include the mergeMods"""
        self.mergeSet = set(mergeMods)
        self.allMods = load_order.get_ordered(self.loadSet | self.mergeSet)
        self.allSet = frozenset(self.allMods)

    def _log_header(self, log, patch_name):
        log.setHeader((u'= %s' % patch_name) + u' ' + u'=' * 30 + u'#', True)
        log(u'{{CONTENTS=1}}')
        #--Load Mods and error mods
        log.setHeader(u'= ' + _(u'Overview'), True)
        log.setHeader(u'=== ' + _(u'Date/Time'))
        log(u'* ' + format_date(time.time()))
        log(u'* ' + _(u'Elapsed Time: ') + u'TIMEPLACEHOLDER')
        def _link(link_id):
            return (readme_url(mopy=bass.dirs[u'mopy'], advanced=True),
                    u'#%s' % link_id)
        if self.patcher_mod_skipcount:
            log.setHeader(u'=== ' + _(u'Skipped Imports'))
            log(_(u'The following import patchers skipped records because the '
                  u'imported record required a missing or non-active mod to '
                  u'work properly. If this was not intentional, rebuild the '
                  u'patch after either deactivating the imported mods listed '
                  u'below or activating the missing mod(s).'))
            for patcher, mod_skipcount in \
                    self.patcher_mod_skipcount.iteritems():
                log(u'* ' + _(u'%s skipped %d records:') % (
                patcher, sum(mod_skipcount.values())))
                for mod, skipcount in mod_skipcount.iteritems():
                    log(u'  * ' + _(
                        u'The imported mod, %s, skipped %d records.') % (
                        mod, skipcount))
        if self.unFilteredMods:
            log.setHeader(u'=== ' + _(u'Unfiltered Mods'))
            log(_(u'The following mods were active when the patch was built. '
                  u'For the mods to work properly, you should deactivate the '
                  u'mods and then rebuild the patch with the mods [['
                  u'%s%s|Merged]] in.') % _link(u'patch-filter'))
            for mod in self.unFilteredMods: log(u'* %s' % mod)
        if self.loadErrorMods:
            log.setHeader(u'=== ' + _(u'Load Error Mods'))
            log(_(u'The following mods had load errors and were skipped while '
                  u'building the patch. Most likely this problem is due to a '
                  u'badly formatted mod. For more info, see [['
                  u'http://www.uesp.net/wiki/Tes4Mod:Wrye_Bash/Bashed_Patch'
                  u'#Error_Messages|Bashed Patch: Error Messages]].'))
            for (mod, e) in self.loadErrorMods: log(
                u'* %s' % mod + u': %s' % e)
        if self.worldOrphanMods:
            log.setHeader(u'=== ' + _(u'World Orphans'))
            log(_(u'The following mods had orphaned world groups, which were '
                  u'skipped. This is not a major problem, but you might want '
                  u"to use Bash's [[%s%s|Remove World Orphans]] command to "
                  u'repair the mods.') % _link(u'modsRemoveWorldOrphans'))
            for mod in self.worldOrphanMods: log(u'* %s' % mod)
        if self.compiledAllMods:
            log.setHeader(u'=== ' + _(u'Compiled All'))
            log(_(u'The following mods have an empty compiled version of '
                  u'genericLoreScript. This is usually a sign that the mod '
                  u'author did a __compile all__ while editing scripts. This '
                  u'may interfere with the behavior of other mods that '
                  u'intentionally modify scripts from %s. (E.g. Cobl '
                  u"and Unofficial Oblivion Patch.) You can use Bash's [["
                  u'%s%s|Decompile All]] command to repair the mods.'
                  ) % ((bush.game.master_file,) + _link(u'modsDecompileAll')))
            for mod in self.compiledAllMods: log(u'* %s' % mod)
        log.setHeader(u'=== ' + _(u'Active Mods'), True)
        for mname in self.allMods:
            version = self.p_file_minfos.getVersion(mname)
            if mname in self.loadSet:
                message = u'* %02X ' % (self.loadMods.index(mname),)
            else:
                message = u'* ++ '
            if version:
                message += _(u'%s  [Version %s]') % (mname,version)
            else:
                message += mname.s
            log(message)
        #--Load Mods and error mods
        if self.pfile_aliases:
            log.setHeader(u'= ' + _(u'Mod Aliases'))
            for alias_target, alias_repl in sorted(self.pfile_aliases.iteritems()):
                log(u'* %s >> %s' % (alias_target, alias_repl))

    def init_patchers_data(self, patchers, progress):
        """Gives each patcher a chance to get its source data."""
        self._patcher_instances = [p for p in patchers if p.isActive]
        if not self._patcher_instances: return
        progress = progress.setFull(len(self._patcher_instances))
        for index, patcher in enumerate(self._patcher_instances):
            progress(index, _(u'Preparing') + u'\n' + patcher.getName())
            patcher.initData(SubProgress(progress, index))
        progress(progress.full, _(u'Patchers prepared.'))
        # initData may set isActive to zero - TODO(ut) track down
        self._patcher_instances = [p for p in patchers if p.isActive]

    #--Instance
    def __init__(self, modInfo, p_file_minfos):
        """Initialization."""
        ModFile.__init__(self,modInfo,None)
        self.tes4.author = u'BASHED PATCH'
        self.tes4.masters = [p_file_minfos.masterName]
        self.longFids = True
        self.keepIds = set()
        # Aliases from one mod name to another. Used by text file patchers.
        self.pfile_aliases = {}
        self.mergeIds = set()
        self.loadErrorMods = []
        self.worldOrphanMods = []
        self.unFilteredMods = []
        self.compiledAllMods = []
        self.patcher_mod_skipcount = defaultdict(Counter)
        #--Config
        self.bodyTags = bush.game.body_tags
        #--Mods
        # checking for files to include in patch, investigate
        loadMods = [m for m in load_order.cached_lower_loading(
            modInfo.name) if load_order.cached_is_active(m)]
        if not loadMods:
            raise BoltError(u"No active mods loading before the bashed patch")
        self.loadMods = tuple(loadMods)
        self.loadSet = frozenset(self.loadMods)
        self.set_mergeable_mods([])
        self.p_file_minfos = p_file_minfos

    def getKeeper(self):
        """Returns a function to add fids to self.keepIds."""
        return self.keepIds.add

    def new_gmst(self, gmst_eid, gmst_val):
        """Creates a new GMST record and adds it to this patch."""
        gmst_rec = MreRecord.type_class[b'GMST'](RecHeader(b'GMST'))
        gmst_rec.eid = gmst_eid
        gmst_rec.value = gmst_val
        gmst_rec.longFids = True
        gmst_rec.fid = (self.fileInfo.name, self.tes4.getNextObject())
        self.keepIds.add(gmst_rec.fid)
        self.tops[b'GMST'].setRecord(gmst_rec)

    def initFactories(self,progress):
        """Gets load factories."""
        progress(0, _(u'Processing.'))
        read_sigs = set(bush.game.readClasses) | set(chain.from_iterable(
                p.getReadClasses for p in self._patcher_instances))
        self.readFactory = LoadFactory(False, by_sig=read_sigs)
        write_sigs = set(bush.game.writeClasses) | set(chain.from_iterable(
                p.getWriteClasses for p in self._patcher_instances))
        self.loadFactory = LoadFactory(True, by_sig=write_sigs)
        #--Merge Factory
        self.mergeFactory = LoadFactory(False, by_sig=(r.rec_sig for r in
                                                       bush.game.mergeClasses))

    def scanLoadMods(self,progress):
        """Scans load+merge mods."""
        nullProgress = Progress()
        progress = progress.setFull(len(self.allMods))
        for index,modName in enumerate(self.allMods):
            modInfo = self.p_file_minfos[modName]
            bashTags = modInfo.getBashTags()
            if modName in self.loadSet and u'Filter' in bashTags:
                self.unFilteredMods.append(modName)
            try:
                loadFactory = (self.readFactory,self.mergeFactory)[modName in self.mergeSet]
                progress(index, u'%s\n' % modName + _(u'Loading...'))
                modFile = ModFile(modInfo,loadFactory)
                modFile.load(True,SubProgress(progress,index,index+0.5))
            except ModError as e:
                deprint(u'load error:', traceback=True)
                self.loadErrorMods.append((modName,e))
                continue
            try:
                #--Error checks
                if b'WRLD' in modFile.tops and modFile.tops[b'WRLD'].orphansSkipped:
                    self.worldOrphanMods.append(modName)
                # TODO adapt for other games
                if bush.game.fsName == u'Oblivion' and b'SCPT' in \
                        modFile.tops and \
                        modName != GPath(bush.game.master_file):
                    gls = modFile.tops[b'SCPT'].getRecord(0x00025811)
                    if gls and gls.compiled_size == 4 and gls.last_index == 0:
                        self.compiledAllMods.append(modName)
                pstate = index+0.5
                isMerged = modName in self.mergeSet
                doFilter = isMerged and u'Filter' in bashTags
                #--iiMode is a hack to support Item Interchange. Actual key used is IIM.
                iiMode = isMerged and u'IIM' in bashTags
                if isMerged:
                    progress(pstate, u'%s\n' % modName + _(u'Merging...'))
                    self.mergeModFile(modFile, doFilter, iiMode)
                else:
                    progress(pstate, u'%s\n' % modName + _(u'Scanning...'))
                    self.update_patch_records_from_mod(modFile)
                for patcher in sorted(self._patcher_instances,
                        key=attrgetter(u'patcher_order')):
                    if iiMode and not patcher.iiMode: continue
                    progress(pstate, u'%s\n%s' % (modName, patcher.getName()))
                    patcher.scan_mod_file(modFile,nullProgress)
            except CancelError:
                raise
            except:
                print(u'MERGE/SCAN ERROR: %s' % modName)
                raise
        progress(progress.full,_(u'Load mods scanned.'))

    def mergeModFile(self, modFile, doFilter, iiMode):
        """Copies contents of modFile into self."""
        def add_to_factories(merged_sig):
            """Makes sure that once we merge a record type, all later plugin
            loads will load that record type too so that we can update the
            merged records according to load order."""
            if merged_sig not in self.loadFactory.recTypes:
                merged_class = self.mergeFactory.type_class[merged_sig]
                self.readFactory.addClass(merged_class)
                self.loadFactory.addClass(merged_class)
        for top_grup_sig,block in modFile.tops.iteritems():
            for s in block.get_all_signatures():
                add_to_factories(s)
            iiSkipMerge = iiMode and top_grup_sig not in bush.game.listTypes
            self.tops[top_grup_sig].merge_records(block, self.loadSet,
                self.mergeIds, iiSkipMerge, doFilter)

    def update_patch_records_from_mod(self, modFile):
        """Scans file and overwrites own records with modfile records."""
        #--Keep all MGEFs
        if b'MGEF' in modFile.tops:
            for record in modFile.tops[b'MGEF'].getActiveRecords():
                self.tops[b'MGEF'].setRecord(record.getTypeCopy())
        #--Merger, override.
        for block_type in set(self.tops) & set(modFile.tops):
            self.tops[block_type].updateRecords(modFile.tops[block_type],
                                                self.mergeIds)

    def buildPatch(self,log,progress):
        """Completes merge process. Use this when finished using
        scanLoadMods."""
        if not self._patcher_instances: return
        self._log_header(log, self.fileInfo.name)
        # Run buildPatch on each patcher
        self.keepIds |= self.mergeIds
        subProgress = SubProgress(progress, 0, 0.9, len(self._patcher_instances))
        for index,patcher in enumerate(sorted(self._patcher_instances,
                key=attrgetter(u'patcher_order'))):
            subProgress(index,_(u'Completing')+u'\n%s...' % patcher.getName())
            patcher.buildPatch(log,SubProgress(subProgress,index))
        # Trim records to only keep ones we actually changed
        progress(0.9,_(u'Completing')+u'\n'+_(u'Trimming records...'))
        for block in self.tops.values():
            block.keepRecords(self.keepIds)
        progress(0.95,_(u'Completing')+u'\n'+_(u'Converting fids...'))
        # Convert masters to short fids
        self.tes4.masters = self.getMastersUsed()
        progress(1.0, _(u'Compiled.'))
        # Build the description
        numRecords = sum([x.getNumRecords(False) for x in self.tops.values()])
        self.tes4.description = (
                _(u'Updated: ') + format_date(time.time()) + u'\n\n' + _(
                u'Records Changed: %d') % numRecords)
        # Flag as ESL if the game supports them and the option is enabled
        # Note that we can always safely mark as ESL as long as the number of
        # new records we created is smaller than 0xFFF, since the BP only ever
        # copies overrides into itself, no new records. The only new records it
        # can contain come from Tweak Settings, which creates them through
        # getNextObject and so properly increments nextObject.
        if (bush.game.has_esl and bass.settings[u'bash.mods.auto_flag_esl'] and
                self.tes4.nextObject <= 0xFFF):
            self.tes4.flags1.eslFile = True
            self.tes4.description += u'\n' + _(
                u'This patch has been automatically ESL-flagged to save a '
                u'load order slot.')
