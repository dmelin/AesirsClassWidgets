# Aesirs Class Widgets

Class-specific utility widgets for World of Warcraft: Forever (interface 16001). Includes Hunter and Mage modules.

## Installation

Copy the entire `AesirsClassWidgets` folder, including `Core.lua`, `Widgets`, and `Media`, into `World of Warcraft/_forever_/Interface/AddOns/`. Restart WoW after first installing this separate addon, then enable **Aesirs Class Widgets** in the AddOns list. Existing addon edits can be loaded with `/reload`.

The addon works without Aesirs Quality of Life. If both are enabled on the first login, the optional load-order dependency allows it to copy the old hunter toolbar positions once. It does not change QoL's settings. Existing Class Widgets positions take precedence. Quality of Life version 1.5.0 removes the original hunter toolbar to prevent duplicates.

## Adding another class

`Core.lua` owns class dispatch, independent widget settings, and shared radial layout helpers. Class modules belong in `Widgets/`. Hunter's entire UI, spell discovery, food selection, and Edit Interface handling live in `Widgets/Hunter.lua`.

Add the new Lua module after `Core.lua` in the TOC, and register its initializer:

```lua
local _, A = ...
A.RegisterClassWidget("PRIEST", "priest", function()
    local settings = A.WidgetSettings("priest")
    -- Build this class's secure buttons and register its relevant events here.
end)
```

Only initializers matching the logged-in player's class run. Each module gets an isolated settings table under `AesirsClassWidgetsDB.widgets[widgetKey]`. New modules must validate event availability and defer secure button changes during combat, following the Hunter module's pattern.

## Tests

```sh
python -m pip install lupa
python tests/test_addon.py
```

Tests run Lua 5.1 against the addon without loading Quality of Life. They cover class dispatch, independent settings, optional migration, menu behavior, food preference, combat deferral, and layout positions.

## Hunter toolbar

The hunter class icon appears only on hunters, initially right of the screen center. Click it to open a radial fan containing **Tracking**, **Aspects**, **Mend Pet**, **Feed Pet**, **Call Pet**, **Revive Pet**, **Tame Beast**, **Dismiss Pet**, and **Beast Training**. Unlearned pet actions are greyed out. All nine main buttons share one evenly spaced circle around the hunter icon.

Buttons use circular icon masks and gold borders. The central hunter button is 44 pixels, first-fan buttons are 35.2 pixels, and submenu buttons are 32 pixels. The first fan has a 60-pixel radius. Submenu spacing scales with the number of learned spells.

Active tracking and aspect entries have a persistent gold glow, independent of the mouse hover highlight. The indicator follows current tracking state and player aspect buffs, including changes during combat. Future submenus should use the shared `A.SetSubmenuActive(button, active)` helper, initializing it when creating their buttons outside combat and updating it from their current active state.

Learned spells represented by the hunter widget suppress the spellbook's missing-action-bar glow and tooltip warning. This is a cosmetic spellbook adjustment and does not occupy action-bar slots. Other spells retain their normal warnings.

Tracking and Aspects open separate second-level fans containing learned spells. Opening one closes the other submenu while leaving the main fan visible. Clicking the hunter icon again or pressing Esc folds the open submenu in, then folds in the main dial. Actions use secure click buttons; spell and food selections update outside combat, with deferred updates applied after combat.

Feed Pet uses Forever's native `C_PetInfo.CanPetEatItem` check for the current pet, excludes locked and excessively old food, and selects from bag slots. It prefers raw ingredients with no player use effect, then plain recovery food, then food with recognized Well Fed/stat bonuses or unknown effects. Lower required/item level, quality, and vendor value break ties. This is a conservative benefit heuristic, not an exact calculation of every possible food effect. The chosen item is shown in the Feed Pet tooltip and is rechecked on click outside combat. Feeding requires a living pet and being out of combat, and consumes one item through the Feed Pet spell plus the selected bag slot.

Open Forever's **Edit Interface** mode to show the toolbar's green drag handle. Drag the hunter icon; its position saves on drop for the active layout. The position is stored by the addon, so dropping it saves immediately rather than participating in the native Save/Cancel or layout export. Tracking/aspect fans close while editing. No native Edit Mode system frames or settings are modified.

API references: [Forever pet information](https://github.com/Atraeau/WoW-Addons/blob/main/docs/api/Pets-Mounts-Collections/C_PetInfo.md), [secure action templates](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_FrameXML/SecureTemplates.lua), [spellbook API](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_APIDocumentationGenerated/SpellBookDocumentation.lua), and [Edit Mode callbacks](https://github.com/Gethe/wow-ui-source/blob/forever/Interface/AddOns/Blizzard_EditMode/Shared/EditModeManager.lua). The toolbar has simulated coverage; live spell casting, feeding, and layout positioning still need an in-game smoke test.


When a summoned pet has XP progress, the visible player XP bar splits into equal halves. Player XP and rested XP stay on the left, and the yellow right half shows pet XP. Hover over the pet half for its exact XP.

## Mage dial

Click the Mage class icon to open **Teleports**, **Portals**, and **Conjure**. The dial shows only learned spells, with the highest learned rank for Conjure Food and Conjure Water and a separate button for each learned mana gem spell. Empty categories stay hidden. Buttons fan out from their parent, and **Esc** closes the dial and any open submenu.

Use **Edit Interface** to drag the Mage dial. Its position saves per layout.
