-- Upon a command being used.
BasePath = ""
if BasePath == "" then
    local pathLookup = debug.getinfo(1, "S").source:sub(2)
    BasePath = pathLookup:match("(.*[/\\])") or ""
    console:log("BasePath: " .. BasePath)
end
LIB_PATH = BasePath .. "lib\\"
-- EXEC_SUFFEX = " & pause"
EXEC_SUFFEX = ""
LastSeenWarp = nil
DisableWarping = false
Forcewarp = nil
InitialLoad = false
DidSetupChecks = false

dofile(LIB_PATH .. "memory.lua")
dofile(LIB_PATH .. "final.lua")
dofile(LIB_PATH .. "ips.lua")

-- Symbols tables references (from the pret decomp work):
-- 	Ruby:
-- 		- 1.0: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokeruby.sym
-- 		- 1.1: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokeruby_rev1.sym
-- 		- 1.2: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokeruby_rev2.sym
-- 	Sapphire:
-- 		- 1.0: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokesapphire.sym
-- 		- 1.1: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokesapphire_rev1.sym
-- 		- 1.2: https://raw.githubusercontent.com/pret/pokeruby/symbols/pokesapphire_rev2.sym
-- 	Emerald:
-- 		- 1.0: https://raw.githubusercontent.com/pret/pokeemerald/symbols/pokeemerald.sym
-- 	FireRed:
-- 		- 1.0: https://raw.githubusercontent.com/pret/pokefirered/symbols/pokefirered.sym
-- 		- 1.1: https://raw.githubusercontent.com/pret/pokefirered/symbols/pokefirered_rev1.sym
-- 		- Non-English versions are based on 1.1
-- 			- Ability script offsets:
-- 				- Spanish script addresses = English 1.1 address - 0x53e
-- 				- Italian script addresses = English 1.1 address - 0x2c06
-- 				- French script addresses = English 1.1 address - 0x189e
-- 				- German script addresses = English 1.1 address + 0x4226
-- 	LeafGreen:
-- 		- 1.0: https://raw.githubusercontent.com/pret/pokefirered/symbols/pokeleafgreen.sym
-- 		- 1.1: https://raw.githubusercontent.com/pret/pokefirered/symbols/pokeleafgreen_rev1.sym

function dump(o)
    if type(o) == 'table' then
       local s = '{ '
       for k,v in pairs(o) do
          if type(k) ~= 'number' then k = '"'..k..'"' end
          s = s .. '['..k..'] = ' .. dump(v) .. ','
       end
       return s .. '} '
    else if type(o) == 'string' then
        return '"' .. o .. '"'
    else
       return tostring(o)
    end
 end
end
 

-- TODO: This should probably be by id.
-- TODO: To fix animations, we may have to use gSaveBlock1Ptr->location or gLastUsedWarp or Task_WarpAndLoadMap or IsNotWaitingForBGMStop
Roms = {}
Roms["POKEMON EMER"] = {
    romName = "Pokemon - Emerald Version (U).gba",
    offsets = {
        Party = 0x020244EC,
        PartySize = 0x020244e9,
        sWarpDestination = 0x020322e4,
        gSaveBlock1 = 0x02025a00,
        gSaveBlock1Ptr = 0x03005d8c,
        gSaveBlock2Ptr = 0x03005d90,
        vars = 0x139C,
    },
    vars = {
        VARS_START = 0x4000,
        VAR_PETALBURG_GYM_STATE = 0x4085,
        VAR_PETALBURG_CITY_STATE = 0x4057,
        VAR_STARTER_MON = 0x4023,
    },
    onSwitchCallbacks = {},
}
Roms["POKEMON FIRE"] = {
    romName = "Pokemon - Fire Red Version (U) (V1.1).gba",
    offsets = {
        Party = 0x02024284,
        PartySize = 0x02024029,
        sWarpDestination = 0x02031dbc,
        gSaveBlock1Ptr = 0x03005008,
        gSaveBlock1 = 0x0202552c, 
        gSaveBlock2Ptr = 0x0300500c,
        vars = 0x1000,
    },
    onSwitchCallbacks = {},
}
NextRom = {
    ["POKEMON EMER"] = "POKEMON FIRE", 
    ["POKEMON FIRE"] = "POKEMON EMER"
}
CurrentGameRom = nil

function ReadEventVar(var)
    local r = CurrentGameRom
    local address = emu:read32(r.offsets.gSaveBlock1Ptr) + r.offsets.vars + (var - r.vars.VARS_START) * 2
    return emu:read8(address) + emu:read8(address + 1) * 256
end
function WriteEventVar(var, value)
    -- TODO: Add support for numbers above 256 (Math!)
    local r = CurrentGameRom
    local address = emu:read32(r.offsets.gSaveBlock1Ptr) + r.offsets.vars + (var - r.vars.VARS_START) * 2
    return emu:write8(address, value)
end

