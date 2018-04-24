############# Failed to load platform plugin "windows" fix #############
import PyQt5
import os
from setuptools.dist import sequence
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
########################################################################

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QWidget, QHBoxLayout, QCheckBox, QHeaderView, qApp
from PyQt5 import QtGui, QtCore
from PyQt5.uic import loadUi
import time
import glob
import re

from VrayDenoiser import utils
from VrayDenoiser.dispatch import Dispatch

class denoiserDefaults():
    inputFile = ''
    mode = 'default'
    elements = 0
    boost = 0
    skipExisting = 1
    frames = 0
    display = 1
    autoClose = 1
    useCpu = 0
    useGpu = 2
    verboseLevel = 3
    abortOnOpenCLError = 0
    strength = 1.0
    radius = 10
    frameBlend = 1
    strips = -1
    autoRadius = 0
    threshold = 0.001
    memLimit = 0
    outputOffset = 0

class mainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.dir = os.path.dirname(__file__)
        self.ui = loadUi(os.path.join(self.dir, 'ui_mainWindow.ui'))
        self.ui.show()
        
        self.formats = ('.exr','.vrimg')
        self.denoised = '_denoised_'
        self.denoiserPath = utils.findFile(r"\Program Files\Chaos Group\V-Ray\3dsmax*\tools\vdenoise.exe")
#         self.deadline = Dispatch()
#         pools = self.deadline.Pools.GetPoolNames()
#         for p in pools: self.ui.pools.addItem(p)
        
        self.setupTable()
        self.ui.selectFolder.clicked.connect(self.populateTable)
        self.ui.table.itemSelectionChanged.connect(self.buildCommand)
        self.ui.submit.clicked.connect(self.submitJobs)
        self.ui.closeEvent = self.closeEvent # shut down web service before exiting
    
    def setupTable(self):
        table = self.ui.table
        table.setRowCount(0)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        table.setColumnWidth(0, 33)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in (2,3,4): # fixed columns
            table.setColumnWidth(i, 60)
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Fixed)
        table.setColumnHidden(4,True)
        
    def closeEvent(self, event):
        self.deadline.stopWebService()
        time.sleep(0.5)
        qApp.quit()
    
    def populateTable(self):
        sequences = self.loadSequences()
        if sequences:
            table = self.ui.table
            table.setRowCount(0)
            for s in reversed(sequences):
                table.insertRow(0)
                i2 = QTableWidgetItem(s['baseName'])            # name
                i3 = QTableWidgetItem(str(s['numFrames']))      # frames
                i4 = QTableWidgetItem(s['fileType'])            # format
                i5 = QTableWidgetItem(s['inputFile'])           # data
                i2.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                i3.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                i4.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                i5.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
                i2.setTextAlignment(QtCore.Qt.AlignCenter)
                i3.setTextAlignment(QtCore.Qt.AlignCenter)
                i4.setTextAlignment(QtCore.Qt.AlignCenter)
                widget = QWidget()
                chBox = QCheckBox()
                chBox.setChecked(True)
                layout = QHBoxLayout(widget)
                layout.addWidget(chBox)
                layout.setAlignment(QtCore.Qt.AlignCenter)
                widget.setLayout(layout)
                table.setCellWidget(0, 0, widget)
                table.setItem(0, 1, i2)
                table.setItem(0, 2, i3)
                table.setItem(0, 3, i4)
                table.setItem(0, 4, i5)
            table.setCurrentCell(0,0)
        
    def loadSequences(self):
        sequences = []
        files = self.getFilesFromFolder()
        if files:
            names = []
            for f in files:
                segNum = re.findall(r'\d+', f)
                if segNum:
                    baseName = f.split(segNum[-1])[0]
                    names.append(baseName)
                else:
                    names.append(f)
            names = sorted(list(set(names)))
            for n in names:
                s = self.getSeqInfo(glob.glob(n + '*')[0])
                sequences.append(s)
        return sequences
    
    def getSeqInfo(self, file): # big thanks to Christopher Evans at http://www.chrisevans3d.com
        d = os.path.dirname(file)
        f = os.path.basename(file)
        segNum = re.findall(r'\d+', f)
        if segNum:
            segNum = segNum[-1]
            numPad = len(segNum)
            baseName = f.split(segNum)[0]
            fileType = f.split('.')[-1]
            globString = baseName
            for i in range(0,numPad): globString += '?'
            inputFile = (d + '\\' + globString + f.split(segNum)[1]).replace('\\','/')
            theGlob = glob.glob(inputFile)
            numFrames = len(theGlob)
        else:
            fileType = f.split('.')[-1]
            baseName = f.split('.'+ fileType)[0]
            numFrames = 1
            inputFile = file
        return {
                'baseName':baseName,
                'fileType':fileType,
                'numFrames':numFrames,
                'inputFile':inputFile
                }
        
    def getFilesFromFolder(self):
        allFiles = []
        userhome = os.path.expanduser('~')
        desktop = userhome + '/Desktop/'
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", desktop)
        if folder:
            if self.ui.scanSubfolders.isChecked():
                for root, dirs, files in os.walk(folder, topdown=False):
                    for f in files:
                        if not self.denoised in f and os.path.splitext(f)[-1].lower() in self.formats:
                            allFiles.append(os.path.join(root, f).replace('\\','/'))
            else:
                allFiles = [os.path.join(folder, f).replace('\\','/') for f in os.listdir(folder) if \
                            not self.denoised in f and os.path.splitext(f)[-1].lower() in self.formats]
        return sorted(allFiles)
    
    def submitJobs(self):
        print(self.ui.table.cellWidget(0,0).layout().takeAt(0).widget().isChecked())
        print('jobs submitted')
    
    def buildCommand(self):
        if self.ui.table.rowCount() != 0:
            row = self.ui.table.currentRow()
            command = ''
            command += self.denoiserPath + ' '
            command += '-inputFile '
            command += '"' + self.ui.table.item(row, 4).text() + '" '
            self.ui.command.setText(command)
        
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())
    
#     print(denoiserDefaults.__dict__.keys())