# coding=utf-8
import glob, mmap, struct, thread, json, time


class Replay:
    debug = 0
    writeInterJSON = 0
    globalReplayData = dict()
    globalTankTypeByDscr = dict()
    globalTankTierByDscr = dict()
    globalTankPremByDscr = dict()

    def __init__(self, filename):
        self.__parseReplay(self, filename)

    def __readBlock(self, mFile, offset, numBlock, filename):
        dataLength = struct.unpack('<I', mFile[offset:4+offset])[0]
        offset += 4
        data = mFile[offset:dataLength+offset]
        if self.debug:
            print 'dataLength =', dataLength
            print data
        jsonData = json.loads(data)
        if numBlock == 1:
            self.globalReplayData[filename] = [jsonData]
        else:
            if "vehicles" in self.globalReplayData[filename][0].keys():
                del self.globalReplayData[filename][0]["vehicles"]
            self.globalReplayData[filename].append([jsonData])
        if self.writeInterJSON:
            with open('./test' + str(numBlock) + '.json', 'w') as jsonFile:
                jsonFile.write(json.dumps(jsonData, sort_keys=True, indent=4))
        return dataLength + 4

    def __parseReplay(self, filename):
        try:
            with open(filename, 'r+b') as f:
                content = mmap.mmap(f.fileno(), 0)
                if self.debug:
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
                            blockLength = self.__readBlock(content, offset, i+1, filename)
                            offset += blockLength
                        except:
                            print "ParseReplay error : offset="+str(offset)+", blockIndice="+str(i+1)+", file="+filename
                            break
                content.close()
        except:
            print "Cannot parse " + filename

    def getVehicleType(self, typeCompDescr):
        return self.globalTankTypeByDscr[typeCompDescr]

    def parseTanks(self):
        with open("./tanks.json", "r") as fd:
            data = fd.read()
            tanksList = json.loads(data)
            for tank in tanksList:
                dscr = tank["compDescr"]
                type = tank["type"]
                tier = tank["tier"]
                isPrem = tank["premium"]
                self.globalTankTypeByDscr[dscr] = type
                self.globalTankTierByDscr[dscr] = tier
                self.globalTankPremByDscr[dscr] = isPrem
