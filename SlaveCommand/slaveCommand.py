'''
Deadline Slave Command tool

Description:

    Provides quick access to installed software packages
    and hardware configurations of all Deadline Nodes.
    Will support custom command submission in future releases.

Features:
    
    - lists all Deadline Nodes
    - lists Node's software and hardware configuration
    - VNC Viewer integration (double-click Node name)
    - multi-field search
    - Node status display:
        RED - failed to connect (off or blocked by firewall)
        YELLOW - Installed Package report hasn't been generated yet
        GREEN - report has been generated and stored on the system
    - all reports are stored in plain text documents
    
Requirements: Windows, Deadline
    
TO DO:
    
    - repurpose for general use, with ability to submit custom commands
    - code refactoring
    - NOT operator for search fields
    - print/save filtered reports
'''

import os
import sys
import time
import glob
import subprocess
import re

############# Failed to load platform plugin "windows" fix #############
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.system('setx QT_QPA_PLATFORM_PLUGIN_PATH ' + '"' + app_path + '"')
    time.sleep(0.5)
elif __file__:
    app_path = os.path.dirname(os.path.abspath(__file__))
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = app_path
########################################################################

from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5 import QtCore, QtGui
from PyQt5.uic import loadUi
from dispatch import Dispatch
import myUtils as utils
import hexConverter

# # not pyinstaller-friendly
# from VrayDenoiser import utils
# from VrayDenoiser.dispatch import Dispatch

class Settings():
    '''Current application settings'''
    appName = 'Deadline Slave Info'
    version = 'v0.2'
    root = os.path.join(os.getenv('APPDATA'), appName)
    reports = os.path.join(root, 'reports')
    returnCodes = os.path.join(root, 'codes')
    lic = os.path.join(root, 'licenses')


