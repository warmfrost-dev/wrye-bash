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
"""This module contains oblivion multitweak item patcher classes that belong
to the Settings Multitweaker - as well as the tweaker itself."""
from __future__ import print_function

import re

from ... import bush # for game
from ...bolt import floats_equal
from ...patcher.patchers.base import MultiTweakItem
from ...patcher.patchers.base import MultiTweaker

_re_old_def = re.compile(u'' r'\[(.+)\]', re.U)
class _ASettingsTweak(MultiTweakItem):
    """Base class for settings tweaks. Allows changing the default choice per
    game."""
    def __init__(self, tweak_default):
        super(_ASettingsTweak, self).__init__()
        if tweak_default is None: return # None == leave default unchanged
        # First drop any existing defaults
        def repl_old_def(x):
            ma_x = _re_old_def.match(x)
            return ma_x.group(1) if ma_x else x
        self.choiceLabels = [repl_old_def(l) for l in self.choiceLabels]
        # Then mark the new choice as default
        for i, choice_label in enumerate(self.choiceLabels):
            if choice_label == tweak_default:
                self.choiceLabels[i] = u'[%s]' % choice_label
                self.default = i
                break

class _AGlobalsTweak(_ASettingsTweak):
    """Sets a global to specified value."""
    tweak_read_classes = b'GLOB',
    show_key_for_custom = True

    @property
    def chosen_value(self):
        # Globals are always stored as floats, regardless of what the CS says
        return float(self.choiceValues[self.chosen][0])

    def wants_record(self, record):
        return (record.eid and # skip missing and empty EDID
                record.eid.lower() == self.tweak_key and
                record.global_value != self.chosen_value)

    def tweak_record(self, record):
        record.global_value = self.chosen_value

    def tweak_log(self, log, count):
        log(u'* ' + _(u'%s set to: %4.2f') % (
            self.tweak_name, self.chosen_value))

#------------------------------------------------------------------------------
class GlobalsTweak_Timescale(_AGlobalsTweak):
    tweak_name = _(u'World: Timescale')
    tweak_tip = _(u'Timescale will be set to:')
    tweak_key = u'timescale'
    tweak_choices = [(u'1',         1),
                     (u'8',         8),
                     (u'10',        10),
                     (u'12',        12),
                     (u'20',        20),
                     (u'24',        24),
                     (u'[30]',      30),
                     (u'40',        40),
                     (_(u'Custom'), 0)]

#------------------------------------------------------------------------------
class GlobalsTweak_ThievesGuild_QuestStealingPenalty(_AGlobalsTweak):
    tweak_name = _(u'Thieves Guild: Quest Stealing Penalty')
    tweak_tip = _(u'The penalty (in Septims) for stealing while doing a '
                  u'Thieves Guild job:')
    tweak_key = u'tgpricesteal'
    tweak_choices = [(u'100',     100),
                     (u'150',     150),
                     (u'[200]',   200),
                     (u'300',     300),
                     (u'400',     400),
                     (_(u'Custom'), 0)]

#------------------------------------------------------------------------------
class GlobalsTweak_ThievesGuild_QuestKillingPenalty(_AGlobalsTweak):
    tweak_name = _(u'Thieves Guild: Quest Killing Penalty')
    tweak_tip = _(u'The penalty (in Septims) for killing while doing a '
                  u'Thieves Guild job:')
    tweak_key = u'tgpriceperkill'
    tweak_choices = [(u'250',     250),
                     (u'500',     500),
                     (u'[1000]', 1000),
                     (u'1500',   1500),
                     (u'2000',   2000),
                     (_(u'Custom'), 0)]

#------------------------------------------------------------------------------
class GlobalsTweak_ThievesGuild_QuestAttackingPenalty(_AGlobalsTweak):
    tweak_name = _(u'Thieves Guild: Quest Attacking Penalty')
    tweak_tip = _(u'The penalty (in Septims) for attacking while doing a '
                  u'Thieves Guild job:')
    tweak_key = u'tgpriceattack'
    tweak_choices = [(u'100',     100),
                     (u'250',     250),
                     (u'[500]',   500),
                     (u'750',     750),
                     (u'1000',   1000),
                     (_(u'Custom'), 0)]

#------------------------------------------------------------------------------
class GlobalsTweak_Crime_ForceJail(_AGlobalsTweak):
    tweak_name = _(u'Crime: Force Jail')
    tweak_tip = _(u'The amount of Bounty at which a jail sentence is '
                  u'mandatory')
    tweak_key = u'crimeforcejail'
    tweak_choices = [(u'1000',   1000),
                     (u'2500',   2500),
                     (u'[5000]', 5000),
                     (u'7500',   7500),
                     (u'10000', 10000),
                     (_(u'Custom'), 0)]

#------------------------------------------------------------------------------
class _AGmstTweak(_ASettingsTweak):
    """Sets a GMST to specified value."""
    tweak_read_classes = b'GMST',
    show_key_for_custom = True

    @property
    def chosen_eids(self):
        return ((self.tweak_key,), self.tweak_key)[isinstance(self.tweak_key,
                                                              tuple)]

    @property
    def chosen_values(self): return self.choiceValues[self.chosen]

    @property
    def eid_was_itpo(self):
        try:
            return self._eid_was_itpo
        except AttributeError:
            self._eid_was_itpo = {e.lower(): False for e in self.chosen_eids}
            return self._eid_was_itpo

    def _find_chosen_value(self, wanted_eid):
        """Returns the value the user chose for the game setting with the
        specified editor ID. Note that wanted_eid must be lower-case!"""
        for test_eid, test_val in zip(self.chosen_eids, self.chosen_values):
            if wanted_eid == test_eid.lower():
                return test_val
        return None

    def _find_original_eid(self, lower_eid):
        """We need to find the original case of the EDID, otherwise getFMSTFid
        blows - plus the dumped record will look nicer :)."""
        for orig_eid in self.chosen_eids:
            if lower_eid == orig_eid.lower():
                return orig_eid
        return lower_eid # fallback, should never happen

    def validate_values(self, chosen_values):
        if bush.game.fsName == u'Oblivion': ##: add a comment why TES4 only!
            for target_value in chosen_values:
                if target_value < 0:
                    return _(u"Oblivion GMST values can't be negative")
        for target_eid, target_value in zip(self.chosen_eids, chosen_values):
            if target_eid.startswith(u'f') and not isinstance(
                    target_value, float):
                    return _(u"The value chosen for GMST '%s' must be a "
                             u'float, but is currently of type %s (%s).') % (
                        target_eid, type(target_value).__name__, target_value)
        return None

    def wants_record(self, record):
        if record.fid[0] not in bush.game.bethDataFiles:
            return False # Avoid adding new masters just for a game setting
        rec_eid = record.eid.lower()
        if rec_eid not in self.eid_was_itpo: return False # not needed
        target_val = self._find_chosen_value(rec_eid)
        if rec_eid.startswith(u'f'):
            ret_val = not floats_equal(record.value, target_val)
        else:
            ret_val = record.value != target_val
        # Remember whether the last entry was ITPO or not
        self.eid_was_itpo[rec_eid] = not ret_val
        return ret_val

    def tweak_record(self, record):
        rec_eid = record.eid.lower()
        # We don't need to create a GMST for this EDID anymore
        self.eid_was_itpo[rec_eid] = True
        record.value = self._find_chosen_value(rec_eid)

    def tweak_log(self, log, count): # count is ignored here
        if len(self.choiceLabels) > 1:
            if self.choiceLabels[self.chosen].startswith(_(u'Custom')):
                if isinstance(self.chosen_values[0], basestring):
                    log(u'* %s: %s %s' % (
                        self.tweak_name, self.choiceLabels[self.chosen],
                        self.chosen_values[0]))
                else:
                    log(u'* %s: %s %4.2f' % (
                        self.tweak_name, self.choiceLabels[self.chosen],
                        self.chosen_values[0]))
            else:
                log(u'* %s: %s' % (
                    self.tweak_name, self.choiceLabels[self.chosen]))
        else:
            log(u'* ' + self.tweak_name)

    def finish_tweaking(self, patch_file):
        # Create new records for any remaining EDIDs
        for remaining_eid, was_itpo in self.eid_was_itpo.iteritems():
            if not was_itpo:
                patch_file.new_gmst(self._find_original_eid(remaining_eid),
                    self._find_chosen_value(remaining_eid))

