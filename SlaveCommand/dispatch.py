from Deadline.DeadlineConnect import DeadlineCon
import myUtils as utils
import subprocess

class Dispatch(DeadlineCon):
    '''
    Convenience class for managing the Deadline Web Service.
    Locates (utils.findFile) and runs deadlinewebservice.exe
    '''
    def __init__(self, host='localhost', port=8082):
        DeadlineCon.__init__(self, host, port)
        self.webServicePath = r'\Program Files\Thinkbox\*\bin\deadlinewebservice.exe'
        self.service = ''
        self.runWebService()
    
    def runWebService(self):
        serv = utils.findFile(self.webServicePath)
        if serv:
            self.service = subprocess.Popen(serv, shell=True, stdin=subprocess.PIPE)
        else:
            self.service = ''
            print('Could not locate deadlinewebservice.exe. Make sure Deadline is installed')
            
    def stopWebService(self):
        try:
            self.service.stdin.write('/exit\n'.encode())
        except: print('Could not Shut Down Deadline Web Service')
    
    def SubmitJob(self, jobInfo, pluginInfo):
        try:
            newJob = self.Jobs.SubmitJob(jobInfo, pluginInfo)
            return newJob
        except:
            return False

if __name__ == '__main__':
    deadline = Dispatch()
    print (deadline.Pools.GetPoolNames())
    deadline.stopWebService()
    