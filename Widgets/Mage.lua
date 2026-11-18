local _, A = ...
local hub, primary, mover
local editing, dirty = false, true
local SUB_RADIUS = 104
local SUB_STEP = math.deg(2 * math.asin(38 / (2 * SUB_RADIUS)))
local categories = {
    { key = "Teleport", title = "Teleports", icon = "Spell_Arcane_Blink", spells = {
        { 3561 }, { 3562 }, { 3565 }, { 3567 }, { 3563 }, { 3566 }, { 1297659 },
    } },
    { key = "Portal", title = "Portals", icon = "Spell_Arcane_PortalStormWind", spells = {
        { 10059 }, { 11416 }, { 11419 }, { 11417 }, { 11418 }, { 11420 },
    } },
    { key = "Conjure", title = "Conjure", icon = "INV_Drink_06", spells = {
        { 587, 597, 990, 6129, 10144, 10145, 28612 },
        { 5504, 5505, 5506, 6127, 10138, 10139, 10140, 468766 },
        { 759 }, { 3552 }, { 10053 }, { 10054 },
    } },
}

local function Refresh()
    if InCombatLockdown() then return end
    dirty = false
    local bank = Enum.SpellBookSpellBank.Player
    local anyKnown = false
    for _, category in ipairs(categories) do
        local known = {}
        for _, ranks in ipairs(category.spells) do
            for rank = #ranks, 1, -1 do
                local id = ranks[rank]
                if C_SpellBook.IsSpellKnown(id, bank) then
                    known[#known + 1] = id
                    break
                end
            end
        end

        local count = #known
        local arc = (count - 1) * SUB_STEP
        if count == 0 then category.fan:Hide() end
        category.button:SetShown(count > 0)
        anyKnown = anyKnown or count > 0
        for i, id in ipairs(known) do
            local button = category.buttons[i]
            if not button then
                button = A.CreateDialButton("AesirsClassWidgetsMage" .. category.key .. i, category.fan,
                    "SecureActionButtonTemplate", nil, 32)
                category.buttons[i] = button
            end
            local info = C_Spell.GetSpellInfo(id)
            button.spellID = id
            button.icon:SetTexture(info and info.iconID)
            button:SetAttribute("type", "spell")
            button:SetAttribute("spell", id)
            local x, y = A.FanOffset(i, count, SUB_RADIUS, category.angle + arc / 2, -arc)
            A.PositionFanButton(button, hub, x, y, category.x, category.y)
            button:Show()
        end
        for i = count + 1, #category.buttons do
            local button = category.buttons[i]
            button:SetAttribute("type", nil)
            button:Hide()
        end
    end
    hub:SetShown(anyKnown or editing)
end

local function Close()
    primary:Hide()
    for _, category in ipairs(categories) do category.fan:Hide() end
end

local function Initialize()
    local settings = A.WidgetSettings("mage")
    settings.positions = settings.positions or {}
    local function RestorePosition()
        if InCombatLockdown() then return end
        local position = settings.positions[A.DialLayoutKey()]
        hub:ClearAllPoints()
        if position then hub:SetPoint("CENTER", UIParent, "BOTTOMLEFT", position.x, position.y)
        else hub:SetPoint("CENTER", UIParent, "CENTER", 260, -100) end
    end

    hub = A.CreateDialButton("AesirsClassWidgetsMageBar", UIParent, "SecureHandlerClickTemplate",
        "Interface\\GLUES\\CHARACTERCREATE\\UI-CHARACTERCREATE-CLASSES", 44)
    hub.icon:SetTexCoord(unpack(CLASS_ICON_TCOORDS.MAGE))
    hub:SetMovable(true)
    hub:SetClampedToScreen(true)
    hub.title = "Aesir Class Widgets: Mage"
    hub.note = "Click for teleports, portals, and conjured supplies. Move using Edit Interface."
    primary = CreateFrame("Frame", nil, hub, "SecureHandlerBaseTemplate")
    primary:SetAllPoints(hub)
    primary:Hide()
    A.BindDialEscape(hub, primary, "AesirsClassWidgetsMageBar")
    hub:SetFrameRef("primary", primary)
    hub:SetAttribute("_onclick", [[
        if down then return end
        local fan = self:GetFrameRef("primary")
        if fan:IsShown() then
            self:CallMethod("AnimateDialClose")
            fan:Hide()
            for i = 1, 3 do self:GetFrameRef("category" .. i):Hide() end
        else
            fan:Show()
        end
    ]])

    local submenus = {}
    for i, category in ipairs(categories) do
        category.angle = 90 - (i - 1) * 120
        category.x, category.y = A.FanOffset(1, 1, 60, category.angle, 0)
        category.buttons = {}
        category.fan = CreateFrame("Frame", nil, primary, "SecureHandlerBaseTemplate")
        category.fan:SetAllPoints(hub)
        category.fan:Hide()
        submenus[i] = category.fan
        hub:SetFrameRef("category" .. i, category.fan)
        local button = A.CreateDialButton("AesirsClassWidgetsMage" .. category.key .. "Menu", primary,
            "SecureHandlerClickTemplate", "Interface\\Icons\\" .. category.icon, 35.2)
        category.button = button
        button.title = category.title
        A.PositionFanButton(button, hub, category.x, category.y, 0, 0)
        button:SetFrameRef("hub", hub)
        button:SetAttribute("category", i)
        button:SetAttribute("_onclick", [[
            if down then return end
            local hub = self:GetFrameRef("hub")
            hub:CallMethod("AnimateSubmenuClose")
            local selected = self:GetAttribute("category")
            for i = 1, 3 do
                local fan = hub:GetFrameRef("category" .. i)
                if i == selected and not fan:IsShown() then fan:Show() else fan:Hide() end
            end
        ]])
    end

    A.EnableDialCloseAnimation(hub, primary, submenus)

    mover = CreateFrame("Frame", nil, hub, "BackdropTemplate")
    mover:SetAllPoints(hub)
    mover:SetFrameLevel(hub:GetFrameLevel() + 20)
    mover:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8X8" })
    mover:SetBackdropColor(0.1, 0.4, 0.1, 0.4)
    mover:EnableMouse(true)
    mover:RegisterForDrag("LeftButton")
    local label = mover:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    label:SetPoint("BOTTOM", mover, "TOP", 0, 5)
    label:SetText("Aesir Class Widgets: Mage\nDrag to move (saved on drop)")
    mover:SetScript("OnDragStart", function()
        if editing and not InCombatLockdown() then hub:StartMoving() end
    end)
    mover:SetScript("OnDragStop", function()
        if InCombatLockdown() then return end
        hub:StopMovingOrSizing()
        local x, y = hub:GetCenter()
        if x and y then settings.positions[A.DialLayoutKey()] = { x = x, y = y } end
        RestorePosition()
    end)
    local function ApplyEditMode()
        if InCombatLockdown() then return end
        Close()
        mover:SetShown(editing)
        RestorePosition()
        Refresh()
    end
    EventRegistry:RegisterCallback("EditMode.Enter", function() editing = true; ApplyEditMode() end, hub)
    EventRegistry:RegisterCallback("EditMode.Exit", function() editing = false; ApplyEditMode() end, hub)
    mover:Hide()

    local events = CreateFrame("Frame")
    for _, event in ipairs({ "PLAYER_ENTERING_WORLD", "SPELLS_CHANGED", "PLAYER_REGEN_ENABLED",
        "EDIT_MODE_LAYOUTS_UPDATED" }) do
        if C_EventUtils.IsEventValid(event) then events:RegisterEvent(event) end
    end
    events:SetScript("OnEvent", function(_, event)
        if event == "PLAYER_REGEN_ENABLED" then
            if mover:IsShown() ~= editing then ApplyEditMode()
            elseif dirty then Refresh() end
            RestorePosition()
        elseif event == "EDIT_MODE_LAYOUTS_UPDATED" then
            RestorePosition()
        else
            dirty = true
            Refresh()
        end
    end)
    RestorePosition()
    Refresh()
end

A.RegisterClassWidget("MAGE", "mage", function()
    if not InCombatLockdown() then
        Initialize()
        return
    end
    local waitForCombat = CreateFrame("Frame")
    waitForCombat:RegisterEvent("PLAYER_REGEN_ENABLED")
    waitForCombat:SetScript("OnEvent", function(self)
        self:UnregisterEvent("PLAYER_REGEN_ENABLED")
        Initialize()
    end)
end)
