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