function CleanupPetalburg()
    -- The Wally tutorial breaks Petalburg gym if you get any badges before doing it, so we pretend we already did it.
    local petalburg_city_state = ReadEventVar(CurrentGameRom.vars.VAR_PETALBURG_CITY_STATE)
    if petalburg_city_state < 3 then
        console:log("Updating.")
        WriteEventVar(CurrentGameRom.vars.VAR_PETALBURG_CITY_STATE, 3)
    end
    local petalburg_gym_state = ReadEventVar(CurrentGameRom.vars.VAR_PETALBURG_GYM_STATE)
    if petalburg_gym_state < 2 then
        console:log("Updating.")
        WriteEventVar(CurrentGameRom.vars.VAR_PETALBURG_GYM_STATE, 2)
    end
end
table.insert(Roms["POKEMON EMER"].onSwitchCallbacks, CleanupPetalburg)

function StatePath()
    return BasePath .. "savestates\\swapper_" .. emu:getGameTitle() .. ".ss0"
end

function RomPath(rom)
    return BasePath .. "Patched ROMs\\" .. rom.romName .. ".patched.gba"
end

function BackupOldStates()
    os.remove(StatePath() .. "_oldest.ss0")
    os.rename(StatePath() .. "_older.ss0", StatePath() .. "_oldest.ss0")
    os.rename(StatePath() .. "_old.ss0", StatePath() .. "_older.ss0")
    os.rename(StatePath(), StatePath() .. "_old.ss0")
end

function FileExists(name)
   local f=io.open(name,"r")
   if f~=nil then io.close(f) return true else return false end
end

function Exec(command)
    -- console:log("Executing command: " .. command)
    local success, _ = os.execute(command)
    return success
end

function CheckROMs(rom)
    -- TODO
end

function SetupIfNeeded()
    console:log("Doing initial setup...")
    if DidSetupChecks then
        return
    end
    -- As needed:
    for _, r in pairs(Roms) do
        if not FileExists(RomPath(r)) then
            console:log("Creating patched ROM " .. LIB_PATH .. r.romName)
            local sourceFile = BasePath .. "Put ROMs Here\\" .. r.romName
            if not FileExists(sourceFile) then
                console:log("ERROR: Missing ROM!  Please put a ROM named exactly " .. r.romName .. " in the 'Put ROMs Here' folder!")
                DisableWarping = true
                return
            end
            local destFile = RomPath(r)
            local success = Exec(string.format('copy "%s" "%s" %s', sourceFile, destFile, EXEC_SUFFEX))
            if not success then
                console:log("ERROR: Copy failed!")
                DisableWarping = true
                return                
            end
            IPSPatch(destFile, string.format("%s\\Patches\\%s.ips", LIB_PATH, r.romName))
            CheckROMs(r)
        end
    end
    DidSetupChecks = true
    console:log("\n\nAutomatic Patching completed successfully.")
    if (WarpMap == nil) then
        console:log("Please type 'NewGame()' in the prompt to randomize the warps.")
        console:log("(Add a number between the brackets to set a fixed seed.)")    
    end
end

function NewGame(seed)
    local seedArg = ""
    if seed then
        seedArg = "--seed=" .. seed
    end
    -- Call shuffle.
    local command = string.format('""%sshuffle.exe" %s --output="%sfinal.lua" --hubsroot="%shubs" %s"', LIB_PATH, seedArg, LIB_PATH, LIB_PATH, EXEC_SUFFEX)
    console:log("Running command: " .. command)
    local result = io.popen(command)
    for l in result:lines() do
        console:log(l)
    end
    result:close()
    dofile(LIB_PATH .. "final.lua")
    console:log("Randomization Complete!")
    console:log("To begin your Pokemon journey, load the Fire Red 1.1 ROM, located in the 'Patched ROMs' folder!")
end
function ng(seed) NewGame(seed) end

function LogFirstPartyMember()
    local offsets = CurrentGameRom.offsets
    local party = ReadBulk(offsets.Party, 600)
    local string = ""
    for i = 0, 99, 1 do
        string = string .. string.format("%02x ", party[i])
    end
    console:log(string)
end

