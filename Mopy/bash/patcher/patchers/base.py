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

"""This module contains base patcher classes."""
from __future__ import print_function
from collections import Counter
from itertools import chain
from operator import itemgetter
# Internal
from .. import getPatchesPath
from ..base import AMultiTweakItem, AMultiTweaker, Patcher, CBash_Patcher, \
    AAliasesPatcher, AListPatcher, AImportPatcher, APatchMerger, \
    AUpdateReferences
from ... import load_order, bush
from ...bolt import GPath, CsvReader, deprint
from ...brec import MreRecord

# Patchers 1 ------------------------------------------------------------------
class ListPatcher(AListPatcher,Patcher): pass

class CBash_ListPatcher(AListPatcher,CBash_Patcher):

    def __init__(self, p_name, p_file, p_sources):
        if not self.allowUnloaded:
            p_sources = [s for s in p_sources if s in p_file.allSet or
                         not p_file.p_file_minfos.rightFileType(s.s)]
        super(CBash_ListPatcher, self).__init__(p_name, p_file, p_sources)
        # used in all subclasses except CBash_RacePatcher,
        # CBash_PatchMerger, CBash_UpdateReferences
        self.mod_count = Counter()

class MultiTweakItem(AMultiTweakItem):
    # Notice the differences from Patcher in scanModFile and buildPatch
    # TODO: scanModFile() have VERY similar code - use getReadClasses here ?

    def getReadClasses(self):
        """Returns load factory classes needed for reading."""
        return self.__class__.tweak_read_classes

    def getWriteClasses(self):
        """Returns load factory classes needed for writing."""
        return self.__class__.tweak_read_classes

    def scanModFile(self,modFile,progress,patchFile): # extra param: patchFile
        """Scans specified mod file to extract info. May add record to patch
        mod, but won't alter it. If adds record, should first convert it to
        long fids."""
        pass

    def buildPatch(self,log,progress,patchFile): # extra param: patchFile
        """Edits patch file as desired. Should write to log."""
        pass ##: raise AbstractError ?

class CBash_MultiTweakItem(AMultiTweakItem):
    # extra CBash_MultiTweakItem class variables
    iiMode = False
    scanRequiresChecked = False
    applyRequiresChecked = False
    # the default scan and edit orders - override as needed
    scanOrder = 32
    editOrder = 32

    def __init__(self, key, *choices, **kwargs):
        super(CBash_MultiTweakItem, self).__init__(key, *choices, **kwargs)
        # extra CBash_MultiTweakItem attribute, mod -> num of tweaked records
        self.mod_count = Counter()

    #--Patch Phase ------------------------------------------------------------
    def getTypes(self):
        """Returns the group types that this patcher checks"""
        return list(self.__class__.tweak_read_classes)

    # def apply(self,modFile,record): # TODO bashTags argument is unused in
    # all subclasses

    def buildPatchLog(self,log):
        """Will write to log."""
        self._patchLog(log, self.mod_count)
        self.mod_count = Counter()

class MultiTweaker(AMultiTweaker,Patcher):

    def getReadClasses(self):
        """Returns load factory classes needed for reading."""
        return chain.from_iterable(tweak.getReadClasses()
            for tweak in self.enabled_tweaks) if self.isActive else ()

    def getWriteClasses(self):
        """Returns load factory classes needed for writing."""
        return chain.from_iterable(tweak.getWriteClasses()
            for tweak in self.enabled_tweaks) if self.isActive else ()

    def scanModFile(self,modFile,progress):
        for tweak in self.enabled_tweaks:
            tweak.scanModFile(modFile,progress,self.patchFile)

    def buildPatch(self,log,progress):
        """Applies individual tweaks."""
        if not self.isActive: return
        log.setHeader(u'= ' + self._patcher_name, True)
        for tweak in self.enabled_tweaks:
            tweak.buildPatch(log,progress,self.patchFile)

class CBash_MultiTweaker(AMultiTweaker,CBash_Patcher):

    def __init__(self, p_name, p_file, enabled_tweaks):
        super(CBash_MultiTweaker, self).__init__(p_name, p_file,
                                                 enabled_tweaks)
        for tweak in self.enabled_tweaks:
            tweak.patchFile = p_file

    def initData(self, progress):
        """Compiles material, i.e. reads source text, esp's, etc. as
        necessary."""
        if not self.isActive: return
        for tweak in self.enabled_tweaks: ##: FIXME allowUnloaded (use or not base class method)
            for top_group_sig in tweak.getTypes():
                self.patchFile.group_patchers[top_group_sig].append(tweak)

    def buildPatchLog(self,log):
        """Will write to log."""
        if not self.isActive: return
        log.setHeader(u'= ' + self._patcher_name, True)
        for tweak in self.enabled_tweaks:
            tweak.buildPatchLog(log)

