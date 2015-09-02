# coding=utf-8
import glob, mmap, struct, thread, json, time

debug = 0
writeInterJSON = 0
globalReplayData = dict()
globalTankTypeByDscr = dict()
globalTankTierByDscr = dict()
globalTankPremByDscr = dict()


def readBlock(mFile, offset, numBlock, filename):
    dataLength = struct.unpack('<I', mFile[offset:4+offset])[0]
    offset += 4
    data = mFile[offset:dataLength+offset]
    if debug:
        print 'dataLength =', dataLength
        print data
    jsonData = json.loads(data)
    if numBlock == 1:
        globalReplayData[filename] = [jsonData]
    else:
        if "vehicles" in globalReplayData[filename][0].keys():
            del globalReplayData[filename][0]["vehicles"]
        globalReplayData[filename].append([jsonData])
    if writeInterJSON:
        with open ('./test' + str(numBlock) +'.json', 'w') as jsonFile:
            jsonFile.write(json.dumps(jsonData, sort_keys=True, indent=4))
    return dataLength + 4


def parseReplay(filename):
    try:
        with open(filename, 'r+b') as f:
            content = mmap.mmap(f.fileno(), 0)
            if debug:
                print len(content)/1000, 'Ko'
            # Skip magic number (4 o)
            offset = 4
            # Read Block count : 2 = replay complete (4 o)
            blockCount = struct.unpack('<I', content[offset:4+offset])[0]
            offset += 4
            # 1st block = "Match start" in json
            # If 2 blocks, the 2nd block = "Battle result" in json
            # If 3 blocks, the 2nd block = "Match End" in json and the 3rd = "Battle result" in json
            if blockCount > 2:
                # Problem
                print "ParseReplay error : offset="+str(offset)+", blockCount="+str(blockCount)+", file="+filename
            else:
                for i in range(0, blockCount):
                    try:
                        blockLength = readBlock(content, offset, i+1, filename)
                        offset = offset + blockLength
                    except:
                        print "ParseReplay error : offset="+str(offset)+", blockIndice="+str(i+1)+", file="+filename
                        break
            content.close()
    except:
        print "Cannot parse " + filename


def threadFcn(filename, nbFiles, cpt):
    parseReplay(file)
    print cpt, '/', nbFiles, cpt*100/nbFiles, '%'
    cpt += 1


def versions():
    # on créé un nouveau dict
    replayVersions = dict()
    # on parcourt les replays
    for replay in globalReplayData.values():
        # on récupère la version
        replayVersion = replay[0]["clientVersionFromXml"]
        if replayVersion in replayVersions:
            replayVersions[replayVersion] += 1
        else:
            replayVersions[replayVersion] = 1
    print json.dumps(replayVersions, sort_keys=True, indent=4)


def getVehicleType(typeCompDescr):
    return globalTankTypeByDscr[typeCompDescr]


def avgArtyPerHalfHour():
    nbArty = [0.0 for i in range(48)];
    nbGames = [0 for i in range(48)];

    for replay in globalReplayData.values():
        if len(replay) > 1 & replay[0]["battleType"] == 1:
            hour = time.localtime(replay[1][0][0]["common"]["arenaCreateTime"])
            idHour = hour.tm_hour * 2 + (hour.tm_min > 30)
            nbGames[idHour] += 1
            cptArty = 0
            # on compte les artys
            playerList = replay[1][0][0]["vehicles"]
            for player in playerList:
                if "typeCompDescr" in playerList[player]:
                    type = playerList[player]["typeCompDescr"]
                    try:
                        type = globalTankTypeByDscr[type]
                    except:
                        print "Unknown vehicle dscr: " + str(type) + ", name: " + replay[1][0][1][player]["vehicleType"]
                        continue
                    if type == 5:  # SPG
                        nbArty[idHour] += 1
    # moyenne sur toutes les parties
    for i in range(48):
        if nbGames[i] != 0:
            nbArty[i] /= nbGames[i]
    print nbArty
    cvs = ""
    for i in range(48):
        cvs += str(nbArty[i]) + ";"
    print cvs
    cvs = ""
    for i in range(48):
        cvs += str(nbGames[i]) + ";"
    print cvs


def parseTanks():
    with open("./tanks.json", "r") as fd:
        data = fd.read()
        tanksList = json.loads(data)
        for tank in tanksList:
            dscr = tank["compDescr"]
            type = tank["type"]
            tier = tank["tier"]
            isPrem = tank["premium"]
            globalTankTypeByDscr[dscr] = type
            globalTankTierByDscr[dscr] = tier
            globalTankPremByDscr[dscr] = isPrem


