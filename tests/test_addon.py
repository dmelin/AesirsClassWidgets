"""Run with Python and lupa: python -m pip install lupa; python tests/test_addon.py."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.test-libs'))
from lupa.lua51 import LuaRuntime


class HunterBarTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT / 'tests' / 'bootstrap.lua').read_text())
        self.lua.execute((ROOT / 'tests' / 'hunter_mock.lua').read_text())
        self.lua.execute((ROOT / 'Core.lua').read_text(), 'AesirsClassWidgets', self.lua.globals().A)
        self.lua.execute((ROOT / 'Widgets' / 'HunterPetXP.lua').read_text(), 'AesirsClassWidgets', self.lua.globals().A)
        self.lua.execute((ROOT / 'Widgets' / 'Hunter.lua').read_text(), 'AesirsClassWidgets', self.lua.globals().A)

    def check(self, code):
        self.lua.execute(code)

    def test_unknown_optional_event_cannot_abort_toolbar_loading(self):
        self.check('invalidEvents.SPELL_TEXT_UPDATE=true')
        self.check('''
            hevent("PLAYER_LOGIN"); assert(widgets.AesirsClassWidgetsHunterBar)
            assert(not hunterEvents.registered.LEARNED_SPELL_IN_TAB)
            assert(not hunterEvents.registered.SPELL_TEXT_UPDATE)
            assert(hunterEvents.registered.SPELLS_CHANGED)
        ''')

    def test_registry_starts_only_matching_class_modules(self):
        self.check('''
            A.RegisterClassWidget("MAGE", "mage", function() mageStarted=true end)
            A.RegisterClassWidget("HUNTER", "testHunter", function() hunterStarted=true end)
            hevent("PLAYER_LOGIN")
            assert(hunterStarted and not mageStarted)
            A.WidgetSettings("mage").test="separate"
            assert(not A.WidgetSettings("hunter").test)
        ''')

    def test_migrates_legacy_positions_without_sharing_settings(self):
        self.check('''
            AesirsQualityOfLifeDB={hunterPositions={["2:Test"]={x=700,y=420}}}
            hevent("PLAYER_LOGIN")
            local hub=widgets.AesirsClassWidgetsHunterBar
            assert(hub.x==700 and hub.y==420)
            local positions=AesirsClassWidgetsDB.widgets.hunter.positions
            positions["2:Test"].x=710
            assert(AesirsQualityOfLifeDB.hunterPositions["2:Test"].x==700)
        ''')

    def test_existing_widget_positions_are_not_overwritten(self):
        self.check('''
            AesirsQualityOfLifeDB={hunterPositions={["2:Test"]={x=700,y=420}}}
            AesirsClassWidgetsDB={widgets={hunter={positions={["2:Test"]={x=600,y=350}}}}}
            hevent("PLAYER_LOGIN")
            assert(widgets.AesirsClassWidgetsHunterBar.x==600)
        ''')

    def test_hunter_only_and_class_icon(self):
        self.check('''
            class="MAGE"; hevent("PLAYER_LOGIN"); assert(not widgets.AesirsClassWidgetsHunterBar)
            class="HUNTER"; hevent("PLAYER_LOGIN")
            assert(widgets.AesirsClassWidgetsHunterBar.icon.coords[2]==0.25)
        ''')

    def test_nested_menus_keep_main_fan_and_exclude_each_other(self):
        self.check('''
            hevent("PLAYER_LOGIN"); click("AesirsClassWidgetsHunterBar")
            local hub=widgets.AesirsClassWidgetsHunterBar
            assert(hub.refs.primary:IsShown())
            click("AesirsClassWidgetsTrackingMenu"); assert(hub.refs.tracking:IsShown())
            click("AesirsClassWidgetsAspectMenu")
            assert(hub.refs.primary:IsShown() and hub.refs.aspects:IsShown() and not hub.refs.tracking:IsShown())
            click("AesirsClassWidgetsTrackingMenu")
            assert(hub.refs.primary:IsShown() and hub.refs.tracking:IsShown() and not hub.refs.aspects:IsShown())
            click("AesirsClassWidgetsHunterBar")
            assert(not hub.refs.primary:IsShown() and not hub.refs.tracking:IsShown())
        ''')

    def test_escape_closes_the_dial_in_combat_and_releases_the_binding(self):
        self.check('''
            hevent("PLAYER_LOGIN")
            local hub=widgets.AesirsClassWidgetsHunterBar
            assert(not pressKey("ESCAPE"))
            combat=true
            for _, name in ipairs({"Tracking", "Aspect"}) do
                click(hub.name)
                click("AesirsClassWidgets"..name.."Menu")
                assert(pressKey("ESCAPE"))
                assert(not hub.refs.primary:IsShown())
                assert(not hub.refs.tracking:IsShown() and not hub.refs.aspects:IsShown())
                assert(not pressKey("ESCAPE"))
            end
        ''')

    def test_each_fan_animates_from_its_parent_button(self):
        self.check('''
            learned[100]=true; learned[13165]=true
            trackingTypes={{spellID=100,name="Track Beasts",texture=1}}
            hevent("PLAYER_LOGIN")
            local hub=widgets.AesirsClassWidgetsHunterBar
            local tracking=widgets.AesirsClassWidgetsTrackingMenu
            local trackSpell=widgets.AesirsClassWidgetsTracking1
            local aspects=widgets.AesirsClassWidgetsAspectMenu
            local aspectSpell=widgets.AesirsClassWidgetsAspect1

            local function checkAnimation(button, x, y)
                local animation=button.fanAnimation
                local slide=animation.animations.Translation
                assert(animation.playing and animation.reverse)
                assert(math.abs(button.x+slide.x-x)<1e-8 and math.abs(button.y+slide.y-y)<1e-8)
            end

            combat=true
            click(hub.name)
            checkAnimation(tracking, 0, 0)
            click(tracking.name)
            checkAnimation(trackSpell, tracking.x, tracking.y)
            click(aspects.name)
            assert(not trackSpell.fanAnimation.playing)
            checkAnimation(aspectSpell, aspects.x, aspects.y)
            pressKey("ESCAPE")
            assert(not aspectSpell.fanAnimation.playing)
            click(hub.name)
            checkAnimation(tracking, 0, 0)
        ''')

    def test_escape_fans_in_the_submenu_then_the_main_dial(self):
        self.check('''
            learned[100]=true
            trackingTypes={{spellID=100,name="Track Beasts",texture=1}}
            hevent("PLAYER_LOGIN")
            local hub=widgets.AesirsClassWidgetsHunterBar
            local tracking=widgets.AesirsClassWidgetsTrackingMenu
            local spell=widgets.AesirsClassWidgetsTracking1
            combat=true
            click(hub.name)
            click(tracking.name)
            assert(pressKey("ESCAPE"))
            assert(not tracking:IsVisible() and not spell:IsVisible())

            local submenu=spell.closeGhost
            local main=tracking.closeGhost
            assert(submenu:IsShown() and main:IsShown())
            assert(submenu.slide.delay==0 and main.slide.delay==submenu.slide.duration)
            assert(submenu.slide.duration==spell.fanSlide.duration*0.6)
            assert(submenu.slide.x==spell.fanSlide.x and submenu.slide.y==spell.fanSlide.y)
            submenu.animation.OnFinished()
            assert(not submenu:IsShown() and main:IsShown())

            click(hub.name)
            assert(not main:IsShown() and not main.animation.playing)
            click(hub.name)
            assert(main:IsShown() and main.slide.delay==0)
        ''')

    def test_only_known_tracking_and_aspects_and_highest_pet_rank(self):
        self.check('''
            learned[13165]=true; learned[6991]=true; learned[100]=true
            trackingTypes={{spellID=100,name="Track Beasts",texture=1},{spellID=101,name="Unknown",texture=2}}
            spellNames[13543]="Mend Pet"
            spellbook={{spellID=136,name="Mend Pet",lowRank=true},{spellID=13543,name="Mend Pet"}}
            hevent("PLAYER_LOGIN")
            assert(widgets.AesirsClassWidgetsTracking1.attributes.spell==100 and not widgets.AesirsClassWidgetsTracking2)
            assert(widgets.AesirsClassWidgetsAspect1.attributes.spell==13165 and not widgets.AesirsClassWidgetsAspect2)
            assert(widgets.AesirsClassWidgetsPetmend.attributes.spell==13543)
        ''')

    def test_submenu_active_glow_tracks_state_changes_in_combat(self):
        self.check('''
            learned[100]=true; learned[101]=true
            learned[13165]=true; learned[13163]=true
            trackingTypes={{spellID=100,name="Track A",texture=1,active=true},
                {spellID=101,name="Track B",texture=2,active=false}}
            activeAuras[13165]={spellId=13165}
            hevent("PLAYER_LOGIN")
            local track1=widgets.AesirsClassWidgetsTracking1
            local track2=widgets.AesirsClassWidgetsTracking2
            local monkey=widgets.AesirsClassWidgetsAspect1
            local hawk=widgets.AesirsClassWidgetsAspect2
            assert(track1.activeGlow.alpha==1 and track2.activeGlow.alpha==0)
            assert(hawk.activeGlow.alpha==1 and monkey.activeGlow.alpha==0)
            assert(math.abs(widgets.AesirsClassWidgetsTrackingMenu.width-35.2)<1e-8)
            assert(math.abs(widgets.AesirsClassWidgetsAspectMenu.width-35.2)<1e-8)
            assert(math.abs(widgets.AesirsClassWidgetsPetmend.width-35.2)<1e-8)
            assert(track1.width==32 and hawk.width==32)
            combat=true
            trackingTypes[1].active=false; trackingTypes[2].active=true
            activeAuras[13165]=nil; activeAuras[13163]={spellId=13163}
            htick()
            assert(track1.activeGlow.alpha==0 and track2.activeGlow.alpha==1)
            assert(hawk.activeGlow.alpha==0 and monkey.activeGlow.alpha==1)
            trackingTypes[2].active=false; activeAuras[13163]=nil
            htick()
            assert(track2.activeGlow.alpha==0 and monkey.activeGlow.alpha==0)
        ''')

    def test_subfans_are_centered_on_parent_rays_and_clear_other_buttons(self):
        self.check('''
            hevent("PLAYER_LOGIN")
            click("AesirsClassWidgetsHunterBar")
            local hub=widgets.AesirsClassWidgetsHunterBar
            local aspectIDs={13165,13163,5118,13159,13161,20043,34074,61846}
            for count=1,8 do
                trackingTypes={}
                for i=1,8 do
                    learned[100+i]=i<=count
                    learned[aspectIDs[i]]=i<=count
                    spellNames[aspectIDs[i]]="Aspect "..i
                    if i<=count then
                        trackingTypes[i]={spellID=100+i,name="Track "..i,texture=i}
                    end
                end
                hevent("SPELLS_CHANGED"); htick()
                for _, menu in ipairs({"Tracking", "Aspect"}) do
                    click("AesirsClassWidgets"..menu.."Menu")
                    local parent=widgets["AesirsClassWidgets"..menu.."Menu"]
                    local sumX,sumY=0,0
                    for i=1,count do
                        local child=widgets["AesirsClassWidgets"..menu..i]
                        assert(child.relative==hub, "subfan must orbit hunter")
                        local radius=math.sqrt(child.x^2+child.y^2)
                        assert(radius>=104-1e-8)
                        assert(child.x*parent.x+child.y*parent.y>0, "child must fan outward")
                        sumX,sumY=sumX+child.x,sumY+child.y
                        for _, other in pairs(widgets) do
                            if other.relative==hub and other~=child and other:IsVisible() then
                                assert((child.x-other.x)^2+(child.y-other.y)^2>=38^2-1e-7)
                            end
                        end
                        if i>1 then
                            local previous=widgets["AesirsClassWidgets"..menu..(i-1)]
                            assert((child.x-previous.x)^2+(child.y-previous.y)^2>=38^2-1e-7)
                        end
                    end
                    assert(math.abs(sumX*parent.y-sumY*parent.x)<1e-7,
                        "parent must sit on the group's center ray")
                end
            end
        ''')

    def test_feed_prefers_raw_then_plain_then_player_buff_food(self):
        self.check('''
            learned[6991]=true
            foods[10]={edible=true}; foods[20]={edible=true}; foods[30]={edible=true}
            itemSpells[20]=200; descriptions[200]="Restores 100 health."
            itemSpells[30]=300; descriptions[300]="Restores 100 health and grants Well Fed."
            bags[0][1]=item(30,3); bags[0][2]=item(20,3); bags[0][3]=item(10,3)
            hevent("PLAYER_LOGIN")
            local feed=widgets.AesirsClassWidgetsPetfeed
            assert(feed.attributes.macrotext:find("/use 0 3",1,true))
            bags[0][3]=nil; click("AesirsClassWidgetsPetfeed")
            assert(feed.attributes.macrotext:find("/use 0 2",1,true))
            bags[0][2]=nil; click("AesirsClassWidgetsPetfeed")
            assert(feed.attributes.macrotext:find("/use 0 1",1,true))
            assert(feed.attributes.macrotext:find("/stopmacro [combat]",1,true))
        ''')

    def test_dismiss_and_training_are_learned_secure_actions(self):
        self.check('''
            learned[2641]=true; learned[5149]=true
            hevent("PLAYER_LOGIN")
            assert(widgets.AesirsClassWidgetsPetdismiss.attributes.spell==2641)
            assert(widgets.AesirsClassWidgetsPettrain.attributes.spell==5149)
            assert(widgets.AesirsClassWidgetsPettrain.attributes.type=="spell")
        ''')

    def test_spellbook_cosmetic_hook_handles_existing_and_future_items(self):
        self.check('''
            ActionButtonUtil={ActionBarActionStatus={NotMissing=1}}
            function hooksecurefunc(target, key, callback)
                local original=target[key]
                target[key]=function(self, ...)
                    original(self, ...); callback(self, ...)
                end
            end
            SpellBookItemMixin={UpdateActionBarStatus=function(self)
                self.actionBarStatus=2; self:UpdateActionBarAnim()
            end}
            local existing={spellBank=0,spellBookItemInfo={spellID=6991},
                UpdateActionBarStatus=SpellBookItemMixin.UpdateActionBarStatus,
                UpdateActionBarAnim=function(self) self.glow=self.actionBarStatus==2 end}
            function EnumerateFrames(previous) if not previous then return existing end end
            learned[6991]=true; learned[2641]=true; hevent("PLAYER_LOGIN")
            assert(existing.actionBarStatus==1 and not existing.glow)
            local future=setmetatable({spellBank=0,spellBookItemInfo={spellID=2641},
                UpdateActionBarAnim=existing.UpdateActionBarAnim}, {__index=SpellBookItemMixin})
            future:UpdateActionBarStatus(); assert(future.actionBarStatus==1 and not future.glow)
            future.spellBookItemInfo.spellID=999
            future:UpdateActionBarStatus(); assert(future.actionBarStatus==2 and future.glow)
            existing.isUnlearned=true; existing:UpdateActionBarStatus()
            assert(existing.actionBarStatus==2)
            existing.isUnlearned=false; learned[6991]=nil
            hevent("SPELLS_CHANGED"); htick(); existing:UpdateActionBarStatus()
            assert(existing.actionBarStatus==2)
        ''')

    def test_feed_rejects_wrong_diet_old_locked_and_missing_pet(self):
        self.check('''
            learned[6991]=true; petLevel=50
            foods[10]={edible=false}; foods[20]={edible=true,level=1}; foods[30]={edible=true,level=50}
            bags[0][1]=item(10,1); bags[0][2]=item(20,1); bags[0][3]=item(30,1); bags[0][3].isLocked=true
            hevent("PLAYER_LOGIN"); assert(not widgets.AesirsClassWidgetsPetfeed.attributes.type)
            bags[0][3].isLocked=false; hevent("BAG_UPDATE_DELAYED"); htick()
            assert(widgets.AesirsClassWidgetsPetfeed.attributes.type=="macro")
            hasPet=false; hevent("UNIT_PET"); htick()
            assert(not widgets.AesirsClassWidgetsPetfeed.attributes.type)
        ''')

    def test_edit_mode_position_saved_per_layout(self):
        self.check('''
            hevent("PLAYER_LOGIN"); local hub=widgets.AesirsClassWidgetsHunterBar
            callbacks["EditMode.Enter"]()
            -- The mover is anonymous and is the last child with drag handlers.
            assert(hunterMover:IsShown())
            hunterMover.scripts.OnDragStart(); assert(hub.moving)
            hub.x,hub.y=700,400; hunterMover.scripts.OnDragStop()
            assert(AesirsClassWidgetsDB.widgets.hunter.positions["2:Test"].x==700)
            callbacks["EditMode.Exit"](); assert(not hunterMover:IsShown())
            layoutName="Other"; hevent("EDIT_MODE_LAYOUTS_UPDATED"); assert(hub.x~=700)
            layoutName="Test"; hevent("EDIT_MODE_LAYOUTS_UPDATED"); assert(hub.x==700)
        ''')

    def test_combat_defers_attributes_but_secure_menus_still_work(self):
        self.check('''
            hevent("PLAYER_LOGIN"); combat=true
            hevent("SPELLS_CHANGED"); htick()
            click("AesirsClassWidgetsHunterBar"); click("AesirsClassWidgetsAspectMenu")
            assert(widgets.AesirsClassWidgetsHunterBar.refs.aspects:IsShown())
            combat=false; hevent("PLAYER_REGEN_ENABLED"); htick()
        ''')

    def test_default_edit_layouts_have_distinct_positions(self):
        self.check('''
            activeLayout=1; hevent("PLAYER_LOGIN"); callbacks["EditMode.Enter"]()
            local hub=widgets.AesirsClassWidgetsHunterBar
            hub.x,hub.y=600,300; hunterMover.scripts.OnDragStop()
            assert(AesirsClassWidgetsDB.widgets.hunter.positions["preset:1"].x==600)
            callbacks["EditMode.Exit"]()
            activeLayout=2; hevent("EDIT_MODE_LAYOUTS_UPDATED"); assert(hub.x~=600)
        ''')


    def test_pet_xp_splits_the_native_bar_and_restores_it_when_dismissed(self):
        self.check('''
            local methods = getmetatable(UIParent).__index
            function methods:SetWidth(width) self.width = width end
            function methods:GetWidth() return self.width end
            function methods:SetStatusBarTexture() end
            function methods:SetStatusBarColor(...) self.barColor = {...} end
            function methods:SetColorTexture() end
            function methods:SetMinMaxValues(low, high) self.maximum = high end
            function methods:SetValue(value) self.value = value end
            function hooksecurefunc(target, key, callback)
                local original = target[key]
                target[key] = function(...) original(...); callback(...) end
            end

            STATUS_BAR_SIZE_ADJUSTMENT = 3
            StatusTrackingBarInfo = { BarsEnum={ Experience=1 } }
            local container = CreateFrame("Frame", nil, UIParent)
            local xp = CreateFrame("Frame", nil, container)
            xp.StatusBar = CreateFrame("StatusBar", nil, xp)
            xp.UpdateTick = function(self) self.tickWidth = self:GetWidth() end
            container.bars = { xp }
            StatusTrackingBarManager = { barContainers={container} }
            local function resize(width)
                container:SetWidth(width)
                StatusTrackingBarManager:CheckForLayoutChange()
            end
            function StatusTrackingBarManager:CheckForLayoutChange()
                local width = container:GetWidth() - STATUS_BAR_SIZE_ADJUSTMENT
                xp:SetWidth(width)
                xp.StatusBar:SetWidth(width)
            end
            local progress = 0
            function GetPetExperience() return progress, 100 end

            hasPet = false
            resize(803)
            local lifecycle = hunterEvents
            -- Capture the XP listener created before the Hunter toolbar listener.
            local create = CreateFrame
            CreateFrame = function(kind, name, parent, template)
                local frame = create(kind, name, parent, template)
                if not parent and not xpEvents then xpEvents = frame end
                return frame
            end
            lifecycle.scripts.OnEvent(lifecycle, "PLAYER_LOGIN")
            assert(xp:GetWidth()==800 and #xp.children==1)

            hasPet=true
            xpEvents.scripts.OnEvent(xpEvents, "UNIT_PET")
            local pet=xp.children[2]
            assert(xp:GetWidth()==400 and xp.StatusBar:GetWidth()==400 and xp.tickWidth==400)
            assert(pet:GetWidth()==398 and pet:IsShown() and pet.value==0 and pet.maximum==100)
            assert(pet.barColor[1]>pet.barColor[3] and pet.barColor[2]>pet.barColor[3])

            progress=75
            xpEvents.scripts.OnEvent(xpEvents, "UNIT_PET_EXPERIENCE")
            assert(pet.value==75)
            resize(403)
            assert(xp:GetWidth()==200 and pet:GetWidth()==198)

            hasPet=false
            xpEvents.scripts.OnEvent(xpEvents, "UNIT_PET")
            assert(xp:GetWidth()==400 and xp.StatusBar:GetWidth()==400 and xp.tickWidth==400)
            assert(not pet:IsShown())
        ''')


class MageDialTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        for file in ('tests/bootstrap.lua', 'tests/hunter_mock.lua'):
            self.lua.execute((ROOT / file).read_text())
        for file in ('Core.lua', 'Widgets/HunterPetXP.lua', 'Widgets/Hunter.lua', 'Widgets/Mage.lua'):
            self.lua.execute((ROOT / file).read_text(), 'AesirsClassWidgets', self.lua.globals().A)

    def test_learned_spell_groups_update_securely_and_use_highest_conjure_rank(self):
        self.lua.execute('''
            class="MAGE"
            learned[3561]=true; learned[1297659]=true; learned[10059]=true
            learned[5504]=true; learned[468766]=true; learned[10054]=true
            hevent("PLAYER_LOGIN")
            assert(not widgets.AesirsClassWidgetsHunterBar)
            local hub=widgets.AesirsClassWidgetsMageBar
            local teleport=widgets.AesirsClassWidgetsMageTeleportMenu
            local city=widgets.AesirsClassWidgetsMageTeleport1
            assert(city.attributes.spell==3561)
            assert(widgets.AesirsClassWidgetsMageTeleport2.attributes.spell==1297659)
            assert(widgets.AesirsClassWidgetsMagePortal1.attributes.spell==10059)
            assert(widgets.AesirsClassWidgetsMageConjure1.attributes.spell==468766)
            assert(widgets.AesirsClassWidgetsMageConjure2.attributes.spell==10054)
            assert(not widgets.AesirsClassWidgetsMageConjure3)

            combat=true
            click(hub.name)
            assert(teleport.fanAnimation.playing)
            click(teleport.name)
            assert(city.fanAnimation.playing and city:IsVisible())
            click("AesirsClassWidgetsMagePortalMenu")
            assert(not city:IsVisible() and hub.refs.category2:IsVisible())
            assert(pressKey("ESCAPE") and not pressKey("ESCAPE"))
            assert(not hub.refs.primary:IsShown() and not hub.refs.category2:IsShown())
            local portal=widgets.AesirsClassWidgetsMagePortal1.closeGhost
            assert(portal.slide.delay==0 and teleport.closeGhost.slide.delay==portal.slide.duration)
            learned[468766]=false
            hevent("SPELLS_CHANGED")
            assert(widgets.AesirsClassWidgetsMageConjure1.attributes.spell==468766)
            combat=false
            hevent("PLAYER_REGEN_ENABLED")
            assert(widgets.AesirsClassWidgetsMageConjure1.attributes.spell==5504)
        ''')

    def test_mage_dial_initializes_after_combat_and_saves_its_own_position(self):
        self.lua.execute('''
            class="MAGE"; combat=true
            hevent("PLAYER_LOGIN")
            assert(not widgets.AesirsClassWidgetsMageBar)
            combat=false
            hevent("PLAYER_REGEN_ENABLED")
            local hub=widgets.AesirsClassWidgetsMageBar
            assert(not hub:IsShown())
            learned[587]=true
            hevent("SPELLS_CHANGED")
            assert(hub:IsShown() and not widgets.AesirsClassWidgetsMageTeleportMenu:IsShown())
            callbacks["EditMode.Enter"]()
            hub.x,hub.y=600,300; hunterMover.scripts.OnDragStop()
            assert(AesirsClassWidgetsDB.widgets.mage.positions["2:Test"].x==600)
            assert(not AesirsClassWidgetsDB.widgets.hunter)
            callbacks["EditMode.Exit"]()
        ''')


if __name__ == '__main__':
    unittest.main(verbosity=2)
