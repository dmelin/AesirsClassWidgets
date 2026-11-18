local _, A = ...
local widgets = {}
local lifecycle = CreateFrame("Frame")

-- Each class module owns its settings and UI. Only matching class modules start.
function A.RegisterClassWidget(classToken, key, initialize)
    assert(not widgets[key], "Duplicate class widget: " .. key)
    widgets[key] = { class = classToken, initialize = initialize }
end

function A.WidgetSettings(key)
    AesirsClassWidgetsDB = AesirsClassWidgetsDB or {}
    AesirsClassWidgetsDB.widgets = AesirsClassWidgetsDB.widgets or {}
    AesirsClassWidgetsDB.widgets[key] = AesirsClassWidgetsDB.widgets[key] or {}
    return AesirsClassWidgetsDB.widgets[key]
end

lifecycle:RegisterEvent("PLAYER_LOGIN")
lifecycle:SetScript("OnEvent", function()
    local _, classToken = UnitClass("player")
    for _, widget in pairs(widgets) do
        if widget.class == classToken and not widget.started then
            widget.started = true
            widget.initialize()
        end
    end
end)

function A.FanOffset(index, count, radius, firstAngle, arc)
    local angle = math.rad(count == 1 and firstAngle + arc / 2
        or firstAngle + (index - 1) * arc / (count - 1))
    return math.cos(angle) * radius, math.sin(angle) * radius
end

-- Submenus share this persistent active indicator. Initialize when creating
-- their buttons outside combat; subsequent updates only change texture alpha.
function A.SetSubmenuActive(button, active)
    if not button.activeGlow then
        local glow = button:CreateTexture(nil, "OVERLAY")
        glow:SetPoint("TOPLEFT", button, "TOPLEFT", -5, 5)
        glow:SetPoint("BOTTOMRIGHT", button, "BOTTOMRIGHT", 5, -5)
        glow:SetTexture("Interface\\AddOns\\AesirsClassWidgets\\Media\\RoundHighlight")
        glow:SetBlendMode("ADD")
        glow:SetVertexColor(1, 0.85, 0.3)
        button.activeGlow = glow
    end
    button.activeGlow:SetAlpha(active and 1 or 0)
end

function A.DialLayoutKey()
    local info = C_EditMode.GetLayouts()
    if not info then return "default" end
    -- The API excludes the two built-in presets from layouts but includes them
    -- in activeLayout. The UI manager prepends those presets in its own copy.
    if info.activeLayout <= 2 then return "preset:" .. info.activeLayout end
    local active = info.layouts and info.layouts[info.activeLayout - 2]
    return active and (tostring(active.layoutType) .. ":" .. active.layoutName) or ("layout:" .. info.activeLayout)
end

local OPEN_DURATION = 0.18
local CLOSE_DURATION = OPEN_DURATION * 0.6

local ART = "Interface\\AddOns\\AesirsClassWidgets\\Media\\"

