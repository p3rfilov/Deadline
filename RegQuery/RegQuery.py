# work in progress
import os
import sys
import time
import glob

############# Failed to load platform plugin "windows" fix #############
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.system('setx QT_QPA_PLATFORM_PLUGIN_PATH ' + '"' + app_path + '"')
    time.sleep(0.5)
elif __file__:
    app_path = os.path.dirname(os.path.abspath(__file__))
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = app_path
########################################################################

from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView
from PyQt5 import QtCore
from PyQt5.uic import loadUi
from VrayDenoiser import utils
from VrayDenoiser.dispatch import Dispatch

class Settings():
    appName = 'Deadline Slave Info'
    version = 'v0.1'
    root = os.path.join(os.getenv('APPDATA'), appName)
    slaveReports = os.path.join(root, 'reports')
    slaveInfo = os.path.join(root, 'info')

class mainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.dir = os.path.dirname(__file__)
        self.ui = loadUi(os.path.join(self.dir, 'ui_mainWindow.ui'))
        self.ui.show()
        self.ui.setWindowTitle(Settings.appName + ' - ' + Settings.version)
        self.dlcommand = utils.findFile(r'\Program Files\Thinkbox\*\bin\deadlinecommandbg.exe')
        
        self.createFolderStructure()
        self.deadline = Dispatch()
        self.slaveInfo = self.getSlaveInfo()
        self.writeSlaveInfoToFiles()
        self.fillTable()
        self.connectUiSignals()
    
    def connectUiSignals(self):
        self.ui.table.itemSelectionChanged.connect(self.displaySlaveInfo)
    
    def createFolderStructure(self):
        if not os.path.exists(Settings.root):
            os.makedirs(Settings.root)
            os.makedirs(Settings.slaveReports)
            os.makedirs(Settings.slaveInfo)
        
    def getSlaveInfo(self):
        info = utils.tryFunction(self.deadline.Slaves.GetSlavesInfoSettings)
        return info
    
    def displaySlaveInfo(self):
        table = self.ui.table
        row = table.currentRow()
        if table.rowCount():
            info = self.readFile(table.item(row, 1).text())
            self.ui.info.document().setPlainText(info)
    
    def setupTable(self):
        table = self.ui.table
        table.setRowCount(0)
        table.setColumnCount(2)
        table.setColumnHidden(1, True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    
    def fillTable(self):
        self.setupTable()
        table = self.ui.table
        files = self.gatherInfoFiles()
        for f in files:
            table.insertRow(0)
            name, _ = os.path.splitext(os.path.basename(f))
            i1 = QTableWidgetItem(name)
            i2 = QTableWidgetItem(f)
            i1.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i2.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i1.setTextAlignment(QtCore.Qt.AlignCenter)
            i2.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setItem(0, 0, i1)
            table.setItem(0, 1, i2)
        table.setCurrentCell(0, 0)
    
    def writeSlaveInfoToFiles(self):
        for info in self.slaveInfo:
            host = str(info['Info']['Host'])
            file = os.path.join(Settings.slaveInfo, host + '.txt')
            self.writeFile(file, info['Info'])
    
    def writeFile(self, file, info):
        if not os.path.exists(file):
            with open(file, 'w') as f:
                for key, val in info.iteritems():
                    line = str(key) + ': ' + str(val) + '\n'
                    f.write(line)
                    
    def readFile(self, file):
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = sorted(f.readlines())
                return ''.join(lines)
    
    def gatherInfoFiles(self):
        files = glob.glob(os.path.join(Settings.slaveInfo, u'*.txt'))
        return reversed(files)
    
    def sendQuery(self, ip):
        pass
#         deadlinecommandbg -outputFiles c:\<slave>.txt c:\exitcode.txt -RemoteControl <ip> Execute "reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall" /s"
        
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    QApplication.addLibraryPath(os.path.dirname(__file__))
    app = QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())
    