# Patchers: 10 ----------------------------------------------------------------
class AliasesPatcher(AAliasesPatcher,Patcher): pass

class CBash_AliasesPatcher(AAliasesPatcher,CBash_Patcher):
    allowUnloaded = False # avoid the srcs check in CBash_Patcher.initData

class PatchMerger(APatchMerger, ListPatcher): pass

class CBash_PatchMerger(APatchMerger, CBash_ListPatcher): pass

class UpdateReferences(AUpdateReferences,ListPatcher):
    # TODO move this to a file it's imported after MreRecord.simpleTypes is set

    def __init__(self, p_name, p_file, p_sources):
        super(UpdateReferences, self).__init__(p_name, p_file,
                                               p_sources)
        self.old_new = {} #--Maps old fid to new fid
        self.old_eid = {} #--Maps old fid to old editor id
        self.new_eid = {} #--Maps new fid to new editor id

    def readFromText(self,textPath):
        """Reads replacement data from specified text file."""
        old_new,old_eid,new_eid = self.old_new,self.old_eid,self.new_eid
        aliases = self.patchFile.aliases
        with CsvReader(textPath) as ins:
            for fields in ins:
                if len(fields) < 7 or fields[2][:2] != u'0x' or fields[6][:2] != u'0x': continue
                oldMod,oldObj,oldEid,newEid,newMod,newObj = fields[1:7]
                oldMod,newMod = map(GPath,(oldMod,newMod))
                oldId = (GPath(aliases.get(oldMod,oldMod)),int(oldObj,16))
                newId = (GPath(aliases.get(newMod,newMod)),int(newObj,16))
                old_new[oldId] = newId
                old_eid[oldId] = oldEid
                new_eid[newId] = newEid

    def initData(self,progress):
        """Get names from source files."""
        if not self.isActive: return
        progress.setFull(len(self.srcs))
        for srcFile in self.srcs:
            srcPath = GPath(srcFile)
            try: self.readFromText(getPatchesPath(srcFile))
            except OSError: deprint(
                u'%s is no longer in patches set' % srcPath, traceback=True)
            progress.plus()

    def getReadClasses(self):
        return tuple(
            MreRecord.simpleTypes | ({'CELL', 'WRLD', 'REFR', 'ACHR', 'ACRE'}))

    def getWriteClasses(self):
        return tuple(
            MreRecord.simpleTypes | ({'CELL', 'WRLD', 'REFR', 'ACHR', 'ACRE'}))

    def scanModFile(self,modFile,progress):
        """Scans specified mod file to extract info. May add record to patch mod,
        but won't alter it."""
        mapper = modFile.getLongMapper()
        patchCells = self.patchFile.CELL
        patchWorlds = self.patchFile.WRLD
        modFile.convertToLongFids(('CELL','WRLD','REFR','ACRE','ACHR'))
