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

"""Specific parser for Wrye Bash."""

from __future__ import division

import os
import traceback
from collections import OrderedDict

import wx.adv as wiz  # wxPython wizard class
from . import ScriptParser         # generic parser class
from . import balt, bass, bolt, bosh, bush, load_order
from .ini_files import OBSEIniFile
from .env import get_file_version
from .gui import BOTTOM, CENTER, CheckBox, GridLayout, HBoxedLayout, HLayout, \
    Label, LayoutOptions, RIGHT, Stretch, TextArea, VLayout, HyperlinkLabel, \
    WizardDialog, EventResult, ListBox, CheckListBox, Image, PictureWithCursor
from .ScriptParser import error

EXTRA_ARGS =   _(u"Extra arguments to '%s'.")
MISSING_ARGS = _(u"Missing arguments to '%s'.")
UNEXPECTED =   _(u"Unexpected '%s'.")

class WizInstallInfo(object):
    __slots__ = (u'canceled', u'select_plugins', u'rename_plugins',
                 u'select_sub_packages', u'ini_edits', u'should_install')
    # canceled: Set to true if the user canceled the wizard, or if an error
    # occurred
    # select_plugins: List of plugins to 'select' for install
    # rename_plugins: Dictionary of renames for plugins.  In the format of:
    #   'original name':'new name'
    # select_sub_packages: List of Subpackages to 'select' for install
    # ini_edits: Dictionary of INI edits to apply/create.  In the format of:
    #   'ini file': {
    #      'section': {
    #         'key': value
    #         }
    #      }
    #    For BatchScript type ini's, the 'section' will either be 'set',
    #    'setGS' or 'SetNumericGameSetting'
    # should_install: Set to True if after configuring this package, it should
    # also be installed.

    def __init__(self):
        self.canceled = False
        self.select_plugins = []
        self.rename_plugins = {}
        self.select_sub_packages = []
        self.ini_edits = {}
        self.should_install = False

class InstallerWizard(WizardDialog):
    """Class used by Wrye Bash, creates a wx Wizard that dynamically creates
    pages based on a script."""
    _def_size = (600, 500)

    def __init__(self, parent, installer, bAuto):
        super(InstallerWizard, self).__init__(parent,
            title=_(u'Installer Wizard'), sizes_dict=bass.settings,
            size_key=u'bash.wizard.size', pos_key=u'bash.wizard.pos')
        #'dummy' page tricks the wizard into always showing the "Next" button,
        #'next' will be set by the parser
        class _PageDummy(wiz.WizardPage): pass
        self.dummy = _PageDummy(self._native_widget) # todo de-wx!
        self.next = None # todo rename
        #True prevents actually moving to the 'next' page.  We use this after the "Next"
        #button is pressed, while the parser is running to return the _actual_ next page
        #'finishing' is to allow the "Next" button to be used when it's name is changed to
        #'Finish' on the last page of the wizard
        self.blockChange = True
        self.finishing = False
        #parser that will spit out the pages
        self.wizard_file = installer.wizard_file()
        self.parser = WryeParser(self, installer, bAuto)
        #Intercept the changing event so we can implement 'blockChange'
        self.on_wiz_page_change.subscribe(self.on_page_change)
        self.ret = WizInstallInfo()

    def save_size(self):
        # Otherwise, regular resize, save the size if we're not maximized
        self.on_closing(destroy=False)

    def on_page_change(self, is_forward, evt_page):
        # type: (bool, PageInstaller) -> EventResult
        if is_forward:
            if not self.finishing:
                # Next, continue script execution
                if self.blockChange:
                    #Tell the current page that next was pressed,
                    #So the parser can continue parsing,
                    #Then show the page that the parser returns,
                    #rather than the dummy page
                    evt_page.OnNext()
                    self.next = self.parser.Continue()
                    self.blockChange = False
                    self._native_widget.ShowPage(self.next)
                    return EventResult.CANCEL
                else:
                    self.blockChange = True
                    return EventResult.FINISH
        else:
            # Previous, pop back to the last state,
            # and resume execution
            self.finishing = False
            self.next = self.parser.Back()
            self.blockChange = False
            self._native_widget.ShowPage(self.next)
            return EventResult.CANCEL

    def Run(self):
        page = self.parser.Begin(self.wizard_file)
        if page:
            self.ret.canceled = not self._native_widget.RunWizard(page)
        # Clean up temp files
        if self.parser.bArchive:
            bass.rmTempDir()
        return self.ret

class PageInstaller(wiz.WizardPage):
    """Base class for all the parser wizard pages, just to handle a couple
    simple things here."""

    def __init__(self, parent):
        self._wiz_parent = parent
        super(PageInstaller, self).__init__(parent._native_widget)
        self._enableForward(True)

    def _enableForward(self, do_enable):
        self._wiz_parent.enable_forward_btn(do_enable)

    def GetNext(self): return self._wiz_parent.dummy

    def GetPrev(self):
        if self._wiz_parent.parser.choiceIdex > 0:
            return self._wiz_parent.dummy
        return None

    def OnNext(self):
        #This is what needs to be implemented by sub-classes,
        #this is where flow control objects etc should be
        #created
        pass

class PageError(PageInstaller):
    """Page that shows an error message, has only a "Cancel" button enabled,
    and cancels any changes made."""

    def __init__(self, parent, title, errorMsg):
        PageInstaller.__init__(self, parent)
        #Disable the "Finish"/"Next" button
        self._enableForward(False)
        #Layout stuff
        VLayout(spacing=5, items=[
            Label(self, title),
            (TextArea(self, editable=False, init_text=errorMsg,
                      auto_tooltip=False),
             LayoutOptions(weight=1, expand=True))
        ]).apply_to(self)
        self.Layout()

    def GetNext(self): return None

    def GetPrev(self): return None

class PageSelect(PageInstaller):
    """A page that shows a message up top, with a selection box on the left
    (multi- or single- selection), with an optional associated image and
    description for each option, shown when that item is selected."""
    def __init__(self, parent, bMany, title, desc, listItems, listDescs, listImages, defaultMap):
        PageInstaller.__init__(self, parent)
        self.listItems = listItems
        self.images = listImages
        self.descs = listDescs
        self.bMany = bMany
        self.index = None
        self.title_desc = Label(self, desc)
        self.textItem = TextArea(self, editable=False, auto_tooltip=False)
        self.bmp_item = PictureWithCursor(self, 0, 0, background=None)
        kwargs = dict(choices=listItems, isHScroll=True,
                      onSelect=self.OnSelect)
        if bMany:
            self.listOptions = CheckListBox(self, **kwargs)
            for index, default in enumerate(defaultMap):
                self.listOptions.lb_check_at_index(index, default)
        else:
            self.listOptions = ListBox(self, **kwargs)
            self._enableForward(False)
            for index, default in enumerate(defaultMap):
                if default:
                    self.listOptions.lb_select_index(index)
                    self.Selection(index)
                    break
        VLayout(item_expand=True, spacing=5, items=[
            HBoxedLayout(self, items=[self.title_desc]),
            Label(self, _(u'Options:')),
            (HLayout(item_expand=True, item_weight=1,
                     items=[self.listOptions, self.bmp_item]),
             LayoutOptions(weight=1)),
            Label(self, _(u'Description:')),
            (self.textItem, LayoutOptions(weight=1))
        ]).apply_to(self)
        self.Layout()
        self.bmp_item.on_mouse_middle_up.subscribe(self._click_on_image)
        self.bmp_item.on_mouse_left_dclick.subscribe(
            lambda selected_index: self._click_on_image())

    def OnSelect(self, lb_selection_dex, lb_selection_str):
        self.listOptions.lb_select_index(lb_selection_dex) # event.Skip() won't do
        self.Selection(lb_selection_dex)

    def _click_on_image(self):
        img = self.images[self.index]
        if img.isfile():
            try:
                img.start()
            except OSError:
                bolt.deprint(u'Failed to open %s.' % img, traceback=True)

    def Selection(self, index):
        self._enableForward(True)
        self.index = index
        self.textItem.text_content = self.descs[index]
        self.bmp_item.set_bitmap(self.images[index])
        # self.Layout() # the bitmap would change size and so blurred

    def OnNext(self):
        temp = []
        if self.bMany:
            index = -1
            for item in self.listItems:
                index += 1
                if self.listOptions.lb_is_checked_at_index(index):
                    temp.append(item)
        else:
            for i in self.listOptions.lb_get_selections():
                temp.append(self.listItems[i])
        if self._wiz_parent.parser.choiceIdex < len(self._wiz_parent.parser.choices):
            oldChoices = self._wiz_parent.parser.choices[self._wiz_parent.parser.choiceIdex]
            if temp == oldChoices:
                pass
            else:
                self._wiz_parent.parser.choices = self._wiz_parent.parser.choices[0:self._wiz_parent.parser.choiceIdex]
                self._wiz_parent.parser.choices.append(temp)
        else:
            self._wiz_parent.parser.choices.append(temp)
        self._wiz_parent.parser.PushFlow('Select', False, ['SelectOne', 'SelectMany', 'Case', 'Default', 'EndSelect'], values=temp, hitCase=False)

