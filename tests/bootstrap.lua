now, class = 0, "HUNTER"
A, bags, sizes, C_Item = {}, {}, {}, {}
for bag=0,4 do bags[bag]={}; sizes[bag]=0 end
sizes[0]=16
function item(id,count) return {itemID=id,stackCount=count,isLocked=false} end
function UnitClass() return class,class end
function InCombatLockdown() return combat end
function GetTime() return now end
C_Container={GetContainerNumSlots=function(bag) return sizes[bag] end,
    GetContainerItemInfo=function(bag,slot) return bags[bag][slot] end}
