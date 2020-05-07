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
"""This module houses the entry point for reading and writing plugin files
through PBash (LoadFactory + ModFile) as well as some related classes."""

import re
from collections import defaultdict
from struct import Struct

from . import bolt, bush, env, load_order
from .bass import dirs
from .bolt import deprint, GPath, SubProgress
from .brec import MreRecord, ModReader, ModWriter, RecordHeader, RecHeader, \
    TopGrupHeader
from .exception import ArgumentError, MasterMapError, ModError, StateError
from .record_groups import MobBase, MobDials, MobICells, MobObjects, MobWorlds

class MasterSet(set):
    """Set of master names."""
    def add(self,element):
        """Add an element it's not empty. Special handling for tuple."""
        if isinstance(element,tuple):
            set.add(self,element[0])
        elif element:
            set.add(self,element)

    def getOrdered(self):
        """Returns masters in proper load order."""
        return load_order.get_ordered(self)

class MasterMap(object):
    """Serves as a map between two sets of masters."""
    def __init__(self,inMasters,outMasters):
        """Initiation."""
        map = {}
        outMastersIndex = outMasters.index
        for index,master in enumerate(inMasters):
            if master in outMasters:
                map[index] = outMastersIndex(master)
            else:
                map[index] = -1
        self.map = map

    def __call__(self,fid,default=-1):
        """Maps a fid from first set of masters to second. If no mapping
        is possible, then either returns default (if defined) or raises MasterMapError."""
        if not fid: return fid
        inIndex = int(fid >> 24)
        outIndex = self.map.get(inIndex,-2)
        if outIndex >= 0:
            return (int(outIndex) << 24 ) | (fid & 0xFFFFFF)
        elif default != -1:
            return default
        else:
            raise MasterMapError(inIndex)

class LoadFactory(object):
    """Factory for mod representation objects."""
    def __init__(self,keepAll,*recClasses):
        self.keepAll = keepAll
        self.recTypes = set()
        self.topTypes = set()
        self.type_class = {}
        self.cellType_class = {}
        addClass = self.addClass
        for recClass in recClasses:
            addClass(recClass)

    def addClass(self,recClass):
        """Adds specified class."""
        cellTypes = (b'WRLD',b'ROAD',b'CELL',b'REFR',b'ACHR',b'ACRE',b'PGRD',b'LAND')
        if isinstance(recClass,basestring):
            recType = recClass
            recClass = MreRecord
        else:
            recType = recClass.classType
        #--Don't replace complex class with default (MreRecord) class
        if recType in self.type_class and recClass == MreRecord:
            return
        self.recTypes.add(recType)
        self.type_class[recType] = recClass
        #--Top type
        if recType in cellTypes:
            topAdd = self.topTypes.add
            topAdd(b'CELL')
            topAdd(b'WRLD')
            if self.keepAll:
                setterDefault = self.type_class.setdefault
                for type in cellTypes:
                    setterDefault(type,MreRecord)
        elif recType == b'INFO':
            self.topTypes.add(b'DIAL')
        else:
            self.topTypes.add(recType)

    def getRecClass(self,type):
        """Returns class for record type or None."""
        default = (self.keepAll and MreRecord) or None
        return self.type_class.get(type,default)

    def getCellTypeClass(self):
        """Returns type_class dictionary for cell objects."""
        if not self.cellType_class:
            types = (b'REFR',b'ACHR',b'ACRE',b'PGRD',b'LAND',b'CELL',b'ROAD')
            getterRecClass = self.getRecClass
            self.cellType_class.update((x,getterRecClass(x)) for x in types)
        return self.cellType_class

    def getUnpackCellBlocks(self,topType):
        """Returns whether cell blocks should be unpacked or not. Only relevant
        if CELL and WRLD top types are expanded."""
        return (
            self.keepAll or
            (self.recTypes & {b'REFR', b'ACHR', b'ACRE', b'PGRD', b'LAND'}) or
            (topType == b'WRLD' and b'LAND' in self.recTypes))

    def getTopClass(self, top_rec_type):
        """Return top block class for top block type, or None.
        :rtype: type[record_groups.MobBase]
        """
        if top_rec_type in self.topTypes:
            if   top_rec_type == b'DIAL': return MobDials
            elif top_rec_type == b'CELL': return MobICells
            elif top_rec_type == b'WRLD': return MobWorlds
            else: return MobObjects
        else:
            return MobBase if self.keepAll else None

    def __repr__(self):
        return u'<LoadFactory: load %u types (%s), %s others>' % (
            len(self.recTypes),
            u', '.join(self.recTypes),
            u'keep' if self.keepAll else u'discard',
        )

