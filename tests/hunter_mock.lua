widgets, callbacks, learned, spellbook, trackingTypes, foods, itemSpells, descriptions = {}, {}, {}, {}, {}, {}, {}, {}
Enum={SpellBookSpellBank={Player=0}}
CLASS_ICON_TCOORDS={HUNTER={0,0.25,0.25,0.5},MAGE={0.25,0.5,0,0.25}}
local methods={}
local function Guard(frame) assert(not combat or secureClick or (frame and frame.kind=="Button" and not frame.template), "insecure protected mutation during combat") end
function methods:SetSize(width,height) self.width,self.height=width,height end
function methods:SetAlpha(alpha) self.alpha=alpha end
function methods:GetAlpha() return self.alpha or 1 end
function methods:GetWidth() return self.width end
function methods:SetScale(scale) self.scale=scale end
function methods:GetEffectiveScale() return self.scale or 1 end
function methods:SetFrameStrata(strata) self.strata=strata end
function methods:GetFrameStrata() return self.strata or "MEDIUM" end
function methods:GetChildren() return unpack(self.children) end
function methods:CallMethod(name, ...) self[name](self, ...) end
function methods:SetBlendMode(mode) self.blendMode=mode end
function methods:SetVertexColor(...) self.color={...} end
function methods:RegisterForClicks() end
function methods:SetNormalTexture() end
function methods:SetHighlightTexture() end
function methods:SetPoint(point, relative, relativePoint, x, y)
    Guard()
    self.relative=relative
    if type(x)=="number" then
        self.x, self.y=x,y
        if relativePoint=="CENTER" and relative==UIParent then self.x,self.y=x+512,y+384 end
    end
end
function methods:CreateTexture() return setmetatable({}, {__index=methods}) end
function methods:CreateMaskTexture() return setmetatable({}, {__index=methods}) end
function methods:AddMaskTexture(mask) self.mask=mask end
function methods:CreateFontString() return setmetatable({}, {__index=methods}) end
function methods:SetTexture(value) self.texture=value end
function methods:GetTexture() return self.texture end
function methods:SetTexCoord(...) self.coords={...} end
function methods:GetTexCoord() return unpack(self.coords or {0, 0, 0, 1, 1, 0, 1, 1}) end
function methods:SetDesaturated(value) self.gray=value end
function methods:IsDesaturated() return self.gray or false end
function methods:SetScript(key, fn) self.scripts[key]=fn end
invalidEvents={LEARNED_SPELL_IN_TAB=true}
C_EventUtils={IsEventValid=function(event) return not invalidEvents[event] end}
function methods:RegisterEvent(event)
    assert(C_EventUtils.IsEventValid(event), "unknown event: "..event)
    self.registered[event]=true
end
function methods:UnregisterEvent(event) self.registered[event]=nil end
function methods:SetAttribute(key,value) Guard(); self.attributes[key]=value end
function methods:GetAttribute(key) return self.attributes[key] end
function methods:GetFrameRef(key) return self.refs[key] end
function methods:SetFrameRef(key,value) Guard(); self.refs[key]=value end
function methods:ClearAllPoints() Guard() end
function methods:SetAllPoints() Guard() end
function methods:IsShown() return self.shown end
function methods:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
local function NotifyVisibility(frame, script)
    if frame.scripts[script] then frame.scripts[script](frame) end
    for _, child in ipairs(frame.children) do
        if child.shown then NotifyVisibility(child, script) end
    end
end
function methods:SetShown(value)
    Guard(self)
    local wasVisible = self:IsVisible()
    self.shown = value
    local visible = self:IsVisible()
    if wasVisible ~= visible then NotifyVisibility(self, visible and "OnShow" or "OnHide") end
end
function methods:Show() self:SetShown(true) end
function methods:Hide() self:SetShown(false) end
function methods:CreateAnimationGroup()
    local group = {animations={}}
    function group:SetScript(key, fn) self[key]=fn end
    function group:Play(reverse) self.reverse=reverse; self.playing=true end
    function group:Stop() self.playing=false end
    function group:CreateAnimation(kind)
        local anim = {
            SetDuration=function(self, duration) self.duration=duration end, SetSmoothing=function() end,
            SetStartDelay=function(self, delay) self.delay=delay end,
            SetFromAlpha=function() end, SetToAlpha=function() end,
            SetOffset=function(self, x, y) self.x,self.y=x,y end,
        }
        self.animations[kind]=anim
        return anim
    end
    return group
