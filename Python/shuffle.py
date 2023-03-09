import argparse, os, json, random
from collections import defaultdict

import logic

argParser = argparse.ArgumentParser()
argParser.add_argument('--seed', type=str, help="The seed (If not present, one will be generated.)")
argParser.add_argument('--spoiler', help="Location to dump the spoiler file.")
argParser.add_argument('--output', help="Location for output.  If not set, output will not be generated.", default="final.lua")
argParser.add_argument('--seedfile', help="Dump the seed in a human-readable way to this file.", default="seed.txt")
argParser.add_argument('--hubsroot', type=str, help="Root directory of the hubs files", default="hubs")

class WarpMapEntry:
    def __init__(self, fromWarpID, fromMapNum, fromMapGroup, fromGame, toWarpID, toMapNum, toMapGroup, toGame, 
                 fromOurX = None, fromOurY = None, fromOurMapNum=None, varIndex=None, varSet=None):
        self.fromWarpID = fromWarpID
        self.fromMapNum = fromMapNum
        self.fromMapGroup = fromMapGroup
        self.fromGame = fromGame
        self.fromOurX = fromOurX
        self.fromOurY = fromOurY
        self.fromOurMapNum = fromOurMapNum
        self.toWarpID = toWarpID
        self.toMapNum = toMapNum
        self.toMapGroup = toMapGroup
        self.toGame = toGame
        self.varIndex = varIndex
        self.varSet = varSet

    def toString(self):
        ourXYString = ""
        if self.fromOurX:
            ourXYString = '["posX"] = %i,["posY"] = %i, ["originMapNum"] = %i,' % (self.fromOurX, self.fromOurY, self.fromOurMapNum)
        varSetString = ""
        if self.varIndex:
            varSetString = '["varIndex"] = "%s", ["varSet"] = %i,' % (self.varIndex, self.varSet)
        return """{
from = { ["warpId"] = %i,["mapNum"] = %i,["y"] = 65535,["mapGroup"] = %i,["x"] = 65535, %s},
to = { ["warpId"] = %i,["mapNum"] = %i,["y"] = 65535,["game"] = "%s",["mapGroup"] = %i,["x"] = 65535, %s} 
},
""" % (self.fromWarpID, self.fromMapNum, self.fromMapGroup, ourXYString, self.toWarpID, self.toMapNum, self.toGame, self.toMapGroup, varSetString)

allHubs = []
deadEndCounts = defaultdict(lambda: 0)
def handleHub(hub, fileName):
    allHubs.append(hub)
    if len(hub["warps"]) == 1 and not "always_available" in hub:
        deadEndCounts[fileName] = deadEndCounts[fileName] + 1

"""
WarpMap = {
    {
        from = { ["warpId"] = 0,["mapNum"] = 1,["y"] = 65535,["game"] = "POKEMON EMER",["mapGroup"] = 2,["x"] = 65535,},
        to = { ["warpId"] = 1,["mapNum"] = 1,["y"] = 65535,["game"] = "POKEMON FIRE",["mapGroup"] = 3,["x"] = 65535,} 
    },
    {
        from = { ["warpId"] = 1,["mapNum"] = 0,["y"] = 65535,["game"] = "POKEMON FIRE",["mapGroup"] = 5,["x"] = 65535,} ,
        to = { ["warpId"] = 0,["mapNum"] = 1,["y"] = 65535,["game"] = "POKEMON EMER",["mapGroup"] = 2,["x"] = 65535,},
    }
}
"""

def findPartner(allWarps, w):
    for other in allWarps:
        for d in [other] + other["duplicates"]:
            if w["destID"] == d["ourID"] and w["destMapNum"] == d["ourMapNum"] and w["destMapGroup"] == d["ourMapGroup"] and w["gameName"] == d["gameName"]:
                return other
    return None

