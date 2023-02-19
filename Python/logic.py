import random, itertools

random.seed()

global SpoilerString
SpoilerString = ""

class State:
    def __init__(self):
        self.currentHubs = []
        self.potentialHubs = []
        self.potentialHallways = []
        self.potentialProviderDeadEnds = []
        self.potentialNonProviderDeadEnds = []
        self.missingRequirementHubs = []
        self.oneWayHubs = []
        self.currentFlags = []

def shortestPathToProvider(currentHubs, target):
    finalResult = ""
    queue = []
    for h in currentHubs:
        if "always_available" in h and h["always_available"]:
            queue.append((h, h["name"] + " -> "))
    while queue:
        e = queue.pop()
        hub = e[0]
        if "visited" in hub:
            continue
        hub["visited"] = True
        if "provides" in hub and target in hub["provides"]:
            finalResult = e[1] + target
            break
        for l in hub["links"]:
            queue.append((l, e[1] + l["name"] + " -> "))
    for h in currentHubs:
        if "visited" in h:
            del h["visited"]
    if not finalResult:
        raise "Despite just adding " + target + " we couldn't find it."
    return finalResult

def findUnlinkedWarp(hub):
    uws = [w for w in hub["warps"] if not "partner" in w]
    if len(uws) == 0:
        return None
    return random.choice(uws)

def findHubWithUnlinkedWarp(hubs):
    hs = hubs[:]
    random.shuffle(hs)
    for h in hs:
        warp = findUnlinkedWarp(h)
        if warp != None:
            return h
    raise Exception("Could not find any unlinked warp among " + len(hubs) + " hubs.")

def link(hubA, hubB):
    hubA["links"].append(hubB)
    hubB["links"].append(hubA)
    warpA = findUnlinkedWarp(hubA)
    warpB = findUnlinkedWarp(hubB)
    if "warps" in warpA:
        print(hubA["name"],"<3",hubB["name"])
        raise "We got a hub in our warps!"
    if "warps" in warpB:
        print(hubA["name"],"<3",hubB["name"])
        raise "We got a hub in our warps!"        
    warpA["partner"] = warpB
    warpB["partner"] = warpA


def metRequirements(currentFlags, h):
    if not "requirements" in h:
        return True
    for req in h["requirements"]:
        if not req in currentFlags:
            return False
    return True

def sortHub(state, h):
    s = state
    if not metRequirements(s.currentFlags, h):
        # print("Adding",h["name"],"to mr.")
        s.missingRequirementHubs.append(h)
    elif h.get("always_available"):
        moveToCurrent(s, h)
    elif len(h.get("warps")) > 2:
        s.potentialHubs.append(h)
    elif len(h.get("warps")) == 2:
        s.potentialHallways.append(h)
    elif h.get("provides"):
        s.potentialProviderDeadEnds.append(h)
    elif h.get("one_way"):
        s.oneWayHubs.append(h)
    else:
        s.potentialNonProviderDeadEnds.append(h)

def newlyMetRequirements(missingRequirementHubs, currentFlags):
    return [h for h in missingRequirementHubs if metRequirements(currentFlags, h)]

def moveToCurrent(state, h):
    s = state
    # print("Adding hub", h["name"])
    [l.remove(h) for l in [s.potentialHubs, s.potentialHallways, s.potentialProviderDeadEnds] if h in l]
    if not "warps" in h:
        print(h["name"] + " is invalid!")
        raise
    if not (h.get("always_available")):
        link(findHubWithUnlinkedWarp(s.currentHubs), h)
    s.currentHubs.append(h)
    if h.get("provides"):
        for p in h.get("provides"):
            if not p in s.currentFlags:
                s.currentFlags.append(p)
                global SpoilerString
                SpoilerString += shortestPathToProvider(s.currentHubs, p) + "\n"
        while newlyMetRequirements(s.missingRequirementHubs, s.currentFlags):
            nmr = newlyMetRequirements(s.missingRequirementHubs, s.currentFlags).pop()
            s.missingRequirementHubs.remove(nmr)
            sortHub(s, nmr)

def countOpenEnds(group):
    count = 0
    for g in group:
        for w in g["warps"]:
            if not "partner" in w:
                count += 1
    return count

def doLogic(allHubs):
    ah = allHubs[:]
    random.shuffle(ah)
    for h in ah:
        h["links"] = []
    s = State()
    for hub in ah:
        sortHub(s, hub)
    
    # Link the two games somewhere early.
    if len(s.currentHubs) != 2:
        raise "Unexpected number of starting hubs."
    link(s.currentHubs[0], s.currentHubs[1])

    # Move all one way hubs to end at the beginning.
    for owh in s.oneWayHubs:
        for w in owh["warps"]:
            w["partner"] = random.choice(random.choice(s.currentHubs)["warps"])

    while True:
        possibleNextHubs = s.potentialHubs + s.potentialHallways + s.potentialProviderDeadEnds
        if len(possibleNextHubs) == 0:
            break
        newHub = random.choice(possibleNextHubs)
        moveToCurrent(s, newHub)        

    print("All hubs and providers are added.  Adding", len(s.potentialNonProviderDeadEnds), "dead ends.")
    for h in s.potentialNonProviderDeadEnds:
        link(findHubWithUnlinkedWarp(s.currentHubs), h)
        s.currentHubs.append(h)
    s.potentialNonProviderDeadEnds = []

    print("All the hubs are linked together. Moving to self links.")
    allUnlinkedWarps = []
    for hu in s.currentHubs:
        for uw in hu["warps"]:
            if not "partner" in uw:
                allUnlinkedWarps.append(uw)
    random.shuffle(allUnlinkedWarps)
    print("We have", len(allUnlinkedWarps), "spare warps.")
    if len(allUnlinkedWarps) % 2 != 0:
        print("Warning! Odd number of unlinked warps:", len(allUnlinkedWarps), "There's going to be a self warp.")
        unlucky = allUnlinkedWarps.pop()
        unlucky["partner"] = unlucky
    for i in range(0, len(allUnlinkedWarps), 2):
        allUnlinkedWarps[i]["partner"] = allUnlinkedWarps[i + 1]
        allUnlinkedWarps[i + 1]["partner"] = allUnlinkedWarps[i]
    
    if s.missingRequirementHubs:
        print("Error: Some hubs never got their requirements fufilled!")
        for m in s.missingRequirementHubs:
            print(m["name"])
            for mr in m["requirements"]:
                if not mr in s.currentFlags:
                    print("Missing", mr)
    return (s.currentHubs + s.oneWayHubs, SpoilerString)

        
        