#------------------------------------------------------------------------------
class GmstTweak_Arrow_LitterCount(_AGmstTweak):
    tweak_name = _(u'Arrow: Litter Count')
    tweak_tip = _(u'Maximum number of spent arrows allowed in cell.')
    tweak_key = (u'iArrowMaxRefCount',)
    tweak_choices = [(u'[15]',      15),
                     (u'25',        25),
                     (u'35',        35),
                     (u'50',        50),
                     (u'100',      100),
                     (u'500',      500),
                     (_(u'Custom'), 15)]

#------------------------------------------------------------------------------
class GmstTweak_Arrow_LitterTime(_AGmstTweak):
    tweak_name = _(u'Arrow: Litter Time')
    tweak_tip = _(u'Time before spent arrows fade away from cells and actors.')
    tweak_key = (u'fArrowAgeMax',)
    tweak_choices = [(_(u'1 Minute'),            60.0),
                     (_(u'[1.5 Minutes]'),       90.0),
                     (_(u'2 Minutes'),          120.0),
                     (_(u'3 Minutes'),          180.0),
                     (_(u'5 Minutes'),          300.0),
                     (_(u'10 Minutes'),         600.0),
                     (_(u'30 Minutes'),        1800.0),
                     (_(u'1 Hour'),            3600.0),
                     (_(u'Custom (in seconds)'), 90.0)]

#------------------------------------------------------------------------------
class GmstTweak_Arrow_RecoveryfromActor(_AGmstTweak):
    tweak_name = _(u'Arrow: Recovery from Actor')
    tweak_tip = _(u'Chance that an arrow shot into an actor can be recovered.')
    tweak_key = (u'iArrowInventoryChance',)
    tweak_choices = [(u'[50%]',     50),
                     (u'60%',       60),
                     (u'70%',       70),
                     (u'80%',       80),
                     (u'90%',       90),
                     (u'100%',     100),
                     (_(u'Custom'), 50)]

#------------------------------------------------------------------------------
class GmstTweak_Arrow_Speed(_AGmstTweak):
    tweak_name = _(u'Arrow: Speed')
    tweak_tip = _(u'Speed of a full power arrow.')
    tweak_key = (u'fArrowSpeedMult',)
    tweak_choices = [(u'[x 1.0]',                  1500.0),
                     (u'x 1.2',                    1800.0),
                     (u'x 1.4',                    2100.0),
                     (u'x 1.6',                    2400.0),
                     (u'x 1.8',                    2700.0),
                     (u'x 2.0',                    3000.0),
                     (u'x 2.2',                    3300.0),
                     (u'x 2.4',                    3600.0),
                     (u'x 2.6',                    3900.0),
                     (u'x 2.8',                    4200.0),
                     (u'x 3.0',                    4500.0),
                     (_(u'Custom (base is 1500)'), 1500.0)]

#------------------------------------------------------------------------------
class GmstTweak_Camera_ChaseTightness(_AGmstTweak):
    tweak_name = _(u'Camera: Chase Tightness')
    tweak_tip = _(u'Tightness of chase camera to player turning.')
    tweak_key = (u'fChase3rdPersonVanityXYMult', u'fChase3rdPersonXYMult')
    tweak_choices = [(u'x 1.5',                             6.0, 6.0),
                     (u'x 2.0',                             8.0, 8.0),
                     (u'x 3.0',                           12.0, 12.0),
                     (u'x 5.0',                           20.0, 20.0),
                     (_(u'ChaseCameraMod.esp (x 24.75)'), 99.0, 99.0),
                     (_(u'Custom'),                         4.0, 4.0)]

#------------------------------------------------------------------------------
class GmstTweak_Camera_ChaseDistance(_AGmstTweak):
    tweak_name = _(u'Camera: Chase Distance')
    tweak_tip = _(u'Distance camera can be moved away from PC using mouse '
                  u'wheel.')
    tweak_key = (u'fVanityModeWheelMax', u'fChase3rdPersonZUnitsPerSecond',
                 u'fVanityModeWheelMult')
    tweak_choices = [(u'x 1.5',     900.0, 450.0, 0.15),
                     (u'x 2',       1200.0, 600.0, 0.2),
                     (u'x 3',       1800.0, 900.0, 0.3),
                     (u'x 5',      3000.0, 1000.0, 0.3),
                     (u'x 10',     6000.0, 2000.0, 0.3),
                     (_(u'Custom'), 600.0, 300.0, 0.15)]

#------------------------------------------------------------------------------
class GmstTweak_Magic_ChameleonRefraction(_AGmstTweak):
    tweak_name = _(u'Magic: Chameleon Refraction')
    tweak_tip = _(u'Chameleon with transparency instead of refraction effect.')
    tweak_key = (u'fChameleonMinRefraction', u'fChameleonMaxRefraction')
    tweak_choices = [(_(u'Zero'),      0.0, 0.0),
                     (_(u'[Normal]'), 0.01, 1.0),
                     (_(u'Full'),      1.0, 1.0),
                     (_(u'Custom'),   0.01, 1.0)]

#------------------------------------------------------------------------------
class GmstTweak_Compass_Disable(_AGmstTweak):
    tweak_name = _(u'Compass: Disable')
    tweak_tip = _(u'No quest and/or points of interest markers on compass.')
    tweak_key = (u'iMapMarkerRevealDistance',)
    tweak_choices = [(_(u'Quests'),          1803),
                     (_(u'POIs'),            1802),
                     (_(u'Quests and POIs'), 1801)]