def tierAnalysis():
    tierList = range(1, 11)
    tierSpread = dict()
    tierSpreadAvg = dict()
    tierSpreadPl = dict()
    tierSpreadAvgPl = dict()
    for tier in tierList:
        tierSpread[tier] = [0, 0, 0, 0, 0]
        tierSpreadAvg[tier] = 0
        tierSpreadPl[tier] = [0, 0, 0, 0, 0]
        tierSpreadAvgPl[tier] = 0
    for replay in globalReplayData.values():
        # need to find max tier value of this replay
        if len(replay) > 1 and replay[0]["battleType"] == 1:
            # retrieve player's tier
            playerId = replay[0]["playerID"]
            if playerId == 0:
                continue
            isInPlatoon = replay[1][0][0]["players"][str(playerId)]["prebattleID"] != 0
            currentTier = -1
            maxTier = 1
            playerList = replay[1][0][0]["vehicles"]
            for player in playerList:
                if "typeCompDescr" in playerList[player]:
                    tier = playerList[player]["typeCompDescr"]
                    type = playerList[player]["typeCompDescr"]
                    prem = playerList[player]["typeCompDescr"]
                    try:
                        tier = globalTankTierByDscr[tier]
                        type = globalTankTypeByDscr[type]
                        prem = globalTankPremByDscr[prem]
                    except:
                        print "Unknown vehicle dscr: " + str(tier) + ", name: " + replay[1][0][1][player]["vehicleType"]
                        continue
                    if type == 1:  # light tank
                        continue
                    if prem == 1:
                        continue
                    if tier > maxTier:
                        maxTier = tier
                    if playerList[player]["accountDBID"] == playerId:
                        currentTier = tier
            if currentTier < 0:
                print "Corrupted replay, cannot find current player, version: " + replay[0]["clientVersionFromXml"]
            else:
                tierDiff = maxTier - currentTier
                if isInPlatoon:
                    tierSpreadPl[currentTier][tierDiff] += 1
                else:
                    tierSpread[currentTier][tierDiff] += 1
    for tier in tierList:
        avgTier = tierSpread[tier][1] + 2 * tierSpread[tier][2] + 3 * tierSpread[tier][3] + 4 * tierSpread[tier][4]
        avgTierPl = tierSpreadPl[tier][1] + 2 * tierSpreadPl[tier][2] + 3 * tierSpreadPl[tier][3] + 4 * tierSpreadPl[tier][4]
        sum = tierSpread[tier][0] + tierSpread[tier][1] + tierSpread[tier][2] + tierSpread[tier][3] + tierSpread[tier][4]
        sumPl = tierSpreadPl[tier][0] + tierSpreadPl[tier][1] + tierSpreadPl[tier][2] + tierSpreadPl[tier][3] + tierSpreadPl[tier][4]
        if sum != 0:
            avgTier /= tierSpread[tier][0] + tierSpread[tier][1] + tierSpread[tier][2] + tierSpread[tier][3] + tierSpread[tier][4] + 0.0
        else:
            avgTier = 0
        if sumPl != 0:
            avgTierPl /= tierSpreadPl[tier][0] + tierSpreadPl[tier][1] + tierSpreadPl[tier][2] + tierSpreadPl[tier][3] + tierSpreadPl[tier][4] + 0.0
        else:
            avgTierPl = 0
        tierSpreadAvg[tier] = avgTier
        tierSpreadAvgPl[tier] = avgTierPl
    print tierSpreadAvg
    print tierSpread
    print tierSpreadAvgPl
    print tierSpreadPl


def dumpGlobalData():
    file = open("./global.json", "w")
    file.write(json.dumps(globalReplayData, indent=4))
    file.close()


def parseAllReplays(folder):
    nbFiles = len(folder)
    cpt = 0
    for file in folder:
        cpt += 1
        try:
            parseReplay(file)
        except:
            print "Cannot parse " + file
        print cpt, '/', nbFiles, cpt*100/nbFiles, '%'

# files = glob.glob("/media/adminesque/Data1/Games/World_of_Tanks/replays/*.wotreplay")
# files = glob.glob("C:\Games\World_of_Tanks - FFA\Replays\*.wotreplay")
# files = glob.glob("./*.wotreplay")

# parseAllReplays(files)
# parseTanks()
# versions()
# avgArtyPerHalfHour()
# tierAnalysis()
# raw_input()
