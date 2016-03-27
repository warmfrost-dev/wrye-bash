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
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2015 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================

#--Game ESM/ESP/BSA files
#  These filenames need to be in lowercase,
bethDataFiles = {
    #--Vanilla
    u'fallout4.esm',
    u'fallout4.cdx',
    u'fallout4 - animations.ba2',
    u'fallout4 - geometry.csg',
    u'fallout4 - interface.ba2',
    u'fallout4 - materials.ba2',
    u'fallout4 - meshes.ba2',
    u'fallout4 - meshesextra.ba2',
    u'fallout4 - misc.ba2',
    u'fallout4 - nvflex.ba2',
    u'fallout4 - shaders.ba2',
    u'fallout4 - sounds.ba2',
    u'fallout4 - startup.ba2',
    u'fallout4 - textures1.ba2',
    u'fallout4 - textures2.ba2',
    u'fallout4 - textures3.ba2',
    u'fallout4 - textures4.ba2',
    u'fallout4 - textures5.ba2',
    u'fallout4 - textures6.ba2',
    u'fallout4 - textures7.ba2',
    u'fallout4 - textures8.ba2',
    u'fallout4 - textures9.ba2',
    u'fallout4 - voices.ba2',
    u'dlcrobot.esm',
    u'dlcrobot.cdx',
    u'dlcrobot - geometry.csg',
    u'dlcrobot - main.ba2',
    u'dlcrobot - textures.ba2',
    u'dlcrobot - voices_en.ba2',
    u'dlcworkshop01.esm',
    u'dlcworkshop01.cdx',
    u'dlcworkshop01 - geometry.csg',
    u'dlcworkshop01 - main.ba2',
    u'dlcworkshop01 - textures.ba2',
    u'dlccoast.esm',
    u'dlccoast.cdx',
    u'dlccoast - geometry.csg',
    u'dlccoast - main.ba2',
    u'dlccoast - textures.ba2',
    u'dlccoast - voices_en.ba2',
    u'dlcworkshop02.esm',
    u'dlcworkshop02 - main.ba2',
    u'dlcworkshop02 - textures.ba2',
    u'dlcworkshop03.esm',
    u'dlcworkshop03.cdx',
    u'dlcworkshop03 - geometry.csg',
    u'dlcworkshop03 - main.ba2',
    u'dlcworkshop03 - textures.ba2',
    u'dlcworkshop03 - voices_en.ba2',
    u'dlcnukaworld.esm',
    u'dlcnukaworld.cdx',
    u'dlcnukaworld - geometry.csg',
    u'dlcnukaworld - main.ba2',
    u'dlcnukaworld - textures.ba2',
    u'dlcnukaworld - voices_en.ba2',
}

#--Every file in the Data directory from Bethsoft
allBethFiles = {
    # Section 1: Vanilla files
    u'Fallout4.esm',
    u'Fallout4.cdx',
    u'Fallout4 - Animations.ba2',
    u'Fallout4 - Geometry.csg',
    u'Fallout4 - Interface.ba2',
    u'Fallout4 - Materials.ba2',
    u'Fallout4 - Meshes.ba2',
    u'Fallout4 - MeshesExtra.ba2',
    u'Fallout4 - Misc.ba2',
    u'Fallout4 - Nvflex.ba2',
    u'Fallout4 - Shaders.ba2',
    u'Fallout4 - Sounds.ba2',
    u'Fallout4 - Startup.ba2',
    u'Fallout4 - Textures1.ba2',
    u'Fallout4 - Textures2.ba2',
    u'Fallout4 - Textures3.ba2',
    u'Fallout4 - Textures4.ba2',
    u'Fallout4 - Textures5.ba2',
    u'Fallout4 - Textures6.ba2',
    u'Fallout4 - Textures7.ba2',
    u'Fallout4 - Textures8.ba2',
    u'Fallout4 - Textures9.ba2',
    u'Fallout4 - Voices.ba2',
    u'DLCRobot.esm',
    u'DLCRobot.cdx',
    u'DLCRobot - Geometry.csg',
    u'DLCRobot - Main.ba2',
    u'DLCRobot - Textures.ba2',
    u'DLCRobot - Voices_en.ba2',
    u'DLCworkshop01.esm',
    u'DLCworkshop01.cdx',
    u'DLCworkshop01 - Geometry.csg',
    u'DLCworkshop01 - Main.ba2',
    u'DLCworkshop01 - Textures.ba2',
    u'DLCCoast.esm',
    u'DLCCoast.cdx',
    u'DLCCoast - Geometry.csg',
    u'DLCCoast - Main.ba2',
    u'DLCCoast - Textures.ba2',
    u'DLCCoast - Voices_en.ba2',
    u'DLCworkshop02.esm',
    u'DLCworkshop02 - Main.ba2',
    u'DLCworkshop02 - Textures.ba2',
    u'DLCworkshop03.esm',
    u'DLCworkshop03.cdx',
    u'DLCworkshop03 - Geometry.csg',
    u'DLCworkshop03 - Main.ba2',
    u'DLCworkshop03 - Textures.ba2',
    u'DLCworkshop03 - Voices_en.ba2',
    u'DLCNukaWorld.esm',
    u'DLCNukaWorld.cdx',
    u'DLCNukaWorld - Geometry.csg',
    u'DLCNukaWorld - Main.ba2',
    u'DLCNukaWorld - Textures.ba2',
    u'DLCNukaWorld - Voices_en.ba2',
    # Section 2: Video Clips
    u'Video\\AGILITY.bk2',
    u'Video\\CHARISMA.bk2',
    u'Video\\Endgame_FEMALE_A.bk2',
    u'Video\\Endgame_FEMALE_B.bk2',
    u'Video\\Endgame_MALE_A.bk2',
    u'Video\\Endgame_MALE_B.bk2',
    u'Video\\ENDURANCE.bk2',
    u'Video\\GameIntro_V3_B.bk2',
    u'Video\\INTELLIGENCE.bk2',
    u'Video\\Intro.bk2',
    u'Video\\LUCK.bk2',
    u'Video\\MainMenuLoop.bk2',
    u'Video\\PERCEPTION.bk2',
    u'Video\\STRENGTH.bk2',
    # Section 3: F4SE INI File
    u'F4SE\\f4se.ini',
    # Section 4: GECK files
	u'Scripts\\Source\\Base\\Base.zip',
	u'Scripts\\Source\\DLC01\\DLC01.zip',
	u'Scripts\\Source\\DLC02\\DLC02.zip',
	u'Scripts\\Source\\DLC03\\DLC03.zip',
	u'Scripts\\Source\\DLC04\\DLC04.zip',
	u'Scripts\\Source\\DLC05\\DLC05.zip',
	u'Scripts\\Source\\DLC06\\DLC06.zip',
	# Section 5: Other Files
	u'LSData\\DtC6dal.dat',
	u'LSData\\DtC6dl.dat',
	u'LSData\\Wt8S9bs.dat',
	u'LSData\\Wt8S9fs.dat',
	u'LSData\\Wt16M9bs.dat',
	u'LSData\\Wt16M9fs.dat',
}

