function ReadBulk(offset, count)
    -- Returns a 0-indexed array
    -- I know this is lua, but this is actually a memory offset here, so 0-indexed makes sense.
    -- Sue me.
    local result = {}
    for i = 0, count - 1 do
        result[i] = emu:read8(offset + i)
    end
    return result
end

function WriteBulk(table, offset, count)
    -- table is 0-indexed.
    -- Sue me.
    for i = 0, count - 1 do
        emu:write8(offset + i, table[i])
    end
end

function ReadWarp(address)
    local result = {}
    result.mapGroup = emu:read8(address)
    result.mapNum = emu:read8(address + 1)
    result.warpId = emu:read8(address + 2)
    -- 8 bytes padding
    result.x = emu:read16(address + 4)
    result.y = emu:read16(address + 6)
    result.game = emu:getGameTitle()
    return result
end

function WriteWarp(address, warp)
    emu:write8(address, warp.mapGroup)
    emu:write8(address + 1, warp.mapNum)
    emu:write8(address + 2, warp.warpId)
    -- 8 bytes padding
    emu:write16(address + 4, warp.x)
    emu:write16(address + 6, warp.y)
end

function ReadPosition(address)
    local result = {}
    result.x = emu:read16(address)
    result.y = emu:read16(address + 2)
    return result
end

function WarpEquals(a, b)
    if a == nil or b == nil then return false end
    return a.mapGroup == b.mapGroup and a.mapNum == b.mapNum and a.warpId == b.warpId
end