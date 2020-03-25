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

__author__ = u'Ganda'

from collections import defaultdict
import wx
import wx.adv as wiz

from .. import balt, bass, bolt, bosh, bush, env
from ..gui import CENTER, CheckBox, HBoxedLayout, HLayout, Label, \
    LayoutOptions, TextArea, VLayout, WizardDialog, EventResult, \
    PictureWithCursor, RadioButton
from ..fomod import FailedCondition, FomodInstaller

class FomodInstallInfo(object):
    __slots__ = (u'canceled', u'install_files', u'should_install')

    def __init__(self):
        # canceled: true if the user canceled or if an error occurred
        self.canceled = False
        # install_files: file->dest mapping of files to install
        self.install_files = bolt.LowerDict()
        # should_install: boolean on whether to install the files
        self.should_install = True

class InstallerFomod(WizardDialog):
    _def_size = (600, 500)

    def __init__(self, parent_window, installer):
        # True prevents actually moving to the 'next' page.
        # We use this after the "Next" button is pressed,
        # while the parser is running to return the _actual_ next page
        self.block_change = True
        # 'finishing' is to allow the "Next" button to be used
        # when its name is changed to 'Finish' on the last page of the wizard
        self.finishing = False
        # saving this list allows for faster processing of the files the fomod
        # installer will return.
        self.files_list = [a[0] for a in installer.fileSizeCrcs]
        fomod_file = installer.fomod_file().s
        data_path = bass.dirs[u'mods']
        ver = env.get_file_version(bass.dirs[u'app'].join(
            *bush.game.version_detect_file).s)
        self.parser = FomodInstaller(fomod_file, self.files_list, data_path,
                                     u'.'.join([unicode(i) for i in ver]))
        super(InstallerFomod, self).__init__(
            parent_window, sizes_dict=bass.settings,
            title=_(u'FOMOD Installer - %s') % self.parser.fomod_name,
            size_key=u'bash.fomod.size', pos_key=u'bash.fomod.pos')
        self.is_archive = isinstance(installer, bosh.InstallerArchive)
        if self.is_archive:
            self.archive_path = bass.getTempDir()
        else:
            self.archive_path = bass.dirs[u'installers'].join(
                installer.archive)
        # 'dummy' page tricks the wizard into always showing the "Next" button
        class _PageDummy(wiz.WizardPage): pass
        self.dummy = _PageDummy(self._native_widget)
        # Intercept the changing event so we can implement 'block_change'
        self.on_wiz_page_change.subscribe(self.on_change)
        self.ret = FomodInstallInfo()
        self.first_page = True

    def save_size(self):
        # Otherwise, regular resize, save the size if we're not maximized
        self.on_closing(destroy=False)

    def on_change(self, is_forward, evt_page):
        if is_forward:
            if not self.finishing:
                # Next, continue script execution
                if self.block_change:
                    # Tell the current page that next was pressed,
                    # So the parser can continue parsing,
                    # Then show the page that the parser returns,
                    # rather than the dummy page
                    selection = evt_page.on_next()
                    self.block_change = False
                    next_page = self.parser.next_(selection)
                    if next_page is None:
                        self.finishing = True
                        self._native_widget.ShowPage(
                            PageFinish(self))
                    else:
                        self.finishing = False
                        self._native_widget.ShowPage(
                            PageSelect(self, next_page))
                    return EventResult.CANCEL
                else:
                    self.block_change = True
        else:
            # Previous, pop back to the last state,
            # and resume execution
            self.block_change = False
            self.finishing = False
            payload = self.parser.previous()
            if payload:  # at the start
                page, previous_selection = payload
                gui_page = PageSelect(self, page)
                gui_page.select(previous_selection)
                self._native_widget.ShowPage(gui_page)
            return EventResult.CANCEL

    def run(self):
        try:
            first_page = self.parser.start()
        except FailedCondition as exc:
            msg = _(u'This installer cannot start due to the following unmet '
                    u'conditions:\n')
            for line in str(exc).splitlines():
                msg += u'  {}\n'.format(line)
            balt.showWarning(self, msg, title=_(u'Cannot Run Installer'),
                             do_center=True)
            self.ret.canceled = True
        else:
            if first_page is not None:  # if installer has any gui pages
                self.ret.canceled = not self._native_widget.RunWizard(
                    PageSelect(self, first_page))
            self.ret.install_files = bolt.LowerDict(self.parser.files())
        # Clean up temp files
        if self.is_archive:
            bass.rmTempDir()
        return self.ret

