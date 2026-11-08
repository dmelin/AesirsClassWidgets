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


if __name__ == '__main__':
    unittest.main(verbosity=2)