# Function Info ---------------------------------------------------------------
conditionFunctionData = ( #--0: no param; 1: int param; 2: formid param
    (  0, 'GetWantBlocking', 0, 0, 0),
    (  1, 'GetDistance', 2, 0, 0),
    (  5, 'GetLocked', 0, 0, 0),
    (  6, 'GetPos', 1, 0, 0),
    (  8, 'GetAngle', 1, 0, 0),
    ( 10, 'GetStartingPos', 1, 0, 0),
    ( 11, 'GetStartingAngle', 1, 0, 0),
    ( 12, 'GetSecondsPassed', 0, 0, 0),
    ( 14, 'GetActorValue', 1, 0, 0),
    ( 18, 'GetCurrentTime', 0, 0, 0),
    ( 24, 'GetScale', 0, 0, 0),
    ( 25, 'IsMoving', 0, 0, 0),
    ( 26, 'IsTurning', 0, 0, 0),
    ( 27, 'GetLineOfSight', 2, 0, 0),
    ( 31, 'GetButtonPressed', 0, 0, 0), # Not in TES5Edit
    ( 32, 'GetInSameCell', 2, 0, 0),
    ( 35, 'GetDisabled', 0, 0, 0),
    ( 36, 'MenuMode', 1, 0, 0),
    ( 39, 'GetDisease', 0, 0, 0),
    ( 41, 'GetClothingValue', 0, 0, 0),
    ( 42, 'SameFaction', 2, 0, 0),
    ( 43, 'SameRace', 2, 0, 0),
    ( 44, 'SameSex', 2, 0, 0),
    ( 45, 'GetDetected', 2, 0, 0),
    ( 46, 'GetDead', 0, 0, 0),
    ( 47, 'GetItemCount', 2, 0, 0),
    ( 48, 'GetGold', 0, 0, 0),
    ( 49, 'GetSleeping', 0, 0, 0),
    ( 50, 'GetTalkedToPC', 0, 0, 0),
    ( 53, 'GetScriptVariable', 2, 1, 0),
    ( 56, 'GetQuestRunning', 2, 0, 0),
    ( 58, 'GetStage', 2, 0, 0),
    ( 59, 'GetStageDone', 2, 1, 0),
    ( 60, 'GetFactionRankDifference', 2, 2, 0),
    ( 61, 'GetAlarmed', 0, 0, 0),
    ( 62, 'IsRaining', 0, 0, 0),
    ( 63, 'GetAttacked', 0, 0, 0),
    ( 64, 'GetIsCreature', 0, 0, 0),
    ( 65, 'GetLockLevel', 0, 0, 0),
    ( 66, 'GetShouldAttack', 2, 0, 0),
    ( 67, 'GetInCell', 2, 0, 0),
    ( 68, 'GetIsClass', 2, 0, 0),
    ( 69, 'GetIsRace', 2, 0, 0),
    ( 70, 'GetIsSex', 2, 0, 0),
    ( 71, 'GetInFaction', 2, 0, 0),
    ( 72, 'GetIsID', 2, 0, 0),
    ( 73, 'GetFactionRank', 2, 0, 0),
    ( 74, 'GetGlobalValue', 2, 0, 0),
    ( 75, 'IsSnowing', 0, 0, 0),
    ( 77, 'GetRandomPercent', 0, 0, 0),
    ( 79, 'GetQuestVariable', 2, 1, 0),
    ( 80, 'GetLevel', 0, 0, 0),
    ( 81, 'IsRotating', 0, 0, 0),
    ( 83, 'GetLeveledEncounterValue', 1, 0, 0), # Not in TES5Edit
    ( 84, 'GetDeadCount', 2, 0, 0),
    ( 91, 'GetIsAlerted', 0, 0, 0),
    ( 98, 'GetPlayerControlsDisabled', 0, 0, 0),
    ( 99, 'GetHeadingAngle', 2, 0, 0),
    (101, 'IsWeaponMagicOut', 0, 0, 0),
    (102, 'IsTorchOut', 0, 0, 0),
    (103, 'IsShieldOut', 0, 0, 0),
    (105, 'IsActionRef', 2, 0, 0), # Not in TES5Edit
    (106, 'IsFacingUp', 0, 0, 0),
    (107, 'GetKnockedState', 0, 0, 0),
    (108, 'GetWeaponAnimType', 0, 0, 0),
    (109, 'IsWeaponSkillType', 1, 0, 0),
    (110, 'GetCurrentAIPackage', 0, 0, 0),
    (111, 'IsWaiting', 0, 0, 0),
    (112, 'IsIdlePlaying', 0, 0, 0),
    (116, 'IsIntimidatedbyPlayer', 0, 0, 0),
    (117, 'IsPlayerInRegion', 2, 0, 0),
    (118, 'GetActorAggroRadiusViolated', 0, 0, 0),
    (119, 'GetCrimeKnown', 1, 2, 0), # Not in TES5Edit
    (122, 'GetCrime', 2, 1, 0),
    (123, 'IsGreetingPlayer', 0, 0, 0),
    (125, 'IsGuard', 0, 0, 0),
    (127, 'HasBeenEaten', 0, 0, 0),
    (128, 'GetStaminaPercentage', 0, 0, 0),
    (129, 'GetPCIsClass', 2, 0, 0),
    (130, 'GetPCIsRace', 2, 0, 0),
    (131, 'GetPCIsSex', 2, 0, 0),
    (132, 'GetPCInFaction', 2, 0, 0),
    (133, 'SameFactionAsPC', 0, 0, 0),
    (134, 'SameRaceAsPC', 0, 0, 0),
    (135, 'SameSexAsPC', 0, 0, 0),
    (136, 'GetIsReference', 2, 0, 0),
    (141, 'IsTalking', 0, 0, 0),
    (142, 'GetWalkSpeed', 0, 0, 0),
    (143, 'GetCurrentAIProcedure', 0, 0, 0),
    (144, 'GetTrespassWarningLevel', 0, 0, 0),
    (145, 'IsTrespassing', 0, 0, 0),
    (146, 'IsInMyOwnedCell', 0, 0, 0),
    (147, 'GetWindSpeed', 0, 0, 0),
    (148, 'GetCurrentWeatherPercent', 0, 0, 0),
    (149, 'GetIsCurrentWeather', 2, 0, 0),
    (150, 'IsContinuingPackagePCNear', 0, 0, 0),
    (152, 'GetIsCrimeFaction', 2, 0, 0),
    (153, 'CanHaveFlames', 0, 0, 0),
    (154, 'HasFlames', 0, 0, 0),
    (157, 'GetOpenState', 0, 0, 0),
    (159, 'GetSitting', 0, 0, 0),
    (160, 'GetFurnitureMarkerID', 0, 0, 0), # Not in TES5Edit
    (161, 'GetIsCurrentPackage', 2, 0, 0),
    (162, 'IsCurrentFurnitureRef', 2, 0, 0),
    (163, 'IsCurrentFurnitureObj', 2, 0, 0),
    (167, 'GetFactionReaction', 2, 2, 0), # Not in TES5Edit
    (170, 'GetDayOfWeek', 0, 0, 0),
    (172, 'GetTalkedToPCParam', 2, 0, 0),
    (175, 'IsPCSleeping', 0, 0, 0),
    (176, 'IsPCAMurderer', 0, 0, 0),
    (180, 'HasSameEditorLocAsRef', 2, 2, 0),
    (181, 'HasSameEditorLocAsRefAlias', 2, 2, 0),
    (182, 'GetEquipped', 2, 0, 0),
    (185, 'IsSwimming', 0, 0, 0),
    (188, 'GetPCSleepHours', 0, 0, 0), # Not in TES5Edit
    (190, 'GetAmountSoldStolen', 0, 0, 0),
    (192, 'GetIgnoreCrime', 0, 0, 0),
    (193, 'GetPCExpelled', 2, 0, 0),
    (195, 'GetPCFactionMurder', 2, 0, 0),
    (197, 'GetPCEnemyofFaction', 2, 0, 0),
    (199, 'GetPCFactionAttack', 2, 0, 0),
    (203, 'GetDestroyed', 0, 0, 0),
    (205, 'GetActionRef', 0, 0, 0), # Not in TES5Edit
    (206, 'GetSelf', 0, 0, 0), # Not in TES5Edit
    (207, 'GetContainer', 0, 0, 0), # Not in TES5Edit
    (208, 'GetForceRun', 0, 0, 0), # Not in TES5Edit
    (210, 'GetForceSneak', 0, 0, 0), # Not in TES5Edit
    (214, 'HasMagicEffect', 2, 0, 0),
    (215, 'GetDefaultOpen', 0, 0, 0),
    (219, 'GetAnimAction', 0, 0, 0),
    (223, 'IsSpellTarget', 2, 0, 0),
    (224, 'GetVATSMode', 0, 0, 0),
    (225, 'GetPersuasionNumber', 0, 0, 0),
    (226, 'GetVampireFeed', 0, 0, 0),
    (227, 'GetCannibal', 0, 0, 0),
    (228, 'GetIsClassDefault', 2, 0, 0),
    (229, 'GetClassDefaultMatch', 0, 0, 0),
    (230, 'GetInCellParam', 2, 2, 0),
    (232, 'GetCombatTarget', 0, 0, 0), # Not in TES5Edit
    (233, 'GetPackageTarget', 0, 0, 0), # Not in TES5Edit
    (235, 'GetVatsTargetHeight', 0, 0, 0),
    (237, 'GetIsGhost', 0, 0, 0),
    (242, 'GetUnconscious', 0, 0, 0),
    (244, 'GetRestrained', 0, 0, 0),
    (246, 'GetIsUsedItem', 2, 0, 0),
    (247, 'GetIsUsedItemType', 2, 0, 0),
    (248, 'IsScenePlaying', 2, 0, 0),
    (249, 'IsInDialogueWithPlayer', 0, 0, 0),
    (250, 'GetLocationCleared', 2, 0, 0),
    (254, 'GetIsPlayableRace', 0, 0, 0),
    (255, 'GetOffersServicesNow', 0, 0, 0),
    (256, 'GetGameSetting', 1, 0, 0), # Not in TES5Edit
    (258, 'HasAssociationType', 2, 2, 0),
    (259, 'HasFamilyRelationship', 2, 0, 0),
    (261, 'HasParentRelationship', 2, 0, 0),
    (262, 'IsWarningAbout', 2, 0, 0),
    (263, 'IsWeaponOut', 0, 0, 0),
    (264, 'HasSpell', 2, 0, 0),
    (265, 'IsTimePassing', 0, 0, 0),
    (266, 'IsPleasant', 0, 0, 0),
    (267, 'IsCloudy', 0, 0, 0),
    (274, 'IsSmallBump', 0, 0, 0),
    (275, 'GetParentRef', 0, 0, 0), # Not in TES5Edit
    (277, 'GetBaseActorValue', 1, 0, 0),
    (278, 'IsOwner', 2, 0, 0),
    (280, 'IsCellOwner', 2, 2, 0),
    (282, 'IsHorseStolen', 0, 0, 0),
    (285, 'IsLeftUp', 0, 0, 0),
    (286, 'IsSneaking', 0, 0, 0),
    (287, 'IsRunning', 0, 0, 0),
    (288, 'GetFriendHit', 0, 0, 0),
    (289, 'IsInCombat', 1, 0, 0),
    (296, 'IsAnimPlaying', 2, 0, 0), # Not in TES5Edit
    (300, 'IsInInterior', 0, 0, 0),
    (303, 'IsActorsAIOff', 0, 0, 0), # Not in TES5Edit
    (304, 'IsWaterObject', 0, 0, 0),
    (305, 'GetPlayerAction', 0, 0, 0),
    (306, 'IsActorUsingATorch', 0, 0, 0),
    (309, 'IsXBox', 0, 0, 0),
    (310, 'GetInWorldspace', 2, 0, 0),
    (312, 'GetPCMiscStat', 1, 0, 0),
    (313, 'GetPairedAnimation', 0, 0, 0),
    (314, 'IsActorAVictim', 0, 0, 0),
    (315, 'GetTotalPersuasionNumber', 0, 0, 0),
    (318, 'GetIdleDoneOnce', 0, 0, 0),
    (320, 'GetNoRumors', 0, 0, 0),
    (323, 'GetCombatState', 0, 0, 0),
    (325, 'GetWithinPackageLocation', 2, 0, 0),
    (327, 'IsRidingMount', 0, 0, 0),
    (329, 'IsFleeing', 0, 0, 0),
    (332, 'IsInDangerousWater', 0, 0, 0),
    (338, 'GetIgnoreFriendlyHits', 0, 0, 0),
    (339, 'IsPlayersLastRiddenMount', 0, 0, 0),
    (353, 'IsActor', 0, 0, 0),
    (354, 'IsEssential', 0, 0, 0),
    (358, 'IsPlayerMovingIntoNewSpace', 0, 0, 0),
    (359, 'GetInCurrentLoc', 2, 0, 0),
    (360, 'GetInCurrentLocAlias', 2, 0, 0),
    (361, 'GetTimeDead', 0, 0, 0),
    (362, 'HasLinkedRef', 2, 0, 0),
    (363, 'GetLinkedRef', 2, 0, 0), # Not in TES5Edit
    (365, 'IsChild', 0, 0, 0),
    (366, 'GetStolenItemValueNoCrime', 2, 0, 0),
    (367, 'GetLastPlayerAction', 0, 0, 0),
    (368, 'IsPlayerActionActive', 1, 0, 0),
    (370, 'IsTalkingActivatorActor', 2, 0, 0),
    (372, 'IsInList', 2, 0, 0),
    (373, 'GetStolenItemValue', 2, 0, 0),
    (375, 'GetCrimeGoldViolent', 2, 0, 0),
    (376, 'GetCrimeGoldNonviolent', 2, 0, 0),
    (378, 'HasShout', 2, 0, 0),
    (381, 'GetHasNote', 2, 0, 0),
    (387, 'GetObjectiveFailed', 2, 1, 0), # Not in TES5Edit
    (390, 'GetHitLocation', 0, 0, 0),
    (391, 'IsPC1stPerson', 0, 0, 0),
    (396, 'GetCauseofDeath', 0, 0, 0),
    (397, 'IsLimbGone', 1, 0, 0),
    (398, 'IsWeaponInList', 2, 0, 0),
    (402, 'IsBribedbyPlayer', 0, 0, 0),
    (403, 'GetRelationshipRank', 2, 0, 0),
    (407, 'GetVATSValue', 1, 1, 0),
    (408, 'IsKiller', 2, 0, 0),
    (409, 'IsKillerObject', 2, 0, 0),
    (410, 'GetFactionCombatReaction', 2, 2, 0),
    (414, 'Exists', 2, 0, 0),
    (415, 'GetGroupMemberCount', 0, 0, 0),
    (416, 'GetGroupTargetCount', 0, 0, 0),
    (419, 'GetObjectiveCompleted', 2, 1, 0), # Not in TES5Edit
    (420, 'GetObjectiveDisplayed', 2, 1, 0), # Not in TES5Edit
    (425, 'GetIsFormType', 2, 0, 0), # Not in TES5Edit
    (426, 'GetIsVoiceType', 2, 0, 0),
    (427, 'GetPlantedExplosive', 0, 0, 0),
    (429, 'IsScenePackageRunning', 0, 0, 0),
    (430, 'GetHealthPercentage', 0, 0, 0),
    (432, 'GetIsObjectType', 2, 0, 0),
    (434, 'GetDialogueEmotion', 0, 0, 0),
    (435, 'GetDialogueEmotionValue', 0, 0, 0),
    (437, 'GetIsCreatureType', 1, 0, 0),
    (444, 'GetInCurrentLocFormList', 2, 0, 0),
    (445, 'GetInZone', 2, 0, 0),
    (446, 'GetVelocity', 1, 0, 0),
    (447, 'GetGraphVariableFloat', 1, 0, 0),
    (448, 'HasPerk', 2, 0, 0),
    (449, 'GetFactionRelation', 2, 0, 0),
    (450, 'IsLastIdlePlayed', 2, 0, 0),
    (453, 'GetPlayerTeammate', 0, 0, 0),
    (454, 'GetPlayerTeammateCount', 0, 0, 0),
    (458, 'GetActorCrimePlayerEnemy', 0, 0, 0),
    (459, 'GetCrimeGold', 2, 0, 0),
    (462, 'GetPlayerGrabbedRef', 0, 0, 0), # Not in TES5Edit
    (463, 'IsPlayerGrabbedRef', 2, 0, 0),
    (465, 'GetKeywordItemCount', 2, 0, 0),
    (467, 'GetBroadcastState', 0, 0, 0), # Not in TES5Edit
    (470, 'GetDestructionStage', 0, 0, 0),
    (473, 'GetIsAlignment', 2, 0, 0),
    (476, 'IsProtected', 0, 0, 0),
    (477, 'GetThreatRatio', 2, 0, 0),
    (479, 'GetIsUsedItemEquipType', 2, 0, 0),
    (480, 'GetPlayerName', 0, 0, 0), # Not in TES5Edit
    (487, 'IsCarryable', 0, 0, 0),
    (488, 'GetConcussed', 0, 0, 0),
    (491, 'GetMapMarkerVisible', 0, 0, 0),
    (493, 'PlayerKnows', 2, 0, 0),
    (494, 'GetPermanentActorValue', 1, 0, 0),
    (495, 'GetKillingBlowLimb', 0, 0, 0),
    (497, 'CanPayCrimeGold', 2, 0, 0),
    (499, 'GetDaysInJail', 0, 0, 0),
    (500, 'EPAlchemyGetMakingPoison', 0, 0, 0),
    (501, 'EPAlchemyEffectHasKeyword', 2, 0, 0),
    (503, 'GetAllowWorldInteractions', 0, 0, 0),
    (508, 'GetLastHitCritical', 0, 0, 0),
    (513, 'IsCombatTarget', 2, 0, 0),
    (515, 'GetVATSRightAreaFree', 2, 0, 0),
    (516, 'GetVATSLeftAreaFree', 2, 0, 0),
    (517, 'GetVATSBackAreaFree', 2, 0, 0),
    (518, 'GetVATSFrontAreaFree', 2, 0, 0),
    (519, 'GetIsLockBroken', 0, 0, 0),
    (520, 'IsPS3', 0, 0, 0),
    (521, 'IsWin32', 0, 0, 0),
    (522, 'GetVATSRightTargetVisible', 2, 0, 0),
    (523, 'GetVATSLeftTargetVisible', 2, 0, 0),
    (524, 'GetVATSBackTargetVisible', 2, 0, 0),
    (525, 'GetVATSFrontTargetVisible', 2, 0, 0),
    (528, 'IsInCriticalStage', 2, 0, 0),
    (530, 'GetXPForNextLevel', 0, 0, 0),
    (533, 'GetInfamy', 2, 0, 0),
    (534, 'GetInfamyViolent', 2, 0, 0),
    (535, 'GetInfamyNonViolent', 2, 0, 0),
    (543, 'GetQuestCompleted', 2, 0, 0),
    (547, 'IsGoreDisabled', 0, 0, 0),
    (550, 'IsSceneActionComplete', 2, 1, 0),
    (552, 'GetSpellUsageNum', 2, 0, 0),
    (554, 'GetActorsInHigh', 0, 0, 0),
    (555, 'HasLoaded3D', 0, 0, 0),
    (559, 'IsImageSpaceActive', 2, 0, 0), # Not in TES5Edit
    (560, 'HasKeyword', 2, 0, 0),
    (561, 'HasRefType', 2, 0, 0),
    (562, 'LocationHasKeyword', 2, 0, 0),
    (563, 'LocationHasRefType', 2, 0, 0),
    (565, 'GetIsEditorLocation', 2, 0, 0),
    (566, 'GetIsAliasRef', 2, 0, 0),
    (567, 'GetIsEditorLocAlias', 2, 0, 0),
    (568, 'IsSprinting', 0, 0, 0),
    (569, 'IsBlocking', 0, 0, 0),
    (570, 'HasEquippedSpell', 2, 0, 0),
    (571, 'GetCurrentCastingType', 2, 0, 0),
    (572, 'GetCurrentDeliveryType', 2, 0, 0),
    (574, 'GetAttackState', 0, 0, 0),
    (575, 'GetAliasedRef', 2, 0, 0), # Not in TES5Edit
    (576, 'GetEventData', 2, 2, 0),
    (577, 'IsCloserToAThanB', 2, 2, 0),
    (579, 'GetEquippedShout', 2, 0, 0),
    (580, 'IsBleedingOut', 0, 0, 0),
    (584, 'GetRelativeAngle', 2, 1, 0),
    (589, 'GetMovementDirection', 0, 0, 0),
    (590, 'IsInScene', 0, 0, 0),
    (591, 'GetRefTypeDeadCount', 2, 2, 0),
    (592, 'GetRefTypeAliveCount', 2, 2, 0),
    (594, 'GetIsFlying', 0, 0, 0),
    (595, 'IsCurrentSpell', 2, 2, 0),
    (596, 'SpellHasKeyword', 2, 2, 0),
    (597, 'GetEquippedItemType', 2, 0, 0),
    (598, 'GetLocationAliasCleared', 2, 0, 0),
    (600, 'GetLocAliasRefTypeDeadCount', 2, 2, 0),
    (601, 'GetLocAliasRefTypeAliveCount', 2, 2, 0),
    (602, 'IsWardState', 2, 0, 0),
    (603, 'IsInSameCurrentLocAsRef', 2, 2, 0),
    (604, 'IsInSameCurrentLocAsRefAlias', 2, 2, 0),
    (605, 'LocAliasIsLocation', 2, 2, 0),
    (606, 'GetKeywordDataForLocation', 2, 2, 0),
    (608, 'GetKeywordDataForAlias', 2, 2, 0),
    (610, 'LocAliasHasKeyword', 2, 2, 0),
    (611, 'IsNullPackageData', 1, 0, 0),
    (612, 'GetNumericPackageData', 1, 0, 0),
    (613, 'IsFurnitureAnimType', 2, 0, 0),
    (614, 'IsFurnitureEntryType', 2, 0, 0),
    (615, 'GetHighestRelationshipRank', 0, 0, 0),
    (616, 'GetLowestRelationshipRank', 0, 0, 0),
    (617, 'HasAssociationTypeAny', 2, 0, 0),
    (618, 'HasFamilyRelationshipAny', 0, 0, 0),
    (619, 'GetPathingTargetOffset', 1, 0, 0),
    (620, 'GetPathingTargetAngleOffset', 1, 0, 0),
    (621, 'GetPathingTargetSpeed', 0, 0, 0),
    (622, 'GetPathingTargetSpeedAngle', 1, 0, 0),
    (623, 'GetMovementSpeed', 0, 0, 0),
    (624, 'GetInContainer', 2, 0, 0),
    (625, 'IsLocationLoaded', 2, 0, 0),
    (626, 'IsLocAliasLoaded', 2, 0, 0),
    (627, 'IsDualCasting', 0, 0, 0),
    (629, 'GetVMQuestVariable', 2, 1, 0),
    (630, 'GetVMScriptVariable', 2, 1, 0),
    (631, 'IsEnteringInteractionQuick', 0, 0, 0),
    (632, 'IsCasting', 0, 0, 0),
    (633, 'GetFlyingState', 0, 0, 0),
    (635, 'IsInFavorState', 0, 0, 0),
    (636, 'HasTwoHandedWeaponEquipped', 0, 0, 0),
    (637, 'IsExitingInstant', 0, 0, 0),
    (638, 'IsInFriendStatewithPlayer', 0, 0, 0),
    (639, 'GetWithinDistance', 2, 1, 0),
    (640, 'GetActorValuePercent', 1, 0, 0),
    (641, 'IsUnique', 0, 0, 0),
    (642, 'GetLastBumpDirection', 0, 0, 0),
    (644, 'IsInFurnitureState', 2, 0, 0),
    (645, 'GetIsInjured', 0, 0, 0),
    (646, 'GetIsCrashLandRequest', 0, 0, 0),
    (647, 'GetIsHastyLandRequest', 0, 0, 0),
    (650, 'IsLinkedTo', 2, 2, 0),
    (651, 'GetKeywordDataForCurrentLocation', 2, 0, 0),
    (652, 'GetInSharedCrimeFaction', 2, 0, 0),
    (653, 'GetBribeAmount', 0, 0, 0), # Not in TES5Edit
    (654, 'GetBribeSuccess', 0, 0, 0),
    (655, 'GetIntimidateSuccess', 0, 0, 0),
    (656, 'GetArrestedState', 0, 0, 0),
    (657, 'GetArrestingActor', 0, 0, 0),
    (659, 'EPTemperingItemIsEnchanted', 0, 0, 0),
    (660, 'EPTemperingItemHasKeyword', 2, 0, 0),
    (661, 'GetReceivedGiftValue', 0, 0, 0), # Not in TES5Edit
    (662, 'GetGiftGivenValue', 0, 0, 0), # Not in TES5Edit
    (664, 'GetReplacedItemType', 2, 0, 0),
    (672, 'IsAttacking', 0, 0, 0),
    (673, 'IsPowerAttacking', 0, 0, 0),
    (674, 'IsLastHostileActor', 0, 0, 0),
    (675, 'GetGraphVariableInt', 1, 0, 0),
    (676, 'GetCurrentShoutVariation', 0, 0, 0),
    (678, 'ShouldAttackKill', 2, 0, 0),
    (680, 'GetActivationHeight', 0, 0, 0),
    (681, 'EPModSkillUsage_IsAdvanceSkill', 1, 0, 0),
    (682, 'WornHasKeyword', 2, 0, 0),
    (683, 'GetPathingCurrentSpeed', 0, 0, 0),
    (684, 'GetPathingCurrentSpeedAngle', 1, 0, 0),
    (691, 'EPModSkillUsage_AdvancedObjectHasKeyword', 2, 0, 0),
    (692, 'EPModSkillUsage_IsAdvanceAction', 2, 0, 0),
    (693, 'EPMagic_SpellHasKeyword', 2, 0, 0),
    (694, 'GetNoBleedoutRecovery', 0, 0, 0),
    (696, 'EPMagic_SpellHasSkill', 1, 0, 0),
    (697, 'IsAttackType', 2, 0, 0),
    (698, 'IsAllowedToFly', 0, 0, 0),
    (699, 'HasMagicEffectKeyword', 2, 0, 0),
    (700, 'IsCommandedActor', 0, 0, 0),
    (701, 'IsStaggered', 0, 0, 0),
    (702, 'IsRecoiling', 0, 0, 0),
    (703, 'IsExitingInteractionQuick', 0, 0, 0),
    (704, 'IsPathing', 0, 0, 0),
    (705, 'GetShouldHelp', 2, 0, 0),
    (706, 'HasBoundWeaponEquipped', 2, 0, 0),
    (707, 'GetCombatTargetHasKeyword', 2, 0, 0),
    (709, 'GetCombatGroupMemberCount', 0, 0, 0),
    (710, 'IsIgnoringCombat', 0, 0, 0),
    (711, 'GetLightLevel', 0, 0, 0),
    (713, 'SpellHasCastingPerk', 2, 0, 0),
    (714, 'IsBeingRidden', 0, 0, 0),
    (715, 'IsUndead', 0, 0, 0),
    (716, 'GetRealHoursPassed', 0, 0, 0),
    (718, 'IsUnlockedDoor', 0, 0, 0),
    (719, 'IsHostileToActor', 2, 0, 0),
    (720, 'GetTargetHeight', 0, 0, 0),
    (721, 'IsPoison', 0, 0, 0),
    (722, 'WornApparelHasKeywordCount', 2, 0, 0),
    (723, 'GetItemHealthPercent', 0, 0, 0),
    (724, 'EffectWasDualCast', 0, 0, 0),
    (725, 'GetKnockStateEnum', 0, 0, 0),
    (726, 'DoesNotExist', 0, 0, 0),
    (730, 'IsOnFlyingMount', 0, 0, 0),
    (731, 'CanFlyHere', 0, 0, 0),
    (732, 'IsFlyingMountPatrolQueud', 0, 0, 0),
    (733, 'IsFlyingMountFastTravelling', 0, 0, 0),

    # extended by SKSE
    (1024, 'GetSKSEVersion', 0, 0, 0),
    (1025, 'GetSKSEVersionMinor', 0, 0, 0),
    (1026, 'GetSKSEVersionBeta', 0, 0, 0),
    (1027, 'GetSKSERelease', 0, 0, 0),
    (1028, 'ClearInvalidRegistrations', 0, 0, 0),
    )
