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
"""Top level windows in wx is Frame and Dialog. I added some more like Panels
and the wx.wiz stuff."""
__author__ = u'Utumno, Infernio'

import wx as _wx
import wx.adv as _adv     # wxPython wizard class

from .base_components import _AComponent, Color, WithFirstShow, csf

# Special constant defining a window as having whatever position the underlying
# GUI implementation picks for it by default.
DEFAULT_POSITION = (-1, -1)

class _TopLevelWin(_AComponent):
    """Methods mixin for top level windows

    Events:
     - _on_close_evt(): request to close the window."""
    _def_pos = _wx.DefaultPosition
    _def_size = _wx.DefaultSize
    _min_size = _size_key = _pos_key = None

    def __init__(self, parent, sizes_dict, icon_bundle, *args, **kwargs):
        # dict holding size/pos info ##: can be bass.settings or balt.sizes
        self._sizes_dict = sizes_dict
        super(_TopLevelWin, self).__init__(parent, *args, **kwargs)
        self._set_pos_size(kwargs, sizes_dict)
        self._on_close_evt = self._evt_handler(_wx.EVT_CLOSE)
        self._on_close_evt.subscribe(self.on_closing)
        if icon_bundle: self.set_icons(icon_bundle)
        if self._min_size: self.set_min_size(*self._min_size)

    def _set_pos_size(self, kwargs, sizes_dict):
        wanted_pos = kwargs.get('pos', None) or sizes_dict.get(
            self._pos_key, self._def_pos)
        # Resolve the special DEFAULT_POSITION constant to a real value
        self.component_position = (
            self._def_pos if wanted_pos == DEFAULT_POSITION else wanted_pos)
        self.component_size = kwargs.get('size', None) or sizes_dict.get(
            self._size_key, self._def_size)

    @property
    def is_maximized(self):
        """Returns True if this window has been maximized."""
        return self._native_widget.IsMaximized()

    @is_maximized.setter
    def is_maximized(self, new_maximized):
        """Maximizes or restores this window."""
        self._native_widget.Maximize(new_maximized)

    @property
    def is_iconized(self):
        """IsIconized(self) -> bool"""
        return self._native_widget.IsIconized()

    # TODO(inf) de-wx! Image API - these use wx.Icon and wx.IconBundle
    def set_icon(self, wx_icon):
        """SetIcon(self, Icon icon)"""
        return self._native_widget.SetIcon(wx_icon)

    def set_icons(self, wx_icon_bundle):
        """SetIcons(self, wxIconBundle icons)"""
        return self._native_widget.SetIcons(wx_icon_bundle)

    def close_win(self, force_close=False):
        """This function simply generates a EVT_CLOSE event whose handler usually
        tries to close the window. It doesn't close the window itself,
        however.  If force is False (the default) then the window's close
        handler will be allowed to veto the destruction of the window."""
        self._native_widget.Close(force_close)

    def on_closing(self, destroy=True):
        """Invoked right before this window is destroyed."""
        if self._sizes_dict and not self.is_iconized and not self.is_maximized:
            if self._pos_key: self._sizes_dict[self._pos_key] = self.component_position
            if self._size_key: self._sizes_dict[self._size_key] = self.component_size
        if destroy: self.destroy_component()

    def ensureDisplayed(self, x=100, y=100): ##: revisit uses
        """Ensure that frame is displayed."""
        if _wx.Display.GetFromWindow(self._native_widget) == -1:
            topLeft = _wx.Display(0).GetGeometry().GetTopLeft()
            self._native_widget.MoveXY(topLeft.x + x, topLeft.y + y)

