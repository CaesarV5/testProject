from PyQt4.QtGui import *
from PyQt4.QtCore import *
from replayParser import *
from threading import Thread
import glob
import sys
import subprocess


class MyProgressBar(QProgressBar):

    def __init__(self):
        QProgressBar.__init__(self)
        self.setAlignment(Qt.AlignCenter)
        self._text = ""

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text


class Application:
    replayPath = "C:\Games\World_of_Tanks - FFA\Replays"
    replayList = []
    isParsing = False
    folderHasChanged = True
    sortedReplays = list()

    def __init__(self):
        self.main()
        parseTanks()

    def main(self):
        self.app = QApplication(sys.argv)
        self.mainWindow = QWidget()
        self.mainWindow.setWindowTitle("WoT Replay Parser")
        self.mainWindow.resize(800, 600)

        self.selectFolderButton = QPushButton(QString("Select replay folder"))
        self.selectFolderButton.setFixedHeight(30)
        QObject.connect(self.selectFolderButton, SIGNAL('clicked()'), self.selectFolder)

        self.folderLabel = QLabel(self.replayPath)
        self.folderLabel.setFixedHeight(30)

        self.updateButton = QPushButton(QString("Update"))
        self.updateButton.setFixedHeight(30)
        QObject.connect(self.updateButton, SIGNAL('clicked()'), self.update)

        self.progBar = MyProgressBar()
        self.progBar.setFixedHeight(30)
        self.progBar.setTextVisible(True)

        self.replayTable = QTableWidget()
        self.replayTable.setContextMenuPolicy(Qt.CustomContextMenu)
        def openMenu(position):
            menu = QMenu()
            openAction = menu.addAction("Open in folder")
            action = menu.exec_(self.replayTable.mapToGlobal(position))
            itemClicked = self.replayTable.itemAt(position)
            row = itemClicked.row()
            replayItem = self.replayTable.item(row, 0)
            if action == openAction:
                fullReplayPath = self.replayPath + '\\' + replayItem.text()
                subprocess.Popen(r'explorer /select, "' + str(fullReplayPath) + '"')
        self.replayTable.customContextMenuRequested.connect(openMenu)

        self.layout = QGridLayout()
        self.layout.addWidget(self.selectFolderButton, 0, 0)
        self.layout.addWidget(self.folderLabel, 0, 1, 1, 2)
        self.layout.addWidget(self.updateButton, 0, 3)
        self.layout.addWidget(self.progBar, 1, 0, 1, 4)
        self.layout.addWidget(self.replayTable, 2, 0, 8, 4)

        self.mainWindow.setLayout(self.layout)
        self.mainWindow.show()
        return self.app.exec_()

    def selectFolder(self):
        folder = str(QFileDialog.getExistingDirectory(None, "Select WoT replay folder", self.replayPath))
        if folder != self.replayPath:
            self.replayPath = folder
            self.folderHasChanged = True
            self.update()

    def update(self):
        # Read folder content
        files = glob.glob(self.replayPath+"\*.wotreplay")
        newFiles = set(self.replayList).difference(files)
        if self.folderHasChanged or len(newFiles) != 0:
            self.replayList = glob.glob(self.replayPath+"\*.wotreplay")
            self.progBar.setText("0 / " + str(len(self.replayList)) + " Replay")
            self.progBar.setValue(0)
            self.progBar.update()
            self.folderLabel.setText(QString(self.replayPath))
            globalReplayData.clear()
            parserThread = Thread(target=self.parseReplays())
            parserThread.start()
            parserThread.join()
            # Sort replays
            self.sortedReplays = sorted(globalReplayData.items(), key=lambda x: time.strptime(x[1][0]["dateTime"], '%d.%m.%Y %H:%M:%S')[0:6], reverse=True)
            self.refreshTable()
            self.folderHasChanged = False

    def refreshTable(self):
        self.replayTable.setRowCount(len(globalReplayData))
        headerLabels = ['File', 'Date', 'Player', 'Vehicle', 'Map', 'Kill(s)', 'Damage', 'Spot',
                        'Experience']
        self.replayTable.setColumnCount(len(headerLabels))
        self.replayTable.setHorizontalHeaderLabels(headerLabels)
        self.replayTable.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.replayTable.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        for cpt in range(0, len(self.sortedReplays)):
            replay = self.sortedReplays[cpt][0]
            # Init
            for i in range(0, self.replayTable.columnCount()):
                self.replayTable.setItem(cpt, i, QTableWidgetItem())

            # Filling
            colCpt = 0
            self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(replay.replace(self.replayPath+"\\", "")))
            colCpt += 1

            date = globalReplayData[replay][0]["dateTime"]
            self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(date))
            colCpt += 1

            playerName = globalReplayData[replay][0]["playerName"]
            self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(playerName))
            colCpt += 1

            tankName = globalReplayData[replay][0]["playerVehicle"]
            self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(tankName))
            colCpt += 1

            map = globalReplayData[replay][0]["mapDisplayName"]
            self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(map))
            colCpt += 1
            if len(globalReplayData[replay]) >= 2:
                # Kills
                playerList = globalReplayData[replay][1][0][1]
                playerId = 0
                for player in playerList.keys():
                    if playerList[player]["name"] == playerName:
                        playerId = player
                if playerId == 0:
                    return
                else:
                    kills = globalReplayData[replay][1][0][2][playerId]["frags"]
                    self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(str(kills)))
                    colCpt += 1
                # Damage
                personal = dict()
                if len(globalReplayData[replay][1][0][0]["personal"]) <= 2:
                    personal = globalReplayData[replay][1][0][0]["personal"].values()[0]
                else:
                    personal = globalReplayData[replay][1][0][0]["personal"]
                damage = personal["damageDealt"]
                self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(str(damage)))
                colCpt += 1

                # Spot
                spot = personal["damageAssistedRadio"] + personal["damageAssistedTrack"]
                self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(str(spot)))
                colCpt += 1

                # Experience
                experience = personal["xp"]
                self.replayTable.setItem(cpt, colCpt, QTableWidgetItem(str(experience)))
                colCpt += 1
            else:
                for i in range(0, self.replayTable.columnCount()):
                    item = self.replayTable.item(cpt, i)
                    item.setBackgroundColor(QColor(246, 165, 165))

            # Tooltips
            for i in range(0, self.replayTable.columnCount()):
                cell = self.replayTable.item(cpt, i)
                cell.setToolTip(cell.text())

        self.replayTable.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
        self.replayTable.setColumnWidth(0, 100)

    def parseReplays(self):
        if not self.isParsing:
            self.isParsing = True
            nbFiles = len(self.replayList)
            cpt = 0
            pourcent = 0
            for file in self.replayList:
                cpt += 1
                parseReplay(file)
                # print cpt, '/', nbFiles, cpt*100/nbFiles, '%'
                # if (cpt*100/nbFiles) > pourcent:
                pourcent = cpt*100/nbFiles
                self.progBar.setValue(cpt*100/nbFiles)
                self.progBar.setText(str(cpt) + " / " + str(len(self.replayList)) +
                                     " Replay (" + str(pourcent) + " %)")
                QCoreApplication.processEvents()
            self.progBar.update()
            self.isParsing = False

if __name__ == '__main__':
    app = Application()
