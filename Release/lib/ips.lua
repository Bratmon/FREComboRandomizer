-- Adapted from https://github.com/thenumbernine/lua-ips/

local data = nil
local patch = nil

local patchIndex = 0
local function readPatchChunk(size)
	local chunk = assert(patch:sub(patchIndex+1, patchIndex + size), "stepped past the end of the file")
	patchIndex = patchIndex + size
	return chunk
end

local function rawToNumber(d)
	-- msb first
	local v = 0
	for i=1,#d do
		v = v * 256
		v = v + d:sub(i,i):byte()
	end
	return v
end

-- offset is 1-based
local function replaceSubset(d, repl, offset)
	if offset <= #d then
		d = d:sub(1, offset-1) .. repl .. d:sub(offset + #repl)
	else
		d = d .. string.char(0):rep(offset - #d - 1) .. repl
	end
	return d
end

function IPSPatch(dataFile, patchFile)
    data = assert(io.open(dataFile, "rb"):read("a"), "Missing ROM!")
    patch = assert(io.open(patchFile, "rb"):read("a"), "Missing patch!")
    patchIndex = 0

    local sig = readPatchChunk(5)
    assert(sig == 'PATCH', "got bad signature: "..tostring(sig))
    while true do
        local offset = readPatchChunk(3)
        if offset == 'EOF' then
            break
        end	-- what if you want an offset that has this value? ips limitations...
        offset = rawToNumber(offset)
        local size = rawToNumber(readPatchChunk(2))
        if size > 0 then
            local subpatch = readPatchChunk(size)
            data = replaceSubset(data, subpatch, offset+1)
        else	--RLE
            local rleSize = rawToNumber(readPatchChunk(2))
            local value = rawToNumber(readPatchChunk(1))
            data = replaceSubset(data, value:rep(rleSize), offset+1)
        end
    end

    io.open(dataFile, "wb"):write(data)
end