class WindowFrame(_TopLevelWin):
    """Wraps a wx.Frame - saves size/position on closing.

    Events:
     - on_activate(): Posted when the frame is activated.
     """
    _frame_settings_key = None
    _min_size = _def_size = (250, 250)
    _wx_widget_type = _wx.Frame

    def __init__(self, parent, title, icon_bundle=None, _base_key=None,
                 sizes_dict={}, caption=False, style=_wx.DEFAULT_FRAME_STYLE,
                 **kwargs):
        _key = _base_key or self.__class__._frame_settings_key
        if _key:
            self._pos_key = _key + u'.pos'
            self._size_key = _key + u'.size'
        if caption: style |= _wx.CAPTION
        if sizes_dict: style |= _wx.RESIZE_BORDER
        if kwargs.pop(u'clip_children', False): style |= _wx.CLIP_CHILDREN
        if kwargs.pop(u'tab_traversal', False): style |= _wx.TAB_TRAVERSAL
        super(WindowFrame, self).__init__(parent, sizes_dict, icon_bundle,
                                          title=title, style=style, **kwargs)
        self.on_activate = self._evt_handler(_wx.EVT_ACTIVATE,
                                             lambda event: [event.GetActive()])
        self.set_background_color(self._bkg_color())

    def show_frame(self): self._native_widget.Show()

    def raise_frame(self): self._native_widget.Raise()

    # TODO(inf) de-wx! Menu should become a wrapped component as well
    def show_popup_menu(self, menu):
        self._native_widget.PopupMenu(menu)

    def _bkg_color(self):
        """Returns the background color to use for this window."""
        return Color.from_wx(_wx.SystemSettings.GetColour(_wx.SYS_COLOUR_MENU))

class DialogWindow(_TopLevelWin):
    """Wrap a dialog control."""
    title = u'OVERRIDE'
    _wx_widget_type = _wx.Dialog

    def __init__(self, parent=None, title=None, icon_bundle=None,
                 sizes_dict=None, caption=False, size_key=None, pos_key=None,
                 style=0, **kwargs):
        self._size_key = size_key or self.__class__.__name__
        self._pos_key = pos_key
        self.title = title or self.__class__.title
        style |= _wx.DEFAULT_DIALOG_STYLE
        if sizes_dict is not None: style |= _wx.RESIZE_BORDER
        else: sizes_dict = {}
        if caption: style |= _wx.CAPTION
        super(DialogWindow, self).__init__(parent, sizes_dict, icon_bundle,
                                           title=self.title, style=style,
                                           **kwargs)
        self._on_size_changed = self._evt_handler(_wx.EVT_SIZE)
        self._on_size_changed.subscribe(self.save_size) # save dialog size

    def save_size(self):
        if self._sizes_dict is not None and self._size_key:
            self._sizes_dict[self._size_key] = self.component_size

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.destroy_component()

    @classmethod
    def display_dialog(cls, *args, **kwargs):
        """Instantiate a dialog, display it and return the ShowModal result."""
        with cls(*args, **kwargs) as dialog:
            return dialog.show_modal()

    def show_modal(self):
        """Begins a new modal dialog and returns a boolean indicating if the
        exit code was fine.

        :return: True if the dialog was closed with a good exit code (e.g. by
            clicking an 'OK' or 'Yes' button), False otherwise."""
        return self.show_modal_raw() in (_wx.ID_OK, _wx.ID_YES)

    # TODO(inf) Investigate uses, they all seem to have weird, fragile logic
    def show_modal_raw(self):
        """Begins a new modal dialog and returns the raw exit code."""
        return self._native_widget.ShowModal()

    def accept_modal(self):
        """Closes the modal dialog with a 'normal' exit code. Equivalent to
        clicking the OK button."""
        self.exit_modal(_wx.ID_OK)

    def cancel_modal(self):
        """Closes the modal dialog with an 'abnormal' exit code. Equivalent to
        clicking the Cancel button."""
        self.exit_modal(_wx.ID_CANCEL)

    # TODO(inf) Investigate uses, see show_modal_raw above
    def exit_modal(self, custom_code):
        """Closes the modal dialog with a custom exit code."""
        self._native_widget.EndModal(custom_code)