class mainWindow(QMainWindow):
    '''Main Deadline Query class'''
    def __init__(self):
        QMainWindow.__init__(self)
        self.dir = os.path.dirname(__file__)
        self.ui = loadUi(os.path.join(self.dir, 'ui_mainWindow.ui'))
        self.ui.show()
        self.ui.setWindowTitle(Settings.appName + ' - ' + Settings.version)
        self.dlcommand = utils.findFile(r'\Program Files\Thinkbox\*\bin\deadlinecommandbg.exe')
        self.vnc = utils.findFile(r'\Program Files\RealVNC\VNC Viewer\vncviewer.exe')
        self.hostIPs = {}
        self.slaveInfo = []
        self.slaveReports = {}
        self.accepted = r'Result: "Connection Accepted.'
        self.softwareCmd = r'reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall" /S /v DisplayName'
        self.winLicenseCmd = r'reg query ""HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion""'
        
        self.createFolderStructure()
        self.deadline = Dispatch() # connect to Deadline Web Service
        self.startUp()
        self.connectUiSignals()
        self.setupFolderWatcher()
    
    def startUp(self):
        '''Main startup function. Generates all the required data fills out the table'''
        self.hostIPs = {}
        self.slaveInfo = []
        self.slaveReports = {}
        self.getSlaveInfo()
        self.createLicenseFolders()
        self.fillTable()
    
    def createLicenseFolders(self):
        for name in self.hostIPs:
            dir = os.path.join(Settings.lic, name)
            if not os.path.exists(dir):
                os.makedirs(dir)
    
    def connectUiSignals(self):
        self.ui.table.itemClicked.connect(self.filterSearch)
        self.ui.table.itemSelectionChanged.connect(self.filterSearch)
        self.ui.table.itemDoubleClicked.connect(self.openVNC)
        self.ui.refreshSel.clicked.connect(self.refreshSelected)
        self.ui.refresh.clicked.connect(self.refreshAll)
        self.ui.folder.clicked.connect(self.openReportFolder)
        self.ui.searchSlaves.textChanged.connect(self.filterSearch)
        self.ui.searchInfo.textChanged.connect(self.filterSearch)
        self.ui.searchSoft.textChanged.connect(self.filterSearch)
        self.ui.clear.clicked.connect(self.clearSearch)
        self.ui.reload.clicked.connect(self.startUp)
        action = self.ui.menuHelp.addAction('&About')
        action.triggered.connect(self.About)
    
    def openVNC(self):
        if os.path.exists(self.vnc):
            table = self.ui.table
            row = table.currentRow()
            ip = table.item(row, 1).text()
            cmd = '\"'
            cmd += self.vnc
            cmd += '\" '
            cmd += ip
            subprocess.Popen(cmd, shell=True)
        else:
            Message.vncMessage()
    
    def filterSearch(self):
        slaveStr = self.ui.searchSlaves.text().lower()
        infoStr = self.ui.searchInfo.text().lower()
        softStr = self.ui.searchSoft.text().lower()
        table = self.ui.table
        rowCount = table.rowCount()
        if rowCount:
            for row in range(rowCount):
                slave = table.item(row, 0).text().lower()
                info = table.item(row, 2).text().lower()
                soft = table.item(row, 3).text().lower()
                if slaveStr in slave and infoStr in info and softStr in soft:
                    table.setRowHidden(row, False)
                else:
                    table.setRowHidden(row, True)
            selRow = table.currentRow()
            self.displaySlaveInfo()
            if selRow >= 0:
                info = table.item(selRow, 2).text().split('\n')
                soft = table.item(selRow, 3).text().split('\n')
                infoFilter = ''
                softFilter = ''
                for s in info:
                    if infoStr in s.lower():
                        infoFilter += s + '\n'
                for s in soft:
                    if softStr in s.lower():
                        softFilter += s + '\n'
                self.ui.info.document().setPlainText(infoFilter)
                self.ui.soft.document().setPlainText(softFilter)
    
    def clearSearch(self):
        self.ui.searchSlaves.clear()
        self.ui.searchInfo.clear()
        self.ui.searchSoft.clear()
        self.filterSearch()
        
    def setupFolderWatcher(self):
        self.watcher = QtCore.QFileSystemWatcher() # watch for file changes
        self.watcher.addPath(Settings.returnCodes)
        self.watcher.directoryChanged.connect(self.setStatusColoursAndWriteReports)
    
    def createFolderStructure(self):
        dirs = (
            Settings.root,
            Settings.reports,
            Settings.returnCodes,
            Settings.lic
            )
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
    
    def openReportFolder(self):
        if os.path.exists(Settings.root):
            subprocess.Popen('explorer "{0}"'.format(Settings.root))
        
    def getSlaveInfo(self):
        info = utils.tryFunction(self.deadline.Slaves.GetSlavesInfoSettings)
        sortedInfo = self.sortSlaveInfo(info)
        self.slaveInfo = sortedInfo
    
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
        else:
            self.ui.info.document().setPlainText('')
            self.ui.soft.document().setPlainText('')
    
    def setupTable(self):
        table = self.ui.table
        table.setRowCount(0)
        table.setColumnCount(4)
        for i in (1,2,3):
            table.setColumnHidden(i, True)
        header = table.verticalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setDefaultSectionSize(20)
    
    def fillTable(self):
        self.setupTable()
        self.gatherReportFiles()
        table = self.ui.table
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
        self.setStatusColoursAndWriteReports()
    
    def setStatusColoursAndWriteReports(self):
        self.gatherReportFiles()
        table = self.ui.table
        green = QtGui.QColor(0,255,0,70)
        yellow = QtGui.QColor(255,255,0,70)
        red = QtGui.QColor(255,0,0,70)
        rowCount = table.rowCount()
        if rowCount:
            for row in range(rowCount):
                name = table.item(row, 0).text()
                report = os.path.join(Settings.reports, name + '.txt')
                if os.path.exists(report):
                    line = self.readFile(report)
                    if name in self.slaveReports.keys() and self.accepted in line:
                        table.item(row, 0).setBackground(green)
                        report = self.slaveReports[name]
                        table.item(row, 3).setText(report)
                    else:
                        table.item(row, 0).setBackground(red)
                else:
                    table.item(row, 0).setBackground(yellow)
                    table.item(row, 3).setText('')
        self.displaySlaveInfo()
    
    def formatSlaveInfo(self, info):
        infoList = []
        for key, val in info.iteritems():
            try:
                # skip lines with unicode objects
                line = str(key) + ': ' + str(val) + '\n'
            except:
                line = str(key) + ': ' + '\n'
            infoList.append(line)
        return ''.join(sorted(infoList))
    
    def refreshSelected(self):
        table = self.ui.table
        row = table.currentRow()
        if table.rowCount() and row >= 0:
            name = table.item(row, 0).text()
            self.sendCommand(name)
        
    def refreshAll(self):
        table = self.ui.table
        rowCount = table.rowCount()
        if rowCount:
            for row in range(rowCount):
                name = table.item(row, 0).text()
                self.sendCommand(name)
                
    def sendCommand(self, name):
        cmd = ''
        self.deleteFiles(name)
        winFile = os.path.join(Settings.lic, name, 'win' + '.txt')
        softFile = os.path.join(Settings.reports, name + '.txt')
        cmd += self.buildQueryCommand(name, self.winLicenseCmd, winFile) + r' & '
        cmd += self.buildQueryCommand(name, self.softwareCmd, softFile)
        subprocess.Popen(cmd, shell=True)
    
    def buildQueryCommand(self, name, command, reportFile):
        '''
        Builds a reg query command for passing to "deadlinecommandbg.exe"
        Inputs: 
            <string> node name 
            <string> command to execute
            <string> a file to write the report to
        Returns:
            <string> Command
        Command result:
            report file: <node>.txt
            return code: /codes/<node>.txt
        '''
#         reportFile = os.path.join(Settings.reports, name + '.txt')
        returnCode = os.path.join(Settings.returnCodes, name + '.txt')
        cmd = ''
        cmd += '\"' + self.dlcommand + '\"'
        cmd += r' -outputFiles ' + '\"' + reportFile + '\"' + ' ' + '\"' + returnCode + '\"'
        cmd += r' -RemoteControl ' + self.hostIPs[name] + ' Execute '
        cmd += '\"'
