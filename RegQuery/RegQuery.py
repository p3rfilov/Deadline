# work in progress
import os
import sys
import time
import glob
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

from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView
from PyQt5 import QtCore
from PyQt5.uic import loadUi
from VrayDenoiser import utils
from VrayDenoiser.dispatch import Dispatch

class Settings():
    appName = 'Deadline Slave Info'
    version = 'v0.1'
    root = os.path.join(os.getenv('APPDATA'), appName)
    reports = os.path.join(root, 'reports')
    returnCodes = os.path.join(root, 'codes')

class mainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.dir = os.path.dirname(__file__)
        self.ui = loadUi(os.path.join(self.dir, 'ui_mainWindow.ui'))
        self.ui.show()
        self.ui.setWindowTitle(Settings.appName + ' - ' + Settings.version)
        self.dlcommand = utils.findFile(r'\Program Files\Thinkbox\*\bin\deadlinecommandbg.exe')
        self.hostIPs = {}
        
        self.createFolderStructure()
        self.deadline = Dispatch()
        self.slaveInfo = self.getSlaveInfo()
        self.slaveReports = self.gatherReportFiles()
        self.fillTable()
        self.connectUiSignals()
    
    def connectUiSignals(self):
        self.ui.table.itemClicked.connect(self.displaySlaveInfo)
        self.ui.table.itemSelectionChanged.connect(self.displaySlaveInfo)
        self.ui.refreshSel.clicked.connect(self.refreshSelected)
        self.ui.refresh.clicked.connect(self.refreshAll)
        self.ui.folder.clicked.connect(self.openReportFolder)
    
    def createFolderStructure(self):
        if not os.path.exists(Settings.root):
            os.makedirs(Settings.root)
            os.makedirs(Settings.reports)
            os.makedirs(Settings.returnCodes)
    
    def openReportFolder(self):
        if os.path.exists(Settings.root):
            subprocess.Popen('explorer "{0}"'.format(Settings.reports))
        
    def getSlaveInfo(self):
        info = utils.tryFunction(self.deadline.Slaves.GetSlavesInfoSettings)
        sortedInfo = self.sortSlaveInfo(info)
        return sortedInfo
    
    def sortSlaveInfo(self, info):
        sortedInfo = []
        for i in info:
            host = str(i['Info']['Host'])
            ip = str(i['Info']['IP'])
            allInfo = i['Info']
            if not host in self.hostIPs.keys():
                self.hostIPs[host] = ip
                sortedInfo.append([host, ip, allInfo])
        return sorted(sortedInfo, key=lambda x:x[0].lower())
    
    def displaySlaveInfo(self):
        table = self.ui.table
        row = table.currentRow()
        if table.rowCount() and row >= 0:
            info = table.item(row, 2).text()
            soft = table.item(row, 3).text()
            self.ui.info.document().setPlainText(info)
            self.ui.soft.document().setPlainText(soft)
    
    def setupTable(self):
        table = self.ui.table
        table.setRowCount(0)
        table.setColumnCount(4)
        for i in (1,2,3):
            table.setColumnHidden(i, True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    
    def fillTable(self):
        self.setupTable()
        table = self.ui.table
        print(self.slaveReports.keys())
        for info in reversed(self.slaveInfo):
            host = info[0]
            ip = info[1]
            report = ''
            if host in self.slaveReports.keys():
                report = self.slaveReports[host]
            table.insertRow(0)
            i1 = QTableWidgetItem(host)                             # name
            i2 = QTableWidgetItem(ip)                               # ip
            i3 = QTableWidgetItem(self.formatSlaveInfo(info[2]))    # info
            i4 = QTableWidgetItem(report)                           # soft
            i1.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i2.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i3.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i4.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
            i1.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setItem(0, 0, i1)
            table.setItem(0, 1, i2)
            table.setItem(0, 2, i3)
            table.setItem(0, 3, i4)
        table.setCurrentCell(0, 0)
    
    def formatSlaveInfo(self, info):
        infoList = []
        for key, val in info.iteritems():
            line = str(key) + ': ' + str(val) + '\n'
            infoList.append(line)
        return ''.join(sorted(infoList))
    
    def refreshSelected(self):
        table = self.ui.table
        row = table.currentRow()
        if table.rowCount() and row >= 0:
            name = table.item(row, 0).text()
            command = self.buildQueryCommand(name)
            subprocess.Popen(command, shell=True)
        
    def refreshAll(self):
        table = self.ui.table
        rowCount = table.rowCount()
        if rowCount:
            for row in range(rowCount):
                name = table.item(row, 0).text()
                cmd = self.buildQueryCommand(name)
                subprocess.Popen(cmd, shell=True)
    
    def buildQueryCommand(self, name):
        '''
        Builds a command for listing the "Uninstall" registry of a given node using "deadlinecommandbg.exe" and "reg query"
        Inputs: 
            Node name
        Returns:
            Command string
        Command result:
            report file: <node>.txt
            return code: /codes/<node>.txt
        '''
        reportFile = os.path.join(Settings.reports, name + '.txt')
        returnCode = os.path.join(Settings.returnCodes, name + '.txt')
        cmd = ''
        cmd += '\"' + self.dlcommand + '\"'
        cmd += r' -outputFiles ' + '\"' + reportFile + '\"' + ' ' + '\"' + returnCode + '\"'
        cmd += r' -RemoteControl ' + self.hostIPs[name] + ' Execute '
        cmd += '\"'
        cmd += r'reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall" /S /v DisplayName'
        cmd += '\"'
        return cmd
    
    def gatherReportFiles(self):
        reportDict = {}
        files = glob.glob(os.path.join(Settings.reports, u'*.txt'))
        for f in files:
            name, _ = os.path.splitext(os.path.basename(f))
            reportDict[name] = self.readFile(f)
        return reportDict
    
    def readFile(self, file):
        if os.path.exists(file):
            with open(file, 'r') as f:
                return f.read()
        
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    QApplication.addLibraryPath(os.path.dirname(__file__))
    app = QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())
    