class StartupDialog(DialogWindow):
    """Dialog shown during early boot, generally due to errors."""
    def __init__(self, *args, **kwargs):
        sd_style = _wx.STAY_ON_TOP | _wx.DIALOG_NO_PARENT
        super(StartupDialog, self).__init__(*args, style=sd_style, **kwargs)

class WizardDialog(DialogWindow, WithFirstShow):
    """Wrap a wx wizard control.

    Events:
     - on_wiz_page_change(is_forward: bool, evt_page: PageInstaller):
     Posted when the user clicks next or previous page. `is_forward` is True
     for next page. PageInstaller needs to have OnNext() - see uses in belt
     - _on_wiz_cancel(): Used internally to save size and position
     - _on_wiz_finished(): Used internally to save size and position
     - _on_show(): used internally to set page size on first showing the wizard
     """
    _wx_widget_type = _adv.Wizard

    def __init__(self, parent, **kwargs):
        kwargs['style'] = _wx.MAXIMIZE_BOX
        super(WizardDialog, self).__init__(parent, **kwargs)
        self.on_wiz_page_change = self._evt_handler(
            _adv.EVT_WIZARD_PAGE_CHANGING,
            lambda event: [event.GetDirection(), event.GetPage()])
        # needed to correctly save size/pos, on_closing seems not enough
        self._on_wiz_cancel = self._evt_handler(_adv.EVT_WIZARD_CANCEL)
        self._on_wiz_cancel.subscribe(self.save_size)
        self._on_wiz_finished = self._evt_handler(_adv.EVT_WIZARD_FINISHED)
        self._on_wiz_finished.subscribe(self.save_size)

    def _handle_first_show(self):
        # we have to set initial size here, see WizardDialog._set_pos_size
        saved_size = self._sizes_dict[self._size_key]
        # enforce min size
        self.component_size = (max(saved_size[0], self._def_size[0]),
                               max(saved_size[1], self._def_size[1]))

    def _set_pos_size(self, kwargs, sizes_dict):
        # default keys for wizard should exist and return settingDefaults
        # values. Moreover _wiz.Wizard does not accept a size argument (!)
        # so this override is needed
        ##: note wx python expects kwargs as strings - PY3: check
        wanted_pos = kwargs.get('pos', None) or sizes_dict[self._pos_key]
        # Resolve the special DEFAULT_POSITION constant to a real value
        kwargs['pos'] = (self._def_pos if wanted_pos == DEFAULT_POSITION
                         else wanted_pos)

    def enable_forward_btn(self, do_enable):
        self._native_widget.FindWindowById(_wx.ID_FORWARD).Enable(do_enable)

    def get_page_size(self):
        """Returns the width and height that each page in the installer will
        have available, in device-independent pixels (DIP)."""
        p_size = self._native_widget.ToDIP(self._native_widget.GetPageSize())
        return p_size.width, p_size.height

# Panels ----------------------------------------------------------------------
class PanelWin(_AComponent):
    _wx_widget_type = _wx.Panel

    def __init__(self, parent, no_border=True):
        super(PanelWin, self).__init__(
            parent, style=_wx.TAB_TRAVERSAL | (no_border and _wx.NO_BORDER))