##        for type in MreRecord.simpleTypes:
##            for record in getattr(modFile,type).getActiveRecords():
##                record = record.getTypeCopy(mapper)
##                if record.fid in self.old_new:
##                    getattr(self.patchFile,type).setRecord(record)
        if 'CELL' in modFile.tops:
            for cellBlock in modFile.CELL.cellBlocks:
                cellImported = False
                if cellBlock.cell.fid in patchCells.id_cellBlock:
                    patchCells.id_cellBlock[cellBlock.cell.fid].cell = cellBlock.cell
                    cellImported = True
                for record in cellBlock.temp:
                    if record.base in self.old_new:
                        if not cellImported:
                            patchCells.setCell(cellBlock.cell)
                            cellImported = True
                        for newRef in patchCells.id_cellBlock[cellBlock.cell.fid].temp:
                            if newRef.fid == record.fid:
                                loc = patchCells.id_cellBlock[cellBlock.cell.fid].temp.index(newRef)
                                patchCells.id_cellBlock[cellBlock.cell.fid].temp[loc] = record
                                break
                        else:
                            patchCells.id_cellBlock[cellBlock.cell.fid].temp.append(record)
                for record in cellBlock.persistent:
                    if record.base in self.old_new:
                        if not cellImported:
                            patchCells.setCell(cellBlock.cell)
                            cellImported = True
                        for newRef in patchCells.id_cellBlock[cellBlock.cell.fid].persistent:
                            if newRef.fid == record.fid:
                                loc = patchCells.id_cellBlock[cellBlock.cell.fid].persistent.index(newRef)
                                patchCells.id_cellBlock[cellBlock.cell.fid].persistent[loc] = record
                                break
                        else:
                            patchCells.id_cellBlock[cellBlock.cell.fid].persistent.append(record)
        if 'WRLD' in modFile.tops:
            for worldBlock in modFile.WRLD.worldBlocks:
                worldImported = False
                if worldBlock.world.fid in patchWorlds.id_worldBlocks:
                    patchWorlds.id_worldBlocks[worldBlock.world.fid].world = worldBlock.world
                    worldImported = True
                for cellBlock in worldBlock.cellBlocks:
                    cellImported = False
                    if worldBlock.world.fid in patchWorlds.id_worldBlocks and cellBlock.cell.fid in patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock:
                        patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].cell = cellBlock.cell
                        cellImported = True
                    for record in cellBlock.temp:
                        if record.base in self.old_new:
                            if not worldImported:
                                patchWorlds.setWorld(worldBlock.world)
                                worldImported = True
                            if not cellImported:
                                patchWorlds.id_worldBlocks[worldBlock.world.fid].setCell(cellBlock.cell)
                                cellImported = True
                            for newRef in patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].temp:
                                if newRef.fid == record.fid:
                                    loc = patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].temp.index(newRef)
                                    patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].temp[loc] = record
                                    break
                            else:
                                patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].temp.append(record)
                    for record in cellBlock.persistent:
                        if record.base in self.old_new:
                            if not worldImported:
                                patchWorlds.setWorld(worldBlock.world)
                                worldImported = True
                            if not cellImported:
                                patchWorlds.id_worldBlocks[worldBlock.world.fid].setCell(cellBlock.cell)
                                cellImported = True
                            for newRef in patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].persistent:
                                if newRef.fid == record.fid:
                                    loc = patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].persistent.index(newRef)
                                    patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].persistent[loc] = record
                                    break
                            else:
                                patchWorlds.id_worldBlocks[worldBlock.world.fid].id_cellBlock[cellBlock.cell.fid].persistent.append(record)

    def buildPatch(self,log,progress):
        """Adds merged fids to patchfile."""
        if not self.isActive: return
        old_new,old_eid,new_eid = self.old_new,self.old_eid,self.new_eid
        keep = self.patchFile.getKeeper()
        count = Counter()
        def swapper(oldId):
            newId = old_new.get(oldId,None)
            return newId if newId else oldId
##        for type in MreRecord.simpleTypes:
##            for record in getattr(self.patchFile,type).getActiveRecords():
##                if record.fid in self.old_new:
##                    record.fid = swapper(record.fid)
##                    count.increment(record.fid[0])
####                    record.mapFids(swapper,True)
##                    record.setChanged()
##                    keep(record.fid)
        for cellBlock in self.patchFile.CELL.cellBlocks:
            for record in cellBlock.temp:
                if record.base in self.old_new:
                    record.base = swapper(record.base)
                    count[cellBlock.cell.fid[0]] += 1
##                    record.mapFids(swapper,True)
                    record.setChanged()
                    keep(record.fid)
            for record in cellBlock.persistent:
                if record.base in self.old_new:
                    record.base = swapper(record.base)
                    count[cellBlock.cell.fid[0]] += 1
##                    record.mapFids(swapper,True)
                    record.setChanged()
                    keep(record.fid)
        for worldBlock in self.patchFile.WRLD.worldBlocks:
            keepWorld = False
            for cellBlock in worldBlock.cellBlocks:
                for record in cellBlock.temp:
                    if record.base in self.old_new:
                        record.base = swapper(record.base)
                        count[cellBlock.cell.fid[0]] += 1
##                        record.mapFids(swapper,True)
                        record.setChanged()
                        keep(record.fid)
                        keepWorld = True
                for record in cellBlock.persistent:
                    if record.base in self.old_new:
                        record.base = swapper(record.base)
                        count[cellBlock.cell.fid[0]] += 1