class ModFile(object):
    """Plugin file representation. **Overrides `__getattr__`** to return its
    collection of records for a top record type. Will load only the top
    record types specified in its LoadFactory."""
    def __init__(self, fileInfo,loadFactory=None):
        self.fileInfo = fileInfo
        self.loadFactory = loadFactory or LoadFactory(True)
        #--Variables to load
        self.tes4 = bush.game.plugin_header_class(RecHeader())
        self.tes4.setChanged()
        self.strings = bolt.StringTable()
        self.tops = {} #--Top groups.
        self.topsSkipped = set() #--Types skipped
        self.longFids = False

    def __getattr__(self, topType, __rh=RecordHeader):
        """Returns top block of specified topType, creating it, if necessary."""
        if topType in self.tops:
            return self.tops[topType]
        elif topType in __rh.top_grup_sigs:
            topClass = self.loadFactory.getTopClass(topType)
            try:
                self.tops[topType] = topClass(TopGrupHeader(0, topType, 0, 0),
                                              self.loadFactory)
            except TypeError:
                raise ModError(
                    self.fileInfo.name,
                    u'Failed to retrieve top class for %s; load factory is '
                    u'%r' % (topType, self.loadFactory))
            self.tops[topType].setChanged()
            return self.tops[topType]
        elif topType == u'__repr__' or topType.startswith(u'cached_'):
            raise AttributeError
        else:
            raise ArgumentError(u'Invalid top group type: '+topType)

    def load(self, do_unpack=False, progress=None, loadStrings=True,
             catch_errors=True):
        """Load file."""
        from . import bosh
        progress = progress or bolt.Progress()
        progress.setFull(1.0)
        with ModReader(self.fileInfo.name,self.fileInfo.getPath().open(
                u'rb')) as ins:
            insRecHeader = ins.unpackRecHeader
            # Main header of the mod file - generally has 'TES4' signature
            header = insRecHeader()
            self.tes4 = bush.game.plugin_header_class(header,ins,True)
            # Check if we need to handle strings
            self.strings.clear()
            if do_unpack and self.tes4.flags1.hasStrings and loadStrings:
                stringsProgress = SubProgress(progress,0,0.1) # Use 10% of progress bar for strings
                lang = bosh.oblivionIni.get_ini_language()
                stringsPaths = self.fileInfo.getStringsPaths(lang)
                stringsProgress.setFull(max(len(stringsPaths),1))
                for i,path in enumerate(stringsPaths):
                    self.strings.loadFile(path,SubProgress(stringsProgress,i,i+1),lang)
                    stringsProgress(i)
                ins.setStringTable(self.strings)
                subProgress = SubProgress(progress,0.1,1.0)
            else:
                ins.setStringTable(None)
                subProgress = progress
            #--Raw data read
            subProgress.setFull(ins.size)
            insAtEnd = ins.atEnd
            insSeek = ins.seek
            insTell = ins.tell
            while not insAtEnd():
                #--Get record info and handle it
                header = insRecHeader()
                if not header.is_top_group_header:
                    raise ModError(self.fileInfo.name,u'Improperly grouped file.')
                label,size = header.label,header.size
                topClass = self.loadFactory.getTopClass(label)
                try:
                    if topClass:
                        self.tops[label] = topClass(header, self.loadFactory)
                        self.tops[label].load(ins, do_unpack and (topClass != MobBase))
                    else:
                        self.topsSkipped.add(label)
                        insSeek(size - RecordHeader.rec_header_size, 1,
                                u'GRUP.%s' % label)
                except:
                    if catch_errors:
                        deprint(u'Error in %s' % self.fileInfo.name.s,
                                traceback=True)
                        break
                    else:
                        # Useful for implementing custom error behavior, see
                        # e.g. Mod_FullLoad
                        raise
                subProgress(insTell())
        #--Done Reading

    def askSave(self,hasChanged=True):
        """CLI command. If hasSaved, will ask if user wants to save the file,
        and then save if the answer is yes. If hasSaved == False, then does nothing."""
        if not hasChanged: return
        fileName = self.fileInfo.name
        if re.match(u'' r'\s*[yY]', raw_input(u'\nSave changes to '+fileName.s+u' [y/n]?: '), flags=re.U):
            self.safeSave()
            print(fileName.s,u'saved.')
        else:
            print(fileName.s,u'not saved.')

    def safeSave(self):
        """Save data to file safely.  Works under UAC."""
        self.fileInfo.tempBackup()
        filePath = self.fileInfo.getPath()
        self.save(filePath.temp)
        if self.fileInfo.mtime is not None: # fileInfo created before the file
            filePath.temp.mtime = self.fileInfo.mtime
        # FIXME If saving a locked (by xEdit f.i.) bashed patch a bogus UAC
        # permissions dialog is displayed (should display file in use)
        env.shellMove(filePath.temp, filePath, parent=None) # silent=True just returns - no error!
        self.fileInfo.extras.clear()

    def save(self,outPath=None):
        """Save data to file.
        outPath -- Path of the output file to write to. Defaults to original file path."""
        if not self.loadFactory.keepAll: raise StateError(u"Insufficient data to write file.")
        outPath = outPath or self.fileInfo.getPath()
        with ModWriter(outPath.open(u'wb')) as out:
            #--Mod Record
            self.tes4.setChanged()
            self.tes4.numRecords = sum(block.getNumRecords() for block in self.tops.values())
            self.tes4.getSize()
            self.tes4.dump(out)
            #--Blocks
            selfTops = self.tops
            for rec_type in RecordHeader.top_grup_sigs:
                if rec_type in selfTops:
                    selfTops[rec_type].dump(out)

    def getLongMapper(self):
        """Returns a mapping function to map short fids to long fids."""
        masters = self.tes4.masters+[self.fileInfo.name]
        maxMaster = len(masters)-1
        def mapper(fid):
            if fid is None: return None
            if isinstance(fid,tuple): return fid
            mod,object = int(fid >> 24),int(fid & 0xFFFFFF)
            return masters[min(mod,maxMaster)],object
        return mapper

    def getShortMapper(self):
        """Returns a mapping function to map long fids to short fids."""
        masters = self.tes4.masters + [self.fileInfo.name]
        indices = {name: index for index, name in enumerate(masters)}
        gLong = self.getLongMapper()
        has_expanded_range = bush.game.Esp.expanded_plugin_range
        if has_expanded_range and len(masters) > 1:
            # Plugin has at least one master, it may freely use the
            # expanded (0x000-0x800) range
            def _master_index(m_name, obj_id):
                return indices[m_name]
        else:
            # 0x000-0x800 are reserved for hardcoded (engine) records
            def _master_index(m_name, obj_id):
                return indices[m_name] if obj_id >= 0x800 else 0
        def mapper(fid):
            if fid is None: return None
            ##: #312: drop this once convertToLongFids is auto-applied
            if isinstance(fid, (int, long)): # PY3: just int here
                fid = gLong(fid)
            modName, object_id = fid
            return (_master_index(modName, object_id) << 24) | object_id
        return mapper

    def convertToLongFids(self,types=None):
        """Convert fids to long format (modname,objectindex).
        :type types: list[str] | tuple[str] | set[str]
        """
        mapper = self.getLongMapper()
        if types is None: types = self.tops.keys()
        else: assert isinstance(types, (list, tuple, set))
        selfTops = self.tops
        for type in types:
            if type in selfTops:
                selfTops[type].convertFids(mapper,True)
        #--Done
        self.longFids = True

    ##: Ideally we'd encapsulate all the long/short fid handling in load/save
    def convertToShortFids(self):
        """Convert fids to short (numeric) format."""
        mapper = self.getShortMapper()
        selfTops = self.tops
        for type in selfTops:
            selfTops[type].convertFids(mapper,False)
        #--Done
        self.longFids = False

    def getMastersUsed(self):
        """Updates set of master names according to masters actually used."""
        if not self.longFids: raise StateError(u"ModFile fids not in long form.")
        for fname in bush.game.masterFiles:
            if dirs['mods'].join(fname).exists():
                masters = MasterSet([GPath(fname)])
                break
        for block in self.tops.values():
            block.updateMasters(masters)
        return masters.getOrdered()

    def _index_mgefs(self):
        """Indexes and cache all MGEF properties and stores them for retrieval
        by the patchers. We do this once at all so we only have to iterate over
        the MGEFs once."""
        m_school = bush.game.mgef_school.copy()
        m_hostiles = bush.game.hostile_effects.copy()
        m_names = bush.game.mgef_name.copy()
        hostile_recs = set()
        nonhostile_recs = set()
        unpack_eid = Struct(u'I').unpack
        if b'MGEF' in self.tops:
            for record in self.MGEF.getActiveRecords():
                m_school[record.eid] = record.school
                target_set = (hostile_recs if record.flags.hostile
                              else nonhostile_recs)
                target_set.add(record.eid)
                target_set.add(unpack_eid(record.eid.encode(u'ascii'))[0])
                m_names[record.eid] = record.full
        self.cached_mgef_school = m_school
        self.cached_mgef_hostiles = m_hostiles - nonhostile_recs | hostile_recs
        self.cached_mgef_names = m_names

    def getMgefSchool(self):
        """Return a dictionary mapping magic effect code to magic effect
        school. This is intended for use with the patch file when it records
        for all magic effects. If magic effects are not available, it will
        revert to constants.py version."""
        try:
            # Try to just return the cached version
            return self.cached_mgef_school
        except AttributeError:
            self._index_mgefs()
            return self.cached_mgef_school

    def getMgefHostiles(self):
        """Return a set of hostile magic effect codes. This is intended for use
        with the patch file when it records for all magic effects. If magic
        effects are not available, it will revert to constants.py version."""
        try:
             # Try to just return the cached version
            return self.cached_mgef_hostiles
        except AttributeError:
            self._index_mgefs()
            return self.cached_mgef_hostiles

    def getMgefName(self):
        """Return a dictionary mapping magic effect code to magic effect name.
        This is intended for use with the patch file when it records for all
        magic effects. If magic effects are not available, it will revert to
        constants.py version."""
        try:
            return self.cached_mgef_names
        except AttributeError:
            self._index_mgefs()
            return self.cached_mgef_names

    def __repr__(self):
        return u'ModFile<%s>' % self.fileInfo.name.s