allConditions = set(entry[0] for entry in conditionFunctionData)
fid1Conditions = set(entry[0] for entry in conditionFunctionData if entry[2] == 2)
fid2Conditions = set(entry[0] for entry in conditionFunctionData if entry[3] == 2)
# Skip 3 and 4 because it needs to be set per runOn
fid5Conditions = set(entry[0] for entry in conditionFunctionData if entry[4] == 2)

#--List of GMST's in the main plugin (Fallout4.esm) that have 0x00000000
#  as the form id.  Any GMST as such needs it Editor Id listed here.
gmstEids = [
    ## TODO: Initial inspection did not seem to have any null FormID GMST's,
    ## double check before enabling the GMST Tweaker
    ]

"""
GLOB record tweaks used by patcher.patchers.multitweak_settings.GmstTweaker

Each entry is a tuple in the following format:
  (DisplayText, MouseoverText, GLOB EditorID, Option1, Option2, ..., OptionN)
  -EditorID can be a plain string, or a tuple of multiple Editor IDs.  If
  it's a tuple, then Value (below) must be a tuple of equal length, providing
  values for each GLOB
Each Option is a tuple:
  (DisplayText, Value)
  - If you enclose DisplayText in brackets like this: _(u'[Default]'),
  then the patcher will treat this option as the default value.
  - If you use _(u'Custom') as the entry, the patcher will bring up a number
  input dialog

To make a tweak Enabled by Default, enclose the tuple entry for the tweak in
a list, and make a dictionary as the second list item with {'defaultEnabled
':True}. See the UOP Vampire face fix for an example of this (in the GMST
Tweaks)
"""
GlobalsTweaks = list()