def createFinalMapping(finalMappings, a, b, include_xy):
    ax = a["x"] if include_xy else None
    ay = a["y"] if include_xy else None
    amn = a["ourMapNum"] if include_xy else None
    finalMappings.append(WarpMapEntry(a["destID"], a["destMapNum"], a["destMapGroup"], a["gameName"], b["ourID"], b["ourMapNum"], b["ourMapGroup"], b["gameName"], ax, ay, amn, b.get("varIndex"), b.get("varSet")))
    for d in a["duplicates"]:
        dx = d["x"] if include_xy else None
        dy = d["y"] if include_xy else None
        dmn = d["ourMapNum"] if include_xy else None
        finalMappings.append(WarpMapEntry(d["destID"], d["destMapNum"], d["destMapGroup"], d["gameName"], b["ourID"], b["ourMapNum"], b["ourMapGroup"], b["gameName"], dx, dy, dmn, b.get("varIndex"), b.get("varSet")))
    # finalMappings.append(WarpMapEntry(b["destID"], b["destMapNum"], b["destMapGroup"], b["gameName"], a["ourID"], a["ourMapNum"], a["ourMapGroup"], a["gameName"]))
    # for d in b["duplicates"]:
    #    finalMappings.append(WarpMapEntry(d["destID"], d["destMapNum"], d["destMapGroup"], d["gameName"], a["ourID"], a["ourMapNum"], a["ourMapGroup"], a["gameName"]))            

def validateAllWarps(allHubs):
    allWarps = []   
    for h in allHubs:
        for w in h["warps"]:
            if not "xy_required" in h:
                for aw in allWarps:
                    if w["destID"] == aw["destID"] and w["destMapGroup"] == aw["destMapGroup"] and w["destMapNum"] == aw["destMapNum"] and w["gameName"] == aw["gameName"]:
                        print("WARNING!  Warp", w, "and warp", aw, "from hub", h["name"],"have the same destination but are not marked as duplicates or xy_required!  The lua script will break!")
            allWarps.append(w)

def countDeadEnds():
    print("Top dead ends:")
    s = sorted(deadEndCounts.items(), key=lambda a: a[1])
    for f in s:
        print("{}: {}".format(f[1], f[0]))

def shuffle():
    (finalHubs, spoilerString) = logic.doLogic(allHubs)

    finalMappings = []
    for h in finalHubs:
        for w in h["warps"]:
            p = w["partner"]
            createFinalMapping(finalMappings, w, p, "xy_required" in h)
    return (finalMappings, spoilerString)

def finish(finalMappings, spoilerTxt, outFileName, spoilerFileName, seedFileName, seed):
    perGameWarpMappings = {}
    for m in finalMappings:
        if not m.fromGame in perGameWarpMappings:
            perGameWarpMappings[m.fromGame] = [m]
        else:
            perGameWarpMappings[m.fromGame].append(m)
    if outFileName:
        outfile = open(outFileName, "w")
        outfile.write("-- Generated with Combo Randomizer shuffle.py from seed " + seed + "\n")
        outfile.write("WarpMap = {")
        for g in perGameWarpMappings:
            outfile.write('["%s"] = {' % g)
            for m in perGameWarpMappings[g]:
                outfile.write(m.toString())
            outfile.write("},")
        outfile.write("}")

    if spoilerFileName:
        spoilerFile = open(spoilerFileName, "w")
        spoilerFile.write(spoilerTxt)

    if seedFileName:
        seedFile = open(seedFileName, "w")
        seedFile.write("Generated with Combo Randomizer from seed " + seed + "\n")


def main():
    args = argParser.parse_args()
    print("Welcome to the shuffler!")
    seed = args.seed
    if not seed:
        seed = str(random.randint(0, 1000000))
        print("No seed was given, so we'll randomly use", seed)
    random.seed(seed)
    print("Loading hub json files...")
    for game in os.listdir(args.hubsroot):
        for fileName in os.listdir(os.path.join(args.hubsroot, game)):
            jfile = json.load(open(os.path.join(args.hubsroot, game, fileName)))
            for i, hub in enumerate(jfile["hubs"]):
                hub["name"] = fileName + "_" + str(i)
                handleHub(hub, fileName)
    print("Validating JSON files.")
    validateAllWarps(allHubs)
    # countDeadEnds()
    print(len(allHubs),"total hubs")
    print("Starting logic.")
    (finalMappings, spoilerTxt) = shuffle()
    finish(finalMappings, spoilerTxt, args.output, args.spoiler, args.seedfile, seed)
    print("Finished generating with seed",seed) 

if __name__ == "__main__":
    main()