_obse_mod_formats = bolt.LowerDict(
    {u']set[': u' %(setting)s to %(value)s%(comment)s',
     u']setGS[': u' %(setting)s %(value)s%(comment)s',
     u']SetNumericGameSetting[': u' %(setting)s %(value)s%(comment)s'})
_obse_del_formats = bolt.LowerDict(
    {u']set[': u' %(setting)s to DELETED', u']setGS[': u' %(setting)s DELETED',
     u']SetNumericGameSetting[': u' %(setting)s DELETED'})

def generateTweakLines(wizardEdits, target):
    lines = [_(u'; Generated by Wrye Bash %s for \'%s\' via wizard') % (
        bass.AppVersion, target.s)]
    for realSection, values in wizardEdits.items():
        if not realSection:
            continue
        realSection = OBSEIniFile.ci_pseudosections.get(realSection,
                                                        realSection)
        try: # OBSE pseudo section
            modFormat = values[0] + _obse_mod_formats[realSection]
            delFormat = u';-' + values[0] + _obse_del_formats[realSection]
        except KeyError: # normal ini, assume pseudosections don't appear there
            lines.append(u'')
            lines.append(u'[%s]' % values[0])
            modFormat = u'%(setting)s=%(value)s%(comment)s'
            delFormat = u';-%(setting)s'
        for realSetting in values[1]:
            setting,value,comment,deleted = values[1][realSetting]
            fmt = delFormat if deleted else modFormat
            lines.append(fmt % (dict(setting=setting, value=value,
                                     comment=comment)))
    return lines

class PageFinish(PageInstaller):
    """Page displayed at the end of a wizard, showing which sub-packages and
    which plugins will be selected. Also displays some notes for the user."""

    def __init__(self, parent, subsList, plugin_list, plugin_renames, bAuto,
                 notes, iniedits):
        PageInstaller.__init__(self, parent)
        subs = sorted(subsList)
        plugins = sorted(plugin_list)
        #--make the list that will be displayed
        displayed_plugins = [x.replace(u'&', u'&&') + (
            u' -> ' + plugin_renames[x] if x in plugin_renames else u'')
                             for x in plugins]
        parent.parser.choiceIdex += 1
        textTitle = Label(self, _(u'The installer script has finished, and '
                                  u'will apply the following settings:'))
        textTitle.wrap(parent._native_widget.GetPageSize()[0] - 10)
        # Sub-packages
        self.listSubs = CheckListBox(
            self, choices=[x.replace(u'&', u'&&') for x in subs],
            onCheck=self._on_select_subs)
        for index,key in enumerate(subs):
            if subsList[key]:
                self.listSubs.lb_check_at_index(index, True)
                self._wiz_parent.ret.select_sub_packages.append(key)
        self.plugin_selection = CheckListBox(self, choices=displayed_plugins,
            onCheck=self._on_select_plugin)
        for index,key in enumerate(plugins):
            if plugin_list[key]:
                self.plugin_selection.lb_check_at_index(index, True)
                self._wiz_parent.ret.select_plugins.append(key)
        self._wiz_parent.ret.rename_plugins = plugin_renames
        # Ini tweaks
        self.listInis = ListBox(self, onSelect=self._on_select_ini,
                                choices=[x.s for x in iniedits.keys()])
        self.listTweaks = ListBox(self)
        self._wiz_parent.ret.ini_edits = iniedits
        # Apply/install checkboxes
        self.checkApply = CheckBox(self, _(u'Apply these selections'),
                                   checked=bAuto)
        self.checkApply.on_checked.subscribe(self._enableForward)
        auto = bass.settings['bash.installers.autoWizard']
        self.checkInstall = CheckBox(self, _(u'Install this package'),
                                     checked=auto)
        self.checkInstall.on_checked.subscribe(self.OnCheckInstall)
        self._wiz_parent.ret.should_install = auto
        # Layout
        layout = VLayout(item_expand=True, spacing=4, items=[
            HBoxedLayout(self, items=[textTitle]),
            (HLayout(item_expand=True, item_weight=1, spacing=5, items=[
                VLayout(item_expand=True,
                        items=[Label(self, _(u'Sub-Packages')),
                               (self.listSubs, LayoutOptions(weight=1))]),
                VLayout(item_expand=True,
                        items=[Label(self, _(u'Plugins')),
                               (self.plugin_selection,
                                LayoutOptions(weight=1))]),
             ]), LayoutOptions(weight=1)),
            Label(self, _(u'Ini Tweaks:')),
            (HLayout(item_expand=True, item_weight=1, spacing=5,
                     items=[self.listInis, self.listTweaks]),
             LayoutOptions(weight=1)),
            Label(self, _(u'Notes:')),
            (TextArea(self, init_text=u''.join(notes), auto_tooltip=False),
             LayoutOptions(weight=1)),
            HLayout(items=[
                Stretch(),
                VLayout(spacing=2, items=[self.checkApply, self.checkInstall])
            ])
        ])
        layout.apply_to(self)
        self._enableForward(bAuto)
        self._wiz_parent.finishing = True
        self.Layout()

    def OnCheckInstall(self, is_checked):
        self._wiz_parent.ret.should_install = is_checked

    def GetNext(self): return None

    # Undo selecting/deselection of items for UI consistency
    def _on_select_subs(self, lb_selection_dex):
        self.listSubs.toggle_checked_at_index(lb_selection_dex)

    def _on_select_plugin(self, lb_selection_dex):
        self.plugin_selection.toggle_checked_at_index(lb_selection_dex)

    def _on_select_ini(self, lb_selection_dex, lb_selection_str):
        ini_path = bolt.GPath(lb_selection_str)
        lines = generateTweakLines(self._wiz_parent.ret.ini_edits[ini_path],
                                   ini_path)
        self.listTweaks.lb_set_items(lines)
        self.listInis.lb_select_index(lb_selection_dex)

