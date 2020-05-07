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
"""GameInfo override for Fallout 4 VR. Inherits from Fallout 4 and tweaks where
necessary."""

from ..fallout4 import Fallout4GameInfo
from ... import brec

class Fallout4VRGameInfo(Fallout4GameInfo):
    displayName = u'Fallout 4 VR'
    fsName = u'Fallout4VR'
    altName = u'Wrye VRash'
    defaultIniFile = u'Fallout4.ini'
    launch_exe = u'Fallout4VR.exe'
    game_detect_file = [u'Fallout4VR.exe']
    version_detect_file = [u'Fallout4VR.exe']
    masterFiles = [u'Fallout4.esm', u'Fallout4_VR.esm',]
    iniFiles = [
        u'Fallout4.ini',
        u'Fallout4Prefs.ini',
        u'Fallout4Custom.ini',
        u'Fallout4VrCustom.ini',
    ]
    regInstallKeys = (u'Bethesda Softworks\\Fallout 4 VR', u'Installed Path')

    espm_extensions = Fallout4GameInfo.espm_extensions - {u'.esl'}
    check_esl = False

    class Se(Fallout4GameInfo.Se):
        se_abbrev = u'F4SEVR'
        long_name = u'Fallout 4 VR Script Extender'
        exe = u'f4sevr_loader.exe'
        ver_files = [u'f4sevr_loader.exe', u'f4sevr_steam_loader.dll']

    class Bsa(Fallout4GameInfo.Bsa):
        vanilla_string_bsas = Fallout4GameInfo.Bsa.vanilla_string_bsas.copy()
        vanilla_string_bsas.update({
            u'fallout4_vr.esm': [u'Fallout4_VR - Main.ba2'],
        })

    class Xe(Fallout4GameInfo.Xe):
        full_name = u'FO4VREdit'
        xe_key_prefix = u'fo4vrView'

    SkipBAINRefresh = {u'fo4vredit backups', u'fo4vredit cache'}

    class Esp(Fallout4GameInfo.Esp):
        validHeaderVersions = (0.95,)
        expanded_plugin_range = False

    allTags = Fallout4GameInfo.allTags | {u'NoMerge'}
    # PatchMerger must come first!
    patchers = (u'PatchMerger',) + Fallout4GameInfo.patchers

    # ---------------------------------------------------------------------
    # --Imported - MreGlob is special import, not in records.py
    # ---------------------------------------------------------------------
    @classmethod
    def init(cls):
        cls._dynamic_import_modules(__name__)
        # First import from fallout4.records file, so MelModel is set correctly
        from .records import MreTes4, MreLvli, MreLvln
        # ---------------------------------------------------------------------
        # These Are normally not mergable but added to brec.MreRecord.type_class
        #
        #       MreCell,
        # ---------------------------------------------------------------------
        # These have undefined FormIDs Do not merge them
        #
        #       MreNavi, MreNavm,
        # ---------------------------------------------------------------------
        # These need syntax revision but can be merged once that is corrected
        #
        #       MreAchr, MreDial, MreLctn, MreInfo, MreFact, MrePerk,
        # ---------------------------------------------------------------------
        cls.mergeClasses = (
            # -- Imported from Skyrim/SkyrimSE
            # Added to records.py
            MreLvli, MreLvln
        )
        # Setting RecordHeader class variables --------------------------------
        header_type = brec.RecordHeader
        header_type.top_grup_sigs = [
            b'GMST', b'KYWD', b'LCRT', b'AACT', b'TRNS', b'CMPO', b'TXST',
            b'GLOB', b'DMGT', b'CLAS', b'FACT', b'HDPT', b'RACE', b'SOUN',
            b'ASPC', b'MGEF', b'LTEX', b'ENCH', b'SPEL', b'ACTI', b'TACT',
            b'ARMO', b'BOOK', b'CONT', b'DOOR', b'INGR', b'LIGH', b'MISC',
            b'STAT', b'SCOL', b'MSTT', b'GRAS', b'TREE', b'FLOR', b'FURN',
            b'WEAP', b'AMMO', b'NPC_', b'PLYR', b'LVLN', b'KEYM', b'ALCH',
            b'IDLM', b'NOTE', b'PROJ', b'HAZD', b'BNDS', b'TERM', b'LVLI',
            b'WTHR', b'CLMT', b'SPGD', b'RFCT', b'REGN', b'NAVI', b'CELL',
            b'WRLD', b'QUST', b'IDLE', b'PACK', b'CSTY', b'LSCR', b'LVSP',
            b'ANIO', b'WATR', b'EFSH', b'EXPL', b'DEBR', b'IMGS', b'IMAD',
            b'FLST', b'PERK', b'BPTD', b'ADDN', b'AVIF', b'CAMS', b'CPTH',
            b'VTYP', b'MATT', b'IPCT', b'IPDS', b'ARMA', b'ECZN', b'LCTN',
            b'MESG', b'DOBJ', b'DFOB', b'LGTM', b'MUSC', b'FSTP', b'FSTS',
            b'SMBN', b'SMQN', b'SMEN', b'DLBR', b'MUST', b'DLVW', b'EQUP',
            b'RELA', b'SCEN', b'ASTP', b'OTFT', b'ARTO', b'MATO', b'MOVT',
            b'SNDR', b'SNCT', b'SOPM', b'COLL', b'CLFM', b'REVB', b'PKIN',
            b'RFGP', b'AMDL', b'LAYR', b'COBJ', b'OMOD', b'MSWP', b'ZOOM',
            b'INNR', b'KSSM', b'AECH', b'SCCO', b'AORU', b'SCSN', b'STAG',
            b'NOCM', b'LENS', b'GDRY', b'OVIS',
        ]
        header_type.valid_header_sigs = (set(header_type.top_grup_sigs) | {
            b'GRUP', b'TES4', b'REFR', b'ACHR', b'PMIS', b'PARW', b'PGRE',
            b'PBEA', b'PFLA', b'PCON', b'PBAR', b'PHZD', b'LAND', b'NAVM',
            b'DIAL', b'INFO'})
        header_type.plugin_form_version = 131
        brec.MreRecord.type_class = dict((x.classType,x) for x in (
            #--Always present
            MreTes4, MreLvli, MreLvln,
            # Imported from Skyrim or SkyrimSE
            # Added to records.py
            ))
        brec.MreRecord.simpleTypes = (
                set(brec.MreRecord.type_class) - {b'TES4', })

GAME_TYPE = Fallout4VRGameInfo