# TODO(inf) Use this for a bunch of stuff in mods_metadata.py (e.g. UDRs)
class ModHeaderReader(object):
    """Allows very fast reading of a plugin's headers, skipping reading and
    decoding of anything but the headers."""
    @staticmethod
    def read_mod_headers(mod_info):
        """Reads the headers of every record in the specified mod, returning
        them as a dict, mapping record signature to a list of the headers of
        every record with that signature. Note that the flags are not processed
        either - if you need that, manually call MreRecord.flags1_() on them.

        :rtype: defaultdict[str, list[RecordHeader]]"""
        ret_headers = defaultdict(list)
        with ModReader(mod_info.name, mod_info.abs_path.open(u'rb')) as ins:
            try:
                ins_at_end = ins.atEnd
                ins_unpack_rec_header = ins.unpackRecHeader
                ins_seek = ins.seek
                while not ins_at_end():
                    header = ins_unpack_rec_header()
                    # Skip GRUPs themselves, only process their records
                    header_rec_type = header.recType
                    if header_rec_type != b'GRUP':
                        ret_headers[header_rec_type].append(header)
                        ins_seek(header.size, 1)
            except OSError as e:
                raise ModError(ins.inName, u'Error scanning %s, file read '
                                           u"pos: %i\nCaused by: '%r'" % (
                    mod_info.name.s, ins.tell(), e))
        return ret_headers