"""
GMST record tweaks used by patcher.patchers.multitweak_settings.GmstTweaker

Each entry is a tuple in the following format:
  (DisplayText, MouseoverText, GMST EditorID, Option1, Option2, ..., OptionN)
  - EditorID can be a plain string, or a tuple of multiple Editor IDs. If
  it's a tuple, then Value (below) must be a tuple of equal length, providing
  values for each GMST
Each Option is a tuple:
  (DisplayText, Value)
  - If you enclose DisplayText in brackets like this: _(u'[Default]'),
  then the patcher will treat this option as the default value.
  - If you use _(u'Custom') as the entry, the patcher will bring up a number
  input dialog

To make a tweak Enabled by Default, enclose the tuple entry for the tweak in
a list, and make a dictionary as the second list item with {'defaultEnabled
':True}. See the UOP Vampire facefix for an example of this (in the GMST
Tweaks)
"""
GmstTweaks = list()

#------------------------------------------------------------------------------
# ListsMerger
#------------------------------------------------------------------------------
listTypes = ('LVLI','LVLN',)
#------------------------------------------------------------------------------
# NamesPatcher
#------------------------------------------------------------------------------
# remaining to add: 'PERK', 'RACE',
namesTypes = set()
#------------------------------------------------------------------------------
# ItemPrices Patcher
#------------------------------------------------------------------------------
pricesTypes = dict()

