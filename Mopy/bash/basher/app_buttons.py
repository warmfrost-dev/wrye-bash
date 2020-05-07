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
from __future__ import division, print_function
import subprocess
import webbrowser
from . import BashStatusBar, BashFrame
from .frames import ModChecker, DocBrowser
from .. import bass, bosh, bolt, balt, bush, mod_files, load_order
from ..balt import ItemLink, Link, Links, SeparatorLink, BoolLink, staticBitmap
from ..bolt import GPath
from ..env import getJava
from ..exception import AbstractError
from ..gui import ClickableImage, EventResult

__all__ = [u'Obse_Button', u'LAA_Button', u'AutoQuit_Button', u'Game_Button',
           u'TESCS_Button', u'App_Tes4View', u'App_BOSS',
           u'App_DocBrowser', u'App_ModChecker', u'App_Settings', u'App_Help',
           u'App_Restart', u'App_GenPickle', u'app_button_factory']

#------------------------------------------------------------------------------
# StatusBar Links--------------------------------------------------------------
#------------------------------------------------------------------------------
class _StatusBar_Hide(ItemLink):
    """The (single) link on the button's menu - hides the button."""
    def _initData(self, window, selection):
        super(_StatusBar_Hide, self)._initData(window, selection)
        tip_ = window.tooltip
        self._text = _(u"Hide '%s'") % tip_
        self._help = _(u"Hides %(buttonname)s's status bar button (can be"
            u" restored through the settings menu).") % ({'buttonname': tip_})

    def Execute(self): Link.Frame.statusBar.HideButton(self.window)

class StatusBar_Button(ItemLink):
    """Launch an application."""
    _tip = u''
    @property
    def sb_button_tip(self): return self._tip

    def __init__(self, uid=None, canHide=True, button_tip=u''):
        """ui: Unique identifier, used for saving the order of status bar icons
               and whether they are hidden/shown.
           canHide: True if this button is allowed to be hidden."""
        super(StatusBar_Button, self).__init__()
        self.mainMenu = Links()
        self.canHide = canHide
        self.gButton = None
        self._tip = button_tip or self.__class__._tip
        if uid is None: uid = (self.__class__.__name__, self._tip)
        self.uid = uid

    def IsPresent(self):
        """Due to the way status bar buttons are implemented debugging is a
        pain - I provided this base class method to early filter out non
        existent buttons."""
        return True

    def GetBitmapButton(self, window, image=None, onRClick=None):
        """Create and return gui button - you must define imageKey - WIP overrides"""
        btn_image = image or balt.images[self.imageKey %
                        bass.settings['bash.statusbar.iconSize']].GetBitmap()
        if self.gButton is not None:
            self.gButton.destroy_component()
        self.gButton = ClickableImage(window, btn_image,
                                      btn_tooltip=self.sb_button_tip)
        self.gButton.on_clicked.subscribe(self.Execute)
        self.gButton.on_right_clicked.subscribe(onRClick or self.DoPopupMenu)
        return self.gButton

    def DoPopupMenu(self):
        if self.canHide:
            if len(self.mainMenu) == 0 or not isinstance(self.mainMenu[-1],
                                                         _StatusBar_Hide):
                if len(self.mainMenu) > 0:
                    self.mainMenu.append(SeparatorLink())
                self.mainMenu.append(_StatusBar_Hide())
        if len(self.mainMenu) > 0:
            self.mainMenu.new_menu(self.gButton, 0)
            return EventResult.FINISH ##: Kept it as such, test if needed

    # Helper function to get OBSE version
    @property
    def obseVersion(self):
        if not bass.settings['bash.statusbar.showversion']: return u''
        for ver_file in bush.game.Se.ver_files:
            ver_path = bass.dirs[u'app'].join(ver_file)
            if ver_path.exists():
                return u' ' + u'.'.join([u'%s' % x for x
                                         in ver_path.strippedVersion])
        else:
            return u''

    def set_sb_button_tooltip(self): pass

