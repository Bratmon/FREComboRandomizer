import sys, os, json

games = [
    {
        "name": "POKEMON EMER",
        "path": "pokeemerald"
    },
    {
        "name": "POKEMON FIRE",
        "path": "pokefirered"
    }
]


class Warp():
    def __init__(self, x, y, ourMapGroup, ourMapNum, ourID, destID, destMapString, gameName):
        self.x = x
        self.y = y
        self.ourMapGroup = ourMapGroup
        self.ourMapNum = ourMapNum
        self.ourID = ourID
        self.destID = destID
        self.destMapString = destMapString
        self.gameName = gameName
        self.destMapGroup = None
        self.destMapNum = None
        self.duplicates = []

    def toJsonable(self):
        result = self.__dict__.copy()
        result["duplicates"] = [d.toJsonable() for d in self.duplicates]
        return result

def withinOneOf(a,b):
    return abs(a - b) <= 1

def duplicateOf(warps, potential):
    for w in warps:
        if potential.destMapString == w.destMapString:
            if withinOneOf(w.destID, potential.destID) and withinOneOf(w.x, potential.x) and withinOneOf(w.y, potential.y):
                return w
            for d in w.duplicates:
                if withinOneOf(d.destID, potential.destID) and withinOneOf(d.x, potential.x) and withinOneOf(d.y, potential.y):
                    return w
    return None

maps_needing_flash = []

def parseGame(game):
    grp = open(os.path.join("maps", game["path"], "map_groups.json"), "r")
    grps = json.load(grp)
    group_order = grps["group_order"]
    mapStrings_to_group_map = {}
    allMapWarps = {}
    for groupNum, group in enumerate(group_order):
        for mapNum, mapDir in enumerate(grps[group]):
            mapWarps = []
            mapFile = open(os.path.join("maps", game["path"], mapDir, "map.json"))
            mapJson = json.load(mapFile)
            mapStrings_to_group_map[mapJson["id"]] = (groupNum, mapNum)
            if mapJson["requires_flash"]:
                maps_needing_flash.append(mapDir)
            if not "warp_events" in mapJson.keys():
                continue
            for warpNum, warp in enumerate(mapJson["warp_events"]):
                if warp["dest_warp_id"] in ["WARP_ID_DYNAMIC", "WARP_ID_SECRET_BASE"]:
                    continue
                warp = Warp(int(warp["x"]), int(warp["y"]), groupNum, mapNum, warpNum, int(warp["dest_warp_id"]), warp["dest_map"], game["name"])
                dup = duplicateOf(mapWarps, warp)
                if dup == None:
                    mapWarps.append(warp)
                else:
                    dup.duplicates.append(warp)
            allMapWarps[mapDir] = mapWarps
            print("Finished map", mapDir)

    for _, w in allMapWarps.items():
        for m in w:
            if m.destMapString == "MAP_DYNAMIC":
                continue
            m.destMapGroup = mapStrings_to_group_map[m.destMapString][0]
            m.destMapNum = mapStrings_to_group_map[m.destMapString][1]
            for d in m.duplicates:
                d.destMapGroup = mapStrings_to_group_map[m.destMapString][0]
                d.destMapNum = mapStrings_to_group_map[m.destMapString][1]

    return allMapWarps

def main():
    gameWarps = {}
    for g in games:
        gameWarps[g["name"]] = parseGame(g)

    for game, warps in gameWarps.items():
        os.makedirs(os.path.join("clean_output", game), exist_ok=True)
        for dir, mapWarps in warps.items():
            if len(mapWarps) == 0:
                continue
            oneWarpDicts = [w.toJsonable() for w in mapWarps]
            j = {"hubs": [{"requirements": [], "warps": oneWarpDicts}]}
            if dir in maps_needing_flash:
                j["hubs"][0]["requirements"] = ["FLASH"]
            json.dump(j, open(os.path.join("clean_output", game, dir + ".json"), "x"), indent=2)
        

if __name__ == "__main__":
    main()