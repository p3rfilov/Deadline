############# Failed to load platform plugin "windows" fix #############
import PyQt5
import os
dirname = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
########################################################################

from PyQt5.QtWidgets import QMainWindow, QFileDialog, qApp
from PyQt5 import QtGui
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
        self.denoiserPath = utils.findFile(r'\Program Files\Chaos Group\V-Ray\3dsmax*\tools\vdenoise.exe')
        self.deadline = Dispatch()
        pools = self.deadline.Pools.GetPoolNames()
        for p in pools: self.ui.pools.addItem(p)
        
        self.ui.selectFolder.clicked.connect(self.loadSequences)
        
        self.ui.closeEvent = self.closeEvent # shut down web service before exiting
        
    def closeEvent(self, event):
        self.deadline.stopWebService()
        time.sleep(0.5)
        qApp.quit()
        
    def loadSequences(self):
        files = self.getFilesFromFolder()
        if files:
            print self.getSeqInfo(files[0])
    
    def getSeqInfo(self, files): # big thanks to Christopher Evans at http://www.chrisevans3d.com
        d = os.path.dirname(files)
        f = os.path.basename(files)
        segNum = re.findall(r'\d+', f)[-1]
        numPad = len(segNum)
        baseName = f.split(segNum)[0]
        fileType = f.split('.')[-1]
        globString = baseName
        for i in range(0,numPad): globString += '?'
        inputFile = (d + '\\' + globString + f.split(segNum)[1]).replace('\\','/')
        theGlob = glob.glob(inputFile)
        numFrames = len(theGlob)
        return [baseName, fileType, numFrames, inputFile]
        
    def getFilesFromFolder(self):
        allFiles = []
        userhome = os.path.expanduser('~')
        desktop = userhome + '/Desktop/'
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", desktop)
        if folder:
            if self.ui.scanSubfolders.isChecked():
                for root, dirs, files in os.walk(folder, topdown=False):
                    for f in files:
                        if os.path.splitext(f)[-1].lower() in self.formats:
                            allFiles.append(os.path.join(root, f).replace('\\','/'))
            else:
                allFiles = [os.path.join(folder, f).replace('\\','/') for f in os.listdir(folder) if os.path.splitext(f)[-1].lower() in self.formats]
        return sorted(allFiles)
    
    def buildCommand(self):
        pass
        
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())
    
#     print(denoiserDefaults.__dict__.keys())