#------------------------------------------------------------------------------
# App Links -------------------------------------------------------------------
#------------------------------------------------------------------------------
class _App_Button(StatusBar_Button):
    """Launch an application."""
    obseButtons = []

    @property
    def version(self):
        if not bass.settings['bash.statusbar.showversion']: return u''
        if self.IsPresent():
            version = self.exePath.strippedVersion
            if version != (0,):
                version = u'.'.join([u'%s'%x for x in version])
                return version
        return u''

    def set_sb_button_tooltip(self):
        if self.gButton: self.gButton.tooltip = self.sb_button_tip

    @property
    def sb_button_tip(self):
        if not bass.settings['bash.statusbar.showversion']: return self._tip
        else:
            return self._tip + u' ' + self.version

    @property
    def obseTip(self):
        if self._obseTip is None: return None
        return self._obseTip % (dict(version=self.version))

    def __init__(self, exePath, exeArgs, images, tip, obseTip=None, uid=None,
                 canHide=True):
        """images: [16x16,24x24,32x32] images"""
        super(_App_Button, self).__init__(uid, canHide, tip)
        self.exeArgs = exeArgs
        self.exePath = exePath
        self.images = images
        #--**SE stuff
        self._obseTip = obseTip
        # used by _App_Button.Execute(): be sure to set them _before_ calling it
        self.extraArgs = ()
        self.wait = False

    def IsPresent(self):
        return self.exePath not in bosh.undefinedPaths and \
               self.exePath.exists()

    def GetBitmapButton(self, window, image=None, onRClick=None):
        if not self.IsPresent(): return None
        size = bass.settings['bash.statusbar.iconSize'] # 16, 24, 32
        idex = (size // 8) - 2 # 0, 1, 2, duh
        super(_App_Button, self).GetBitmapButton(
            window, self.images[idex].GetBitmap(), onRClick)
        if self.obseTip is not None:
            _App_Button.obseButtons.append(self)
            if BashStatusBar.obseButton.button_state:
                self.gButton.tooltip = self.obseTip
        return self.gButton

    def ShowError(self,error):
        balt.showError(Link.Frame,
                       (u'%s'%error + u'\n\n' +
                        _(u'Used Path: ') + self.exePath.s + u'\n' +
                        _(u'Used Arguments: ') + u'%s' % (self.exeArgs,)),
                       _(u"Could not launch '%s'") % self.exePath.stail)

    def _showUnicodeError(self):
        balt.showError(Link.Frame, _(
            u'Execution failed, because one or more of the command line '
            u'arguments failed to encode.'),
                       _(u"Could not launch '%s'") % self.exePath.stail)

    def Execute(self):
        if not self.IsPresent():
            balt.showError(Link.Frame,
                           _(u'Application missing: %s') % self.exePath.s,
                           _(u"Could not launch '%s'" % self.exePath.stail)
                           )
            return
        self._app_button_execute()

    def _app_button_execute(self):
        dir_ = bolt.Path.getcwd().s
        args = u'"%s"' % self.exePath.s
        args += u' '.join([u'%s' % arg for arg in self.exeArgs])
        try:
            import win32api
            r, executable = win32api.FindExecutable(self.exePath.s)
            executable = win32api.GetLongPathName(executable)
            win32api.ShellExecute(0,u"open",executable,args,dir_,1)
        except Exception as error:
            if isinstance(error,WindowsError) and error.winerror == 740:
                # Requires elevated permissions
                try:
                    import win32api
                    win32api.ShellExecute(0,'runas',executable,args,dir_,1)
                except Exception as error:
                    self.ShowError(error)
            else:
                # Most likely we're here because FindExecutable failed (no file association)
                # Or because win32api import failed.  Try doing it using os.startfile
                # ...Changed to webbrowser.open because os.startfile is windows specific and is not cross platform compatible
                cwd = bolt.Path.getcwd()
                self.exePath.head.setcwd()
                try:
                    webbrowser.open(self.exePath.s)
                except UnicodeError:
                    self._showUnicodeError()
                except Exception as error:
                    self.ShowError(error)
                finally:
                    cwd.setcwd()

class _ExeButton(_App_Button):

    def _app_button_execute(self):
        self._run_exe(self.exePath, [self.exePath.s])

    def _run_exe(self, exe_path, exe_args):
        exe_args.extend(self.exeArgs)
        if self.extraArgs: exe_args.extend(self.extraArgs)
        Link.Frame.set_status_info(u' '.join(exe_args[1:]))
        cwd = bolt.Path.getcwd()
        exe_path.head.setcwd()
        try:
            popen = subprocess.Popen(exe_args, close_fds=True)
            if self.wait:
                popen.wait()
        except UnicodeError:
            self._showUnicodeError()
        except WindowsError as werr:
            if werr.winerror != 740:
                self.ShowError(werr)
            try:
                import win32api
                win32api.ShellExecute(0, 'runas', exe_path.s,
                    u'%s' % self.exeArgs, bass.dirs[u'app'].s, 1)
            except:
                self.ShowError(werr)
        except Exception as error:
            self.ShowError(error)
        finally:
            cwd.setcwd()

class _JavaButton(_App_Button):
    """_App_Button pointing to a .jar file."""

    @property
    def version(self): return u''

    def __init__(self, exePath, exeArgs, *args, **kwargs):
        super(_JavaButton, self).__init__(exePath, exeArgs, *args, **kwargs)
        self.java = getJava()
        self.appArgs = u''.join(self.exeArgs)

    def IsPresent(self):
        return self.java.exists() and self.exePath.exists()

    def _app_button_execute(self):
        cwd = bolt.Path.getcwd()
        self.exePath.head.setcwd()
        try:
            subprocess.Popen(
                (self.java.stail, u'-jar', self.exePath.stail, self.appArgs),
                executable=self.java.s, close_fds=True)
        except UnicodeError:
            self._showUnicodeError()
        except Exception as error:
            self.ShowError(error)
        finally:
            cwd.setcwd()

class _LnkOrDirButton(_App_Button):

    def _app_button_execute(self): webbrowser.open(self.exePath.s)

def _parse_button_arguments(exePathArgs):
    """Expected formats:
        exePathArgs (string): exePath
        exePathArgs (tuple): (exePath,*exeArgs)
        exePathArgs (list):  [exePathArgs,altExePathArgs,...]"""
    if isinstance(exePathArgs, list):
        use = exePathArgs[0]
        for item in exePathArgs:
            if isinstance(item, tuple):
                exePath = item[0]
            else:
                exePath = item
            if exePath.exists():
                # Use this one
                use = item
                break
        exePathArgs = use
    if isinstance(exePathArgs, tuple):
        exePath = exePathArgs[0]
        exeArgs = exePathArgs[1:]
    else:
        exePath = exePathArgs
        exeArgs = tuple()
    return exePath, exeArgs

def app_button_factory(exePathArgs, *args, **kwargs):
    exePath, exeArgs = _parse_button_arguments(exePathArgs)
    if exePath and exePath.cext == u'.exe': # note: sometimes exePath is None
        return _ExeButton(exePath, exeArgs, *args, **kwargs)
    if exePath and exePath.cext == u'.jar':
        return _JavaButton(exePath, exeArgs, *args, **kwargs)
    if exePath and( exePath.cext == u'.lnk' or exePath.isdir()):
        return _LnkOrDirButton(exePath, exeArgs, *args, **kwargs)
    return _App_Button(exePath, exeArgs, *args, **kwargs)

#------------------------------------------------------------------------------
class _Mods_xEditExpert(BoolLink):
    """Toggle xEdit expert mode (when launched via Bash)."""
    _text = _(u'Expert Mode')
    _help = _(u'Launch %s in expert mode.') % bush.game.Xe.full_name
    key = bush.game.Xe.xe_key_prefix + u'.iKnowWhatImDoing'

class _Mods_xEditSkipBSAs(BoolLink):
    """Toggle xEdit expert mode (when launched via Bash)."""
    _text = _(u'Skip BSAs')
    _help = _(u'Skip loading BSAs when opening %s. Will disable some of its '
              u'functions.') % bush.game.Xe.full_name
    key = bush.game.Xe.xe_key_prefix + u'.skip_bsas'

class App_Tes4View(_ExeButton):
    """Allow some extra args for Tes4View."""

# arguments
# -fixup (wbAllowInternalEdit true default)
# -nofixup (wbAllowInternalEdit false)
# -showfixup (wbShowInternalEdit true default)
# -hidefixup (wbShowInternalEdit false)
# -skipbsa (wbLoadBSAs false)
# -forcebsa (wbLoadBSAs true default)
# -fixuppgrd
# -IKnowWhatImDoing
# -FNV
#  or name begins with FNV
# -FO3
#  or name begins with FO3
# -TES4
#  or name begins with TES4
# -TES5
#  or name begins with TES5
# -lodgen
#  or name ends with LODGen.exe
#  (requires TES4 mode)
# -masterupdate
#  or name ends with MasterUpdate.exe
#  (requires FO3 or FNV)
#  -filteronam
#  -FixPersistence
#  -NoFixPersistence
# -masterrestore
#  or name ends with MasterRestore.exe
#  (requires FO3 or FNV)
# -edit
#  or name ends with Edit.exe
# -translate
#  or name ends with Trans.exe
    def __init__(self, *args, **kwdargs):
        exePath, exeArgs = _parse_button_arguments(args[0])
        super(App_Tes4View, self).__init__(exePath, exeArgs, *args[1:], **kwdargs)
        if bush.game.Xe.xe_key_prefix:
            self.mainMenu.append(_Mods_xEditExpert())
            self.mainMenu.append(_Mods_xEditSkipBSAs())

    def IsPresent(self): # FIXME(inf) What on earth is this? What's the point??
        if self.exePath in bosh.undefinedPaths or not self.exePath.exists():
            testPath = bass.tooldirs['Tes4ViewPath']
            if testPath not in bosh.undefinedPaths and testPath.exists():
                self.exePath = testPath
                return True
            return False
        return True

    def Execute(self):
        is_expert = bush.game.Xe.xe_key_prefix and bass.settings[
            bush.game.Xe.xe_key_prefix + u'.iKnowWhatImDoing']
        skip_bsas = bush.game.Xe.xe_key_prefix and bass.settings[
            bush.game.Xe.xe_key_prefix + u'.skip_bsas']
        extraArgs = bass.inisettings[
            'xEditCommandLineArguments'].split() if is_expert else []
        if is_expert:
            extraArgs.append(u'-IKnowWhatImDoing')
        if skip_bsas:
            extraArgs.append(u'-skipbsa')
        self.extraArgs = tuple(extraArgs)
        super(App_Tes4View, self).Execute()

#------------------------------------------------------------------------------
class _Mods_BOSSDisableLockTimes(BoolLink):
    """Toggle Lock Load Order disabling when launching BOSS through Bash."""
    _text = _(u'BOSS Disable Lock Load Order')
    key = 'BOSS.ClearLockTimes'
    _help = _(u"If selected, will temporarily disable Bash's Lock Load Order "
              u'when running BOSS through Bash.')

#------------------------------------------------------------------------------
class _Mods_BOSSLaunchGUI(BoolLink):
    """If BOSS.exe is available then boss_gui.exe should be too."""
    _text, key, _help = _(u'Launch using GUI'), 'BOSS.UseGUI', \
                        _(u"If selected, Bash will run BOSS's GUI.")

class App_BOSS(_ExeButton):
    """loads BOSS"""
    def __init__(self, *args, **kwdargs):
        exePath, exeArgs = _parse_button_arguments(args[0])
        super(App_BOSS, self).__init__(exePath, exeArgs, *args[1:], **kwdargs)
        self.boss_path = self.exePath
        self.mainMenu.append(_Mods_BOSSLaunchGUI())
        self.mainMenu.append(_Mods_BOSSDisableLockTimes())

    def Execute(self):
        if bass.settings['BOSS.UseGUI']:
            self.exePath = self.boss_path.head.join(u'boss_gui.exe')
        else:
            self.exePath = self.boss_path
        self.wait = bool(bass.settings['BOSS.ClearLockTimes'])
        extraArgs = []
        if balt.getKeyState(82) and balt.getKeyState_Shift():
            extraArgs.append(u'-r 2',) # Revert level 2 - BOSS version 1.6+
        elif balt.getKeyState(82):
            extraArgs.append(u'-r 1',) # Revert level 1 - BOSS version 1.6+
        if balt.getKeyState(83):
            extraArgs.append(u'-s',) # Silent Mode - BOSS version 1.6+
        if balt.getKeyState(67): #c - print crc calculations in BOSS log.
            extraArgs.append(u'-c',)
        if bass.tooldirs['boss'].version >= (2, 0, 0, 0):
            # After version 2.0, need to pass in the -g argument
            extraArgs.append(u'-g%s' % bush.game.fsName,)
        self.extraArgs = tuple(extraArgs)
        super(App_BOSS, self).Execute()
        if bass.settings['BOSS.ClearLockTimes']:
            # Clear the saved times from before
            with load_order.Unlock():
                # Refresh to get the new load order that BOSS specified. If
                # on timestamp method scan the data dir, if not loadorder.txt
                # should have changed, refreshLoadOrder should detect that
                bosh.modInfos.refresh(
                    refresh_infos=not bosh.load_order.using_txt_file())
            # Refresh UI, so WB is made aware of the changes to load order
            BashFrame.modList.RefreshUI(refreshSaves=True, focus_list=False)

#------------------------------------------------------------------------------
class Game_Button(_ExeButton):
    """Will close app on execute if autoquit is on."""
    def __init__(self, exe_path_args, version_path, images, tip, obse_tip):
        exePath, exeArgs = _parse_button_arguments(exe_path_args)
        super(Game_Button, self).__init__(exePath, exeArgs, images=images,
            tip=tip, obseTip=obse_tip, uid=u'Oblivion')
        self._version_path = version_path

    @property
    def sb_button_tip(self):
        tip_ = self._tip + u' ' + self.version if self.version else self._tip
        if BashStatusBar.laaButton.button_state:
            tip_ += u' + ' + bush.game.Laa.laa_name
        return tip_

    @property
    def obseTip(self):
        # Oblivion (version)
        tip_ = self._obseTip % (dict(version=self.version))
        # + OBSE
        tip_ += u' + %s%s' % (bush.game.Se.se_abbrev, self.obseVersion)
        # + LAA
        if BashStatusBar.laaButton.button_state:
            tip_ += u' + ' + bush.game.Laa.laa_name
        return tip_

    def _app_button_execute(self):
        exe_xse = bass.dirs[u'app'].join(bush.game.Se.exe)
        exe_laa = bass.dirs[u'app'].join(bush.game.Laa.exe)
        exe_path = self.exePath # Default to the regular launcher
        if BashStatusBar.laaButton.button_state:
            # Should use the LAA Launcher if it's present
            exe_path = (exe_laa if exe_laa.isfile() else exe_path)
        elif BashStatusBar.obseButton.button_state:
            # Should use the xSE launcher if it's present
            exe_path = (exe_xse if exe_xse.isfile() else exe_path)
        self._run_exe(exe_path, [exe_path.s])
        if bass.settings.get(u'bash.autoQuit.on', False):
            Link.Frame.close_win(True)

    @property
    def version(self):
        if not bass.settings['bash.statusbar.showversion']: return u''
        version = self._version_path.strippedVersion
        if version != (0,):
            version = u'.'.join([u'%s'%x for x in version])
            return version
        return u''

#------------------------------------------------------------------------------
class TESCS_Button(_ExeButton):
    """CS/CK button. Needs a special tooltip when OBSE is enabled."""
    def __init__(self, ck_path, ck_images, ck_tip, ck_xse_tip, ck_xse_arg,
                 ck_uid=u'TESCS'):
        super(TESCS_Button, self).__init__(
            exePath=ck_path, exeArgs=(), images=ck_images, tip=ck_tip,
            obseTip=ck_xse_tip, uid=ck_uid)
        self.xse_args = (ck_xse_arg,) if ck_xse_arg else ()

    @property
    def obseTip(self):
        # CS/CK (version)
        tip_ = self._obseTip % {u'version': self.version}
        if not self.xse_args: return tip_
        # + OBSE
        tip_ += u' + %s%s' % (bush.game.Se.se_abbrev, self.obseVersion)
        # + CSE
        cse_path = bass.dirs[u'mods'].join(u'obse', u'plugins',
                                           u'Construction Set Extender.dll')
        if cse_path.exists():
            version = cse_path.strippedVersion
            if version != (0,):
                version = u'.'.join([u'%i'%x for x in version])
            else:
                version = u''
            tip_ += u' + CSE %s' % version
        return tip_

    def _app_button_execute(self):
        exe_xse = bass.dirs[u'app'].join(bush.game.Se.exe)
        if (self.xse_args and BashStatusBar.obseButton.button_state
                and exe_xse.isfile()):
            # If the script extender for this game has CK support, the xSE
            # loader is present and xSE is enabled, use that executable and
            # pass the editor argument to it
            self._run_exe(exe_xse, [exe_xse.s] + list(self.xse_args))
        else:
            # Fall back to the standard CK executable, with no arguments
            super(TESCS_Button, self)._app_button_execute()

#------------------------------------------------------------------------------
class _StatefulButton(StatusBar_Button):
    _state_key = u'OVERRIDE' # bass settings key for button state (un/checked)
    _state_img_key = u'OVERRIDE' # image key with state and size placeholders
    _default_state = True

    @property
    def sb_button_tip(self): raise AbstractError

    def SetState(self, state=None):
        """Set state related info. If newState != None, sets to new state
        first. For convenience, returns state when done."""
        if state is None: #--Default
            self.button_state = self.button_state
        elif state == -1: #--Invert
            self.button_state = True ^ self.button_state
        if self.gButton:
            self.gButton.image = balt.images[self.imageKey %
                        bass.settings['bash.statusbar.iconSize']].GetBitmap()
            self.gButton.tooltip = self.sb_button_tip

    @property
    def button_state(self): return self._present and bass.settings.get(
        self._state_key, self._default_state)
    @button_state.setter
    def button_state(self, val):
        bass.settings[self._state_key] = val

    @property
    def imageKey(self): return self.__class__._state_img_key % (
        [u'off', u'on'][self.button_state], u'%d')

    @property
    def _present(self): return True

    def GetBitmapButton(self, window, image=None, onRClick=None):
        if not self._present: return None
        self.SetState()
        return super(_StatefulButton, self).GetBitmapButton(window, image,
                                                            onRClick)

    def Execute(self):
        """Invert state."""
        self.SetState(-1)

class Obse_Button(_StatefulButton):
    """Obse on/off state button."""
    _state_key = 'bash.obse.on'
    _state_img_key = u'checkbox.green.%s.%s'
    @property
    def _present(self):
        return (bool(bush.game.Se.se_abbrev)
                and bass.dirs[u'app'].join(bush.game.Se.exe).exists())

    def SetState(self,state=None):
        super(Obse_Button, self).SetState(state)
        if bush.game.Laa.launchesSE and not state and BashStatusBar.laaButton.gButton is not None:
            # 4GB Launcher automatically launches the SE, so turning of the SE
            # required turning off the 4GB Launcher as well
            BashStatusBar.laaButton.SetState(state)
        self.UpdateToolTips()
        return state

    @property
    def sb_button_tip(self): return ((_(u"%s%s Disabled"), _(u"%s%s Enabled"))[
        self.button_state]) % (bush.game.Se.se_abbrev, self.obseVersion)

    def UpdateToolTips(self):
        tipAttr = ('sb_button_tip', 'obseTip')[self.button_state]
        for button in _App_Button.obseButtons:
            button.gButton.tooltip = getattr(button, tipAttr, u'')

class LAA_Button(_StatefulButton):
    """4GB Launcher on/off state button."""
    _state_key = 'bash.laa.on'
    _state_img_key = u'checkbox.blue.%s.%s'
    @property
    def _present(self):
        return bass.dirs[u'app'].join(bush.game.Laa.exe).exists()

    def SetState(self,state=None):
        super(LAA_Button, self).SetState(state)
        if bush.game.Laa.launchesSE and BashStatusBar.obseButton.gButton is not None:
            if state:
                # If the 4gb launcher launches the SE, enable the SE when enabling this
                BashStatusBar.obseButton.SetState(state)
            else:
                # We need the obse button to update the tooltips anyway
                BashStatusBar.obseButton.UpdateToolTips()
        return state

    @property
    def sb_button_tip(self): return bush.game.Laa.laa_name + (
        _(u' Disabled'), _(u' Enabled'))[self.button_state]

#------------------------------------------------------------------------------
class AutoQuit_Button(_StatefulButton):
    """Button toggling application closure when launching Oblivion."""
    _state_key = 'bash.autoQuit.on'
    _state_img_key = u'checkbox.red.%s.%s'
    _default_state = False

    @property
    def imageKey(self): return self._state_img_key % (
        [u'off', u'x'][self.button_state], u'%d')

    @property
    def sb_button_tip(self): return (_(u"Auto-Quit Disabled"), _(u"Auto-Quit Enabled"))[
        self.button_state]

#------------------------------------------------------------------------------
class App_Help(StatusBar_Button):
    """Show help browser."""
    imageKey, _tip = u'help.%s', _(u"Help File")

    def Execute(self):
        html = bass.dirs[u'mopy'].join(u'Docs\Wrye Bash General Readme.html')
        if html.exists():
            html.start()
        else:
            balt.showError(Link.Frame, _(u'Cannot find General Readme file.'))

#------------------------------------------------------------------------------
class App_DocBrowser(StatusBar_Button):
    """Show doc browser."""
    imageKey, _tip = u'doc.%s', _(u"Doc Browser")

    def Execute(self):
        if not Link.Frame.docBrowser:
            DocBrowser().show_frame()
            bass.settings['bash.modDocs.show'] = True
        Link.Frame.docBrowser.raise_frame()

#------------------------------------------------------------------------------
class App_Settings(StatusBar_Button):
    """Show settings dialog."""
    imageKey, _tip = 'settingsbutton.%s', _(u'Settings')

    def GetBitmapButton(self, window, image=None, onRClick=None):
        return super(App_Settings, self).GetBitmapButton(
            window, image, lambda: self.Execute())

    def Execute(self):
        BashStatusBar.SettingsMenu.new_menu(Link.Frame.statusBar, None)

#------------------------------------------------------------------------------
class App_Restart(StatusBar_Button):
    """Restart Wrye Bash"""
    _tip = _(u"Restart")

    def GetBitmapButton(self, window, image=None, onRClick=None):
        size = bass.settings['bash.statusbar.iconSize']
        return super(App_Restart, self).GetBitmapButton(
            window, staticBitmap(window, special='undo', size=(size,size)),
            onRClick)

    def Execute(self): Link.Frame.Restart()

#------------------------------------------------------------------------------
class App_GenPickle(StatusBar_Button):
    """Generate PKL File. Ported out of bish.py which wasn't working."""
    imageKey, _tip = 'pickle.%s', _(u"Generate PKL File")

    def Execute(self): self._update_pkl()

    @staticmethod
    def _update_pkl(fileName=None):
        """Update map of GMST eids to fids in bash\db\Oblivion_ids.pkl,
        based either on a list of new eids or the gmsts in the specified mod
        file. Updated pkl file is dropped in Mopy directory."""
        #--Data base
        import cPickle as pickle  # PY3
        try:
            fids = pickle.load(GPath(bush.game.pklfile).open('r'))['GMST']
            if fids:
                maxId = max(fids.values())
            else:
                maxId = 0
        except:
            fids = {}
            maxId = 0
        maxId = max(maxId, 0xf12345)
        maxOld = maxId
        print('maxId', hex(maxId))
        #--Eid list? - if the GMST has a 00000000 eid when looking at it in
        # the CS with nothing but oblivion.esm loaded you need to add the
        # gmst to this list, rebuild the pickle and overwrite the old one.
        for eid in bush.game.gmstEids:
            if eid not in fids:
                maxId += 1
                fids[eid] = maxId
                print('%08X  %08X %s' % (0, maxId, eid))
        #--Source file
        if fileName:
            sorter = lambda a: a.eid
            loadFactory = mod_files.LoadFactory(False, bush.game_mod.records.MreGmst)
            modInfo = bosh.modInfos[GPath(fileName)]
            modFile = mod_files.ModFile(modInfo, loadFactory)
            modFile.load(True)
            for gmst in sorted(modFile.GMST.records, key=sorter):
                print(gmst.eid, gmst.value)
                if gmst.eid not in fids:
                    maxId += 1
                    fids[gmst.eid] = maxId
                    print('%08X  %08X %s' % (gmst.fid, maxId, gmst.eid))
        #--Changes?
        if maxId > maxOld:
            outData = {'GMST': fids}
            pickle.dump(outData, GPath(bush.game.pklfile).open('w'))
            print(_(u"%d new gmst ids written to " + bush.game.pklfile) % (
                (maxId - maxOld),))
        else:
            print(_(u'No changes necessary. PKL data unchanged.'))

#------------------------------------------------------------------------------
class App_ModChecker(StatusBar_Button):
    """Show mod checker."""
    imageKey, _tip = 'modchecker.%s', _(u"Mod Checker")

    def Execute(self):
        if not Link.Frame.modChecker:
            ModChecker().show_frame()
        Link.Frame.modChecker.raise_frame()
