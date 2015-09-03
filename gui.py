import Tkinter as tk
import tkFileDialog
from replayParser import *


class Application(tk.Frame):
    replayPath = "C:/Games/World_of_Tanks - FFA/Replays/"
    replayList = []

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()

    def createWidgets(self):
        self.quitButton = tk.Button(self, text='Quit', command=self.quit)
        self.quitButton.grid()
        self.folderButton = tk.Button(self, text='Select replay folder', command=self.chooseReplayPath)
        self.folderButton.grid()
        self.folderLabel = tk.Label(self)
        self.folderLabel.grid()
        self.infoLabel = tk.Label(self)
        self.infoLabel.grid()
        # Table
        self.replayCanvas = tk.Canvas(self, width=400, height=400)
        self.replayCanvas.grid()
        self.replayTable = SimpleTable(self, 10, 2)
        self.replayCanvas.create_window(150, 100, window=self.replayTable)
        vbar = tk.Scrollbar(self.replayTable, orient=tk.VERTICAL)
        vbar.grid(row=0, column=3)
        vbar.config(command=self.replayCanvas.yview)
        self.replayCanvas.config(yscrollcommand=vbar.set)
        # self.replayCanvas.pack(side=LEFT,expand=True,fill=BOTH)
        # Update widgets fields
        self.updateGUI()

    def chooseReplayPath(self):
        dirName = tkFileDialog.askdirectory(initialdir=self.replayPath, title="Choose WoT replay folder")
        self.replayPath = dirName
        self.updateGUI()

    def updateGUI(self):
        self.folderLabel.config(text=self.replayPath)
        try:
            self.replayList = glob.glob(self.replayPath+"/*.wotreplay")
        except:
            print "Erreur de lecture de dossier a rajouter"
        self.infoLabel.config(text=str(len(self.replayList))+" replay(s) to scan")

        self.update()


class SimpleTable(tk.Frame):
    def __init__(self, parent, rows=10, columns=2):
        # use black background so it "peeks through" to
        # form grid lines
        tk.Frame.__init__(self, parent, background="black")
        self._widgets = []
        for row in range(rows):
            current_row = []
            for column in range(columns):
                label = tk.Label(self, text="%s/%s" % (row, column),
                                 borderwidth=0, width=10)
                label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                current_row.append(label)
            self._widgets.append(current_row)

        for column in range(columns):
            self.grid_columnconfigure(column, weight=1)

    def set(self, row, column, value):
        widget = self._widgets[row][column]
        widget.configure(text=value)

app = Application()
app.master.title('WoT Replay Parser')
app.mainloop()