#------------------------------------------------------------------------------
# StatsImporter
#------------------------------------------------------------------------------
statsTypes = dict()
statsHeaders = tuple()

#------------------------------------------------------------------------------
# SoundPatcher
#------------------------------------------------------------------------------
# Needs longs in SoundPatcher
soundsLongsTypes = {'ACTI', 'ADDN', 'ALCH', 'AMMO', 'APPA', 'ARMA', 'ARMO',
                    'ASPC', 'BOOK', 'CONT', 'DOOR', 'EFSH', 'EXPL', 'FLOR',
                    'HAZD', 'INGR', 'IPCT', 'KEYM', 'LIGH', 'MGEF', 'MISC',
                    'MSTT', 'SCRL', 'SLGM', 'SNCT', 'SNDR', 'SOPM', 'SOUN',
                    'TACT', 'TREE', 'WATR', 'WEAP', 'WTHR'}
soundsTypes = {
    "ACTI": ('dropSound','pickupSound',),
    "ADDN": ('ambientSound',),
    "ALCH": ('dropSound','pickupSound','soundConsume',),
    "AMMO": ('pickupSound','dropSound',),
    "APPA": ('pickupSound','dropSound',),
    "ARMA": ('footstepSound',),
    "ARMO": ('pickupSound','dropSound',),
    "ASPC": ('ambientSound','regionData','reverb',),
    "BOOK": ('pickupSound','dropSound',),
    "CONT": ('soundOpen','soundClose',),
    "DOOR": ('soundOpen','soundClose','soundLoop',),
    "EFSH": ('ambientSound',),
    "EXPL": ('sound1','sound2',),
    "FLOR": ('harvestSound',),
    "HAZD": ('sound',),
    "INGR": ('pickupSound','dropSound',),
    "IPCT": ('sound1','sound2',),
    "KEYM": ('pickupSound','dropSound',),
    "LIGH": ('sound',),
    #Needs to loop over all the sounds
    "MGEF": ('sounds',),
    # "REGN": ('entries',),
    "MISC": ('pickupSound','dropSound',),
    "MSTT": ('sound',),
    "SCRL": ('pickupSound','dropSound',),
    "SLGM": ('pickupSound','dropSound',),
    "SNCT": ('parent','staticVolumeMultiplier',),
    # Sounds does not need to loop here
    "SNDR": ('category','outputModel','sounds','looping','rumbleSendValue',
             'pctFrequencyShift','pctFrequencyVariance','priority',
             'dbVariance','staticAttenuation',),
    "SOPM": ('reverbSendpct','outputType','ch0_l','ch0_r','ch0_c','ch0_lFE',
             'ch0_rL','ch0_rR','ch0_bL','ch0_bR','ch1_l','ch1_r','ch1_c',
             'ch1_lFE','ch1_rL','ch1_rR','ch1_bL','ch1_bR','ch2_l','ch2_r',
             'ch2_c','ch2_lFE','ch2_rL','ch2_rR','ch2_bL','ch2_bR',
             'minDistance','maxDistance','curve1','curve2','curve3',
             'curve4','curve5',),
    "SOUN": ('soundDescriptor',),
    "TACT": ('soundLoop',),
    "TREE": ('harvestSound',),
    "WATR": ('openSound',),
    "WEAP": ('pickupSound','dropSound','attackSound','attackSound2D',
             'attackLoopSound','attackFailSound','idleSound',
             'equipSound','unequipSound','detectionSoundLevel',),
    #Needs to loop over all the sounds
    "WTHR": ('sounds',),
}
soundsFidTypes = {
}