##                        record.mapFids(swapper,True)
                        record.setChanged()
                        keep(record.fid)
                        keepWorld = True
            if keepWorld:
                keep(worldBlock.world.fid)

        log.setHeader(u'= ' + self._patcher_name)
        self._srcMods(log)
        log(u'\n=== '+_(u'Records Patched'))
        for srcMod in load_order.get_ordered(count.keys()):
            log(u'* %s: %d' % (srcMod.s,count[srcMod]))

class CBash_UpdateReferences(AUpdateReferences, CBash_ListPatcher):
    _read_write_records = (
        'MOD', 'FACT', 'RACE', 'MGEF', 'SCPT', 'LTEX', 'ENCH', 'SPEL', 'BSGN',
        'ACTI', 'APPA', 'ARMO', 'BOOK', 'CLOT', 'CONT', 'DOOR', 'INGR', 'LIGH',
        'MISC', 'FLOR', 'FURN', 'WEAP', 'AMMO', 'NPC_', 'CREA', 'LVLC', 'SLGM',
        'KEYM', 'ALCH', 'SGST', 'LVLI', 'WTHR', 'CLMT', 'REGN', 'CELLS',
        'WRLD', 'ACHRS', 'ACRES', 'REFRS', 'DIAL', 'INFOS', 'QUST', 'IDLE',
        'PACK', 'LSCR', 'LVSP', 'ANIO', 'WATR')

    def __init__(self, p_name, p_file, p_sources):
        super(CBash_UpdateReferences, self).__init__(p_name, p_file, p_sources)
        self.old_eid = {} #--Maps old fid to old editor id
        self.new_eid = {} #--Maps new fid to new editor id
        self.mod_count_old_new = {}

    def initData(self, progress):
        """Compiles material, i.e. reads source text, esp's, etc. as necessary."""
        if not self.isActive: return
        from ...parsers import CBash_FidReplacer
        fidReplacer = CBash_FidReplacer(aliases=self.patchFile.aliases)
        progress.setFull(len(self.srcs))
        for srcFile in self.srcs:
            if not self.patchFile.p_file_minfos.rightFileType(srcFile):
                try: fidReplacer.readFromText(getPatchesPath(srcFile))
                except OSError: deprint(
                    u'%s is no longer in patches set' % srcFile, traceback=True)
            progress.plus()
        #--Finish
        self.old_new = fidReplacer.old_new
        self.old_eid.update(fidReplacer.old_eid)
        self.new_eid.update(fidReplacer.new_eid)
        self.isActive = bool(self.old_new)
        if not self.isActive: return
        # resets isActive !!
        for top_group_sig in self.getTypes():
            self.patchFile.group_patchers[top_group_sig].append(self)

    def mod_apply(self, modFile):
        """Changes the mod in place without copying any records."""
        counts = modFile.UpdateReferences(self.old_new)
        #--Done
        if sum(counts):
            self.mod_count_old_new[modFile.GName] = [(count,self.old_eid[old_newId[0]],self.new_eid[old_newId[1]]) for count, old_newId in zip(counts, self.old_new.iteritems())]

    def apply(self,modFile,record,bashTags):
        """Edits patch file as desired. """
        if record.GetRecordUpdatedReferences():
            override = record.CopyAsOverride(self.patchFile, UseWinningParents=True)
            if override:
                record._RecordID = override._RecordID

    def buildPatchLog(self,log):
        """Will write to log."""
        if not self.isActive: return
        #--Log
        mod_count_old_new = self.mod_count_old_new

        log.setHeader(u'= ' + self._patcher_name)
        self._srcMods(log)
        log(u'\n')
        for mod in load_order.get_ordered(mod_count_old_new.keys()):
            entries = mod_count_old_new[mod]
            log(u'\n=== %s' % mod.s)
            entries.sort(key=itemgetter(1))
            log(u'  * '+_(u'Updated References') + u': %d' % sum([count for count, old, new in entries]))
            log(u'\n'.join([u'    * %3d %s >> %s' % entry for entry in entries if entry[0] > 0]))

        self.old_new = {} #--Maps old fid to new fid
        self.old_eid = {} #--Maps old fid to old editor id
        self.new_eid = {} #--Maps new fid to new editor id
        self.mod_count_old_new = {}