class Splitter(_AComponent):
    _wx_widget_type = _wx.SplitterWindow

    def __init__(self, parent, allow_split=True, min_pane_size=0,
                 sash_gravity=0):
        super(Splitter, self).__init__(parent, style=_wx.SP_LIVE_UPDATE)
        if not allow_split: # Don't allow unsplitting
            self._native_widget.Bind(_wx.EVT_SPLITTER_DCLICK,
                                     lambda event: event.Veto())
        if min_pane_size:
            self.set_min_pane_size(min_pane_size)
        if sash_gravity:
            self.set_sash_gravity(sash_gravity)
        self._panes = None

    def make_panes(self, sash_position=0, first_pane=None, second_pane=None,
                   vertically=False):
        self._panes = [first_pane or PanelWin(self),
                       second_pane or PanelWin(self)]
        split = self._native_widget.SplitVertically if vertically else \
            self._native_widget.SplitHorizontally
        split(self._panes[0]._native_widget, self._panes[1]._native_widget,
              sash_position)
        return self._panes[0], self._panes[1]

    def get_sash_pos(self): return self._native_widget.GetSashPosition()

    def set_sash_pos(self, sash_position):
        self._native_widget.SetSashPosition(sash_position)

    def set_min_pane_size(self, min_pane_size):
        self._native_widget.SetMinimumPaneSize(min_pane_size * csf())

    def set_sash_gravity(self, sash_gravity):
        self._native_widget.SetSashGravity(sash_gravity)

class _APageComponent(_AComponent):
    """Abstract base class for 'page' compoenents, i.e. notebooks and
    listbooks."""
    def add_page(self, page_component, page_title):
        self._native_widget.AddPage(self._resolve(page_component), page_title)

    def get_selected_page_index(self):
        return self._native_widget.GetSelection()

    def set_selected_page_index(self, page_index):
        self._native_widget.SetSelection(page_index)

class TabbedPanel(_APageComponent):
    """A panel with tabs, each of which contains a different panel."""
    _wx_widget_type = _wx.Notebook

    def __init__(self, parent, multiline=False):
        super(TabbedPanel, self).__init__(
            parent, style=_wx.NB_MULTILINE if multiline else 0)
        self.on_nb_page_change = self._evt_handler(
            _wx.EVT_NOTEBOOK_PAGE_CHANGED,
            lambda event: [event.GetId(), event.GetSelection()])

class ListPanel(_APageComponent):
    """A panel with a list of options that each correspond to a different
    panel."""
    _wx_widget_type =  _wx.Listbook

    def __init__(self, parent):
        super(ListPanel, self).__init__(parent)
        left_list = self._native_widget.GetChildren()[0]
        left_list.SetSingleStyle(_wx.LC_LIST | _wx.LC_ALIGN_LEFT)

class ScrollableWindow(_AComponent):
    """A window with a scrollbar."""
    _wx_widget_type = _wx.ScrolledWindow

    def __init__(self, parent, scroll_horizontal=True, scroll_vertical=True):
        super(ScrollableWindow, self).__init__(parent)
        scroll_h = (20 if scroll_horizontal else 0) * csf()
        scroll_v = (20 if scroll_vertical else 0) * csf()
        units_h = (50 if scroll_horizontal else 0) * csf()
        units_v = (50 if scroll_vertical else 0) * csf()
        self._native_widget.SetScrollbars(scroll_h, scroll_v, units_h, units_v)

class CenteredSplash(_AComponent):
    """A centered splash screen without a timeout. Only disappears when either
    the entire application terminates or stop_splash is called."""
    _wx_widget_type = _adv.SplashScreen

    def __init__(self, splash_path):
        """Creates a new CenteredSplash with an image read from the specified
        path."""
        splash_bitmap = _wx.Image(splash_path).ConvertToBitmap()
        # Center image on the screen and image will stay until clicked by
        # user or is explicitly destroyed when the main window is ready
        splash_style = _adv.SPLASH_CENTER_ON_SCREEN | _adv.SPLASH_NO_TIMEOUT
        # Can't use _AComponent.__init__ here, because for some ungodly reason
        # parent is the *third* parameter in SplashScreen
        self._native_widget = self._wx_widget_type(splash_bitmap, splash_style,
                                                   1, None) # Timeout - ignored
        self._on_close_evt = self._evt_handler(_wx.EVT_CLOSE)
        self._on_close_evt.subscribe(self.stop_splash)
        _wx.Yield()

    def stop_splash(self):
        """Hides and terminates the splash screen."""
        self.destroy_component()
        ##: Apparently won't be hidden if warnTooManyModsBsas warns(?)
        self.visible = False
