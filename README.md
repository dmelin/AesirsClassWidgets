# Aesirs Class Widgets

Class-specific utility widgets for World of Warcraft: Forever (interface 16001). Hunter is the first module; other class widgets can be added independently.

## Installation

Copy the entire `AesirsClassWidgets` folder, including `Core.lua`, `Widgets`, and `Media`, into `World of Warcraft/_forever_/Interface/AddOns/`. Restart WoW after first installing this separate addon, then enable **Aesirs Class Widgets** in the AddOns list. Existing addon edits can be loaded with `/reload`.

The addon works without Aesirs Quality of Life. If both are enabled on the first login, the optional load-order dependency allows it to copy the old hunter toolbar positions once. It does not change QoL's settings. Existing Class Widgets positions take precedence. Quality of Life version 1.5.0 removes the original hunter toolbar to prevent duplicates.

## Adding another class

`Core.lua` owns class dispatch, independent widget settings, and shared radial layout helpers. Class modules belong in `Widgets/`. Hunter's entire UI, spell discovery, food selection, and Edit Interface handling live in `Widgets/Hunter.lua`.

Add the new Lua module after `Core.lua` in the TOC, and register its initializer:

```lua
local _, A = ...
A.RegisterClassWidget("MAGE", "mage", function()
    local settings = A.WidgetSettings("mage")
    -- Build this class's secure buttons and register its relevant events here.
end)
```

Only initializers matching the logged-in player's class run. Each module gets an isolated settings table under `AesirsClassWidgetsDB.widgets[widgetKey]`. No Mage or other class widget is implemented yet. New modules must validate event availability and defer secure button changes during combat, following the Hunter module's pattern.

## Tests

```sh
python -m pip install lupa
python tests/test_addon.py
```

Tests run Lua 5.1 against the addon without loading Quality of Life. They cover class dispatch, independent settings, optional migration, menu behavior, food preference, combat deferral, and layout positions.

## Hunter toolbar

The hunter class icon appears only on hunters, initially right of the screen center. Click it to open a radial fan containing **Tracking**, **Aspects**, **Mend Pet**, **Feed Pet**, **Call Pet**, **Revive Pet**, and **Tame Beast**. Unlearned pet actions are greyed out.

Buttons use circular icon masks and gold borders. The central hunter button is 44 pixels, other buttons are 32 pixels, and the first fan has a compact 48-pixel radius. Submenu spacing scales with the number of learned spells.

Tracking and Aspects open separate second-level fans containing learned spells. Opening one closes the other submenu while leaving the main fan visible. Clicking the hunter icon again closes both levels. Actions use secure click buttons; spell and food selections update outside combat, with deferred updates applied after combat.

Feed Pet uses Forever's native `C_PetInfo.CanPetEatItem` check for the current pet, excludes locked and excessively old food, and selects from bag slots. It prefers raw ingredients with no player use effect, then plain recovery food, then food with recognized Well Fed/stat bonuses or unknown effects. Lower required/item level, quality, and vendor value break ties. This is a conservative benefit heuristic, not an exact calculation of every possible food effect. The chosen item is shown in the Feed Pet tooltip and is rechecked on click outside combat. Feeding requires a living pet and being out of combat, and consumes one item through the Feed Pet spell plus the selected bag slot.

Open Forever's **Edit Interface** mode to show the toolbar's green drag handle. Drag the hunter icon; its position saves on drop for the active layout. The position is stored by the addon, so dropping it saves immediately rather than participating in the native Save/Cancel or layout export. Tracking/aspect fans close while editing. No native Edit Mode system frames or settings are modified.

API references: [Forever pet information](https://github.com/Atraeau/WoW-Addons/blob/main/docs/api/Pets-Mounts-Collections/C_PetInfo.md), [secure action templates](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua), [spellbook API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellBookDocumentation.lua), and [Edit Mode callbacks](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_EditMode/Shared/EditModeManager.lua). The toolbar has simulated coverage; live spell casting, feeding, and layout positioning still need an in-game smoke test.