function swap(panic)
    console:log(string.format("Starting swap with CurrentGame: '%s'", emu:getGameTitle()))
    local title = emu:getGameTitle()
    -- Save the Pokemon party.
    local offsets = CurrentGameRom.offsets
    local party = ReadBulk(offsets.Party, 600)
    local size = emu:read8(offsets.PartySize)
    console:log(string.format("Party of size %d", size))

    local trainerName = ReadBulk(emu:read32(offsets.gSaveBlock2Ptr) + 0, 8)
    local playerGender = emu:read8(emu:read32(offsets.gSaveBlock2Ptr) + 8)
    local trainerID = ReadBulk(emu:read32(offsets.gSaveBlock2Ptr) + 10, 4)
    console:log(string.format("Trainer Name: %s; ID: %s", dump(trainerName), dump(trainerID)))

    -- Save a savestate
    if panic == nil then
        BackupOldStates()
        emu:saveStateFile(StatePath()) 
    end

    -- Swap Games
    local nextRom = Roms[NextRom[title]]
    emu:loadFile(RomPath(nextRom))
    emu:autoloadSave()
    emu:reset()
    CurrentGameRom = Roms[emu:getGameTitle()]
    offsets = CurrentGameRom.offsets
    LastSeenWarp = nil
    
    -- Load a savestate
    if FileExists(StatePath()) then
        emu:loadStateFile(StatePath())
    else 
        if emu:getGameTitle() == "POKEMON EMER" then
            if playerGender == 0 then
                emu:loadStateFile(LIB_PATH .. "savestate_templates\\" .. "boy_template.ss0")
            else
                emu:loadStateFile(LIB_PATH .. "savestate_templates\\" .. "girl_template.ss0")
            end
        else
            console:log("ERROR: Savestate is missing!")
        end
    end

    if panic == nil then
        -- And copy in the party.
        WriteBulk(party, offsets.Party, 600)
        emu:write8(offsets.PartySize, size)
        WriteBulk(trainerName, emu:read32(offsets.gSaveBlock2Ptr) + 0, 8)
        WriteBulk(trainerID, emu:read32(offsets.gSaveBlock2Ptr) + 10, 4)
        for _, f in ipairs(CurrentGameRom.onSwitchCallbacks) do
            f()
        end
    end
end

function panic()
    swap(true)
end

-- First arg is warpId if one arg is given.
function force(mapGroup, mapNum, warpID)
    if mapGroup == nil then
        Forcewarp = nil
        return
    end
    if mapNum == nil then
        Forcewarp["warpId"] = mapGroup
    else
        Forcewarp = {
            ["warpId"] = warpID,["mapNum"] = mapNum,["y"] = 65535,["game"] = emu:getGameTitle(),["mapGroup"] = mapGroup,["x"] = 65535,
        }
    end
    console:log(dump(Forcewarp))
    DisableWarping = false
end

function f(...) force(...) end

function WhereGo(destLocation, currentLocation, currentPos)
    if Forcewarp ~= nil then
        return Forcewarp
    end
    if (WarpMap == nil) then
        console:log("ERROR: WarpMap not found.  Please run NewGame() again (or try running it with a different seed)")
        return nil
    end
    for fromGame, mapping in pairs(WarpMap) do
        if fromGame == currentLocation.game then
            for _, obj in pairs(mapping) do
                local theSame = true
                local from = obj.from
                if from.mapGroup ~= destLocation.mapGroup then theSame = false end
                if from.mapNum ~= destLocation.mapNum then theSame = false end
                if from.warpId ~= destLocation.warpId then theSame = false end
                if from.posX ~= nil and from.posX ~= currentPos.x then theSame = false end
                if from.posY ~= nil and from.posY ~= currentPos.y then theSame = false end
                if from.originMapNum ~= nil and from.originMapNum ~= currentLocation.mapNum then theSame = false end
                if theSame then 
                    return obj.to
                end
            end
        end
    end
    console:log("Could not find any valid warps for " .. dump(currentLocation) .. dump(currentPos))
    return nil
end

function disable()
    DisableWarping = true    
end
function d() disable() end

function enable()
    DisableWarping = false    
end
function e() enable() end

Reentrant = false
ReProblemLogged = false
function OnFrame()
    if Reentrant then
        if not ReProblemLogged then
            console:log("Crash in OnFrame!")
            ReProblemLogged = true
        end
        return
    end
    Reentrant = true
    CurrentGameRom = Roms[emu:getGameTitle()]
    if CurrentGameRom == nil then
        console:log(string.format("Got unexpected rom name '%s'", emu:getGameTitle()))
    end

    local warp = ReadWarp(CurrentGameRom.offsets.sWarpDestination)
    if LastSeenWarp ~= nil then
        if not WarpEquals(warp, LastSeenWarp) then
            console:log("Warp detected!")
            console:log("The game wants us to go to " .. dump(warp))
            local ptr = emu:read32(CurrentGameRom.offsets.gSaveBlock1Ptr)
            local pos = ReadPosition(ptr)
            local currentLocation = ReadWarp(ptr + 0x04)
            console:log("We are currently in " .. dump(currentLocation) .. " at position " .. dump(pos))
            if not DisableWarping then
                local realDest = WhereGo(warp, currentLocation, pos)
                console:log("Our logic has chosen to take us to " .. dump(realDest) .. " instead.")
                if realDest ~= nil then
                    if realDest.game ~= emu:getGameTitle() then
                        swap()
                    end
                    WriteWarp(CurrentGameRom.offsets.sWarpDestination, realDest)
                end                    
            end
        end
    end
    LastSeenWarp = ReadWarp(CurrentGameRom.offsets.sWarpDestination)
    Reentrant = false
end
CallBackId = callbacks:add("frame", OnFrame)
SetupIfNeeded()

function Echo(...)
    console:log(...)
end

console:log("Good luck.")