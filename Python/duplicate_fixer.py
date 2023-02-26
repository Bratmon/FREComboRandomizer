# Correct duplicates in the wrong place.
import argparse, os, json

argParser = argparse.ArgumentParser()
argParser.add_argument('--hubsroot', type=str, help="Root directory of the hubs files", default="hubs")

def isTooFar(warpA, warpB):
    return abs(warpA["x"] - warpB["x"]) > 1 or abs(warpA["y"] - warpB["y"]) > 1

def isGoodSolution(currentW, proposedW):
    for w in [currentW] + currentW["duplicates"]:
        if isTooFar(w, proposedW):
            return False
    return True

# Returns true if we need to write the new json.
def handleJfile(jfile, fileName):
    clean = True
    for i, hub in enumerate(jfile["hubs"]):
        for j, w in enumerate(hub["warps"]):
            if len(w["duplicates"]) > 1:
                if not isGoodSolution(w, w):
                    for d in w["duplicates"]:
                        if isGoodSolution(w, d):
                            print(fileName + "/" + str(i), "has a suspicious hub. Fixing.")
                            clean = False
                            w["duplicates"].remove(d)
                            d["duplicates"] = w["duplicates"]
                            d["duplicates"].append(w)
                            w["duplicates"] = []
                            hub["warps"][j] = d
                            break
    return not clean


def main():
    args = argParser.parse_args()
    print("Loading hub json files...")
    for game in os.listdir(args.hubsroot):
        for fileName in os.listdir(os.path.join(args.hubsroot, game)):
            jfile = json.load(open(os.path.join(args.hubsroot, game, fileName)))
            if handleJfile(jfile, fileName):
                json.dump(jfile, open(os.path.join(args.hubsroot, game, fileName), "w"), indent=2)


if __name__ == "__main__":
    main()