# Patchers: 40 ----------------------------------------------------------------
class SpecialPatcher(CBash_Patcher):
    """Provides scan_more method only used in CBash importers (17) and CBash
    race patchers (3/4 except CBash_RacePatcher_Eyes)."""
    group = _(u'Special')
    scanOrder = 40
    editOrder = 40

    def scan_more(self,modFile,record,bashTags):
        if modFile.GName in self.srcs:
            self.scan(modFile,record,bashTags)
        #Must check for "unloaded" conflicts that occur past the winning record
        #If any exist, they have to be scanned
        minfs = self.patchFile.p_file_minfos
        for conflict in record.Conflicts(True):
            if conflict != record:
                mod = conflict.GetParentMod()
                if mod.GName in self.srcs:
                    tags = minfs[mod.GName].getBashTags()
                    self.scan(mod,conflict,tags)
            else: return

# Patchers: 20 ----------------------------------------------------------------
class ImportPatcher(AImportPatcher, ListPatcher):
    # Override in subclasses as needed
    logMsg = u'\n=== ' + _(u'Modified Records')

    def _patchLog(self,log,type_count):
        log.setHeader(u'= ' + self._patcher_name)
        self._srcMods(log)
        self._plog(log,type_count)

    def _plog(self,log,type_count):
        """Most common logging pattern - override as needed.

        Used in:
        GraphicsPatcher, ActorImporter, KFFZPatcher, DeathItemPatcher,
        ImportFactions, ImportScripts, NamesPatcher, SoundPatcher.
        """
        log(self.__class__.logMsg)
        for type_,count in sorted(type_count.iteritems()):
            if count: log(u'* ' + _(u'Modified %(type)s Records: %(count)d')
                          % {'type': type_, 'count': count})

    def _plog1(self,log,mod_count): # common logging variation
        log(self.__class__.logMsg % sum(mod_count.values()))
        for mod in load_order.get_ordered(mod_count):
            log(u'* %s: %3d' % (mod.s,mod_count[mod]))

    def _plog2(self,log,allCounts):
        log(self.__class__.logMsg)
        for top_rec_type, count, counts in allCounts:
            if not count: continue
            typeName = bush.game.record_type_name[top_rec_type]
            log(u'* %s: %d' % (typeName, count))
            for modName in sorted(counts):
                log(u'  * %s: %d' % (modName.s, counts[modName]))

    # helpers WIP
    def _parse_sources(self, progress, parser):
        if not self.isActive: return None
        parser_instance = parser()
        parser_instance.aliases = self.patchFile.aliases
        parser_instance.called_from_patcher = True
        progress.setFull(len(self.srcs))
        for srcFile in self.srcs:
            srcPath = GPath(srcFile)
            minfs = self.patchFile.p_file_minfos
            if minfs.rightFileType(srcPath):
                if srcPath not in minfs: continue
                srcInfo = minfs[srcPath]
                parser_instance.readFromMod(srcInfo)
            else:
                try:
                    parser_instance.readFromText(getPatchesPath(srcFile))
                except OSError:
                    deprint(u'%s is no longer in patches set' % srcPath,
                        traceback=True)
                except UnicodeError as e: # originally in NamesPatcher, keep ?
                    print(srcPath.stail, u'is not saved in UTF-8 format:', e)
            progress.plus()
        return parser_instance

class CBash_ImportPatcher(AImportPatcher, CBash_ListPatcher, SpecialPatcher):
    scanRequiresChecked = True
    applyRequiresChecked = False

    def buildPatchLog(self,log):
        """Will write to log."""
        if not self.isActive: return
        #--Log
        log.setHeader(u'= ' + self._patcher_name)
        self._clog(log)

    def _clog(self,log):
        """Most common logging pattern - override as needed.

        Used in:
        CBash_CellImporter, CBash_KFFZPatcher, CBash_NPCAIPackagePatcher,
        CBash_ImportRelations, CBash_RoadImporter, CBash_SpellsPatcher.
        You must define logMsg as a class attribute in subclasses except
        CBash_ImportFactions and CBash_ImportInventory.
        """
        mod_count = self.mod_count
        log(self.__class__.logMsg % sum(mod_count.values()))
        for srcMod in load_order.get_ordered(mod_count.keys()):
            log(u'  * %s: %d' % (srcMod.s,mod_count[srcMod]))
        self.mod_count = Counter()

    # helpers WIP
    def _parse_texts(self, parser_class, progress):
        actorFactions = parser_class(aliases=self.patchFile.aliases)
        progress.setFull(len(self.srcs))
        for srcFile in self.srcs:
            if not self.patchFile.p_file_minfos.rightFileType(srcFile):
                try: actorFactions.readFromText(getPatchesPath(srcFile))
                except OSError:
                    deprint(u'%s is no longer in patches set' % srcFile,
                            traceback=True)
            progress.plus()
        return actorFactions