#------------------------------------------------------------------------------
class GmstTweak_Compass_RecognitionDistance(_AGmstTweak):
    tweak_name = _(u'Compass: Recognition Distance')
    tweak_tip = _(u'Distance at which markers (dungeons, towns etc.) begin to '
                  u'show on the compass.')
    tweak_key = (u'iMapMarkerVisibleDistance',)
    tweak_choices = [(_(u'75% Shorter'),  3125),
                     (_(u'50% Shorter'),  6250),
                     (_(u'25% Shorter'),  9375),
                     (_(u'[Default]'),   12500),
                     (_(u'25% Further'), 15625),
                     (_(u'50% Further'), 18750),
                     (_(u'75% Further'), 21875),
                     (_(u'Custom'),      12500)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_UnconsciousnessDuration(_AGmstTweak):
    tweak_name = _(u'Actor: Unconsciousness Duration')
    tweak_tip = _(u'Time which essential NPCs stay unconscious.')
    tweak_key = (u'fEssentialDeathTime',)
    tweak_choices = [(_(u'[10 Seconds]'),        10.0),
                     (_(u'20 Seconds'),          20.0),
                     (_(u'30 Seconds'),          30.0),
                     (_(u'1 Minute'),            60.0),
                     (_(u'1 1/2 Minutes'),       90.0),
                     (_(u'2 Minutes'),          120.0),
                     (_(u'3 Minutes'),          180.0),
                     (_(u'5 Minutes'),          300.0),
                     (_(u'Custom (in seconds)'), 10.0)]

#------------------------------------------------------------------------------
class GmstTweak_Movement_FatigueFromRunningEncumbrance(_AGmstTweak):
    tweak_name = _(u'Movement: Fatigue from Running/Encumbrance')
    tweak_tip = _(u'Fatigue cost of running and encumbrance.')
    tweak_key = (u'fFatigueRunBase', u'fFatigueRunMult')
    tweak_choices = [(u'x 1.5',    12.0, 6.0),
                     (u'x 2',      16.0, 8.0),
                     (u'x 3',     24.0, 12.0),
                     (u'x 4',     32.0, 16.0),
                     (u'x 5',     40.0, 20.0),
                     (_(u'Custom'), 8.0, 4.0)]

#------------------------------------------------------------------------------
class GmstTweak_Player_HorseTurningSpeed(_AGmstTweak):
    tweak_name = _(u'Player: Horse Turning Speed')
    tweak_tip = _(u'Speed at which your horse can turn.')
    tweak_key = (u'iHorseTurnDegreesPerSecond',
                 u'iHorseTurnDegreesRampUpPerSecond')
    tweak_choices = [(_(u'[Default]'),                           45, 80),
                     (u'x1.5',                                  68, 120),
                     (u'x2',                                    90, 160),
                     (u'x3',                                   135, 240),
                     (_(u'Custom (Turning and ramp-up speeds)'), 45, 80)]

#------------------------------------------------------------------------------
class GmstTweak_Camera_PCDeathTime(_AGmstTweak):
    tweak_name = _(u'Camera: PC Death Time')
    tweak_tip = _(u"Time after player's death before reload menu appears.")
    tweak_key = (u'fPlayerDeathReloadTime',)
    tweak_choices = [(_(u'15 Seconds'),     15.0),
                     (_(u'30 Seconds'),     30.0),
                     (_(u'1 Minute'),       60.0),
                     (_(u'5 Minute'),      300.0),
                     (_(u'Unlimited'), 9999999.0),
                     (_(u'Custom'),         15.0)]

#------------------------------------------------------------------------------
class GmstTweak_World_CellRespawnTime(_AGmstTweak):
    tweak_name = _(u'World: Cell Respawn Time')
    tweak_tip = _(u'Time before unvisited cell respawns. But longer times '
                  u'increase save sizes.')
    tweak_key = (u'iHoursToRespawnCell',)
    tweak_choices = [(_(u'1 Day'),             24),
                     (_(u'[3 Days]'),          72),
                     (_(u'5 Days'),           120),
                     (_(u'10 Days'),          240),
                     (_(u'20 Days'),          480),
                     (_(u'1 Month'),          720),
                     (_(u'6 Months'),        4368),
                     (_(u'1 Year'),          8760),
                     (_(u'Custom (in hours)'), 72)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_RechargeWeapons(_AGmstTweak):
    tweak_name = _(u'Combat: Recharge Weapons')
    tweak_tip = _(u'Allow recharging weapons during combat.')
    tweak_key = (u'iAllowRechargeDuringCombat',)
    tweak_choices = [(_(u'[Allow]'),  1),
                     (_(u'Disallow'), 0)]

#------------------------------------------------------------------------------
class GmstTweak_Magic_BoltSpeed(_AGmstTweak):
    tweak_name = _(u'Magic: Bolt Speed')
    tweak_tip = _(u'Speed of magic bolt/projectile.')
    tweak_key = (u'fMagicProjectileBaseSpeed',)
    tweak_choices = [(u'x 1.2',                 1200.0),
                     (u'x 1.4',                 1400.0),
                     (u'x 1.6',                 1600.0),
                     (u'x 1.8',                 1800.0),
                     (u'x 2.0',                 2000.0),
                     (u'x 2.2',                 2200.0),
                     (u'x 2.4',                 2400.0),
                     (u'x 2.6',                 2600.0),
                     (u'x 2.8',                 2800.0),
                     (u'x 3.0',                 3000.0),
                     (_(u'Custom (base 1000)'), 1000.0)]

#------------------------------------------------------------------------------
class GmstTweak_Msg_EquipMiscItem(_AGmstTweak):
    tweak_name = _(u'Msg: Equip Misc. Item')
    tweak_tip = _(u'Message upon equipping misc. item.')
    tweak_key = (u'sCantEquipGeneric',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_AutoSaving(_AGmstTweak):
    tweak_name = _(u'Msg: Auto Saving')
    tweak_tip = _(u'Message upon auto saving.')
    tweak_key = (u'sAutoSaving',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_HarvestFailure(_AGmstTweak):
    tweak_name = _(u'Msg: Harvest Failure')
    tweak_tip = _(u'Message upon failure at harvesting flora.')
    tweak_key = (u'sFloraFailureMessage',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_HarvestSuccess(_AGmstTweak):
    tweak_name = _(u'Msg: Harvest Success')
    tweak_tip = _(u'Message upon success at harvesting flora.')
    tweak_key = (u'sFloraSuccessMessage',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_QuickSave(_AGmstTweak):
    tweak_name = _(u'Msg: Quick Save')
    tweak_tip = _(u'Message upon quick saving.')
    tweak_key = (u'sQuickSaving',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_HorseStabled(_AGmstTweak):
    tweak_name = _(u'Msg: Horse Stabled')
    tweak_tip = _(u'Message upon fast traveling with a horse to a city.')
    tweak_key = (u'sFastTravelHorseatGate',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_NoFastTravel(_AGmstTweak):
    tweak_name = _(u'Msg: No Fast Travel')
    tweak_tip = _(u'Message when attempting to fast travel when fast travel '
                  u'is unavailable due to location.')
    tweak_key = (u'sNoFastTravelScriptBlock',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_LoadingArea(_AGmstTweak):
    tweak_name = _(u'Msg: Loading Area')
    tweak_tip = _(u'Message when background loading area.')
    tweak_key = (u'sLoadingArea',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_QuickLoad(_AGmstTweak):
    tweak_name = _(u'Msg: Quick Load')
    tweak_tip = _(u'Message when quick loading.')
    tweak_key = (u'sQuickLoading',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_Msg_NotEnoughCharge(_AGmstTweak):
    tweak_name = _(u'Msg: Not Enough Charge')
    tweak_tip = _(u'Message when enchanted item is out of charge.')
    tweak_key = (u'sNoCharge',)
    tweak_choices = [(_(u'[None]'),         u' '),
                     (u'.',                 u'.'),
                     (_(u'Hmm...'), _(u'Hmm...')),
                     (_(u'Custom'),      _(u' '))]

#------------------------------------------------------------------------------
class GmstTweak_CostMultiplier_Repair(_AGmstTweak):
    tweak_name = _(u'Cost Multiplier: Repair')
    tweak_tip = _(u'Cost factor for repairing items.')
    tweak_key = (u'fRepairCostMult',)
    tweak_choices = [(u'0.1',       0.1),
                     (u'0.2',       0.2),
                     (u'0.3',       0.3),
                     (u'0.4',       0.4),
                     (u'0.5',       0.5),
                     (u'0.6',       0.6),
                     (u'0.7',       0.7),
                     (u'0.8',       0.8),
                     (u'[0.9]',     0.9),
                     (u'1.0',       1.0),
                     (_(u'Custom'), 0.9)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_GreetingDistance(_AGmstTweak):
    tweak_name = _(u'Actor: Greeting Distance')
    tweak_tip = _(u'Distance (in units) at which NPCs will greet the player.')
    tweak_key = (u'fAIMinGreetingDistance',)
    tweak_choices = [(u'50',         50.0),
                     (u'100',       100.0),
                     (u'125',       125.0),
                     (u'[150]',     150.0),
                     (u'200',       200.0),
                     (u'300',       300.0),
                     (_(u'Custom'), 150.0)]

#------------------------------------------------------------------------------
class GmstTweak_CostMultiplier_Recharge(_AGmstTweak):
    tweak_name = _(u'Cost Multiplier: Recharge')
    tweak_tip = _(u'Cost factor for recharging items.')
    tweak_key = (u'fRechargeGoldMult',)
    tweak_choices = [(u'0.1',       0.1),
                     (u'0.2',       0.2),
                     (u'0.3',       0.3),
                     (u'0.5',       0.5),
                     (u'0.7',       0.7),
                     (u'1.0',       1.0),
                     (u'1.5',       1.5),
                     (u'[2.0]',     2.0),
                     (_(u'Custom'), 2.0)]

#------------------------------------------------------------------------------
class GmstTweak_MasterofMercantileextragoldamount(_AGmstTweak):
    tweak_name = _(u'Master of Mercantile extra gold amount')
    tweak_tip = _(u'How much more barter gold all merchants have for a master '
                  u'of mercantile.')
    tweak_key = (u'iPerkExtraBarterGoldMaster',)
    tweak_choices = [(u'300',       300),
                     (u'400',       400),
                     (u'[500]',     500),
                     (u'600',       600),
                     (u'800',       800),
                     (u'1000',     1000),
                     (_(u'Custom'), 500)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_MaxActors(_AGmstTweak):
    tweak_name = _(u'Combat: Max Actors')
    tweak_tip = _(u'Maximum number of actors that can actively be in combat '
                  u'with the player.')
    tweak_key = (u'iNumberActorsInCombatPlayer',)
    tweak_choices = [(u'[10]',      10),
                     (u'15',        15),
                     (u'20',        20),
                     (u'30',        30),
                     (u'40',        40),
                     (u'50',        50),
                     (u'80',        80),
                     (_(u'Custom'), 10)]

#------------------------------------------------------------------------------
class GmstTweak_Crime_AlarmDistance(_AGmstTweak):
    tweak_name = _(u'Crime: Alarm Distance')
    tweak_tip = _(u'Distance from player that NPCs (guards) will be alerted '
                  u'of a crime.')
    tweak_key = (u'iCrimeAlarmRecDistance',)
    tweak_choices = [(u'6000',      6000),
                     (u'[4000]',    4000),
                     (u'3000',      3000),
                     (u'2000',      2000),
                     (u'1000',      1000),
                     (u'500',        500),
                     (_(u'Custom'), 4000)]

#------------------------------------------------------------------------------
class GmstTweak_Crime_PrisonDurationModifier(_AGmstTweak):
    tweak_name = _(u'Crime: Prison Duration Modifier')
    tweak_tip = _(u'Days in prison is your bounty divided by this number.')
    tweak_key = (u'iCrimeDaysInPrisonMod',)
    tweak_choices = [(u'50',         50),
                     (u'60',         60),
                     (u'70',         70),
                     (u'80',         80),
                     (u'90',         90),
                     (u'[100]',     100),
                     (_(u'Custom'), 100)]

#------------------------------------------------------------------------------
class GmstTweak_CostMultiplier_Enchantment(_AGmstTweak):
    tweak_name = _(u'Cost Multiplier: Enchantment')
    tweak_tip = _(u'Cost factor for enchanting items, OOO default is 120, '
                  u'vanilla 10.')
    tweak_key = (u'fEnchantmentGoldMult',)
    tweak_choices = [(u'[10]',      10.0),
                     (u'20',        20.0),
                     (u'30',        30.0),
                     (u'50',        50.0),
                     (u'70',        70.0),
                     (u'90',        90.0),
                     (u'120',      120.0),
                     (u'150',      150.0),
                     (_(u'Custom'), 10.0)]

#------------------------------------------------------------------------------
class GmstTweak_CostMultiplier_SpellMaking(_AGmstTweak):
    tweak_name = _(u'Cost Multiplier: Spell Making')
    tweak_tip = _(u'Cost factor for making spells.')
    tweak_key = (u'fSpellmakingGoldMult',)
    tweak_choices = [(u'[3]',       3.0),
                     (u'5',         5.0),
                     (u'8',         8.0),
                     (u'10',       10.0),
                     (u'15',       15.0),
                     (_(u'Custom'), 3.0)]

#------------------------------------------------------------------------------
class GmstTweak_AI_MaxActiveActors(_AGmstTweak):
    tweak_name = _(u'AI: Max Active Actors')
    tweak_tip = _(u'Maximum actors whose AI can be active. Must be higher '
                  u'than Combat: Max Actors')
    tweak_key = (u'iAINumberActorsComplexScene',)
    tweak_choices = [(u'20',                 20),
                     (u'[25]',               25),
                     (u'30',                 30),
                     (u'35',                 35),
                     (_(u'MMM Default: 40'), 40),
                     (u'50',                 50),
                     (u'60',                 60),
                     (u'100',               100),
                     (_(u'Custom'),          25)]

#------------------------------------------------------------------------------
class GmstTweak_Magic_MaxPlayerSummons(_AGmstTweak):
    tweak_name = _(u'Magic: Max Player Summons')
    tweak_tip = _(u'Maximum number of creatures the player can summon.')
    tweak_key = (u'iMaxPlayerSummonedCreatures',)
    tweak_choices = [(u'[1]',       1),
                     (u'3',         3),
                     (u'5',         5),
                     (u'8',         8),
                     (u'10',       10),
                     (_(u'Custom'), 1)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_MaxAllyHits(_AGmstTweak):
    tweak_name = _(u'Combat: Max Ally Hits')
    tweak_tip = _(u'Maximum number of hits on an ally allowed in combat '
                  u'before the ally will attack the hitting character.')
    tweak_key = (u'iAllyHitAllowed',)
    tweak_choices = [(u'0',         0),
                     (u'3',         3),
                     (u'[5]',       5),
                     (u'8',         8),
                     (u'10',       10),
                     (u'15',       15),
                     (_(u'Custom'), 5)]

#------------------------------------------------------------------------------
class GmstTweak_Magic_MaxNPCSummons(_AGmstTweak):
    tweak_name = _(u'Magic: Max NPC Summons')
    tweak_tip = _(u'Maximum number of creatures that each NPC can summon')
    tweak_key = (u'iAICombatMaxAllySummonCount',)
    tweak_choices = [(u'1',         1),
                     (u'[3]',       3),
                     (u'5',         5),
                     (u'8',         8),
                     (u'10',       10),
                     (u'15',       15),
                     (_(u'Custom'), 3)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Assault(_AGmstTweak):
    tweak_name = _(u'Bounty: Assault')
    tweak_tip = _(u"Bounty for attacking a 'good' npc.")
    tweak_key = (u'iCrimeGoldAttackMin',)
    tweak_choices = [(u'40',         40),
                     (u'100',       100),
                     (u'200',       200),
                     (u'300',       300),
                     (u'400',       400),
                     (u'[500]',     500),
                     (u'650',       650),
                     (u'800',       800),
                     (_(u'Custom'), 500)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_HorseTheft(_AGmstTweak):
    tweak_name = _(u'Bounty: Horse Theft')
    tweak_tip = _(u'Bounty for horse theft')
    tweak_key = (u'iCrimeGoldStealHorse',)
    tweak_choices = [(u'10',         10),
                     (u'25',         25),
                     (u'50',         50),
                     (u'100',       100),
                     (u'200',       200),
                     (u'[250]',     250),
                     (u'300',       300),
                     (u'450',       450),
                     (_(u'Custom'), 100)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Theft(_AGmstTweak):
    tweak_name = _(u'Bounty: Theft')
    tweak_tip = _(u'Bounty for stealing, as fraction of item value.')
    tweak_key = (u'fCrimeGoldSteal',)
    tweak_choices = [(u'1/4',      0.25),
                     (u'[1/2]',     0.5),
                     (u'3/4',      0.75),
                     (u'1',         1.0),
                     (_(u'Custom'), 0.5)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_Alchemy(_AGmstTweak):
    tweak_name = _(u'Combat: Alchemy')
    tweak_tip = _(u'Allow alchemy during combat.')
    tweak_key = (u'iAllowAlchemyDuringCombat',)
    tweak_choices = [(_(u'Allow'),      1),
                     (_(u'[Disallow]'), 0)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_Repair(_AGmstTweak):
    tweak_name = _(u'Combat: Repair')
    tweak_tip = _(u'Allow repairing armor/weapons during combat.')
    tweak_key = (u'iAllowRepairDuringCombat',)
    tweak_choices = [(_(u'Allow'),      1),
                     (_(u'[Disallow]'), 0)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_MaxCompanions(_AGmstTweak):
    tweak_name = _(u'Actor: Max Companions')
    tweak_tip = _(u'Maximum number of actors following the player.')
    tweak_key = (u'iNumberActorsAllowedToFollowPlayer',)
    tweak_choices = [(u'2',         2),
                     (u'4',         4),
                     (u'[6]',       6),
                     (u'8',         8),
                     (u'10',       10),
                     (_(u'Custom'), 6)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_TrainingLimit(_AGmstTweak):
    tweak_name = _(u'Actor: Training Limit')
    tweak_tip = _(u'Maximum number of Training allowed by trainers.')
    tweak_key = (u'iTrainingSkills',)
    tweak_choices = [(u'1',               1),
                     (u'[5]',             5),
                     (u'8',               8),
                     (u'10',             10),
                     (u'20',             20),
                     (_(u'Unlimited'), 9999),
                     (_(u'Custom'),       0)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_MaximumArmorRating(_AGmstTweak):
    tweak_name = _(u'Combat: Maximum Armor Rating')
    tweak_tip = _(u'The Maximum amount of protection you will get from armor.')
    tweak_key = (u'fMaxArmorRating',)
    tweak_choices = [(u'50',        50.0),
                     (u'75',        75.0),
                     (u'[85]',      85.0),
                     (u'90',        90.0),
                     (u'95',        95.0),
                     (u'100',      100.0),
                     (_(u'Custom'), 85.0)]

#------------------------------------------------------------------------------
class GmstTweak_Warning_InteriorDistancetoHostiles(_AGmstTweak):
    tweak_name = _(u'Warning: Interior Distance to Hostiles')
    tweak_tip = _(u'The minimum distance hostile actors have to be to be '
                  u'allowed to sleep, travel etc, when inside interiors.')
    tweak_key = (u'fHostileActorInteriorDistance',)
    tweak_choices = [(u'10',          10.0),
                     (u'100',        100.0),
                     (u'500',        500.0),
                     (u'1000',      1000.0),
                     (u'[2000]',    2000.0),
                     (u'3000',      3000.0),
                     (u'4000',      4000.0),
                     (_(u'Custom'), 2000.0)]

#------------------------------------------------------------------------------
class GmstTweak_Warning_ExteriorDistancetoHostiles(_AGmstTweak):
    tweak_name = _(u'Warning: Exterior Distance to Hostiles')
    tweak_tip = _(u'The minimum distance hostile actors have to be to be '
                  u'allowed to sleep, travel etc, when outside.')
    tweak_key = (u'fHostileActorExteriorDistance',)
    tweak_choices = [(u'10',          10.0),
                     (u'100',        100.0),
                     (u'500',        500.0),
                     (u'1000',      1000.0),
                     (u'2000',      2000.0),
                     (u'[3000]',    3000.0),
                     (u'4000',      4000.0),
                     (u'5000',      5000.0),
                     (u'6000',      6000.0),
                     (_(u'Custom'), 3000.0)]

#------------------------------------------------------------------------------
class GmstTweak_UOPVampireAgingandFaceFix(_AGmstTweak):
    tweak_name = _(u'UOP Vampire Aging and Face Fix.esp')
    tweak_tip = _(u"Duplicate of UOP component that disables vampire aging "
                  u"(fixes a bug). Use instead of 'UOP Vampire Aging & Face "
                  u"Fix.esp' to save an esp slot.")
    tweak_key = (u'iVampirismAgeOffset',)
    tweak_choices = [(u'Fix it!', 0)]
    default_enabled = True

#------------------------------------------------------------------------------
class GmstTweak_AI_MaxDeadActors(_AGmstTweak):
    tweak_name = _(u'AI: Max Dead Actors')
    tweak_tip = _(u"Maximum number of dead actors allowed before they're "
                  u"removed.")
    tweak_key = (u'iRemoveExcessDeadCount',
                 u'iRemoveExcessDeadTotalActorCount',
                 u'iRemoveExcessDeadComplexTotalActorCount',
                 u'iRemoveExcessDeadComplexCount', u'fRemoveExcessDeadTime',
                 u'fRemoveExcessComplexDeadTime')
    tweak_choices = [(u'[x 1]',     15, 20, 20, 3, 10.0, 2.5),
                     (u'x 1.5',     22, 30, 30, 6, 30.0, 7.5),
                     (u'x 2',      30, 40, 40, 9, 50.0, 12.5),
                     (u'x 2.5',   37, 50, 50, 12, 70.0, 17.5),
                     (u'x 3',     45, 60, 60, 15, 90.0, 22.5),
                     (u'x 3.5',  52, 70, 70, 18, 110.0, 27.5),
                     (u'x 4',    60, 80, 80, 21, 130.0, 32.5),
                     (_(u'Custom'), 15, 20, 20, 3, 10.0, 2.5)]

#------------------------------------------------------------------------------
class GmstTweak_Player_InventoryQuantityPrompt(_AGmstTweak):
    tweak_name = _(u'Player: Inventory Quantity Prompt')
    tweak_tip = _(u'Number of items in a stack at which point the game '
                  u'prompts for a quantity.')
    tweak_key = (u'iInventoryAskQuantityAt',)
    tweak_choices = [(_(u'Always Prompt'),    1),
                     (u'2',                   2),
                     (u'[3]',                 3),
                     (u'4',                   4),
                     (u'5',                   5),
                     (u'10',                 10),
                     (u'20',                 20),
                     (_(u'Never Prompt'), 99999),
                     (_(u'Custom'),           5)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Trespassing(_AGmstTweak):
    tweak_name = _(u'Bounty: Trespassing')
    tweak_tip = _(u'Bounty for trespassing.')
    tweak_key = (u'iCrimeGoldTresspass',)
    tweak_choices = [(u'1',         1),
                     (u'[5]',       5),
                     (u'8',         8),
                     (u'10',       10),
                     (u'20',       20),
                     (_(u'Custom'), 5)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Pickpocketing(_AGmstTweak):
    tweak_name = _(u'Bounty: Pickpocketing')
    tweak_tip = _(u'Bounty for pickpocketing.')
    tweak_key = (u'iCrimeGoldPickpocket',)
    tweak_choices = [(u'5',          5),
                     (u'8',          8),
                     (u'10',        10),
                     (u'[25]',      25),
                     (u'50',        50),
                     (u'100',      100),
                     (_(u'Custom'), 25)]

#------------------------------------------------------------------------------
class GmstTweak_LeveledCreatureMaxLevelDifference(_AGmstTweak):
    tweak_name = _(u'Leveled Creature Max Level Difference')
    tweak_tip = _(u'Maximum difference to player level for leveled creatures.')
    tweak_key = (u'iLevCreaLevelDifferenceMax',)
    tweak_choices = [(u'1',               1),
                     (u'5',               5),
                     (u'[8]',             8),
                     (u'10',             10),
                     (u'20',             20),
                     (_(u'Unlimited'), 9999),
                     (_(u'Custom'),       8)]

#------------------------------------------------------------------------------
class GmstTweak_LeveledItemMaxLevelDifference(_AGmstTweak):
    tweak_name = _(u'Leveled Item Max Level Difference')
    tweak_tip = _(u'Maximum difference to player level for leveled items.')
    tweak_key = (u'iLevItemLevelDifferenceMax',)
    tweak_choices = [(u'1',               1),
                     (u'5',               5),
                     (u'[8]',             8),
                     (u'10',             10),
                     (u'20',             20),
                     (_(u'Unlimited'), 9999),
                     (_(u'Custom'),       8)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_StrengthEncumbranceMultiplier(_AGmstTweak):
    tweak_name = _(u'Actor: Strength Encumbrance Multiplier')
    tweak_tip = _(u"Actor's Strength X this = Actor's Encumbrance capacity.")
    tweak_key = (u'fActorStrengthEncumbranceMult',)
    tweak_choices = [(u'1',                 1.0),
                     (u'3',                 3.0),
                     (u'[5]',               5.0),
                     (u'8',                 8.0),
                     (u'10',               10.0),
                     (u'20',               20.0),
                     (_(u'Unlimited'), 999999.0),
                     (_(u'Custom'),         5.0)]

#------------------------------------------------------------------------------
class GmstTweak_Visuals_NPCBlood(_AGmstTweak):
    tweak_name = _(u'Visuals: NPC Blood')
    tweak_tip = _(u'Changes or disables NPC Blood splatter textures.')
    tweak_key = (u'sBloodTextureDefault', u'sBloodTextureExtra1',
                 u'sBloodTextureExtra2', u'sBloodParticleDefault',
                 u'sBloodParticleExtra1', u'sBloodParticleExtra2')
    tweak_choices = [(_(u'No Blood'), u'', u'', u'', u'', u'', u''),
                     (_(u'Custom'),   u'', u'', u'', u'', u'', u'')]

#------------------------------------------------------------------------------
class GmstTweak_AI_MaxSmileDistance(_AGmstTweak):
    tweak_name = _(u'AI: Max Smile Distance')
    tweak_tip = _(u'Maximum distance for NPCs to start smiling.')
    tweak_key = (u'fAIMaxSmileDistance',)
    tweak_choices = [(_(u'No Smiles'),         0.0),
                     (_(u'[Default (128)]'), 128.0),
                     (_(u'Custom'),          128.0)]

#------------------------------------------------------------------------------
class GmstTweak_Player_MaxDraggableWeight(_AGmstTweak):
    tweak_name = _(u'Player: Max Draggable Weight')
    tweak_tip = _(u'Maximum weight to be able move things with the drag key.')
    tweak_key = (u'fMoveWeightMax',)
    tweak_choices = [(u'115',                          115.0),
                     (u'[150]',                        150.0),
                     (u'250',                          250.0),
                     (u'500',                          500.0),
                     (_(u'MovableBodies.esp (1500)'), 1500.0),
                     (_(u'Custom'),                    150.0)]

#------------------------------------------------------------------------------
class GmstTweak_AI_ConversationChance(_AGmstTweak):
    tweak_name = _(u'AI: Conversation Chance')
    tweak_tip = _(u'Chance of NPCs engaging each other in conversation '
                  u'(possibly also with the player).')
    tweak_key = (u'fAISocialchanceForConversation',)
    tweak_choices = [(u'10%',        10.0),
                     (u'25%',        25.0),
                     (u'50%',        50.0),
                     (u'[100%]',    100.0),
                     (_(u'Custom'), 100.0)]

#------------------------------------------------------------------------------
class GmstTweak_AI_ConversationChance_Interior(_AGmstTweak):
    tweak_name = _(u'AI: Conversation Chance - Interior')
    tweak_tip = _(u'Chance of NPCs engaging each other in conversation '
                  u'(possibly also with the player) - in interiors.')
    tweak_key = (u'fAISocialchanceForConversationInterior',)
    tweak_choices = [(u'10%',        10.0),
                     (u'[25%]',      25.0),
                     (u'50%',        50.0),
                     (u'100%',      100.0),
                     (_(u'Custom'), 100.0)]

#------------------------------------------------------------------------------
class GmstTweak_Crime_PickpocketingChance(_AGmstTweak):
    tweak_name = _(u'Crime: Pickpocketing Chance')
    tweak_tip = _(u'Improve chances of successful pickpocketing.')
    tweak_key = (u'fPickPocketMinChance', u'fPickPocketMaxChance')
    tweak_choices = [(_(u'0% to 50%'),                   0.0, 50.0),
                     (_(u'0% to 75%'),                   0.0, 75.0),
                     (_(u'[0% to 90%]'),                 0.0, 90.0),
                     (_(u'0% to 100%'),                 0.0, 100.0),
                     (_(u'25% to 100%'),               25.0, 100.0),
                     (_(u'50% to 100%'),               50.0, 100.0),
                     (_(u'Custom (Min and Max Chance)'), 0.0, 90.0)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_MaxJumpHeight(_AGmstTweak):
    tweak_name = _(u'Actor: Max Jump Height')
    tweak_tip = _(u'Increases the height to which you can jump. First value '
                  u'is min, second is max.')
    tweak_key = (u'fJumpHeightMin', u'fJumpHeightMax')
    tweak_choices = [(u'0.5x',       38.0, 82.0),
                     (u'[1x]',      76.0, 164.0),
                     (u'2x',       152.0, 328.0),
                     (u'3x',       228.0, 492.0),
                     (u'4x',       304.0, 656.0),
                     (_(u'Custom'), 76.0, 164.0)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Murder(_AGmstTweak):
    tweak_name = _(u'Bounty: Murder')
    tweak_tip = _(u'Bounty for committing a witnessed murder.')
    tweak_key = (u'iCrimeGoldMurder',)
    tweak_choices = [(u'500',        500),
                     (u'750',        750),
                     (u'[1000]',    1000),
                     (u'1250',      1250),
                     (u'1500',      1500),
                     (_(u'Custom'), 1000)]

#------------------------------------------------------------------------------
class GmstTweak_Bounty_Jailbreak(_AGmstTweak):
    tweak_name = _(u'Bounty: Jailbreak')
    tweak_tip = _(u'Bounty for escaping from jail.')
    tweak_key = (u'iCrimeGoldJailBreak',)
    tweak_choices = [(u'[50]',       50),
                     (u'100',       100),
                     (u'125',       125),
                     (u'150',       150),
                     (u'175',       175),
                     (u'200',       200),
                     (_(u'Custom'), 100)]

#------------------------------------------------------------------------------
class GmstTweak_Camera_ChaseDistance_Fo3(_AGmstTweak):
    tweak_name = _(u'Camera: Chase Distance')
    tweak_tip = _(u'Distance camera can be moved away from PC using mouse '
                  u'wheel.')
    tweak_key = (u'fVanityModeWheelMax', u'fChase3rdPersonZUnitsPerSecond')
    tweak_choices = [(u'x 1.5',    900.0, 1200.0),
                     (u'x 2',     1200.0, 1600.0),
                     (u'x 3',     1800.0, 2400.0),
                     (u'x 5',     3000.0, 4000.0),
                     (u'x 10',    6000.0, 5000.0),
                     (_(u'Custom'), 600.0, 800.0)]

#------------------------------------------------------------------------------
class GmstTweak_Actor_MaxJumpHeight_Fo3(_AGmstTweak):
    tweak_name = _(u'Actor: Max Jump Height')
    tweak_tip = _(u'Increases the height to which you can jump.')
    tweak_key = (u'fJumpHeightMin',)
    tweak_choices = [(u'0.5x',      38.0),
                     (u'[1x]',      76.0),
                     (u'2x',       152.0),
                     (u'3x',       228.0),
                     (u'4x',       304.0),
                     (_(u'Custom'), 76.0)]

#------------------------------------------------------------------------------
class GmstTweak_CostMultiplier_Repair_Fo3(_AGmstTweak):
    tweak_name = _(u'Cost Multiplier: Repair')
    tweak_tip = _(u'Cost factor for repairing items.')
    tweak_key = (u'fItemRepairCostMult',)
    tweak_choices = [(u'1.0',       1.0),
                     (u'1.25',     1.25),
                     (u'1.5',       1.5),
                     (u'1.75',     1.75),
                     (u'[2.0]',     2.0),
                     (u'2.5',       2.5),
                     (u'3.0',       3.0),
                     (_(u'Custom'), 2.0)]

#------------------------------------------------------------------------------
class GmstTweak_Gore_CombatDismemberPartChance(_AGmstTweak):
    tweak_name = _(u'Gore: Combat Dismember Part Chance')
    tweak_tip = _(u'The chance that body parts will be dismembered.')
    tweak_key = (u'iCombatDismemberPartChance',)
    tweak_choices = [(u'0',          0),
                     (u'25',        25),
                     (u'[50]',      50),
                     (u'80',        80),
                     (u'100',      100),
                     (_(u'Custom'), 50)]

#------------------------------------------------------------------------------
class GmstTweak_Gore_CombatExplodePartChance(_AGmstTweak):
    tweak_name = _(u'Gore: Combat Explode Part Chance')
    tweak_tip = _(u'The chance that body parts will explode.')
    tweak_key = (u'iCombatExplodePartChance',)
    tweak_choices = [(u'0',          0),
                     (u'25',        25),
                     (u'50',        50),
                     (u'[75]',      75),
                     (u'100',      100),
                     (_(u'Custom'), 75)]

#------------------------------------------------------------------------------
class GmstTweak_LeveledItemMaxleveldifference(_AGmstTweak):
    tweak_name = _(u'Leveled Item Max level difference')
    tweak_tip = _(u'Maximum difference to player level for leveled items.')
    tweak_key = (u'iLevItemLevelDifferenceMax',)
    tweak_choices = [(u'1',               1),
                     (u'5',               5),
                     (u'[8]',             8),
                     (u'10',             10),
                     (u'20',             20),
                     (_(u'Unlimited'), 9999),
                     (_(u'Custom'),       8)]

#------------------------------------------------------------------------------
class GmstTweak_Movement_BaseSpeed(_AGmstTweak):
    tweak_name = _(u'Movement: Base Speed')
    tweak_tip = _(u'Changes base movement speed.')
    tweak_key = (u'fMoveBaseSpeed',)
    tweak_choices = [(u'[77.0]',    77.0),
                     (u'90.0',      90.0),
                     (_(u'Custom'), 77.0)]

#------------------------------------------------------------------------------
class GmstTweak_Movement_SneakMultiplier(_AGmstTweak):
    tweak_name = _(u'Movement: Sneak Multiplier')
    tweak_tip = _(u'Movement speed is multiplied by this when the actor is sneaking.')
    tweak_key = (u'fMoveSneakMult',)
    tweak_choices = [(u'[0.57]',    0.57),
                     (u'0.66',      0.66),
                     (_(u'Custom'), 0.57)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_VATSPlayerDamageMultiplier(_AGmstTweak):
    tweak_name = _(u'Combat: VATS Player Damage Multiplier')
    tweak_tip = _(u'Multiplier of damage that player receives in VATS.')
    tweak_key = (u'fVATSPlayerDamageMult',)
    tweak_choices = [(u'0.10',       0.1),
                     (u'0.25',      0.25),
                     (u'0.50',       0.5),
                     (u'[0.75]',    0.75),
                     (u'1.00',       1.0),
                     (_(u'Custom'), 0.75)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_AutoAimFix(_AGmstTweak):
    tweak_name = _(u'Combat: Auto Aim Fix')
    tweak_tip = _(u'Increase Auto Aim settings to a level at which snipers '
                  u'can benefit from them.')
    tweak_key = (u'fAutoAimMaxDistance', u'fAutoAimScreenPercentage',
                 u'fAutoAimMaxDegrees', u'fAutoAimMissRatioLow',
                 u'fAutoAimMissRatioHigh', u'fAutoAimMaxDegreesMiss')
    tweak_choices = [(_(u'Harder'), 50000.0, -180.0, 1.1, 1.0, 1.3, 3.0)]

#------------------------------------------------------------------------------
class GmstTweak_Player_PipBoyLightKeypressDelay(_AGmstTweak):
    tweak_name = _(u'Player: PipBoy Light Keypress Delay')
    tweak_tip = _(u'Seconds of delay until the PipBoy light switches on.')
    tweak_key = (u'fPlayerPipBoyLightTimer',)
    tweak_choices = [(u'0.3',       0.3),
                     (u'0.4',       0.4),
                     (u'0.5',       0.5),
                     (u'0.6',       0.6),
                     (u'0.7',       0.7),
                     (u'[0.8]',     0.8),
                     (u'1.0',       1.0),
                     (_(u'Custom'), 0.8)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_VATSPlaybackDelay(_AGmstTweak):
    tweak_name = _(u'Combat: VATS Playback Delay')
    tweak_tip = _(u'Seconds of delay after the VATS Camera finished playback.')
    tweak_key = (u'fVATSPlaybackDelay',)
    tweak_choices = [(u'0.01',      0.01),
                     (u'0.05',      0.05),
                     (u'0.10',       0.1),
                     (u'[0.17]',    0.17),
                     (u'0.25',      0.25),
                     (_(u'Custom'), 0.17)]

#------------------------------------------------------------------------------
class GmstTweak_Combat_NPCDeathXPThreshold(_AGmstTweak):
    tweak_name = _(u'Combat: NPC Death XP Threshold')
    tweak_tip = _(u'Percentage of total damage you have to inflict in order '
                  u'to get XP.')
    tweak_key = (u'iXPDeathRewardHealthThreshold',)
    tweak_choices = [(u'0%',         0),
                     (u'25%',       25),
                     (u'[40%]',     40),
                     (u'50%',       50),
                     (u'75%',       75),
                     (_(u'Custom'), 40)]

#------------------------------------------------------------------------------
class GmstTweak_Hacking_MaximumNumberofWords(_AGmstTweak):
    tweak_name = _(u'Hacking: Maximum Number of Words')
    tweak_tip = _(u'The maximum number of words appearing in the terminal '
                  u'hacking mini-game.')
    tweak_key = (u'iHackingMaxWords',)
    tweak_choices = [(u'1',          1),
                     (u'4',          4),
                     (u'8',          8),
                     (u'12',        12),
                     (u'16',        16),
                     (u'[20]',      20),
                     (_(u'Custom'), 20)]

#------------------------------------------------------------------------------
class GmstTweak_Visuals_ShellCameraDistance(_AGmstTweak):
    tweak_name = _(u'Visuals: Shell Camera Distance')
    tweak_tip = _(u'Maximum distance at which gun arisings (shell case, '
                  u'particle, decal) show from camera.')
    tweak_key = (u'fGunParticleCameraDistance', u'fGunShellCameraDistance',
                 u'fGunDecalCameraDistance')
    tweak_choices = [(u'x 1.5',     3072.0, 768.0, 3072.0),
                     (u'x 2',      4096.0, 1024.0, 4096.0),
                     (u'x 3',      6144.0, 1536.0, 6144.0),
                     (u'x 4',      8192.0, 2048.0, 8192.0),
                     (u'x 5',    10240.0, 2560.0, 10240.0),
                     (_(u'Custom'), 2048.0, 512.0, 2048.0)]

#------------------------------------------------------------------------------
class GmstTweak_Visuals_ShellLitterTime(_AGmstTweak):
    tweak_name = _(u'Visuals: Shell Litter Time')
    tweak_tip = _(u'Time before shell cases fade away from cells.')
    tweak_key = (u'fGunShellLifetime',)
    tweak_choices = [(_(u'[10 Seconds]'),        10.0),
                     (_(u'20 Seconds'),          20.0),
                     (_(u'30 Seconds'),          30.0),
                     (_(u'1 Minute'),            60.0),
                     (_(u'3 Minutes'),          180.0),
                     (_(u'5 Minutes'),          300.0),
                     (_(u'Custom (in seconds)'), 10.0)]

#------------------------------------------------------------------------------
class GmstTweak_Visuals_ShellLitterCount(_AGmstTweak):
    tweak_name = _(u'Visuals: Shell Litter Count')
    tweak_tip = _(u'Maximum number of debris (shell case, etc) allowed in '
                  u'cell.')
    tweak_key = (u'iDebrisMaxCount',)
    tweak_choices = [(u'[50]',      50),
                     (u'100',      100),
                     (u'500',      500),
                     (u'1000',    1000),
                     (u'3000',    3000),
                     (_(u'Custom'), 50)]

#------------------------------------------------------------------------------
class GmstTweak_Hacking_TerminalSpeedAdjustment(_AGmstTweak):
    tweak_name = _(u'Hacking: Terminal Speed Adjustment')
    tweak_tip = _(u'The display speed at the time of terminal hacking.')
    tweak_key = (u'iHackingDumpRate', u'iHackingInputRate',
                 u'iHackingOutputRate', u'iHackingFlashOffDuration',
                 u'iHackingFlashOnDuration', u'iComputersDisplayRateMenus',
                 u'iComputersDisplayRateNotes')
    tweak_choices = [(u'x 2',       1000, 40, 134, 250, 375, 300, 300),
                     (u'x 4',       2000, 80, 268, 125, 188, 600, 600),
                     (u'[x 6]',     3000, 120, 402, 83, 126, 900, 900),
                     (_(u'Custom'), 3000, 120, 402, 83, 126, 900, 900)]

#------------------------------------------------------------------------------
class TweakSettingsPatcher(MultiTweaker):
    """Tweaks GLOB and GMST records in various ways."""
    _tweak_classes = {globals()[t] for t in bush.game.settings_tweaks}

    @classmethod
    def tweak_instances(cls):
        # Sort alphabetically first for aesthetic reasons
        tweak_classes = sorted(cls._tweak_classes, key=lambda c: c.tweak_name)
        # After that, sort to make tweaks instantiate & run in the right order
        tweak_classes.sort(key=lambda c: c.tweak_order)
        # Retrieve the defaults, which may be changed per game, for each tweak
        s_defaults = bush.game.settings_defaults
        return [t(s_defaults[t.__name__]) for t in tweak_classes]