class PageVersions(PageInstaller):
    """Page for displaying what versions an installer requires/recommends and
    what you have installed for Game, *SE, *GE, and Wrye Bash."""
    def __init__(self, parent, bGameOk, gameHave, gameNeed, bSEOk, seHave,
                 seNeed, bGEOk, geHave, geNeed, bWBOk, wbHave, wbNeed):
        PageInstaller.__init__(self, parent)
        bmp = [Image(
            bass.dirs['images'].join(u'error_cross_24.png').s).GetBitmap(),
            Image(bass.dirs['images'].join(u'checkmark_24.png').s).GetBitmap()]
        versions_layout = GridLayout(h_spacing=5, v_spacing=5,
                                     stretch_cols=[0, 1, 2, 3])
        versions_layout.append_row([None, Label(self, _(u'Need')),
                                    Label(self, _(u'Have'))])
        # Game
        if bush.game.patchURL != u'':
            linkGame = HyperlinkLabel(self, bush.game.displayName,
                                      bush.game.patchURL,
                                      always_unvisited=True)
        else:
            linkGame = Label(self, bush.game.displayName)
        linkGame.tooltip = bush.game.patchTip
        versions_layout.append_row([linkGame, Label(self, gameNeed),
                                    Label(self, gameHave),
                                    balt.staticBitmap(self, bmp[bGameOk])])
        def _link_row(tool, tool_name, need, have, ok, title=None, url=None,
                      tooltip_=None):
            if tool is None or tool_name != u'':
                link = HyperlinkLabel(self, title or tool.long_name,
                                      url or tool.url, always_unvisited=True)
                link.tooltip = tooltip_ or tool.url_tip
                versions_layout.append_row([link, Label(self, need),
                                            Label(self, have),
                                            balt.staticBitmap(self, bmp[ok])])
        # Script Extender
        _link_row(bush.game.Se, bush.game.Se.se_abbrev, seNeed, seHave, bSEOk)
        # Graphics extender
        _link_row(bush.game.Ge, bush.game.Ge.ge_abbrev, geNeed, geHave, bGEOk)
        # Wrye Bash
        _link_row(None, u'', wbNeed, wbHave, bWBOk, title=u'Wrye Bash',
                  url=u'https://www.nexusmods.com/oblivion/mods/22368',
                  tooltip_=u'https://www.nexusmods.com/oblivion')
        versions_box = HBoxedLayout(self, _(u'Version Requirements'),
                                    item_expand=True, item_weight=1,
                                    items=[versions_layout])
        text_warning = Label(self, _(u'WARNING: The following version '
                                     u'requirements are not met for using '
                                     u'this installer.'))
        text_warning.wrap(parent._native_widget.GetPageSize()[0] - 20)
        self.checkOk = CheckBox(self, _(u'Install anyway.'))
        self.checkOk.on_checked.subscribe(self._enableForward)
        VLayout(items=[
            Stretch(1), (text_warning, LayoutOptions(h_align=CENTER)),
            Stretch(1), (versions_box, LayoutOptions(expand=True, weight=1)),
            Stretch(2),
            (self.checkOk, LayoutOptions(h_align=RIGHT, v_align=BOTTOM,
                                         border=5))
        ]).apply_to(self)
        self._enableForward(False)
        self.Layout()