#         cmd += r'reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall" /S /v DisplayName'
        cmd += command
        cmd += '\"'
        return cmd
    
    def gatherReportFiles(self):
        '''Gathers, formats and stores all the report data in a dictionary'''
        reportDict = {}
        reports = glob.glob(os.path.join(Settings.reports, u'*.txt'))
        for f in reports:
            name, _ = os.path.splitext(os.path.basename(f))
            report = self.formatReport(self.readFile(f))
            licenses = self.gatherLicFiles(name)
            reportDict[name] = licenses + report
        self.slaveReports = reportDict
    
    def formatHeader(self, text):
        str = text
        str += '\n\n'
        return str
        
    def formatFooter(self):
        str = '\n'
        str += '-' * 100
        str += '\n\n'
        return str
    
    def formatReport(self, string):
        if self.accepted in string:
            lines = sorted(string.split('\n'))
            formattedString = self.formatHeader('INSTALLED PACKAGES')
            char_list = ['    DisplayName    ', 'REG_SZ    ']
            for line in lines:
                if 'REG_SZ' in line:
                    str = re.sub("|".join(char_list), '', line)
                    formattedString += str + '\n'
            formattedString += self.formatFooter()
            return formattedString
        else:
            return string
    
    def gatherLicFiles(self, name):
        allLicInfo = ''
        licFiles = glob.glob(os.path.join(Settings.lic, name, u'*.txt'))
        for f in licFiles:
            fname, _ = os.path.splitext(os.path.basename(f))
            if fname == 'win':
                winInfo = self.formatWinInfo(self.readFile(f))
                allLicInfo += winInfo
        return allLicInfo
        
    def formatWinInfo(self, string):
        if self.accepted in string:
            lines = sorted(string.split('\n'))
            formattedString = self.formatHeader('WINDOWS INFO')
            char_list = ['    REG_SZ    ', '    REG_BINARY    ']
            for line in lines:
                if 'REG_SZ' in line:
                    str = re.sub("|".join(char_list), ': ', line)
                    formattedString += str + '\n'
                elif 'DigitalProductId' in line and 'REG_BINARY' in line:
                    str = re.sub("|".join(char_list), '#', line)
                    nameId = str.split('#')
                    name = nameId[0]
                    hexId = list(nameId[-1]) # hexConverter.DecodeKey takes a list
                    decodedId = hexConverter.DecodeKey(hexId)
                    formattedString += name + ': ' + decodedId + '\n'
            formattedString += self.formatFooter()
            return formattedString
        else:
            return string
    
    def readFile(self, file, firstLine=False):
        if os.path.exists(file):
            with open(file, 'r') as f:
                if not firstLine:
                    return f.read()
                else:
                    return f.readline()
        else:
            return ''
    
    def deleteFiles(self, name):
        report = os.path.join(Settings.reports, name + '.txt')
        code = os.path.join(Settings.returnCodes, name + '.txt')
        try:
            if os.path.exists(code):
                os.remove(code)
            if os.path.exists(report):  
                os.remove(report)
        except:
            print('Could not remove files for ' + name)
        
    def About(self):
        msg = QMessageBox()
        msg.setFixedSize(500, 500)
        msg.setIcon(QMessageBox.Information)
        msg.setText(
'''
-------------------------------------------------

Deadline Slave Command tool

Author: Andrej Perfilov
Written in Python 2.7 and Qt 5.6

-------------------------------------------------
'''
            )
        msg.setDetailedText(
'''
Description:

Provides quick access to installed software packages
and hardware configurations of all Deadline Nodes.

Features:
    
    - lists all Deadline Nodes
    - lists Node's software and hardware configuration
    - VNC Viewer integration (double-click Node name)
    - multi-field search
    - Node status display:
        RED - failed to connect (off or blocked by firewall)
        YELLOW - Installed Package report hasn't been generated yet
        GREEN - report has been generated and stored on the system
    - all reports are stored in plain text documents
    
Requirements: Windows, Deadline
'''
            )
        msg.setWindowTitle('About')
        msg.exec_()
        msg.setWindowModality(QtCore.Qt.ApplicationModal)


class Message():
    @staticmethod
    def vncMessage():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText('\nCould not find VNC Viewer!\n      ')
        msg.setWindowTitle('VNC Viewer')
        msg.exec_()


class Palette():
    '''This class changes the colour palette for a given QApplication object'''
    @staticmethod
    def applyDarkPalette(app):
        '''
        Changes the palette to a "Dark theme"
        Inputs: QApplication object
        Outputs: QApplication object
        '''
        app.setStyle('Dark Theme')
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53,53,53))
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15,15,15))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53,53,53))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53,53,53))
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(142,45,197).lighter())
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        app.setPalette(palette)
        return app
    

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    QApplication.addLibraryPath(os.path.dirname(__file__))
    app = QApplication(sys.argv)
#     Palette.applyDarkPalette(app)
    window = mainWindow()
    sys.exit(app.exec_())
    