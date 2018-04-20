from Deadline.DeadlineConnect import DeadlineCon
import win32api
import glob
import os
import subprocess

class Dispatch(DeadlineCon):
    def __init__(self, host='localhost', port=8082):
        DeadlineCon.__init__(self, host, port)
        self.webServicePath = r'\Program Files\Thinkbox\Deadline8\bin\deadlinewebservice.exe'
        self.service = ''
    
    def runWebService(self):
        def getWebServiceLoacation():
            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split('\000')[:-1]
            for d in drives:
                exe = glob.glob(d + self.webServicePath)[0]
                if os.path.isfile(exe):
                    return exe
            return None
        
        serv = getWebServiceLoacation()
        if serv:
            self.service = subprocess.Popen(serv, shell=True)
        else: self.service = ''
            
    def killWebService(self):
        try:
            cmd = ['taskkill', '/F', '/T', '/PID', str(self.service.pid)]
            subprocess.call(cmd)
        except: print('Could not kill Deadline Web Service')
    
    def getJobs(self):
        return self.Jobs.GetJobs()
    
    def getPools(self):
        return self.Pools.GetPoolNames()
    
    def SubmitJob(self, jobInfo, pluginInfo):
        try:
            newJob = self.Jobs.SubmitJob(jobInfo, pluginInfo)
            return newJob
        except:
            return False

if __name__ == '__main__':
    deadline = Dispatch()
    deadline.runWebService()
    print (deadline.getPools())
    deadline.killWebService()
    