end
local bindings = {}
function methods:SetBindingClick(_, key, name)
    assert(secureClick)
    bindings[key]=name
end
function methods:ClearBinding(key)
    assert(secureClick)
    bindings[key]=nil
end
function SecureHandlerWrapScript(frame, script, _, snippet)
    local run = loadstring("return function(self) "..snippet.." end")()
    frame:SetScript(script, function(self)
        local previous = secureClick
        secureClick=true
        run(self)
        secureClick=previous
    end)
end
function pressKey(key)
    local target = bindings[key]
    if target then click(target) end
    return target ~= nil
end
function methods:SetMovable() end
function methods:SetClampedToScreen() end
function methods:SetFrameLevel() end
function methods:GetFrameLevel() return 5 end
function methods:SetBackdrop() end
function methods:SetBackdropColor() end
function methods:SetBackdropBorderColor() end
function methods:EnableMouse() end
function methods:RegisterForDrag() hunterMover=self end
function methods:SetText(text) self.text=text end
function methods:StartMoving() self.moving=true end
function methods:StopMovingOrSizing() self.moving=false end
function methods:GetCenter() return self.x,self.y end
function CreateFrame(kind,name,parent,template)
    local obj=setmetatable({kind=kind,name=name,parent=parent,template=template,shown=true,children={},attributes={},refs={},scripts={},registered={}}, {__index=methods})
    if parent then table.insert(parent.children,obj) end
    if name then widgets[name]=obj; _G[name]=obj end
    if not name and not parent then hunterEvents=obj end
    return obj
end
UIParent=CreateFrame("Frame","MockUIParent")
EventRegistry={RegisterCallback=function(_,event,fn) callbacks[event]=fn end}
C_EditMode={GetLayouts=function() return {activeLayout=activeLayout or 3,layouts={{layoutType=2,layoutName=layoutName or "Test"}}} end}
function UnitExists() return hasPet~=false end
function UnitIsDeadOrGhost() return petDead end
function UnitLevel(unit) return unit=="pet" and (petLevel or 10) or 15 end
spellNames={[136]="Mend Pet",[6991]="Feed Pet",[883]="Call Pet",[982]="Revive Pet",[1515]="Tame Beast",
    [19705]="Well Fed",[13165]="Aspect of the Hawk",[13163]="Aspect of the Monkey",[5118]="Aspect of the Cheetah"}
C_Spell={GetSpellName=function(id) return spellNames[id] end,
    GetSpellInfo=function(id) return {iconID=id,name=spellNames[id]} end,
    GetSpellDescription=function(id) return descriptions[id] end}
C_SpellBook={IsSpellKnown=function(id) return learned[id] end,
    GetNumSpellBookSkillLines=function() return 1 end,
    GetSpellBookSkillLineInfo=function() return {itemIndexOffset=0,numSpellBookItems=#spellbook} end,
    GetSpellBookItemInfo=function(slot) return spellbook[slot] end,
    IsSpellBookItemLowRank=function(slot) return spellbook[slot].lowRank end}
C_Minimap={GetNumTrackingTypes=function() return #trackingTypes end,GetTrackingInfo=function(i) return trackingTypes[i] end}
activeAuras={}
C_UnitAuras={GetPlayerAuraBySpellID=function(id) return activeAuras[id] end}
C_PetInfo={CanPetEatItem=function(id) return foods[id] and foods[id].edible end}
function C_Item.GetItemInfo(id)
    local d=foods[id]
    if not d or d.uncached then return end
    return d.name or ("Food "..id), "item:"..id, d.quality or 1,d.level or 10,d.required or 0,nil,nil,nil,nil,nil,d.price or 1
end
function C_Item.GetItemSpell(id) if itemSpells[id] then return "Eat",itemSpells[id] end end
function hevent(name)
    hunterEvents.scripts.OnEvent(hunterEvents,name)
end
function htick()
    hunterEvents.scripts.OnUpdate(hunterEvents,0.3)
end
function click(name)
    local obj=widgets[name]
    if obj.scripts.PreClick then obj.scripts.PreClick(obj) end
    local snippet=obj.attributes._onclick
    if snippet then
        secureClick=true
        loadstring("return function(self,button,down) "..snippet.." end")()(obj,"LeftButton",false)
        secureClick=false
    end
end
