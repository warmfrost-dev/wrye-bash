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
"""GameInfo override for TES IV: Oblivion."""

from .. import GameInfo
from ... import brec
from ...brec import MreGlob

class OblivionGameInfo(GameInfo):
    displayName = u'Oblivion'
    fsName = u'Oblivion'
    altName = u'Wrye Bash'
    defaultIniFile = u'Oblivion_default.ini'
    launch_exe = u'Oblivion.exe'
    game_detect_file = [u'Oblivion.exe']
    version_detect_file  = [u'Oblivion.exe']
    masterFiles = [u'Oblivion.esm', u'Nehrim.esm']
    iniFiles = [u'Oblivion.ini']
    pklfile = u'bash\\db\\Oblivion_ids.pkl'
    masterlist_dir = u'Oblivion'
    regInstallKeys = (u'Bethesda Softworks\\Oblivion', u'Installed Path')
    nexusUrl = u'https://www.nexusmods.com/oblivion/'
    nexusName = u'Oblivion Nexus'
    nexusKey = 'bash.installers.openOblivionNexus.continue'

    patchURL = u'http://www.elderscrolls.com/downloads/updates_patches.htm'
    patchTip = u'http://www.elderscrolls.com/'

    using_txt_file = False
    has_standalone_pluggy = True

    class Ck(GameInfo.Ck):
        ck_abbrev = u'TESCS'
        long_name = u'Construction Set'
        exe = u'TESConstructionSet.exe'
        se_args = u'-editor'
        image_name = u'tescs%s.png'

    class Se(GameInfo.Se):
        se_abbrev = u'OBSE'
        long_name = u'Oblivion Script Extender'
        exe = u'obse_loader.exe'
        # Not sure why we need obse_1_2_416.dll, was there before refactoring
        ver_files = [u'obse_loader.exe', u'obse_steam_loader.dll',
                     u'obse_1_2_416.dll']
        plugin_dir = u'OBSE'
        cosave_tag = u'OBSE'
        cosave_ext = u'.obse'
        url = u'http://obse.silverlock.org/'
        url_tip = u'http://obse.silverlock.org/'

    class Ge(GameInfo.Ge):
        ge_abbrev = u'OBGE'
        long_name = u'Oblivion Graphics Extender'
        exe = [(u'obse', u'plugins', u'obge.dll'),
               (u'obse', u'plugins', u'obgev2.dll'),
               (u'obse', u'plugins', u'oblivionreloaded.dll'),
               ]
        url = u'https://www.nexusmods.com/oblivion/mods/30054'
        url_tip = u'https://www.nexusmods.com/oblivion'

    class Ini(GameInfo.Ini):
        allow_new_lines = False
        bsa_redirection_key = (u'Archive', u'sArchiveList')
        supports_mod_inis = False

    class Ess(GameInfo.Ess):
        canEditMore = True

    class Bsa(GameInfo.Bsa):
        allow_reset_timestamps = True
        valid_versions = {0x67}

    class Xe(GameInfo.Xe):
        full_name = u'TES4Edit'
        expert_key = 'tes4View.iKnowWhatImDoing'

    # BAIN:
    dataDirs = GameInfo.dataDirs | {
        u'_tejon',
        u'distantlod',
        u'facegen',
        u'fonts',
        u'menus',
        u'obse',
        u'pluggy',
        u'scripts',
        u'shaders',
        u'streamline',
        u'trees',
    }
    SkipBAINRefresh = {
        u'tes4edit backups',
        u'tes4edit cache',
        u'bgsee',
        u'conscribe logs',
    }
    wryeBashDataFiles = GameInfo.wryeBashDataFiles | {
        u'ArchiveInvalidationInvalidated!.bsa'}
    ignoreDataFiles = {
        u'OBSE\\Plugins\\Construction Set Extender.dll',
        u'OBSE\\Plugins\\Construction Set Extender.ini'
    }
    ignoreDataFilePrefixes = {
        u'Meshes\\Characters\\_Male\\specialanims\\0FemaleVariableWalk_'
    }
    ignoreDataDirs = {
        u'OBSE\\Plugins\\ComponentDLLs\\CSE',
        u'LSData'
    }

    class Esp(GameInfo.Esp):
        canBash = True
        canCBash = True
        canEditHeader = True
        validHeaderVersions = (0.8,1.0)
        stringsFiles = []

    allTags = {
        u'Actors.ACBS', u'Actors.AIData', u'Actors.AIPackages',
        u'Actors.AIPackagesForceAdd', u'Actors.Anims', u'Actors.CombatStyle',
        u'Actors.DeathItem', u'Actors.Skeleton', u'Actors.Spells',
        u'Actors.SpellsForceAdd', u'Actors.Stats', u'Body-F', u'Body-M',
        u'Body-Size-F', u'Body-Size-M', u'C.Climate', u'C.Light', u'C.Music',
        u'C.Name', u'C.Owner', u'C.RecordFlags', u'C.Regions', u'C.Water',
        u'Creatures.Blood', u'Creatures.Type', u'Deactivate', u'Delev',
        u'Derel', u'Eyes', u'Factions', u'Filter', u'Graphics', u'Hair',
        u'IIM', u'Invent', u'MustBeActiveIfImported', u'Names', u'NoMerge',
        u'NPC.Class', u'Npc.EyesOnly', u'Npc.HairOnly', u'NPC.Race',
        u'NpcFaces', u'NpcFacesForceFullImport', u'R.AddSpells',
        u'R.Attributes-F', u'R.Attributes-M', u'R.ChangeSpells',
        u'R.Description', u'R.Ears', u'R.Head', u'R.Mouth', u'R.Relations',
        u'R.Skills', u'R.Teeth', u'Relations', u'Relev', u'Roads', u'Scripts',
        u'Sound', u'SpellStats', u'Stats', u'Text', u'Voice-F', u'Voice-M',
    }

    patchers = (u'PatchMerger', # PatchMerger must come first !
        u'ActorImporter', u'AlchemicalCatalogs', u'AliasesPatcher',
        u'AssortedTweaker', u'CellImporter', u'ClothesTweaker', u'CoblExhaustion',
        u'ContentsChecker', u'DeathItemPatcher', u'GmstTweaker',
        u'GraphicsPatcher', u'ImportActorsSpells', u'ImportFactions',
        u'ImportInventory', u'ImportRelations', u'ImportScripts', u'KFFZPatcher',
        u'ListsMerger', u'MFactMarker', u'NamesPatcher', u'NamesTweaker',
        u'NPCAIPackagePatcher', u'NpcFacePatcher', u'RacePatcher',
        u'RoadImporter', u'SEWorldEnforcer', u'SoundPatcher', u'SpellsPatcher',
        u'StatsPatcher', u'TextImporter', u'TweakActors', u'UpdateReferences',
    )

    CBash_patchers = (u'CBash_PatchMerger', # PatchMerger must come first !
        u'CBash_ActorImporter', u'CBash_AlchemicalCatalogs',
        u'CBash_AliasesPatcher', u'CBash_AssortedTweaker',
        u'CBash_CellImporter', u'CBash_ClothesTweaker',
        u'CBash_CoblExhaustion', u'CBash_ContentsChecker',
        u'CBash_DeathItemPatcher', u'CBash_GmstTweaker',
        u'CBash_GraphicsPatcher', u'CBash_ImportActorsSpells',
        u'CBash_ImportFactions', u'CBash_ImportInventory',
        u'CBash_ImportRelations', u'CBash_ImportScripts', u'CBash_KFFZPatcher',
        u'CBash_ListsMerger', u'CBash_MFactMarker', u'CBash_NamesPatcher',
        u'CBash_NamesTweaker', u'CBash_NPCAIPackagePatcher',
        u'CBash_NpcFacePatcher', u'CBash_RacePatcher', u'CBash_RoadImporter',
        u'CBash_SEWorldEnforcer', u'CBash_SoundPatcher',
        u'CBash_SpellsPatcher', u'CBash_StatsPatcher', u'CBash_TweakActors',
        u'CBash_UpdateReferences',
    )

    weaponTypes = (
        _(u'Blade (1 Handed)'),
        _(u'Blade (2 Handed)'),
        _(u'Blunt (1 Handed)'),
        _(u'Blunt (2 Handed)'),
        _(u'Staff'),
        _(u'Bow'),
        )

    raceNames = {
        0x23fe9 : _(u'Argonian'),
        0x224fc : _(u'Breton'),
        0x191c1 : _(u'Dark Elf'),
        0x19204 : _(u'High Elf'),
        0x00907 : _(u'Imperial'),
        0x22c37 : _(u'Khajiit'),
        0x224fd : _(u'Nord'),
        0x191c0 : _(u'Orc'),
        0x00d43 : _(u'Redguard'),
        0x00019 : _(u'Vampire'),
        0x223c8 : _(u'Wood Elf'),
        }
    raceShortNames = {
        0x23fe9 : u'Arg',
        0x224fc : u'Bre',
        0x191c1 : u'Dun',
        0x19204 : u'Alt',
        0x00907 : u'Imp',
        0x22c37 : u'Kha',
        0x224fd : u'Nor',
        0x191c0 : u'Orc',
        0x00d43 : u'Red',
        0x223c8 : u'Bos',
        }
    raceHairMale = {
        0x23fe9 : 0x64f32, #--Arg
        0x224fc : 0x90475, #--Bre
        0x191c1 : 0x64214, #--Dun
        0x19204 : 0x7b792, #--Alt
        0x00907 : 0x90475, #--Imp
        0x22c37 : 0x653d4, #--Kha
        0x224fd : 0x1da82, #--Nor
        0x191c0 : 0x66a27, #--Orc
        0x00d43 : 0x64215, #--Red
        0x223c8 : 0x690bc, #--Bos
        }
    raceHairFemale = {
        0x23fe9 : 0x64f33, #--Arg
        0x224fc : 0x1da83, #--Bre
        0x191c1 : 0x1da83, #--Dun
        0x19204 : 0x690c2, #--Alt
        0x00907 : 0x1da83, #--Imp
        0x22c37 : 0x653d0, #--Kha
        0x224fd : 0x1da83, #--Nor
        0x191c0 : 0x64218, #--Orc
        0x00d43 : 0x64210, #--Red
        0x223c8 : 0x69473, #--Bos
        }

    @classmethod
    def init(cls):
        cls._dynamic_import_modules(__name__)
        from .records import MreActi, MreAlch, MreAmmo, MreAnio, MreAppa, \
            MreArmo, MreBook, MreBsgn, MreClas, MreClot, MreCont, MreCrea, \
            MreDoor, MreEfsh, MreEnch, MreEyes, MreFact, MreFlor, MreFurn, \
            MreGras, MreHair, MreIngr, MreKeym, MreLigh, MreLscr, MreLvlc, \
            MreLvli, MreLvsp, MreMgef, MreMisc, MreNpc, MrePack, MreQust, \
            MreRace, MreScpt, MreSgst, MreSlgm, MreSoun, MreSpel, MreStat, \
            MreTree, MreWatr, MreWeap, MreWthr, MreClmt, MreCsty, MreIdle, \
            MreLtex, MreRegn, MreSbsp, MreSkil, MreAchr, MreAcre, MreCell, \
            MreGmst, MreRefr, MreRoad, MreTes4, MreWrld, MreDial, MreInfo
        cls.mergeClasses = (
            MreActi, MreAlch, MreAmmo, MreAnio, MreAppa, MreArmo, MreBook,
            MreBsgn, MreClas, MreClot, MreCont, MreCrea, MreDoor, MreEfsh,
            MreEnch, MreEyes, MreFact, MreFlor, MreFurn, MreGlob, MreGras,
            MreHair, MreIngr, MreKeym, MreLigh, MreLscr, MreLvlc, MreLvli,
            MreLvsp, MreMgef, MreMisc, MreNpc, MrePack, MreQust, MreRace,
            MreScpt, MreSgst, MreSlgm, MreSoun, MreSpel, MreStat, MreTree,
            MreWatr, MreWeap, MreWthr, MreClmt, MreCsty, MreIdle, MreLtex,
            MreRegn, MreSbsp, MreSkil, MreGmst,
        )
        cls.readClasses = (MreMgef, MreScpt,)
        cls.writeClasses = (MreMgef,)
        # Setting RecordHeader class variables - Oblivion is special
        __rec_type = brec.RecordHeader
        __rec_type.rec_header_size = 20
        __rec_type.rec_pack_format = ['=4s', 'I', 'I', 'I', 'I']
        __rec_type.rec_pack_format_str = ''.join(__rec_type.rec_pack_format)
        __rec_type.pack_formats = {0: '=4sI4s2I'}
        __rec_type.pack_formats.update(
            {x: '=4s4I' for x in {1, 6, 7, 8, 9, 10}})
        __rec_type.pack_formats.update({x: '=4sIi2I' for x in {2, 3}})
        __rec_type.pack_formats.update({x: '=4sIhh2I' for x in {4, 5}})
        # Similar to other games
        __rec_type.topTypes = [
            'GMST', 'GLOB', 'CLAS', 'FACT', 'HAIR', 'EYES', 'RACE', 'SOUN',
            'SKIL', 'MGEF', 'SCPT', 'LTEX', 'ENCH', 'SPEL', 'BSGN', 'ACTI',
            'APPA', 'ARMO', 'BOOK', 'CLOT', 'CONT', 'DOOR', 'INGR', 'LIGH',
            'MISC', 'STAT', 'GRAS', 'TREE', 'FLOR', 'FURN', 'WEAP', 'AMMO',
            'NPC_', 'CREA', 'LVLC', 'SLGM', 'KEYM', 'ALCH', 'SBSP', 'SGST',
            'LVLI', 'WTHR', 'CLMT', 'REGN', 'CELL', 'WRLD', 'DIAL', 'QUST',
            'IDLE', 'PACK', 'CSTY', 'LSCR', 'LVSP', 'ANIO', 'WATR', 'EFSH']
        __rec_type.recordTypes = set(
            __rec_type.topTypes + ['GRUP', 'TES4', 'ROAD', 'REFR', 'ACHR',
                                   'ACRE', 'PGRD', 'LAND', 'INFO'])
        brec.MreRecord.type_class = dict((x.classType,x) for x in (
            MreAchr, MreAcre, MreActi, MreAlch, MreAmmo, MreAnio, MreAppa,
            MreArmo, MreBook, MreBsgn, MreCell, MreClas, MreClot, MreCont,
            MreCrea, MreDoor, MreEfsh, MreEnch, MreEyes, MreFact, MreFlor,
            MreFurn, MreGlob, MreGmst, MreGras, MreHair, MreIngr, MreKeym,
            MreLigh, MreLscr, MreLvlc, MreLvli, MreLvsp, MreMgef, MreMisc,
            MreNpc, MrePack, MreQust, MreRace, MreRefr, MreRoad, MreScpt,
            MreSgst, MreSkil, MreSlgm, MreSoun, MreSpel, MreStat, MreTree,
            MreTes4, MreWatr, MreWeap, MreWrld, MreWthr, MreClmt, MreCsty,
            MreIdle, MreLtex, MreRegn, MreSbsp, MreDial, MreInfo,))
        brec.MreRecord.simpleTypes = (
            set(brec.MreRecord.type_class) - {'TES4', 'ACHR', 'ACRE', 'REFR',
                                              'CELL', 'PGRD', 'ROAD', 'LAND',
                                              'WRLD', 'INFO', 'DIAL'})

GAME_TYPE = OblivionGameInfo
