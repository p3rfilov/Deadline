import win32api
import glob
import time

def findFile(path):
    '''
    Scans all drives for a given file path. Returns the last found match.
    Input (path) example: r'\Program Files\Thinkbox\*\bin\deadlinewebservice.exe'
    '''
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
    for d in drives:
        files = glob.glob(d + path)
        if files:
            return files[-1] # return last element
    return None

def tryFunction(function, max_try=5):
    result = []
    for i in range(max_try):
        try:
            result = function()
            break
        except:
            print('Failed to call ' + str(function) + '. Will try again in 1s')
            time.sleep(1)
    return result