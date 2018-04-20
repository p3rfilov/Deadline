from Deadline.DeadlineConnect import DeadlineCon
from VrayDenoiser import utils
import subprocess

class Dispatch(DeadlineCon):
    def __init__(self, host='localhost', port=8082):
        DeadlineCon.__init__(self, host, port)
        self.webServicePath = r'\Program Files\Thinkbox\*\bin\deadlinewebservice.exe'
        self.service = ''
        self.runWebService()
    
    def runWebService(self):
        serv = utils.findFile(self.webServicePath)
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
    print (deadline.getPools())
#     deadline.killWebService()
    