class PageInstaller(wiz.WizardPage):
    """Base class for all the parser wizard pages, just to handle a couple
    simple things here."""

    def __init__(self, parent):
        super(PageInstaller, self).__init__(parent._native_widget)
        self._page_parent = parent
        self._enableForward(True)

    def _enableForward(self, do_enable):
        self._page_parent.enable_forward_btn(do_enable)

    def GetNext(self):
        return self._page_parent.dummy

    def GetPrev(self):
        if self._page_parent.parser.has_previous():
            return self._page_parent.dummy
        return None

    def on_next(self):
        """Create flow control objects etc, implemented by sub-classes."""
        pass

class PageError(PageInstaller):
    """Page that shows an error message, has only a "Cancel" button enabled,
    and cancels any changes made."""

    def __init__(self, parent, title, error_msg):
        super(PageError, self).__init__(parent)
        # Disable the "Finish"/"Next" button
        self._enableForward(False)
        VLayout(spacing=5, items=[
            Label(parent, title),
            (TextArea(self, init_text=error_msg, editable=False,
                auto_tooltip=False), LayoutOptions(expand=True, weight=1)),
        ]).apply_to(self)
        # TODO(inf) Are all these Layout() calls needed? belt does them, so I
        #  assume that's why they're here, but belt isn't a good GUI example :P
        #  If yes, then: de-wx!
        self.Layout()

    def GetNext(self):
        return None

    def GetPrev(self):
        return None

class PageSelect(PageInstaller):
    """A Page that shows a message up top, with a selection box on the left
    (multi- or single- selection), with an optional associated image and
    description for each option, shown when that item is selected."""

    _option_type_string = defaultdict(str)
    _option_type_string[u'Required'] = _(u'=== This option is required '
                                         u'===\n\n')
    _option_type_string[u'Recommended'] = _(u'=== This option is recommended '
                                            u'===\n\n')
    _option_type_string[u'CouldBeUsable'] = _(u'=== This option could result '
                                              u'in instability ===\n\n')
    _option_type_string[u'NotUsable'] = _(u'=== This option cannot be '
                                          u'selected ===\n\n')

    def __init__(self, parent, page):
        super(PageSelect, self).__init__(parent)
        self.group_option_map = defaultdict(list)
        self.bmp_item = PictureWithCursor(self, 0, 0, background=None)
        self._img_cache = {} # creating images can be really expensive
        self.text_item = TextArea(self, editable=False, auto_tooltip=False)
        # TODO(inf) de-wx!
        panel_groups = wx.ScrolledWindow(self)
        panel_groups.SetScrollbars(20, 20, 50, 50)
        groups_layout = VLayout(spacing=5, item_expand=True)
        for group in page:
            options_layout = VLayout(spacing=2)
            first_selectable = None
            any_selected = False
            # whenever there is a required option in a exactlyone/atmostone
            # group all other options need to be disabled to ensure the
            # required stays selected
            required_disable = False
            # group type forces selection
            group_type = group.type
            group_force_selection = group_type in (u'SelectExactlyOne',
                                                   u'SelectAtLeastOne')
            for option in group:
                if group_type in (u'SelectExactlyOne', u'SelectAtMostOne'):
                    button = RadioButton(panel_groups, label=option.name,
                                         is_group=option is group[0])
                else:
                    button = CheckBox(panel_groups, label=option.name)
                    if group_type == u'SelectAll':
                        button.is_checked = True
                        any_selected = True
                        button.enabled = False
                if option.type == u'Required':
                    button.is_checked =  True
                    any_selected = True
                    if group_type in (u'SelectExactlyOne', u'SelectAtMostOne'):
                        required_disable = True
                    else:
                        button.enabled = False
                elif option.type == u'Recommended':
                    if not any_selected or not group_force_selection:
                        button.is_checked = True
                        any_selected = True
                elif option.type in (u'Optional', u'CouldBeUsable'):
                    if first_selectable is None:
                        first_selectable = button
                elif option.type == u'NotUsable':
                    button.is_checked = False
                    button.enabled = False
                # TODO(inf) This is very hacky, there has to a better way than
                #  abusing __dict__ for this
                LinkOptionObject_(button, option)
                options_layout.add(button)
                button._native_widget.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
                self.group_option_map[group].append(button)
            if not any_selected and group_force_selection:
                if first_selectable is not None:
                    first_selectable.is_checked = True
                    any_selected = True
            if required_disable:
                for button in self.group_option_map[group]:
                    button.enabled = False
            if group_type == u'SelectAtMostOne':
                none_button = wx.RadioButton(panel_groups, label=_(u'None'))
                if not any_selected:
                    none_button.SetValue(True)
                elif required_disable:
                    none_button.Disable()
                options_layout.add(none_button)
            groups_layout.add(HBoxedLayout(
                panel_groups, title=group.name, item_expand=True,
                item_weight=1, items=[options_layout]))
        groups_layout.apply_to(panel_groups)
        VLayout(spacing=10, item_expand=True, items=[
            (HLayout(spacing=5, item_expand=True, item_weight=1, items=[
                HBoxedLayout(self, title=page.name, item_expand=True,
                             item_weight=1, items=[panel_groups]),
                VLayout(spacing=5, item_expand=True, item_weight=1,
                        items=[self.bmp_item, self.text_item]),
            ]), LayoutOptions(weight=1)),
        ]).apply_to(self)
        self.Layout()

    # fixme XXX: hover doesn't work on disabled buttons
    # fixme XXX: types other than optional should be shown in some visual way (button colour?)
    def on_hover(self, event):
        button = event.GetEventObject()
        option = button.option_object
        self._enableForward(True)
        img = self._page_parent.archive_path.join(option.image)
        try:
            image = self._img_cache[img]
        except KeyError:
            image = img
        self._img_cache[img] = self.bmp_item.set_bitmap(image)
        self.text_item.text_content = (self._option_type_string[option.type]
                                       + option.description)

    def on_error(self, msg):
        msg += _(u'\nPlease ensure the FOMOD files are correct and contact '
                 u'the Wrye Bash Dev Team.')
        balt.showWarning(self, msg, do_center=True)

    def on_next(self):
        selection = []
        for group, option_buttons in self.group_option_map.iteritems():
            group_selected = [a.option_object for a in option_buttons
                              if a.is_checked]
            option_len = len(group_selected)
            if group.type == u'SelectExactlyOne' and option_len != 1:
                msg = _(u'Group "{}" should have exactly 1 option selected '
                        u'but has {}.').format(group.name, option_len)
                self.on_error(msg)
            elif group.type == u'SelectAtMostOne' and option_len > 1:
                msg = _(u'Group "{}" should have at most 1 option selected '
                        u'but has {}.').format(group.name, option_len)
                self.on_error(msg)
            elif group.type == u'SelectAtLeast' and option_len < 1:
                msg = _(u'Group "{}" should have at least 1 option selected '
                        u'but has {}.').format(group.name, option_len)
                self.on_error(msg)
            elif (group.type == u'SelectAll'
                  and option_len != len(option_buttons)):
                msg = _(u'Group "{}" should have all options selected but has '
                        u'only {}.').format(group.name, option_len)
                self.on_error(msg)
            selection.extend(group_selected)
        return selection

    def select(self, selection):
        for button_list in self.group_option_map.itervalues():
            for button in button_list:
                if button.option_object in selection:
                    button.is_checked = True

