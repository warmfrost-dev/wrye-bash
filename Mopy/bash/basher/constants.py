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

"""This module contains some constants ripped out of basher.py"""
from .. import bass, bush
from ..balt import ImageList, defPos
from ..gui import Image

# Color Descriptions ----------------------------------------------------------
colorInfo = {
    'default.text': (_(u'Default Text'),
        _(u'This is the text color used for list items when no other is '
        u'specified.  For example, an ESP that is not mergeable or ghosted, '
        u'and has no other problems.'),
    ),
    'default.bkgd': (_(u'Default Background'),
        _(u'This is the text background color used for list items when no '
          u'other is specified.  For example, an ESM that is not ghosted.'),
    ),
    'mods.text.esm': (_(u'ESM'),
        _(u'Tabs: Mods, Saves') + u'\n\n' +
        _(u'This is the text color used for ESMs in the Mods Tab, and in the '
          u'Masters info on both the Mods Tab and Saves Tab.'),),
    'mods.text.esl': (_(u'ESL'),
        _(u'Tabs: Mods, Saves') + u'\n\n' +
        _(u'This is the text color used for ESLs in the Mods Tab, and in the '
          u'Masters info on both the Mods Tab and Saves Tab.'),),
    'mods.text.eslm': (_(u'ESLM'),
        _(u'Tabs: Mods, Saves') + u'\n\n' +
        _(u'This is the text color used for ESLs with a master flag in the '
          u'Mods Tab, and in the Masters info on both the Mods Tab and Saves '
          u'Tab.'),),
    'mods.text.noMerge': (_(u"'NoMerge' Plugin"),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u"This is the text color used for a mergeable plugin that is "
          u"tagged 'NoMerge'."),
    ),
    'mods.text.bashedPatch': (_(u"Bashed Patch"),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u"This is the text color used for Bashed Patches."),
    ),
    'mods.bkgd.doubleTime.exists': (_(u'Inactive Time Conflict'),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u'This is the background color used for a plugin with an inactive '
          u'time conflict.  This means that two or more plugins have the same '
          u'timestamp, but only one (or none) of them is active.'),
    ),
    'mods.bkgd.doubleTime.load': (_(u'Active Time Conflict'),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u'This is the background color used for a plugin with an active '
          u'time conflict.  This means that two or more plugins with the same '
          u'timestamp are active.'),
    ),
    'mods.bkgd.deactivate': (_(u"'Deactivate' Plugin"),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u"This is the background color used for an active plugin that is "
          u"tagged 'Deactivate'."),
    ),
    'mods.bkgd.ghosted': (_(u'Ghosted Plugin'),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u'This is the background color used for a ghosted plugin.'),
    ),
    'ini.bkgd.invalid': (_(u'Invalid INI Tweak'),
        _(u'Tabs: INI Edits') + u'\n\n' +
        _(u'This is the background color used for a tweak file that is invalid'
          u' for the currently selected target INI.'),
    ),
    'tweak.bkgd.invalid': (_(u'Invalid Tweak Line'),
        _(u'Tabs: INI Edits') + u'\n\n' +
        _(u'This is the background color used for a line in a tweak file that '
          u'is invalid for the currently selected target INI.'),
    ),
    'tweak.bkgd.mismatched': (_(u'Mismatched Tweak Line'),
        _(u'Tabs: INI Edits') + u'\n\n' +
        _(u'This is the background color used for a line in a tweak file that '
          u'does not match what is set in the target INI.'),
    ),
    'tweak.bkgd.matched': (_(u'Matched Tweak Line'),
        _(u'Tabs: INI Edits') + u'\n\n' +
        _(u'This is the background color used for a line in a tweak file that '
          u'matches what is set in the target INI.'),
    ),
    'installers.text.complex': (_(u'Complex Installer'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the text color used for a complex BAIN package.'),
    ),
    'installers.text.invalid': (_(u'Invalid'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the text color used for invalid packages.'),
    ),
    'installers.text.marker': (_(u'Marker'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the text color used for Markers.'),
    ),
    'installers.bkgd.skipped': (_(u'Skipped Files'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the background color used for a package with files that '
          u'will not be installed by BAIN.  This means some files are selected'
          u' to be installed, but due to your current Skip settings (for '
          u'example, Skip DistantLOD), will not be installed.'),
    ),
    'installers.bkgd.outOfOrder': (_(u'Installer Out of Order'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the background color used for an installer with files '
          u'installed, that should be overridden by a package with a higher '
          u'install order.  It can be repaired with an Anneal or Anneal All.'),
    ),
    'installers.bkgd.dirty': (_(u'Dirty Installer'),
        _(u'Tabs: Installers') + u'\n\n' +
        _(u'This is the background color used for an installer that is '
          u'configured in a "dirty" manner.  This means changes have been made'
          u' to its configuration, and an Anneal or Install needs to be '
          u'performed to make the install match what is configured.'),
    ),
    'screens.bkgd.image': (_(u'Screenshot Background'),
        _(u'Tabs: Saves, Screens') + u'\n\n' +
        _(u'This is the background color used for images.'),
    ),
}
if bush.game.check_esl:
    colorInfo['mods.text.mergeable'] = (_(u'ESL Capable plugin'),
            _(u'Tabs: Mods') + u'\n\n' +
            _(u'This is the text color used for ESL Capable plugins.'),
        )
else:
    colorInfo['mods.text.mergeable'] = (_(u'Mergeable Plugin'),
            _(u'Tabs: Mods') + u'\n\n' +
            _(u'This is the text color used for mergeable plugins.'),
        )

if bush.game.Esp.check_master_sizes:
    colorInfo[u'mods.bkgd.size_mismatch'] = (_(u'Size Mismatch'),
        _(u'Tabs: Mods') + u'\n\n' +
        _(u'This is the background color used for plugin masters that have a '
          u'stored size not matching the one of the plugin on disk, and for '
          u'plugins that have at least one such master.')
    )

#--Load config/defaults
settingDefaults = { ##: (178) belongs to bosh (or better to a settings package)
    #--Basics
    'bash.version': 0,
    'bash.CBashEnabled': True,
    'bash.backupPath': None,
    'bash.frameMax': False, # True if maximized
    'bash.page':1,
    'bash.useAltName':True,
    'bash.pluginEncoding': 'cp1252',    # Western European
    #--Colors
    'bash.colors': {
        #--Common Colors
        u'default.text':                 (0,   0,   0),   # 'BLACK'
        u'default.bkgd':                 (255, 255, 255), # 'WHITE'
        #--Mods Tab
        u'mods.text.esm':                (0,   0,   255), # 'BLUE'
        u'mods.text.mergeable':          (0,   153, 0),
        u'mods.text.noMerge':            (150, 130, 0),
        u'mods.bkgd.doubleTime.exists':  (255, 220, 220),
        u'mods.bkgd.doubleTime.load':    (255, 100, 100),
        u'mods.bkgd.deactivate':         (255, 100, 100),
        u'mods.bkgd.ghosted':            (232, 232, 232),
        u'mods.text.eslm':               (123, 29,  223),
        u'mods.text.esl':                (226, 54,  197),
        u'mods.text.bashedPatch':        (30,  157, 251),
        #--INI Edits Tab
        u'ini.bkgd.invalid':             (223, 223, 223),
        u'tweak.bkgd.invalid':           (255, 213, 170),
        u'tweak.bkgd.mismatched':        (255, 255, 191),
        u'tweak.bkgd.matched':           (193, 255, 193),
        #--Installers Tab
        u'installers.text.complex':      (35,  35,  142), # 'NAVY'
        u'installers.text.invalid':      (128, 128, 128), # 'GREY'
        u'installers.text.marker':       (230, 97,  89),
        u'installers.bkgd.skipped':      (224, 224, 224),
        u'installers.bkgd.outOfOrder':   (255, 255, 0),
        u'installers.bkgd.dirty':        (255, 187, 51),
        #--Screens Tab
        u'screens.bkgd.image':           (100, 100, 100),
    },
    #--BSA Redirection
    'bash.bsaRedirection':True,
    #--Wrye Bash: Load Lists
    'bash.loadLists.data': {}, ##: to be removed
    # Wrye Bash: Load Order
    u'bash.load_order.lock_active_plugins': True,
    #--Wrye Bash: StatusBar
    'bash.statusbar.iconSize': 16,
    'bash.statusbar.hide': set(),
    'bash.statusbar.order': [],
    'bash.statusbar.showversion': False,
    #--Wrye Bash: Group and Rating
    'bash.mods.groups': [
        u'Root',
        u'Library',
        u'Cosmetic',
        u'Clothing',
        u'Weapon',
        u'Tweak',
        u'Overhaul',
        u'Misc.',
        u'Magic',
        u'NPC',
        u'Home',
        u'Place',
        u'Quest',
        u'Last',
    ],
    'bash.mods.ratings': ['+','1','2','3','4','5','=','~'],
    #--Wrye Bash: Col (Sort) Names
    'bash.colNames': {
        'Mod Status': _(u'Mod Status'),
        'Author': _(u'Author'),
        'Cell': _(u'Cell'),
        'CRC':_(u'CRC'),
        'Current Order': _(u'Current LO'),
        'Date': _(u'Date'),
        'Day': _(u'Day'),
        'File': _(u'File'),
        'Files': _(u'Files'),
        'Group': _(u'Group'),
        'Header': _(u'Header'),
        'Installer':_(u'Installer'),
        'Karma': _(u'Karma'),
        'Load Order': _(u'Load Order'),
        'Modified': _(u'Modified'),
        'Name': _(u'Name'),
        'Num': _(u'MI'),
        'Order': _(u'Order'),
        'Package': _(u'Package'),
        'PlayTime':_(u'Hours'),
        'Player': _(u'Player'),
        'Rating': _(u'Rating'),
        'Save Order': _(u'Save Order'),
        'Size': _(u'Size'),
        'Status': _(u'Status'),
        'Subject': _(u'Subject'),
        },
    #--Wrye Bash: Masters
    'bash.masters.cols': ['File', 'Num', 'Current Order'],
    'bash.masters.esmsFirst': 1,
    'bash.masters.selectedFirst': 0,
    'bash.masters.sort': 'Num',
    'bash.masters.colReverse': {},
    'bash.masters.colWidths': {
        'File':80,
        'Num':30,
        'Current Order':60,
        },
    #--Wrye Bash: Mod Docs
    'bash.modDocs.show': False,
    'bash.modDocs.dir': None,
    #--Installers
    'bash.installers.cols': ['Package','Order','Modified','Size','Files'],
    'bash.installers.colReverse': {},
    'bash.installers.sort': 'Order',
    'bash.installers.colWidths': {
        'Package':230,
        'Order':25,
        'Modified':135,
        'Size':75,
        'Files':55,
        },
    'bash.installers.page':0,
    'bash.installers.enabled': True,
    'bash.installers.autoAnneal': True,
    'bash.installers.autoWizard':True,
    'bash.installers.wizardOverlay':True,
    'bash.installers.fastStart': True,
    'bash.installers.autoRefreshBethsoft': False,
    'bash.installers.autoRefreshProjects': True,
    'bash.installers.removeEmptyDirs':True,
    'bash.installers.skipScreenshots':False,
    'bash.installers.skipScriptSources':False,
    'bash.installers.skipImages':False,
    'bash.installers.skipDocs':False,
    'bash.installers.skipDistantLOD':False,
    'bash.installers.skipLandscapeLODMeshes':False,
    'bash.installers.skipLandscapeLODTextures':False,
    'bash.installers.skipLandscapeLODNormals':False,
    'bash.installers.skipTESVBsl':True,
    'bash.installers.allowOBSEPlugins':True,
    'bash.installers.renameStrings':True,
    u'bash.installers.redirect_scripts': True,
    'bash.installers.sortProjects':False,
    'bash.installers.sortActive':False,
    'bash.installers.sortStructure':False,
    'bash.installers.conflictsReport.showLower':True,
    'bash.installers.conflictsReport.showInactive':False,
    u'bash.installers.conflictsReport.showBSAConflicts': True,
    'bash.installers.goodDlls':{},
    'bash.installers.badDlls':{},
    'bash.installers.onDropFiles.action':None,
    'bash.installers.commentsSplitterSashPos':0,
    #--Wrye Bash: Wizards
    u'bash.fomod.size': (600, 500),
    u'bash.fomod.pos': tuple(defPos),
    u'bash.fomod.use_table': False,
    'bash.wizard.size': (600, 500),
    'bash.wizard.pos': tuple(defPos),
    #--Wrye Bash: INI Tweaks
    'bash.ini.cols': ['File','Installer'],
    'bash.ini.sort': 'File',
    'bash.ini.colReverse': {},
    'bash.ini.sortValid': True,
    'bash.ini.colWidths': {
        'File':300,
        'Installer':100,
        },
    'bash.ini.choices': {},
    'bash.ini.choice': 0,
    'bash.ini.allowNewLines': bush.game.Ini.allow_new_lines,
    #--Wrye Bash: Mods
    'bash.mods.autoGhost': False,
    'bash.mods.auto_flag_esl': True,
    'bash.mods.cols': ['File', 'Load Order', 'Installer', 'Modified', 'Size',
                       'Author', 'CRC'],
    'bash.mods.esmsFirst': 1,
    'bash.mods.selectedFirst': 0,
    'bash.mods.sort': 'Load Order',
    'bash.mods.colReverse': {},
    'bash.mods.colWidths': {
        'Author':100,
        'File':200,
        'Group':10,
        'Installer':100,
        'Load Order':25,
        'Modified':135,
        'Rating':10,
        'Size':75,
        'CRC':60,
        'Mod Status':50,
        },
    'bash.mods.renames': {},
    'bash.mods.scanDirty': True,
    'bash.mods.export.skip': u'',
    'bash.mods.export.deprefix': u'',
    'bash.mods.export.skipcomments': False,
    #--Wrye Bash: Saves
    'bash.saves.cols': ['File','Modified','Size','PlayTime','Player','Cell'],
    'bash.saves.sort': 'Modified',
    'bash.saves.colReverse': {
        'Modified':1,
        },
    'bash.saves.colWidths': {
        'File':375,
        'Modified':135,
        'Size':65,
        'PlayTime':50,
        'Player':70,
        'Cell':80,
        },
    #Wrye Bash: BSAs
    'bash.BSAs.cols': ['File', 'Modified', 'Size'],
    'bash.BSAs.colReverse': {
        'Modified':1,
        },
    'bash.BSAs.colWidths': {
        'File':150,
        'Modified':150,
        'Size':75,
        },
    'bash.BSAs.sort': 'File',
    #--Wrye Bash: Screens
    'bash.screens.cols': ['File', 'Modified', 'Size'],
    'bash.screens.sort': 'File',
    'bash.screens.colReverse': {
        'Modified':1,
        },
    'bash.screens.colWidths': {
        'File':100,
        'Modified':150,
        'Size':75,
        },
    'bash.screens.jpgQuality': 95,
    'bash.screens.jpgCustomQuality': 75,
    #--Wrye Bash: People
    'bash.people.cols': ['Name','Karma','Header'],
    'bash.people.sort': 'Name',
    'bash.people.colReverse': {},
    'bash.people.colWidths': {
        'Name': 80,
        'Karma': 25,
        'Header': 50,
        },
    #--BOSS:
    'BOSS.ClearLockTimes':True,
    'BOSS.AlwaysUpdate':True,
    'BOSS.UseGUI':False,
}

# No need to store defaults for all the xEdits for all games
settingDefaults[bush.game.Xe.xe_key_prefix + u'.iKnowWhatImDoing'] = False
settingDefaults[bush.game.Xe.xe_key_prefix + u'.skip_bsas'] = False

if bush.game.Esp.check_master_sizes:
    settingDefaults[u'bash.colors'][u'mods.bkgd.size_mismatch'] = (255, 238,
                                                                   217)

# Images ----------------------------------------------------------------------
#------------------------------------------------------------------------------
imDirJn = bass.dirs[u'images'].join
def _png(fname): return Image(imDirJn(fname))

#--Image lists
karmacons = ImageList(16,16)
karmacons.images.extend({
    'karma+5': _png(u'checkbox_purple_inc.png'),
    'karma+4': _png(u'checkbox_blue_inc.png'),
    'karma+3': _png(u'checkbox_blue_inc.png'),
    'karma+2': _png(u'checkbox_green_inc.png'),
    'karma+1': _png(u'checkbox_green_inc.png'),
    'karma+0': _png(u'checkbox_white_off.png'),
    'karma-1': _png(u'checkbox_yellow_off.png'),
    'karma-2': _png(u'checkbox_yellow_off.png'),
    'karma-3': _png(u'checkbox_orange_off.png'),
    'karma-4': _png(u'checkbox_orange_off.png'),
    'karma-5': _png(u'checkbox_red_off.png'),
    }.items())
installercons = ImageList(16,16)
installercons.images.extend({
    #--Off/Archive
    'off.green':  _png(u'checkbox_green_off.png'),
    'off.grey':   _png(u'checkbox_grey_off.png'),
    'off.red':    _png(u'checkbox_red_off.png'),
    'off.white':  _png(u'checkbox_white_off.png'),
    'off.orange': _png(u'checkbox_orange_off.png'),
    'off.yellow': _png(u'checkbox_yellow_off.png'),
    #--Off/Archive - Wizard
    'off.green.wiz':    _png(u'checkbox_green_off_wiz.png'),
    #grey
    'off.red.wiz':      _png(u'checkbox_red_off_wiz.png'),
    'off.white.wiz':    _png(u'checkbox_white_off_wiz.png'),
    'off.orange.wiz':   _png(u'checkbox_orange_off_wiz.png'),
    'off.yellow.wiz':   _png(u'checkbox_yellow_off_wiz.png'),
    #--On/Archive
    'on.green':  _png(u'checkbox_green_inc.png'),
    'on.grey':   _png(u'checkbox_grey_inc.png'),
    'on.red':    _png(u'checkbox_red_inc.png'),
    'on.white':  _png(u'checkbox_white_inc.png'),
    'on.orange': _png(u'checkbox_orange_inc.png'),
    'on.yellow': _png(u'checkbox_yellow_inc.png'),
    #--On/Archive - Wizard
    'on.green.wiz':  _png(u'checkbox_green_inc_wiz.png'),
    #grey
    'on.red.wiz':    _png(u'checkbox_red_inc_wiz.png'),
    'on.white.wiz':  _png(u'checkbox_white_inc_wiz.png'),
    'on.orange.wiz': _png(u'checkbox_orange_inc_wiz.png'),
    'on.yellow.wiz': _png(u'checkbox_yellow_inc_wiz.png'),
    #--Off/Directory
    'off.green.dir':  _png(u'diamond_green_off.png'),
    'off.grey.dir':   _png(u'diamond_grey_off.png'),
    'off.red.dir':    _png(u'diamond_red_off.png'),
    'off.white.dir':  _png(u'diamond_white_off.png'),
    'off.orange.dir': _png(u'diamond_orange_off.png'),
    'off.yellow.dir': _png(u'diamond_yellow_off.png'),
    #--Off/Directory - Wizard
    'off.green.dir.wiz':  _png(u'diamond_green_off_wiz.png'),
    #grey
    'off.red.dir.wiz':    _png(u'diamond_red_off_wiz.png'),
    'off.white.dir.wiz':  _png(u'diamond_white_off_wiz.png'),
    'off.orange.dir.wiz': _png(u'diamond_orange_off_wiz.png'),
    'off.yellow.dir.wiz': _png(u'diamond_yellow_off_wiz.png'),
    #--On/Directory
    'on.green.dir':  _png(u'diamond_green_inc.png'),
    'on.grey.dir':   _png(u'diamond_grey_inc.png'),
    'on.red.dir':    _png(u'diamond_red_inc.png'),
    'on.white.dir':  _png(u'diamond_white_inc.png'),
    'on.orange.dir': _png(u'diamond_orange_inc.png'),
    'on.yellow.dir': _png(u'diamond_yellow_inc.png'),
    #--On/Directory - Wizard
    'on.green.dir.wiz':  _png(u'diamond_green_inc_wiz.png'),
    #grey
    'on.red.dir.wiz':    _png(u'diamond_red_inc_wiz.png'),
    'on.white.dir.wiz':  _png(u'diamond_white_off_wiz.png'),
    'on.orange.dir.wiz': _png(u'diamond_orange_inc_wiz.png'),
    'on.yellow.dir.wiz': _png(u'diamond_yellow_inc_wiz.png'),
    #--Broken
    'corrupt':   _png(u'red_x.png'),
    }.items())

#--Buttons
def imageList(template):
    return [Image(imDirJn(template % x)) for x in (16,24,32)]

# TODO(65): game handling refactoring - some of the buttons are game specific
toolbar_buttons = (
    (u'ISOBL', imageList(u'tools/isobl%s.png'),
    _(u"Launch InsanitySorrow's Oblivion Launcher")),
    (u'ISRMG', imageList(u"tools/insanity'sreadmegenerator%s.png"),
    _(u"Launch InsanitySorrow's Readme Generator")),
    (u'ISRNG', imageList(u"tools/insanity'srng%s.png"),
    _(u"Launch InsanitySorrow's Random Name Generator")),
    (u'ISRNPCG', imageList(u'tools/randomnpc%s.png'),
    _(u"Launch InsanitySorrow's Random NPC Generator")),
    (u'OBFEL', imageList(u'tools/oblivionfaceexchangerlite%s.png'),
    _(u'Oblivion Face Exchange Lite')),
    (u'OBMLG', imageList(u'tools/modlistgenerator%s.png'),
    _(u'Oblivion Mod List Generator')),
    (u'BSACMD', imageList(u'tools/bsacommander%s.png'),
    _(u'Launch BSA Commander')),
    (u'Tabula', imageList(u'tools/tabula%s.png'),
     _(u'Launch Tabula')),
    (u'Tes4FilesPath', imageList(u'tools/tes4files%s.png'),
    _(u'Launch TES4Files')),
)

modeling_tools_buttons = (
    (u'AutoCad', imageList(u'tools/autocad%s.png'), _(u'Launch AutoCad')),
    (u'BlenderPath', imageList(u'tools/blender%s.png'), _(u'Launch Blender')),
    (u'Dogwaffle', imageList(u'tools/dogwaffle%s.png'),
     _(u'Launch Dogwaffle')),
    (u'GmaxPath', imageList(u'tools/gmax%s.png'), _(u'Launch Gmax')),
    (u'MayaPath', imageList(u'tools/maya%s.png'), _(u'Launch Maya')),
    (u'MaxPath', imageList(u'tools/3dsmax%s.png'), _(u'Launch 3dsMax')),
    (u'Milkshape3D', imageList(u'tools/milkshape3d%s.png'),
     _(u'Launch Milkshape 3D')),
    (u'Mudbox', imageList(u'tools/mudbox%s.png'), _(u'Launch Mudbox')),
    (u'Sculptris', imageList(u'tools/sculptris%s.png'),
     _(u'Launch Sculptris')),
    (u'SpeedTree', imageList(u'tools/speedtree%s.png'),
     _(u'Launch SpeedTree')),
    (u'Treed', imageList(u'tools/treed%s.png'), _(u'Launch Tree\[d\]')),
    (u'Wings3D', imageList(u'tools/wings3d%s.png'), _(u'Launch Wings 3D')),
)

texture_tool_buttons = (
    (u'AniFX', imageList(u'tools/anifx%s.png'), _(u'Launch AniFX')),
    (u'ArtOfIllusion', imageList(u'tools/artofillusion%s.png'),
     _(u'Launch Art Of Illusion')),
    (u'Artweaver', imageList(u'tools/artweaver%s.png'),
     _(u'Launch Artweaver')),
    (u'CrazyBump', imageList(u'tools/crazybump%s.png'),
     _(u'Launch CrazyBump')),
    (u'DDSConverter', imageList(u'tools/ddsconverter%s.png'),
     _(u'Launch DDSConverter')),
    (u'DeepPaint', imageList(u'tools/deeppaint%s.png'),
     _(u'Launch DeepPaint')),
    (u'FastStone', imageList(u'tools/faststoneimageviewer%s.png'),
     _(u'Launch FastStone Image Viewer')),
    (u'Genetica', imageList(u'tools/genetica%s.png'), _(u'Launch Genetica')),
    (u'GeneticaViewer', imageList(u'tools/geneticaviewer%s.png'),
     _(u'Launch Genetica Viewer')),
    (u'GIMP', imageList(u'tools/gimp%s.png'), _(u'Launch GIMP')),
    (u'IcoFX', imageList(u'tools/icofx%s.png'), _(u'Launch IcoFX')),
    (u'Inkscape', imageList(u'tools/inkscape%s.png'), _(u'Launch Inkscape')),
    (u'IrfanView', imageList(u'tools/irfanview%s.png'),
     _(u'Launch IrfanView')),
    (u'Krita', imageList(u'tools/krita%s.png'), _(u'Launch Krita')),
    (u'MaPZone', imageList(u'tools/mapzone%s.png'), _(u'Launch MaPZone')),
    (u'MyPaint', imageList(u'tools/mypaint%s.png'), _(u'Launch MyPaint')),
    (u'NVIDIAMelody', imageList(u'tools/nvidiamelody%s.png'),
     _(u'Launch Nvidia Melody')),
    (u'PaintNET', imageList(u'tools/paint.net%s.png'), _(u'Launch Paint.NET')),
    (u'PaintShopPhotoPro', imageList(u'tools/paintshopprox3%s.png'),
     _(u'Launch PaintShop Photo Pro')),
    (u'PhotoshopPath', imageList(u'tools/photoshop%s.png'),
     _(u'Launch Photoshop')),
    (u'PhotoScape', imageList(u'tools/photoscape%s.png'),
     _(u'Launch PhotoScape')),
    (u'PhotoSEAM', imageList(u'tools/photoseam%s.png'),
     _(u'Launch PhotoSEAM')),
    (u'Photobie', imageList(u'tools/photobie%s.png'), _(u'Launch Photobie')),
    (u'PhotoFiltre', imageList(u'tools/photofiltre%s.png'),
     _(u'Launch PhotoFiltre')),
    (u'PixelStudio', imageList(u'tools/pixelstudiopro%s.png'),
     _(u'Launch Pixel Studio Pro')),
    (u'Pixia', imageList(u'tools/pixia%s.png'), _(u'Launch Pixia')),
    (u'TextureMaker', imageList(u'tools/texturemaker%s.png'),
     _(u'Launch TextureMaker')),
    (u'TwistedBrush', imageList(u'tools/twistedbrush%s.png'),
     _(u'Launch TwistedBrush')),
    (u'WTV', imageList(u'tools/wtv%s.png'),
     _(u'Launch Windows Texture Viewer')),
    (u'xNormal', imageList(u'tools/xnormal%s.png'), _(u'Launch xNormal')),
    (u'XnView', imageList(u'tools/xnview%s.png'), _(u'Launch XnView')),
)

audio_tools = (
    (u'Audacity', imageList(u'tools/audacity%s.png'), _(u'Launch Audacity')),
    (u'ABCAmberAudioConverter',
     imageList(u'tools/abcamberaudioconverter%s.png'),
    _(u'Launch ABC Amber Audio Converter')),
    (u'Switch', imageList(u'tools/switch%s.png'), _(u'Launch Switch')),
)

misc_tools = (
    (u'Fraps', imageList(u'tools/fraps%s.png'), _(u'Launch Fraps')),
    (u'MAP', imageList(u'tools/interactivemapofcyrodiil%s.png'),
        _(u'Interactive Map of Cyrodiil and Shivering Isles')),
    (u'LogitechKeyboard', imageList(u'tools/logitechkeyboard%s.png'),
        _(u'Launch LogitechKeyboard')),
    (u'MediaMonkey', imageList(u'tools/mediamonkey%s.png'),
        _(u'Launch MediaMonkey')),
    (u'NPP', imageList(u'tools/notepad++%s.png'), _(u'Launch Notepad++')),
    (u'Steam', imageList(u'steam%s.png'), _(u'Launch Steam')),
    (u'EVGAPrecision', imageList(u'tools/evgaprecision%s.png'),
        _(u'Launch EVGA Precision')),
    (u'WinMerge', imageList(u'tools/winmerge%s.png'), _(u'Launch WinMerge')),
    (u'FreeMind', imageList(u'tools/freemind%s.png'), _(u'Launch FreeMind')),
    (u'Freeplane', imageList(u'tools/freeplane%s.png'),
     _(u'Launch Freeplane')),
    (u'FileZilla', imageList(u'tools/filezilla%s.png'),
     _(u'Launch FileZilla')),
    (u'EggTranslator', imageList(u'tools/eggtranslator%s.png'),
        _(u'Launch Egg Translator')),
    (u'RADVideo', imageList(u'tools/radvideotools%s.png'),
        _(u'Launch RAD Video Tools')),
    (u'WinSnap', imageList(u'tools/winsnap%s.png'), _(u'Launch WinSnap')),
)
