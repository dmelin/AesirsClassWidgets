local _, A = ...
local PET_FILL_INSET = 2

function A.InitializeHunterPetXP()
    local petBars = {}

    local function Update()
        local manager = StatusTrackingBarManager
        if not manager or not StatusTrackingBarInfo or not GetPetExperience then return end

        local current, maximum
        if UnitExists("pet") then current, maximum = GetPetExperience() end
        local split = current ~= nil and maximum ~= nil and maximum > 0
        local experience = StatusTrackingBarInfo.BarsEnum.Experience

        for _, container in ipairs(manager.barContainers) do
            local playerBar = container.bars[experience]
            if playerBar and (split or petBars[playerBar]) then
                local petBar = petBars[playerBar]
                if not petBar then
                    petBar = CreateFrame("StatusBar", nil, playerBar)
                    petBar:Hide()
                    petBar:SetPoint("TOPLEFT", playerBar.StatusBar, "TOPRIGHT", PET_FILL_INSET, 0)
                    petBar:SetPoint("BOTTOMLEFT", playerBar.StatusBar, "BOTTOMRIGHT", PET_FILL_INSET, 0)
                    petBar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar")
                    petBar:SetStatusBarColor(1, 0.78, 0.12)
                    local background = petBar:CreateTexture(nil, "BACKGROUND")
                    background:SetAllPoints()
                    background:SetColorTexture(0.14, 0.10, 0.03, 1)

                    petBar:EnableMouse(true)
                    petBar:SetScript("OnEnter", function(self)
                        local xp, needed = GetPetExperience()
                        if not needed or needed <= 0 then return end
                        GameTooltip:SetOwner(self, "ANCHOR_TOP")
                        GameTooltip:SetText("Pet Experience")
                        GameTooltip:AddLine(XP_STATUS_BAR_TEXT:format(xp, needed), 1, 1, 1)
                        GameTooltip:Show()
                    end)
                    petBar:SetScript("OnLeave", function() GameTooltip:Hide() end)
                    petBars[playerBar] = petBar
                end

                -- Keep Blizzard's player fill, tooltip and rested XP on the left.
                -- The container remains full width, including its border and dividers.
                local fullWidth = container:GetWidth() - STATUS_BAR_SIZE_ADJUSTMENT
                local playerWidth = split and fullWidth / 2 or fullWidth
                if playerBar:GetWidth() ~= playerWidth or playerBar.StatusBar:GetWidth() ~= playerWidth then
                    playerBar:SetWidth(playerWidth)
                    playerBar.StatusBar:SetWidth(playerWidth)
                    playerBar:UpdateTick()
                end
                if split then
                    petBar:SetWidth(fullWidth / 2 - PET_FILL_INSET)
                    petBar:SetMinMaxValues(0, maximum)
                    petBar:SetValue(current)
                end
                petBar:SetShown(split)
            end
        end
    end

    local events = CreateFrame("Frame")
    local hooked
    local function Refresh()
        if StatusTrackingBarManager and not hooked then
            hooksecurefunc(StatusTrackingBarManager, "CheckForLayoutChange", Update)
            hooked = true
        end
        Update()
    end

    for _, event in ipairs({ "PLAYER_ENTERING_WORLD", "UNIT_PET", "UNIT_PET_EXPERIENCE" }) do
        if C_EventUtils.IsEventValid(event) then events:RegisterEvent(event) end
    end
    events:SetScript("OnEvent", Refresh)
    Refresh()
end