class WryeParser(ScriptParser.Parser):
    """A derived class of Parser, for handling BAIN install wizards."""
    codeboxRemaps = {
        'Link': {
            # These are links that have different names than their text
            u'SelectOne':u'SelectOne1',
            u'SelectMany':u'SelectMany1',
            u'=':u'Assignment',
            u'+=':u'CompountAssignmentetc',
            u'-=':u'CompountAssignmentetc',
            u'*=':u'CompountAssignmentetc',
            u'/=':u'CompountAssignmentetc',
            u'^=':u'CompountAssignmentetc',
            u'+':u'Addition',
            u'-':u'Subtraction',
            u'*':u'Multiplication',
            u'/':u'Division',
            u'^':u'Exponentiation',
            u'and':u'Andampand',
            u'&':u'Andampand',
            u'or':u'Oror',
            u'|':u'Oror',
            u'not':u'Notnot',
            u'!':u'Notnot',
            u'in':u'Inin',
            u'in:':u'CaseInsensitiveInin',
            u'==':u'Equal',
            u'==:':u'CaseinsensitiveEqual',
            u'!=':u'NotEqual',
            u'!=:':u'CaseinsensitiveNotEqual',
            u'>=':u'GreaterThanorEqualgt',
            u'>=:':u'CaseInsensitiveGreaterThanorEqualgt',
            u'>':u'GreaterThangt',
            u'>:':u'CaseInsensitiveGreaterThangt',
            u'<=':u'LessThanorEquallt',
            u'<=:':u'CaseInsensitiveLessThanorEquallt',
            u'<':u'LessThanlt',
            u'<:':u'CaseInsensitiveLessThanlt',
            u'.':u'DotOperator',
            u'SubPackages':u'ForContinueBreakEndFor',
            },
        'Text': {
            # These are symbols that need to be replaced to be xhtml compliant
            u'&':u'&amp;',
            u'<':u'&lt;',
            u'<:':u'&lt;:',
            u'<=':u'&lt;=',
            u'<=:':u'&lt;=:',
            u'>':u'&gt;',
            u'>:':u'&gt;:',
            u'>=':u'&gt;=',
            u'>=:':u'&gt;=:',
            },
        'Color': {
            # These are items that we want colored differently
            u'in':u'blue',
            u'in:':u'blue',
            u'and':u'blue',
            u'or':u'blue',
            u'not':u'blue',
            },
        }

    @staticmethod
    def codebox(lines,pre=True,br=True):
        self = WryeParser(None, None, None, codebox=True) ##: drop this !
        def colorize(text_, color=u'black', link=True):
            href = text_
            text_ = WryeParser.codeboxRemaps['Text'].get(text_, text_)
            if color != u'black' or link:
                color = WryeParser.codeboxRemaps['Color'].get(text_, color)
                text_ = u'<span style="color:%s;">%s</span>' % (color, text_)
            if link:
                href = WryeParser.codeboxRemaps['Link'].get(href,href)
                text_ = u'<a href="#%s">%s</a>' % (href, text_)
            return text_
        self.cLine = 0
        outLines = []
        lastBlank = 0
        while self.cLine < len(lines):
            line = lines[self.cLine]
            self.cLine += 1
            self.tokens = []
            self.TokenizeLine(line)
            tokens = self.tokens
            line = line.strip(u'\r\n')
            lastEnd = 0
            dotCount = 0
            outLine = u''
            for i in tokens:
                start,stop = i.pos
                if start is not None and stop is not None:
                    # Not an inserted token from the parser
                    if i.type == ScriptParser.STRING:
                        start -= 1
                        stop  += 1
                    # Padding
                    padding = line[lastEnd:start]
                    outLine += padding
                    lastEnd = stop
                    # The token
                    token_txt = line[start:stop]
                    # Check for ellipses
                    if i.text == u'.':
                        dotCount += 1
                        if dotCount == 3:
                            dotCount = 0
                            outLine += u'...'
                        continue
                    else:
                        while dotCount > 0:
                            outLine += colorize(u'.')
                            dotCount -= 1
                    if i.type == ScriptParser.KEYWORD:
                        outLine += colorize(token_txt,u'blue')
                    elif i.type == ScriptParser.FUNCTION:
                        outLine += colorize(token_txt,u'purple')
                    elif i.type in (ScriptParser.INTEGER, ScriptParser.DECIMAL):
                        outLine += colorize(token_txt,u'cyan',False)
                    elif i.type == ScriptParser.STRING:
                        outLine += colorize(token_txt,u'brown',False)
                    elif i.type == ScriptParser.OPERATOR:
                        outLine += colorize(i.text)
                    elif i.type == ScriptParser.CONSTANT:
                        outLine += colorize(token_txt,u'cyan')
                    elif i.type == ScriptParser.NAME:
                        outLine += u'<i>%s</i>' % token_txt
                    else:
                        outLine += token_txt
            if self.runon:
                outLine += u' \\'
            if lastEnd < len(line):
                comments = line[lastEnd:]
                if u';' in comments:
                    outLine += colorize(comments,u'green',False)
            if outLine == u'':
                if len(outLines) != 0:
                    lastBlank = len(outLines)
                else:
                    continue
            else:
                lastBlank = 0
            if pre:
                outLine = u'<span class="code-n" style="display: inline;">%s</span>\n' % outLine
            else:
                if br:
                    outLine = u'<span class="code-n">%s</span><br />\n' % outLine
                else:
                    outLine = u'<span class="code-n">%s</span>' % outLine
            outLines.append(outLine)
        if lastBlank:
            outLines = outLines[:lastBlank]
        return outLines

    def __init__(self, wiz_parent, installer, bAuto, codebox=False):
        ScriptParser.Parser.__init__(self)
        if not codebox:
            self._wiz_parent = wiz_parent
            self.installer = installer
            self.bArchive = isinstance(installer, bosh.InstallerArchive)
            self._path = bolt.GPath(installer.archive) if installer else None
            if installer and installer.fileRootIdex:
                root_path = installer.extras_dict.get('root_path', u'')
                self._path = self._path.join(root_path)
            self.bAuto = bAuto
            self.page = None
            self.choices = []
            self.choiceIdex = -1
            # FIXME(inf) Yet more FOMOD hacks - the 'if s' part, specifically.
            #  After deactivating the fomod, we're still left with a subpackage
            #  with an empty string, so skip that. The other improvements (i.e.
            #  the dict comprehensions) can stay.
            self.sublist = bolt.LowerDict({
                s: False for s in installer.subNames if s})
            self.plugin_list = bolt.LowerDict({
                p: False for sub_plugins in installer.espmMap.itervalues()
                for p in sub_plugins})
        #--Constants
        self.SetConstant(u'SubPackages',u'SubPackages')
        #--Operators
        #Assignment
        self.SetOperator(u'=' , self.Ass, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'+=', self.AssAdd, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'-=', self.AssMin, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'*=', self.AssMul, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'/=', self.AssDiv, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'%=', self.AssMod, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        self.SetOperator(u'^=', self.AssExp, ScriptParser.OP.ASS, ScriptParser.RIGHT)
        #Comparison
        self.SetOperator(u'==', self.opE, ScriptParser.OP.CO2)
        self.SetOperator(u'!=', self.opNE, ScriptParser.OP.CO2)
        self.SetOperator(u'>=', self.opGE, ScriptParser.OP.CO1)
        self.SetOperator(u'>' , self.opG, ScriptParser.OP.CO1)
        self.SetOperator(u'<=', self.opLE, ScriptParser.OP.CO1)
        self.SetOperator(u'<' , self.opL, ScriptParser.OP.CO1)
        self.SetOperator(u'==:', self.opEc, ScriptParser.OP.CO2, passTokens=False)  # Case insensitive ==
        self.SetOperator(u'!=:', self.opNEc, ScriptParser.OP.CO2, passTokens=False) # Case insensitive !=
        self.SetOperator(u'>=:', self.opGEc, ScriptParser.OP.CO1, passTokens=False) # Case insensitive >=
        self.SetOperator(u'>:', self.opGc, ScriptParser.OP.CO1, passTokens=False)   # Case insensitive >
        self.SetOperator(u'<=:', self.opLEc, ScriptParser.OP.CO1, passTokens=False) # Case insensitive <=
        self.SetOperator(u'<:', self.opLc, ScriptParser.OP.CO1, passTokens=False)   # Case insensitive <
        #Membership operators
        self.SetOperator(u'in', self.opIn, ScriptParser.OP.MEM, passTokens=False)
        self.SetOperator(u'in:', self.opInCase, ScriptParser.OP.MEM, passTokens=False) # Case insensitive in
        #Boolean
        self.SetOperator(u'&' , self.opAnd, ScriptParser.OP.AND)
        self.SetOperator(u'and', self.opAnd, ScriptParser.OP.AND)
        self.SetOperator(u'|', self.opOr, ScriptParser.OP.OR)
        self.SetOperator(u'or', self.opOr, ScriptParser.OP.OR)
        self.SetOperator(u'!', self.opNot, ScriptParser.OP.NOT, ScriptParser.RIGHT)
        self.SetOperator(u'not', self.opNot, ScriptParser.OP.NOT, ScriptParser.RIGHT)
        #Pre-increment/decrement
        self.SetOperator(u'++', self.opInc, ScriptParser.OP.UNA)
        self.SetOperator(u'--', self.opDec, ScriptParser.OP.UNA)
        #Math
        self.SetOperator(u'+', self.opAdd, ScriptParser.OP.ADD)
        self.SetOperator(u'-', self.opMin, ScriptParser.OP.ADD)
        self.SetOperator(u'*', self.opMul, ScriptParser.OP.MUL)
        self.SetOperator(u'/', self.opDiv, ScriptParser.OP.MUL)
        self.SetOperator(u'%', self.opMod, ScriptParser.OP.MUL)
        self.SetOperator(u'^', self.opExp, ScriptParser.OP.EXP, ScriptParser.RIGHT)
        #--Functions
        self.SetFunction(u'CompareObVersion', self.fnCompareGameVersion, 1)      # Retained for compatibility
        self.SetFunction(u'CompareGameVersion', self.fnCompareGameVersion, 1)
        self.SetFunction(u'CompareOBSEVersion', self.fnCompareSEVersion, 1)      # Retained for compatibility
        self.SetFunction(u'CompareSEVersion', self.fnCompareSEVersion, 1)
        self.SetFunction(u'CompareOBGEVersion', self.fnCompareGEVersion, 1)      # Retained for compatibility
        self.SetFunction(u'CompareGEVersion', self.fnCompareGEVersion, 1)
        self.SetFunction(u'CompareWBVersion', self.fnCompareWBVersion, 1)
        self.SetFunction(u'DataFileExists', self.fnDataFileExists, 1, ScriptParser.KEY.NO_MAX)
        self.SetFunction(u'GetPluginLoadOrder', self.fn_get_plugin_lo, 1, 2)
        self.SetFunction(u'GetEspmStatus', self.fn_get_plugin_status, 1)         # Retained for compatibility
        self.SetFunction(u'GetPluginStatus', self.fn_get_plugin_status, 1)
        self.SetFunction(u'EditINI', self.fnEditINI, 4, 5)
        self.SetFunction(u'DisableINILine',self.fnDisableINILine, 3)
        self.SetFunction(u'Exec', self.fnExec, 1)
        self.SetFunction(u'EndExec', self.fnEndExec, 1)
        self.SetFunction(u'str', self.fnStr, 1)
        self.SetFunction(u'int', self.fnInt, 1)
        self.SetFunction(u'float', self.fnFloat, 1)
        #--String functions
        self.SetFunction(u'len', self.fnLen, 1, dotFunction=True)
        self.SetFunction(u'endswith', self.fnEndsWith, 2, ScriptParser.KEY.NO_MAX, dotFunction=True)
        self.SetFunction(u'startswith', self.fnStartsWith, 2, ScriptParser.KEY.NO_MAX, dotFunction=True)
        self.SetFunction(u'lower', self.fnLower, 1, dotFunction=True)
        self.SetFunction(u'find', self.fnFind, 2, 4, dotFunction=True)
        self.SetFunction(u'rfind', self.fnRFind, 2, 4, dotFunction=True)
        #--String pathname functions
        self.SetFunction(u'GetFilename', self.fnGetFilename, 1)
        self.SetFunction(u'GetFolder', self.fnGetFolder, 1)
        #--Keywords
        self.SetKeyword(u'SelectSubPackage', self.kwdSelectSubPackage, 1)
        self.SetKeyword(u'DeSelectSubPackage', self.kwdDeSelectSubPackage, 1)
        # The keyowrds with 'espm' in their name are retained for backwards
        # compatibility only - use their 'plugin' equivalents instead
        self.SetKeyword(u'SelectEspm', self.kwd_select_plugin, 1)
        self.SetKeyword(u'SelectPlugin', self.kwd_select_plugin, 1)
        self.SetKeyword(u'DeSelectEspm', self.kwd_de_select_plugin, 1)
        self.SetKeyword(u'DeSelectPlugin', self.kwd_de_select_plugin, 1)
        self.SetKeyword(u'SelectAll', self.kwdSelectAll)
        self.SetKeyword(u'DeSelectAll', self.kwdDeSelectAll)
        self.SetKeyword(u'SelectAllEspms', self.kwd_select_all_plugins)
        self.SetKeyword(u'SelectAllPlugins', self.kwd_select_all_plugins)
        self.SetKeyword(u'DeSelectAllEspms', self.kwd_de_select_all_plugins)
        self.SetKeyword(u'DeSelectAllPlugins', self.kwd_de_select_all_plugins)
        self.SetKeyword(u'RenameEspm', self.kwd_rename_plugin, 2)
        self.SetKeyword(u'RenamePlugin', self.kwd_rename_plugin, 2)
        self.SetKeyword(u'ResetEspmName', self.kwd_reset_plugin_name, 1)
        self.SetKeyword(u'ResetPluginName', self.kwd_reset_plugin_name, 1)
        self.SetKeyword(u'ResetAllEspmNames', self.kwd_reset_all_plugin_names)
        self.SetKeyword(u'ResetAllPluginNames',self.kwd_reset_all_plugin_names)
        self.SetKeyword(u'Note', self.kwdNote, 1)
        self.SetKeyword(u'If', self.kwdIf, 1 )
        self.SetKeyword(u'Elif', self.kwdElif, 1)
        self.SetKeyword(u'Else', self.kwdElse)
        self.SetKeyword(u'EndIf', self.kwdEndIf)
        self.SetKeyword(u'While', self.kwdWhile, 1)
        self.SetKeyword(u'Continue', self.kwdContinue)
        self.SetKeyword(u'EndWhile', self.kwdEndWhile)
        self.SetKeyword(u'For', self.kwdFor, 3, ScriptParser.KEY.NO_MAX, passTokens=True, splitCommas=False)
        self.SetKeyword(u'from', self.kwdDummy)
        self.SetKeyword(u'to', self.kwdDummy)
        self.SetKeyword(u'by', self.kwdDummy)
        self.SetKeyword(u'EndFor', self.kwdEndFor)
        self.SetKeyword(u'SelectOne', self.kwdSelectOne, 7, ScriptParser.KEY.NO_MAX)
        self.SetKeyword(u'SelectMany', self.kwdSelectMany, 4, ScriptParser.KEY.NO_MAX)
        self.SetKeyword(u'Case', self.kwdCase, 1)
        self.SetKeyword(u'Default', self.kwdDefault)
        self.SetKeyword(u'Break', self.kwdBreak)
        self.SetKeyword(u'EndSelect', self.kwdEndSelect)
        self.SetKeyword(u'Return', self.kwdReturn)
        self.SetKeyword(u'Cancel', self.kwdCancel, 0, 1)
        self.SetKeyword(u'RequireVersions', self.kwdRequireVersions, 1, 4)

    @property
    def path(self): return self._path

    def Begin(self, file_path):
        self.variables.clear()
        self.Flow = []
        self.notes = []
        self.plugin_renames = {}
        self.iniedits = {}
        self.cLine = 0
        self.reversing = 0
        self.ExecCount = 0
        if file_path.exists() and file_path.isfile():
            try:
                with file_path.open(encoding='utf-8-sig') as script:
                    # Ensure \n line endings for the script parser
                    self.lines = [x.replace(u'\r\n',u'\n') for x in script.readlines()]
                return self.Continue()
            except UnicodeError:
                balt.showWarning(self._wiz_parent, _(u'Could not read the wizard file.  Please ensure it is encoded in UTF-8 format.'))
                return
        balt.showWarning(self._wiz_parent, _(u'Could not open wizard file'))
        return None

    def Continue(self):
        self.page = None
        while self.cLine < len(self.lines):
            newline = self.lines[self.cLine]
            try:
                self.RunLine(newline)
            except ScriptParser.ParserError as e:
                bolt.deprint(u'Error in wizard script', traceback=True)
                return PageError(self._wiz_parent, _(u'Installer Wizard'),
                                 _(u'An error occurred in the wizard script:') + '\n'
                                 + _(u'Line %s:\t%s') % (self.cLine, newline.strip(u'\n')) + '\n'
                                 + _(u'Error:\t%s') % e)
            except Exception:
                bolt.deprint(u'Error while running wizard', traceback=True)
                msg = u'\n'.join([_(u'An unhandled error occurred while '
                    u'parsing the wizard:'), _(u'Line %s:\t%s') % (self.cLine,
                    newline.strip(u'\n')), u'', traceback.format_exc()])
                return PageError(self._wiz_parent, _(u'Installer Wizard'), msg)
            if self.page:
                return self.page
        self.cLine += 1
        self.cLineStart = self.cLine
        return PageFinish(self._wiz_parent, self.sublist, self.plugin_list,
                          self.plugin_renames, self.bAuto, self.notes,
                          self.iniedits)

    def Back(self):
        if self.choiceIdex == 0:
            return
        # Rebegin
        self.variables.clear()
        self.Flow = []
        self.notes = []
        self.plugin_renames = {}
        self.iniedits = {}
        i = 0
        while self.ExecCount > 0 and i < len(self.lines):
            line = self.lines[i]
            i += 1
            if line.startswith(u'EndExec('):
                numLines = int(line[8:-1])
                del self.lines[i-numLines:i]
                i -= numLines
                self.ExecCount -= 1
        for i in self.sublist:
            self.sublist[i] = False
        for i in self.plugin_list:
            self.plugin_list[i] = False
        self.cLine = 0
        self.reversing = self.choiceIdex-1
        self.choiceIdex = -1
        return self.Continue()

    def _is_plugin_in_package(self, plugin_name, package):
        if package not in self.installer.espmMap: return False
        plugin_name = plugin_name.lower()
        v = self.installer.espmMap[package]
        for j in v:
            if plugin_name == j.lower():
                return True
        return False

    def _plugin_in_active_package(self, plugin_name):
        for i in self.sublist:
            if self._is_plugin_in_package(plugin_name, i):
                if self.sublist[i]:
                    return True
        return False

    def _resolve_plugin_rename(self, plugin_name):
        plugin_name = plugin_name.lower()
        for i in self.plugin_list:
            if plugin_name == i.lower():
                return i
        return None

    # Assignment operators
    def Ass(self, l, r):
        if l.type not in [ScriptParser.VARIABLE,ScriptParser.NAME]:
            error(_(u'Cannot assign a value to %s, type is %s.') % (l.text, ScriptParser.Types[l.type]))
        self.variables[l.text] = r.tkn
        return r.tkn

    def AssAdd(self, l, r): return self.Ass(l, l+r)
    def AssMin(self, l, r): return self.Ass(l, l-r)
    def AssMul(self, l, r): return self.Ass(l, l*r)
    def AssDiv(self, l, r): return self.Ass(l, l/r)
    def AssMod(self, l, r): return self.Ass(l, l%r)
    def AssExp(self, l, r): return self.Ass(l, l**r)

    # Comparison operators
    def opE(self, l, r): return l == r

    def opEc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() == r.lower()
        else:
            return l == r

    def opNE(self, l, r): return l != r

    def opNEc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() != r.lower()
        else:
            return l != r

    def opGE(self, l, r): return l >= r

    def opGEc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() >= r.lower()
        else:
            return l >= r

    def opG(self, l, r): return l > r

    def opGc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() > r.lower()
        else:
            return l > r

    def opLE(self, l, r): return l <= r

    def opLEc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() <= r.lower()
        else:
            return l <= r

    def opL(self, l, r): return l < r

    def opLc(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() < r.lower()
        else:
            return l < r

    # Membership tests
    def opIn(self, l, r): return l in r

    def opInCase(self, l, r):
        if isinstance(l, basestring) and isinstance(r, basestring):
            return l.lower() in r.lower()
        else:
            return l in r

    # Boolean operators
    def opAnd(self, l, r): return l and r
    def opOr(self, l, r): return l or r
    def opNot(self, l): return not l

    # Pre-increment/decrement
    def opInc(self, l):
        if l.type not in [ScriptParser.VARIABLE,ScriptParser.NAME]:
            error(_(u'Cannot increment %s, type is %s.') % (l.text, ScriptParser.Types[l.type]))
        new_val = l.tkn + 1
        self.variables[l.text] = new_val
        return new_val
    def opDec(self, l):
        if l.type not in [ScriptParser.VARIABLE,ScriptParser.NAME]:
            error(_(u'Cannot decrement %s, type is %s.') % (l.text, ScriptParser.Types[l.type]))
        new_val = l.tkn - 1
        self.variables[l.text] = new_val
        return new_val

    # Math operators
    def opAdd(self, l, r): return l + r
    def opMin(self, l, r): return l - r
    def opMul(self, l, r): return l * r
    def opDiv(self, l, r): return l / r
    def opMod(self, l, r): return l % r
    def opExp(self, l, r): return l ** r

    # Functions...
    def fnCompareGameVersion(self, obWant):
        ret = self._TestVersion(
            self._TestVersion_Want(obWant),
            bass.dirs['app'].join(*bush.game.version_detect_file))
        return ret[0]

    def fnCompareSEVersion(self, seWant):
        if bush.game.Se.se_abbrev != u'':
            ver_path = None
            for ver_file in bush.game.Se.ver_files:
                ver_path = bass.dirs['app'].join(ver_file)
                if ver_path.exists(): break
            return self._TestVersion(self._TestVersion_Want(seWant), ver_path)
        else:
            # No script extender available for this game
            return 1

    def fnCompareGEVersion(self, geWant):
        if bush.game.Ge.ge_abbrev != u'':
            ret = self._TestVersion_GE(self._TestVersion_Want(geWant))
            return ret[0]
        else:
            # No graphics extender available for this game
            return 1

    def fnCompareWBVersion(self, wbWant):
        wbHave = bass.AppVersion
        return bolt.cmp_(float(wbHave), float(wbWant))

    def fnDataFileExists(self, *filenames):
        for filename in filenames:
            if not bass.dirs['mods'].join(filename).exists():
                # Check for ghosted mods
                if bolt.GPath(filename) in bosh.modInfos:
                    return True # It's a ghosted mod
                return False
        return True

    def fn_get_plugin_lo(self, filename, default_val=-1):
        try:
            return load_order.cached_lo_index(bolt.GPath(filename))
        except KeyError: # has no LO
            return default_val

    def fn_get_plugin_status(self, filename):
        p_name = bolt.GPath(filename)
        if p_name in bosh.modInfos.merged: return 3   # Merged
        if load_order.cached_is_active(p_name): return 2  # Active
        if p_name in bosh.modInfos.imported: return 1 # Imported (not active/merged)
        if p_name in bosh.modInfos: return 0          # Inactive
        return -1                                   # Not found

    def fnEditINI(self, ini_name, section, setting, value, comment=u''):
        self._handleINIEdit(ini_name, section, setting, value, comment, False)

    def fnDisableINILine(self, ini_name, section, setting):
        self._handleINIEdit(ini_name, section, setting, u'', u'', True)

    def _handleINIEdit(self, ini_name, section, setting, value, comment,
                       disable):
        """
        Common implementation for the EditINI and DisableINILine wizard
        functions.

        :param ini_name: The name of the INI file to edit. If it's not one of
            the game's default INIs (e.g. Skyrim.ini), it's treated as relative
            to the Data folder.
        :param section: The section of the INI file to edit.
        :param setting: The name of the setting to edit.
        :param value: The value to assign. If disabling a line, this is
            ignored.
        :param comment: The comment to place with the edit. Pass an empty
            string if no comment should be placed.
        :param disable: Whether or not this edit should disable the setting in
            question.
        """
        ini_path = bolt.GPath(ini_name)
        section = section.strip()
        setting = setting.strip()
        comment = comment.strip()
        real_section = OBSEIniFile.ci_pseudosections.get(section, section)
        if comment and not comment.startswith(u';'):
            comment = u';' + comment
        self.iniedits.setdefault(ini_path, bolt.LowerDict()).setdefault(
            real_section, [section, bolt.LowerDict()])
        self.iniedits[ini_path][real_section][0] = section
        self.iniedits[ini_path][real_section][1][setting] = (setting, value,
                                                             comment, disable)

    def fnExec(self, strLines):
        lines = strLines.split(u'\n')
        # Manual EndExec calls are illegal - if we don't check here, a wizard
        # could exploit this by doing something like this:
        #   Exec("EndExec(1)\nAnythingHere\nReturn")
        # ... which doesn't really cause harm, but is pretty strange and
        # inconsistent
        if any([l.strip().startswith(u'EndExec(') for l in lines]):
            error(UNEXPECTED % u'EndExec')
        lines.append(u'EndExec(%i)' % (len(lines)+1))
        self.lines[self.cLine:self.cLine] = lines
        self.ExecCount += 1

    def fnEndExec(self, numLines):
        if self.ExecCount == 0:
            error(UNEXPECTED % u'EndExec')
        del self.lines[self.cLine-numLines:self.cLine]
        self.cLine -= numLines
        self.ExecCount -= 1

    def fnStr(self, data): return unicode(data)

    def fnInt(self, data):
        try:
            return int(data)
        except ValueError:
            return 0

    def fnFloat(self, data):
        try:
            return float(data)
        except ValueError:
            return 0.0

    def fnLen(self, data):
        try:
            return len(data)
        except TypeError:
            return 0

    def fnEndsWith(self, String, *args):
        if not isinstance(String, basestring):
            error(_(u"Function 'endswith' only operates on string types."))
        return String.endswith(args)

    def fnStartsWith(self, String, *args):
        if not isinstance(String, basestring):
            error(_(u"Function 'startswith' only operates on string types."))
        return String.startswith(args)

    def fnLower(self, String):
        if not isinstance(String, basestring):
            error(_(u"Function 'lower' only operates on string types."))
        return String.lower()

    def fnFind(self, String, sub, start=0, end=-1):
        if not isinstance(String, basestring):
            error(_(u"Function 'find' only operates on string types."))
        if end < 0: end += len(String) + 1
        return String.find(sub, start, end)

    def fnRFind(self, String, sub, start=0, end=-1):
        if not isinstance(String, basestring):
            error(_(u"Function 'rfind' only operates on string types."))
        if end < 0: end += len(String) + 1
        return String.rfind(sub, start, end)

    def fnGetFilename(self, String): return os.path.basename(String)
    def fnGetFolder(self, String): return os.path.dirname(String)

    # Dummy keyword, for reserving a keyword, but handled by other keywords
    # (like from, to, and by)
    def kwdDummy(self): pass

    # Keywords, mostly for flow control (If, Select, etc)
    def kwdIf(self, bActive):
        if self.LenFlow() > 0 and self.PeekFlow().type == u'If' and not self.PeekFlow().active:
            #Inactive portion of an If-Elif-Else-EndIf statement, but we hit an If, so we need
            #To not count the next 'EndIf' towards THIS one
            self.PushFlow(u'If', False, [u'If', u'EndIf'])
            return
        self.PushFlow(u'If', bActive, [u'If', u'Else', u'Elif', u'EndIf'], ifTrue=bActive, hitElse=False)

    def kwdElif(self, bActive):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'If' or self.PeekFlow().hitElse:
            error(UNEXPECTED % u'Elif')
        if self.PeekFlow().ifTrue:
            self.PeekFlow().active = False
        else:
            self.PeekFlow().active = bActive
            self.PeekFlow().ifTrue = self.PeekFlow().active or self.PeekFlow().ifTrue

    def kwdElse(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'If' or self.PeekFlow().hitElse:
            error(UNEXPECTED % u'Else')
        if self.PeekFlow().ifTrue:
            self.PeekFlow().active = False
            self.PeekFlow().hitElse = True
        else:
            self.PeekFlow().active = True
            self.PeekFlow().hitElse = True

    def kwdEndIf(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'If':
            error(UNEXPECTED % u'EndIf')
        self.PopFlow()

    def kwdWhile(self, bActive):
        if self.LenFlow() > 0 and self.PeekFlow().type == u'While' and not self.PeekFlow().active:
            # Within an un-true while statement, but we hit a new While, so we
            # need to ignore the next 'EndWhile' towards THIS one
            self.PushFlow(u'While', False, [u'While', u'EndWhile'])
            return
        self.PushFlow(u'While', bActive, [u'While', u'EndWhile'],
                      cLine=self.cLine - 1)

    def kwdContinue(self):
        #Find the next up While or For statement to continue from
        index = self.LenFlow()-1
        iType = None
        while index >= 0:
            iType = self.PeekFlow(index).type
            if iType in [u'While',u'For']:
                break
            index -= 1
        if index < 0:
            # No while statement was found
            error(UNEXPECTED % u'Continue')
        #Discard any flow control statments that happened after
        #the While/For, since we're resetting either back to the
        #the While/For', or the EndWhile/EndFor
        while self.LenFlow() > index+1:
            self.PopFlow()
        flow = self.PeekFlow()
        if iType == u'While':
            # Continue a While loop
            self.cLine = flow.cLine
            self.PopFlow()
        else:
            # Continue a For loop
            if flow.ForType == 0:
                # Numeric loop
                if self.variables[flow.varname] == flow.end:
                    # For loop is done
                    self.PeekFlow().active = False
                else:
                    # keep going
                    self.cLine = flow.cLine
                self.variables[flow.varname] += flow.by
            elif flow.ForType == 1:
                # Iterator type
                flow.index += 1
                if flow.index == len(flow.List):
                    # Loop is done
                    self.PeekFlow().active = False
                else:
                    # Re-loop
                    self.cLine = flow.cLine
                    self.variables[flow.varname] = flow.List[flow.index]

    def kwdEndWhile(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'While':
            error(UNEXPECTED % u'EndWhile')
        #Re-evaluate the while loop's expression, if needed
        flow = self.PopFlow()
        if flow.active:
            self.cLine = flow.cLine

    def kwdFor(self, *args):
        if self.LenFlow() > 0 and self.PeekFlow().type == u'For' and not self.PeekFlow().active:
            #Within an ending For statement, but we hit a new For, so we need to ignore the
            #next 'EndFor' towards THIS one
            self.PushFlow(u'For', False, [u'For', u'EndFor'])
            return
        varname = args[0]
        if varname.type not in [ScriptParser.VARIABLE,ScriptParser.NAME]:
            error(_(u"Invalid syntax for 'For' statement.  Expected format:")
                    +u'\n For var_name from value_start to value_end [by value_increment]\n For var_name in SubPackages\n For var_name in subpackage_name'
                  )
        if args[1].text == 'from':
            #For varname from value_start to value_end [by value_increment]
            if (len(args) not in [5,7]) or (args[3].text != u'to') or (len(args)==7 and args[5].text != u'by'):
                error(_(u"Invalid syntax for 'For' statement.  Expected format:")
                      +u'\n For var_name from value_start to value_end\n For var_name from value_start to value_end by value_increment'
                      )
            start = self.ExecuteTokens([args[2]])
            end = self.ExecuteTokens([args[4]])
            if len(args) == 7:
                by = self.ExecuteTokens([args[6]])
            elif start > end:
                by = -1
            else:
                by = 1
            self.variables[varname.text] = start
            self.PushFlow(u'For', True, [u'For', u'EndFor'], ForType=0, cLine=self.cLine, varname=varname.text, end=end, by=by)
        elif args[1].text == u'in':
            # For name in SubPackages / For name in SubPackage
            if args[2].text == u'SubPackages':
                if len(args) > 4:
                    error(_(u"Invalid syntax for 'For' statement.  Expected format:")
                          +u'\n For var_name in Subpackages\n For var_name in subpackage_name'
                          )
                List = sorted(self.sublist.keys())
            else:
                name = self.ExecuteTokens(args[2:])
                subpackage = name if name in self.sublist else None
                if subpackage is None:
                    error(_(u"SubPackage '%s' does not exist.") % name)
                List = []
                if isinstance(self.installer,bosh.InstallerProject):
                    sub = bass.dirs['installers'].join(self.path, subpackage)
                    for root_dir, dirs, files in sub.walk():
                        for file_ in files:
                            rel = root_dir.join(file_).relpath(sub)
                            List.append(rel.s)
                else:
                    # Archive
                    for file_, _size, _crc in self.installer.fileSizeCrcs:
                        rel = bolt.GPath(file_).relpath(subpackage)
                        if not rel.s.startswith(u'..'):
                            List.append(rel.s)
                List.sort()
            if len(List) == 0:
                self.variables[varname.text] = u''
                self.PushFlow(u'For', False, [u'For',u'EndFor'])
            else:
                self.variables[varname.text] = List[0]
                self.PushFlow(u'For', True, [u'For',u'EndFor'], ForType=1, cLine=self.cLine, varname=varname.text, List=List, index=0)
        else:
            error(_(u"Invalid syntax for 'For' statement.  Expected format:")
                  +u'\n For var_name from value_start to value_end [by value_increment]\n For var_name in SubPackages\n For var_name in subpackage_name'
                  )

    def kwdEndFor(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'For':
            error(UNEXPECTED % u'EndFor')
        #Increment the variable, then test to see if we should end or keep going
        flow = self.PeekFlow()
        if flow.active:
            if flow.ForType == 0:
                # Numerical loop
                if self.variables[flow.varname] == flow.end:
                    #For loop is done
                    self.PopFlow()
                else:
                    #Need to keep going
                    self.cLine = flow.cLine
                    self.variables[flow.varname] += flow.by
            elif flow.ForType == 1:
                # Iterator type
                flow.index += 1
                if flow.index == len(flow.List):
                    self.PopFlow()
                else:
                    self.cLine = flow.cLine
                    self.variables[flow.varname] = flow.List[flow.index]
        else:
            self.PopFlow()

    def kwdSelectOne(self, *args):
        self._KeywordSelect(False, u'SelectOne', *args)

    def kwdSelectMany(self, *args):
        self._KeywordSelect(True, u'SelectMany', *args)

    def _KeywordSelect(self, bMany, name, *args):
        args = list(args)
        if self.LenFlow() > 0 and self.PeekFlow().type == u'Select' and not self.PeekFlow().active:
            #We're inside an invalid Case for a Select already, so just add a blank FlowControl for
            #this select
            self.PushFlow(u'Select', False, [u'SelectOne', u'SelectMany', u'EndSelect'])
            return
        # Escape ampersands, since they're treated as escape characters by wx
        main_desc = args.pop(0).replace(u'&', u'&&')
        if len(args) % 3:
            error(MISSING_ARGS % name)
        images = []
        titles = OrderedDict()
        descs = []
        image_paths = []
        while len(args):
            title = args.pop(0)
            is_default = title[0] == u'|'
            if is_default:
                title = title[1:]
            titles[title] = is_default
            descs.append(args.pop(0))
            images.append(args.pop(0))
        if self.bAuto:
            # auto wizard will resolve SelectOne/SelectMany only if default(s)
            # were specified.
            defaults = [t for t, default in titles.items() if default]
            if not bMany: defaults = defaults[:1]
            if defaults:
                self.PushFlow(u'Select', False,
                              [u'SelectOne', u'SelectMany', u'Case',
                               u'Default', u'EndSelect'], values=defaults,
                              hitCase=False)
                return
        self.choiceIdex += 1
        if self.reversing:
            # We're using the 'Back' button
            self.reversing -= 1
            self.PushFlow(u'Select', False, [u'SelectOne', u'SelectMany', u'Case', u'Default', u'EndSelect'], values = self.choices[self.choiceIdex], hitCase=False)
            return
        # If not an auto-wizard, or an auto-wizard with no default option
        if self.bArchive:
            imageJoin = bass.getTempDir().join
        else:
            imageJoin = bass.dirs['installers'].join(self.path).join
        for i in images:
            path = imageJoin(i)
            if not path.exists() and bass.dirs['mopy'].join(i).exists():
                path = bass.dirs['mopy'].join(i)
            image_paths.append(path)
        self.page = PageSelect(self._wiz_parent, bMany, _(u'Installer Wizard'),
                               main_desc, titles.keys(), descs, image_paths,
                               titles.values())

    def kwdCase(self, value):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'Select':
            error(UNEXPECTED % u'Case')
        if value in self.PeekFlow().values or unicode(value) in self.PeekFlow().values:
            self.PeekFlow().hitCase = True
            self.PeekFlow().active = True

    def kwdDefault(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'Select':
            error(UNEXPECTED % u'Default')
        if self.PeekFlow().hitCase:
            return
        self.PeekFlow().active = True
        self.PeekFlow().hitCase = True

    def kwdBreak(self):
        if self.LenFlow() > 0 and self.PeekFlow().type == u'Select':
            # Break for SelectOne/SelectMany
            self.PeekFlow().active = False
        else:
            # Test for a While/For statement earlier
            index = self.LenFlow() - 1
            while index >= 0:
                if self.PeekFlow(index).type in (u'While', u'For'):
                    break
                index -= 1
            if index < 0:
                # No while or for statements found
                error(UNEXPECTED % u'Break')
            self.PeekFlow(index).active = False

            # We're going to jump to the EndWhile/EndFor, so discard
            # any flow control structs on top of the While/For one
            while self.LenFlow() > index + 1:
                self.PopFlow()
            self.PeekFlow().active = False

    def kwdEndSelect(self):
        if self.LenFlow() == 0 or self.PeekFlow().type != u'Select':
            error(UNEXPECTED % u'EndSelect')
        self.PopFlow()

    # Package selection functions
    def kwdSelectSubPackage(self, subpackage):
        self._SelectSubPackage(True, subpackage)

    def kwdDeSelectSubPackage(self, subpackage):
        self._SelectSubPackage(False, subpackage)

    def _SelectSubPackage(self, bSelect, subpackage):
        package = subpackage if subpackage in self.sublist else None
        if package:
            self.sublist[package] = bSelect
            for i in self.installer.espmMap[package]:
                if bSelect:
                    self._select_plugin(True, i)
                else:
                    if not self._plugin_in_active_package(i):
                        self._select_plugin(False, i)
        else:
            error(_(u"Sub-package '%s' is not a part of the installer.") % subpackage)

    def kwdSelectAll(self): self._SelectAll(True)
    def kwdDeSelectAll(self): self._SelectAll(False)

    def _SelectAll(self, bSelect):
        for i in self.sublist.keys():
            self.sublist[i] = bSelect
        for i in self.plugin_list.keys():
            self.plugin_list[i] = bSelect

    def kwd_select_plugin(self, plugin_name):
        self._select_plugin(True, plugin_name)

    def kwd_de_select_plugin(self, plugin_name):
        self._select_plugin(False, plugin_name)

    def _select_plugin(self, should_activate, plugin_name):
        resolved_name = self._resolve_plugin_rename(plugin_name)
        if resolved_name:
            self.plugin_list[resolved_name] = should_activate
        else:
            error(_(u"Plugin '%s' is not a part of the installer.") %
                  plugin_name)

    def kwd_select_all_plugins(self): self._select_all_plugins(True)
    def kwd_de_select_all_plugins(self): self._select_all_plugins(False)

    def _select_all_plugins(self, should_activate):
        for i in self.plugin_list.keys():
            self.plugin_list[i] = should_activate

    def kwd_rename_plugin(self, plugin_name, new_name):
        plugin_name = self._resolve_plugin_rename(plugin_name)
        if plugin_name:
            # Keep same extension
            if plugin_name.lower()[-4:] != new_name.lower()[-4:]:
                raise ScriptParser.ParserError(_(u'Cannot rename %s to %s: '
                                                 u'the extensions must '
                                                 u'match.') %
                                               (plugin_name, new_name))
            self.plugin_renames[plugin_name] = new_name

    def kwd_reset_plugin_name(self, plugin_name):
        plugin_name = self._resolve_plugin_rename(plugin_name)
        if plugin_name and plugin_name in self.plugin_renames:
            del self.plugin_renames[plugin_name]

    def kwd_reset_all_plugin_names(self):
        self.plugin_renames = dict()

    def kwdNote(self, note):
        self.notes.append(u'- %s\n' % note)

    def kwdRequireVersions(self, game, se=u'None', ge=u'None', wbWant=u'0.0'):
        if self.bAuto: return
        gameWant = self._TestVersion_Want(game)
        if gameWant == u'None': game = u'None'
        seWant = self._TestVersion_Want(se)
        if seWant == u'None': se = u'None'
        geWant = self._TestVersion_Want(ge)
        if geWant == u'None': ge = u'None'
        if not wbWant: wbWant = u'0.0'
        wbHave = bass.AppVersion
        ret = self._TestVersion(
            gameWant, bass.dirs['app'].join(*bush.game.version_detect_file))
        bGameOk = ret[0] >= 0
        gameHave = ret[1]
        if bush.game.Se.se_abbrev != u'':
            ver_path = None
            for ver_file in bush.game.Se.ver_files:
                ver_path = bass.dirs['app'].join(ver_file)
                if ver_path.exists(): break
            ret = self._TestVersion(seWant, ver_path)
            bSEOk = ret[0] >= 0
            seHave = ret[1]
        else:
            bSEOk = True
            seHave = u'None'
        if bush.game.Ge.ge_abbrev != u'':
            ret = self._TestVersion_GE(geWant)
            bGEOk = ret[0] >= 0
            geHave = ret[1]
        else:
            bGEOk = True
            geHave = u'None'
        try:
            bWBOk = float(wbHave) >= float(wbWant)
        except ValueError:
            # Error converting to float, just assume it's OK
            bWBOk = True
        if not bGameOk or not bSEOk or not bGEOk or not bWBOk:
            self.page = PageVersions(self._wiz_parent, bGameOk, gameHave, game,
                                     bSEOk, seHave, se, bGEOk, geHave, ge,
                                     bWBOk, wbHave, wbWant)

    def _TestVersion_GE(self, want):
        if isinstance(bush.game.Ge.exe, str):
            files = [bass.dirs['mods'].join(bush.game.Ge.exe)]
        else:
            files = [bass.dirs['mods'].join(*x) for x in bush.game.Ge.exe]
        ret = [-1, u'None']
        for file in reversed(files):
            ret = self._TestVersion(want, file)
            if ret[1] != u'None':
                return ret
        return ret

    def _TestVersion_Want(self, want):
        try:
            need = [int(i) for i in want.split(u'.')]
        except ValueError:
            need = u'None'
        return need

    def _TestVersion(self, need, file_):
        if file_ and file_.exists():
            have = get_file_version(file_.s)
            ver = u'.'.join([unicode(i) for i in have])
            if need == u'None':
                return [1, ver]
            for have_part, need_part in zip(have, need):
                if have_part > need_part:
                    return [1, ver]
                elif have_part < need_part:
                    return [-1, ver]
            return [0, ver]
        elif need == u'None':
            return [0, u'None']
        return [-1, u'None']

    def kwdReturn(self):
        self.page = PageFinish(self._wiz_parent, self.sublist, self.plugin_list,
                               self.plugin_renames, self.bAuto, self.notes,
                               self.iniedits)

    def kwdCancel(self, msg=_(u"No reason given")):
        self.page = PageError(self._wiz_parent, _(u'The installer wizard was canceled:'), msg)

bolt.codebox = WryeParser.codebox
