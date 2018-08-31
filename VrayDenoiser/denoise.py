import os
import sys
import time
import glob
import re
import subprocess

############# Failed to load platform plugin "windows" fix #############
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.system('setx QT_QPA_PLATFORM_PLUGIN_PATH ' + '"' + app_path + '"')
    time.sleep(0.5)
elif __file__:
    app_path = os.path.dirname(os.path.abspath(__file__))
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = app_path
########################################################################

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QWidget, QHBoxLayout, QCheckBox, QHeaderView, qApp
from PyQt5 import QtCore, QtGui
from PyQt5.uic import loadUi
from VrayDenoiser import utils
from VrayDenoiser.dispatch import Dispatch

class denoiserDefaults():
    inputFile = ''
    mode = 'mild'
    elements = 0
    boost = 0
    skipExisting = 0
    frames = 0
    display = 1
    autoClose = 1
    useCpu = 0
    useGpu = 2
    verboseLevel = 3
    abortOnOpenCLError = 1
    strength = 0.5
    radius = 5
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
        self.ui.setWindowTitle('V-Ray Denoise - Deadline Submission - ' + 'v0.4')
        
        self.formats = ('.exr','.vrimg')
        self.denoised = '_denoised'
        self.defaultPool = 'gpu_rendering'
        self.denoiserPath = utils.findFile(r"\Program Files\Chaos Group\V-Ray\3dsmax*\tools\vdenoise.exe")
        self.deadline = Dispatch()
         
        self.setupPools()
        self.setupTable()
        self.changeMode()
        
        self.ui.selectFolder.clicked.connect(self.populateTable)
        self.ui.table.itemSelectionChanged.connect(self.currentRowChenged)
        self.ui.checkAll.clicked.connect(lambda: self.ckeckAllRows(True))
        self.ui.uncheckAll.clicked.connect(lambda: self.ckeckAllRows(False))
        self.ui.submit.clicked.connect(self.submitJobs)
        self.ui.runLocally.clicked.connect(self.runLocally)
        self.ui.mode.currentIndexChanged.connect(self.changeMode)
        self.ui.closeEvent = self.closeEvent # shut down web service before exiting
    
    def setupPools(self):
        '''Collect available pools and select the default one if found'''
        pools = utils.tryFunction(self.deadline.Pools.GetPoolNames)
        for p in pools: self.ui.pools.addItem(p)
        index = self.ui.pools.findText(self.defaultPool, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.ui.pools.setCurrentIndex(index)
    
    def setupTable(self):
        self.ui.progressBar.setValue(0)
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
    
    def changeMode(self):
        '''On denoise mode changed, set parameters and enable/disable strength and radius spinners'''
        mode = self.ui.mode.currentText()
        if mode == 'custom':
            self.ui.strength.setEnabled(True)
            self.ui.radius.setEnabled(True)
        else:
            self.ui.strength.setEnabled(False)
            self.ui.radius.setEnabled(False)
        if mode == 'mild':
            self.ui.strength.setValue(0.5)
            self.ui.radius.setValue(5.0)
        elif mode == 'default':
            self.ui.strength.setValue(1.0)
            self.ui.radius.setValue(10.0)
        elif mode == 'strong':
            self.ui.strength.setValue(2.0)
            self.ui.radius.setValue(15.0)
    
    def ckeckAllRows(self, state):
        table = self.ui.table
        count = table.rowCount()
        if count:
            for row in range(count):
                table.cellWidget(row,0).layout().itemAt(0).widget().setChecked(state)
       
    def closeEvent(self, event):
        '''Shut down web service before closing''' 
        self.deadline.stopWebService()
        time.sleep(0.5)
        qApp.quit()
    
    def populateTable(self):
        sequences = self.loadSequences()
        if sequences:
            table = self.ui.table
            self.setupTable()
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
                if s['missingFrames']:
                    table.item(0, 2).setBackground(QtGui.QColor(255,0,0,120))
                    table.item(0, 2).setToolTip('This sequence is incomplete!\nMissing frames: ' + str(s['missingFrames']))
            table.setCurrentCell(0,0)
       
    def loadSequences(self):
        '''Collect and return all sequences in a given folder (getFilesFromFolder)''' 
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
        '''
        Collects sequence info (number of frames, format, etc.)
        input: file path
        output: dictionary
        '''
        missingFrames = []
        d = os.path.dirname(file)
        f = os.path.basename(file)
        fName = f.split('.')[:-1][-1]
        segNum = re.findall(r'\d+', f)
        if segNum and fName.endswith(segNum[-1]): # file is part of a sequence 
            segNum = segNum[-1]
            numPad = len(segNum)
            baseName = f.split(segNum)[0]
            fileType = f.split('.')[-1]
            globString = baseName
            for i in range(0,numPad): globString += '?'
            inputFile = (d + '\\' + globString + f.split(segNum)[1]).replace('\\','/')
            allFiles = sorted(glob.glob(inputFile))
            numFrames = len(allFiles)
            
            # find missing frames
            first = re.findall(r'\d+', os.path.basename(allFiles[0]))[-1]
            last = re.findall(r'\d+', os.path.basename(allFiles[-1]))[-1]
            expectedRange = len(range(int(first), int(last)+1))
            if expectedRange != numFrames:
                index = int(first)
                for name in allFiles:
                    number = int(name.replace('.' + fileType, '')[-numPad:])
                    if number != index:
                        missingFrames.append(index)
                        index += 1
                    index += 1
        else: # file is NOT part of a sequence
            fileType = f.split('.')[-1]
            baseName = f.split('.'+ fileType)[0]
            numFrames = 1
            inputFile = file
        return {
                'baseName':baseName,
                'fileType':fileType,
                'numFrames':numFrames,
                'inputFile':inputFile,
                'missingFrames':missingFrames
                }
    
    def getFilesFromFolder(self):
        '''Returns a sorted list of files in a picked folder. Supports recursive nested folder scanning'''
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
        self.ui.progressBar.setValue(0)
        table = self.ui.table
        count = table.rowCount()
        index = 0
        if count:
            for row in range(count):
                if table.cellWidget(row,0).layout().itemAt(0).widget().isChecked():
                    result = self.buildJobInfoAndSubmit(row)
                index += 1
                self.ui.progressBar.setValue(index/float(count)*100)
                QApplication.processEvents()
    
    def buildJobInfoAndSubmit(self, row):
        table = self.ui.table
        name = table.item(row, 1).text()
        batch = os.path.basename(os.path.dirname(table.item(row, 4).text())) + ' - Denoiser'
        cmd = self.buildCommand(row)
        jobInfo = {
            'Name': name,
            'BatchName': batch,
            'Frames': '0-' + str(self.ui.tasks.value()-1),
            'Pool': self.ui.pools.currentText(),
            'Priority': str(self.ui.priority.value()),
            'Plugin': 'CommandLine'
            }
        pluginInfo = {
            'Executable': self.denoiserPath,
            'Arguments': cmd,
            'StartupDirectory': ''
            }
        result = self.deadline.SubmitJob(jobInfo, pluginInfo)
        return result
    
    def currentRowChenged(self):
        row = self.ui.table.currentRow()
        self.buildCommand(row)
    
    def buildCommand(self, row):
        if self.ui.table.rowCount():
            cmd = ''
            if row >= 0:
                cmd += ' -elements=' + str(int(self.ui.elements.isChecked()))
                cmd += ' -boost=' + self.ui.boost.currentText()
                cmd += ' -skipExisting=' + str(int(self.ui.skipExisting.isChecked()))
                cmd += ' -display=' + str(int(self.ui.display.isChecked()))
                cmd += ' -autoClose=' + str(int(self.ui.autoClose.isChecked()))
                cmd += ' -useGpu=' + self.ui.useGpu.currentText()
                cmd += ' -verboseLevel=' + self.ui.verboseLevel.currentText()
                cmd += ' -strength=' + str(self.ui.strength.value())
                cmd += ' -radius=' + str(self.ui.radius.value())
                cmd += ' -frameBlend=' + str(self.ui.frameBlend.value())
                cmd += ' -strips=' + str(self.ui.strips.value())
                cmd += ' -autoRadius=' + str(int(self.ui.autoRadius.isChecked()))
                cmd += ' -threshold=' + str(self.ui.threshold.value())
                cmd += ' -memLimit=' + str(self.ui.memLimit.value())
                cmd += ' -abortOnOpenCLError=' + str(int(self.ui.abortOnOpenCLError.isChecked()))
                cmd += ' -inputFile='
                cmd += '"' + self.ui.table.item(row, 4).text() + '"'
            self.ui.command.setText('"' + self.denoiserPath + '"' + cmd)
            return cmd
        
    def runLocally(self):
        self.ui.progressBar.setValue(0)
        table = self.ui.table
        count = table.rowCount()
        cmd = ''
        if count:
            for row in range(count):
                if table.cellWidget(row,0).layout().itemAt(0).widget().isChecked():
                    self.buildCommand(row)
                    cmd += self.ui.command.text() + r' & '
            service = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
        
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    QApplication.addLibraryPath(os.path.dirname(__file__))
    app = QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())
    