#------------------------------------------------------------------------------
# Strings SoundPatcher
#------------------------------------------------------------------------------
stringSoundsRecs = ()
#------------------------------------------------------------------------------
# CellImporter
#------------------------------------------------------------------------------
cellAutoKeys = {u'C.Acoustic', u'C.Climate', u'C.Light', u'C.Location',
                u'C.Music', u'C.Name', u'C.Owner', u'C.RecordFlags',
                u'C.Regions', u'C.SkyLighting', u'C.Water'}

cellRecAttrs = {
    u'C.Acoustic': ('acousticSpace',),
    u'C.Climate': ('climate',),
    u'C.Encounter': ('encounterZone',),
    u'C.ImageSpace': ('imageSpace',),
    u'C.Light': ('ambientRed','ambientGreen','ambientBlue','unused1',
         'directionalRed','directionalGreen','directionalBlue','unused2',
         'fogRed','fogGreen','fogBlue','unused3',
         'fogNear','fogFar','directionalXY','directionalZ',
         'directionalFade','fogClip','fogPower',
         'redXplus','greenXplus','blueXplus','unknownXplus', # 'X+'
         'redXminus','greenXminus','blueXminus','unknownXminus', # 'X-'
         'redYplus','greenYplus','blueYplus','unknownYplus', # 'Y+'
         'redYminus','greenYminus','blueYminus','unknownYminus', # 'Y-'
         'redZplus','greenZplus','blueZplus','unknownZplus', # 'Z+'
         'redZminus','greenZminus','blueZminus','unknownZminus', # 'Z-'
         'redSpec','greenSpec','blueSpec','unknownSpec', # Specular Color Values
         'fresnelPower', # Fresnel Power
         'fogColorFarRed','fogColorFarGreen','fogColorFarBlue','unused4',
         'fogMax','lightFadeBegin','lightFadeEnd','inherits','lightTemplate',),
    u'C.Location': ('location',),
    u'C.Music': ('music',),
    u'C.Name': ('full',),
    u'C.Owner': ('ownership',),
    u'C.RecordFlags': ('flags1',), # Yes seems funky but thats the way it is
    u'C.Regions': ('regions',),
    u'C.Water': ('water','waterHeight','waterNoiseTexture','waterEnvironmentMap',),
}
cellRecFlags = {
    u'C.Acoustic': '',
    u'C.Climate': 'showSky',
    u'C.Encounter': '',
    u'C.ImageSpace': '',
    u'C.Light': '',
    u'C.Location': '',
    u'C.Music': '',
    u'C.Name': '',
    u'C.Owner': 'publicPlace',
    u'C.RecordFlags': '',
    u'C.Regions': '',
    u'C.SkyLighting': 'useSkyLighting',
    u'C.Water': 'hasWater',
}
#------------------------------------------------------------------------------
# GraphicsPatcher
#------------------------------------------------------------------------------
graphicsLongsTypes = {'ACTI', 'ALCH', 'AMMO', 'APPA', 'ARMA', 'ARMO', 'BOOK',
                      'CLAS', 'CONT', 'DOOR', 'EFSH', 'FLOR', 'FURN', 'GRAS',
                      'INGR', 'KEYM', 'LIGH', 'LSCR', 'SLGM', 'STAT', 'TREE',
                      'WEAP', 'WTHR', 'MGEF'}