class PageFinish(PageInstaller):
    def __init__(self, parent):
        super(PageFinish, self).__init__(parent)
        # TODO(inf) de-wx! Font API? If we do this, revert the display_files
        #  change below
        #label_title.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        #text_item.SetFont(wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL, 0, ""))
        check_install = CheckBox(self, _(u'Install this package'),
                                 checked=self._page_parent.ret.should_install)
        check_install.on_checked.subscribe(self.on_check)
        installer_output = self.display_files(self._page_parent.parser.files())
        VLayout(spacing=10, item_expand=True, items=[
            (Label(self, _(u'Files To Install')),
             LayoutOptions(expand=False, h_align=CENTER)),
            (TextArea(self, editable=False, auto_tooltip=False,
                      init_text=installer_output), LayoutOptions(weight=1)),
            check_install,
        ]).apply_to(self)
        self.Layout()

    def on_check(self, is_checked):
        self._page_parent.ret.should_install = is_checked

    def GetNext(self):
        return None

    @staticmethod
    def display_files(file_dict):
        if not file_dict: return u''
        lines = [u'{} -> {}'.format(v, k) for k, v in file_dict.iteritems()]
        lines.sort(key=unicode.lower)
        return u'\n'.join(lines)

# FIXME(inf) Hacks until wx.RadioButton is wrapped, ugly names are on purpose
def LinkOptionObject_(component, target_option):
    component.option_object = target_option
    if not isinstance(component, RadioButton):
        component._native_widget.option_object = target_option