local function Tooltip(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    if self.spellID then GameTooltip:SetSpellByID(self.spellID)
    else GameTooltip:SetText(self.title or "Aesir Class Widgets") end
    if self.note then GameTooltip:AddLine(self.note, 1, 0.82, 0.3, true) end
    GameTooltip:Show()
end

function A.PositionFanButton(button, hub, x, y, originX, originY)
    if not button.fanAnimation then
        local animation = button:CreateAnimationGroup()
        local slide = animation:CreateAnimation("Translation")
        slide:SetDuration(OPEN_DURATION)
        slide:SetSmoothing("IN")
        local fade = animation:CreateAnimation("Alpha")
        fade:SetFromAlpha(1)
        fade:SetToAlpha(0)
        fade:SetDuration(OPEN_DURATION)
        button.fanAnimation = animation
        button.fanSlide = slide
        button:SetScript("OnShow", function()
            if button.closeGhost then
                button.closeGhost.animation:Stop()
                button.closeGhost:Hide()
            end
            animation:Play(true)
        end)
        button:SetScript("OnHide", function() animation:Stop() end)
    end

    button:ClearAllPoints()
    button:SetPoint("CENTER", hub, "CENTER", x, y)
    button.fanCloseX, button.fanCloseY = originX - x, originY - y
    button.fanSlide:SetOffset(button.fanCloseX, button.fanCloseY)
end

function A.CreateDialButton(name, parent, template, icon, size)
    local button = CreateFrame("Button", name, parent, template)
    button:SetSize(size or 32, size or 32)
    button:RegisterForClicks("AnyUp", "AnyDown")
    button:SetNormalTexture(ART .. "RoundBorder")
    button:SetHighlightTexture(ART .. "RoundHighlight", "ADD")
    button.icon = button:CreateTexture(nil, "ARTWORK")
    button.icon:SetPoint("TOPLEFT", 3, -3)
    button.icon:SetPoint("BOTTOMRIGHT", -3, 3)
    button.icon:SetTexture(icon)
    button.mask = button:CreateMaskTexture()
    button.mask:SetAllPoints(button.icon)
    button.mask:SetTexture("Interface\\CHARACTERFRAME\\TempPortraitAlphaMask", "CLAMPTOBLACKADDITIVE", "CLAMPTOBLACKADDITIVE")
    button.icon:AddMaskTexture(button.mask)
    button:SetScript("OnEnter", Tooltip)
    button:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return button
end

function A.BindDialEscape(hub, primary, hubName)
    SecureHandlerWrapScript(primary, "OnShow", hub, string.format([[
        self:SetBindingClick(true, "ESCAPE", %q, "LeftButton")
    ]], hubName))
    SecureHandlerWrapScript(primary, "OnHide", hub, [[
        self:ClearBinding("ESCAPE")
    ]])
end

local function AnimateButtonClose(button, delay)
    local x, y = button:GetCenter()
    if not x then return end
    local ghost = button.closeGhost
    if not ghost then
        ghost = A.CreateDialButton(nil, UIParent, nil, nil, button:GetWidth())
        ghost:EnableMouse(false)
        local animation = ghost:CreateAnimationGroup()
        local slide = animation:CreateAnimation("Translation")
        slide:SetDuration(CLOSE_DURATION)
        slide:SetSmoothing("IN")
        local fade = animation:CreateAnimation("Alpha")
        fade:SetDuration(CLOSE_DURATION)
        fade:SetFromAlpha(1)
        fade:SetToAlpha(0)
        animation:SetScript("OnFinished", function() ghost:Hide() end)
        ghost.animation, ghost.slide, ghost.fade = animation, slide, fade
        button.closeGhost = ghost
    end

    ghost.animation:Stop()
    ghost:SetScale(button:GetEffectiveScale() / UIParent:GetEffectiveScale())
    ghost:SetFrameStrata(button:GetFrameStrata())
    ghost:SetFrameLevel(button:GetFrameLevel())
    ghost:SetPoint("CENTER", UIParent, "BOTTOMLEFT", x, y)
    ghost.icon:SetTexture(button.icon:GetTexture())
    ghost.icon:SetTexCoord(button.icon:GetTexCoord())
    ghost.icon:SetDesaturated(button.icon:IsDesaturated())
    if button.activeGlow then A.SetSubmenuActive(ghost, button.activeGlow:GetAlpha() > 0) end
    ghost.slide:SetOffset(button.fanCloseX, button.fanCloseY)
    ghost.slide:SetStartDelay(delay)
    ghost.fade:SetStartDelay(delay)
    ghost:Show()
    ghost.animation:Play()
end

local function AnimateFanClose(fan, delay)
    local animated = false
    for _, button in ipairs({ fan:GetChildren() }) do
        if button.fanAnimation and button:IsVisible() then
            AnimateButtonClose(button, delay)
            animated = true
        end
    end
    return animated
end

function A.EnableDialCloseAnimation(hub, primary, submenus)
    -- Secure clicks hide the real action buttons immediately. Independent visual
    -- copies can finish the animation without delaying protected changes in combat.
    local function AnimateOpenSubmenu()
        for _, fan in ipairs(submenus) do
            if fan:IsVisible() and AnimateFanClose(fan, 0) then
                return CLOSE_DURATION
            end
        end
        return 0
    end
    hub.AnimateSubmenuClose = AnimateOpenSubmenu
    hub.AnimateDialClose = function()
        AnimateFanClose(primary, AnimateOpenSubmenu())
    end
end