graphicsTypes = {
    "ACTI": ('model',),
    "ALCH": ('iconPath','model',),
    "AMMO": ('iconPath','model',),
    "APPA": ('iconPath','model',),
    "ARMA": ('male_model','female_model','male_model_1st','female_model_1st',),
    "ARMO": ('model2','maleIconPath','model4','femaleIconPath','addons',),
    "BOOK": ('iconPath','model','inventoryArt',),
    "CLAS": ('iconPath',),
    "CONT": ('model',),
    "DOOR": ('model',),
    "EFSH": ('unused1','memSBlend','memBlendOp','memZFunc','fillRed',
    'fillGreen','fillBlue','unused2','fillAlphaIn','fillFullAlpha',
    'fillAlphaOut','fillAlphaRatio','fillAlphaAmp','fillAlphaPulse',
    'fillAnimSpeedU','fillAnimSpeedV','edgeEffectOff','edgeRed',
    'edgeGreen','edgeBlue','unused3','edgeAlphaIn','edgeFullAlpha',
    'edgeAlphaOut','edgeAlphaRatio','edgeAlphaAmp','edgeAlphaPulse',
    'fillFullAlphaRatio','edgeFullAlphaRatio','memDestBlend',
    'partSourceBlend','partBlendOp','partZTestFunc','partDestBlend',
    'partBSRampUp','partBSFull','partBSRampDown','partBSRatio',
    'partBSPartCount','partBSLifetime','partBSLifetimeDelta',
    'partSSpeedNorm','partSAccNorm','partSVel1','partSVel2',
    'partSVel3','partSAccel1','partSAccel2','partSAccel3',
    'partSKey1','partSKey2','partSKey1Time','partSKey2Time',
    'key1Red','key1Green','key1Blue','unused4','key2Red',
    'key2Green','key2Blue','unused5','key3Red','key3Green',
    'key3Blue','unused6','colorKey1Alpha','colorKey2Alpha',
    'colorKey3Alpha','colorKey1KeyTime','colorKey2KeyTime',
    'colorKey3KeyTime','partSSpeedNormDelta','partSSpeedRotDeg',
    'partSSpeedRotDegDelta','partSRotDeg','partSRotDegDelta',
    'addonModels','holesStart','holesEnd','holesStartVal',
    'holesEndVal','edgeWidthAlphaUnit','edgeAlphRed',
    'edgeAlphGreen','edgeAlphBlue','unused7','expWindSpeed',
    'textCountU','textCountV','addonModelIn','addonModelOut',
    'addonScaleStart','addonScaleEnd','addonScaleIn','addonScaleOut',
    'ambientSound','key2FillRed','key2FillGreen',
    'key2FillBlue','unused8','key3FillRed','key3FillGreen',
    'key3FillBlue','unused9','key1ScaleFill','key2ScaleFill',
    'key3ScaleFill','key1FillTime','key2FillTime','key3FillTime',
    'colorScale','birthPosOffset','birthPosOffsetRange','startFrame',
    'startFrameVariation','endFrame','loopStartFrame',
    'loopStartVariation','frameCount','frameCountVariation',
    'flags','fillTextScaleU',
    'fillTextScaleV','sceneGraphDepthLimit',),
    "FLOR": ('model',),
    "FURN": ('model',),
    "GRAS": ('model',),
    "INGR": ('iconPath','model',),
    "KEYM": ('iconPath','model',),
    "LIGH": ('iconPath','model',),
    "LSCR": ('iconPath',),
    "SLGM": ('iconPath','model',),
    "STAT": ('model',),
    "TREE": ('model',),
    "WEAP": ('model1','model2','iconPath','firstPersonModelObject',),
    "WTHR": ('wthrAmbientColors',),
}
graphicsFidTypes = {
    "MGEF": ('castingLight','hitShader','enchantShader',)
}
graphicsModelAttrs = ('model',)
#------------------------------------------------------------------------------
# Inventory Patcher
#------------------------------------------------------------------------------
inventoryTypes = ('NPC_','CONT',)

# Record type to name dictionary
record_type_name = {}

# xEdit menu string and key for expert setting
xEdit_expert = (_(u'FO4Edit Expert'), 'fo4View.iKnowWhatImDoing')
