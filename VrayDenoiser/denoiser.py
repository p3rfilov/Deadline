from VrayDenoiser import utils

class denoiserSettings():
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

class Denoiser():
    def __init__(self):
        self.denoiserPath = utils.findFile(r'\Program Files\Chaos Group\V-Ray\3dsmax*\tools\vdenoise.exe')
    
    def buildCommand(self):
        pass
        
if __name__ == '__main__':
    d = Denoiser()
    print(denoiserSettings.__dict__.keys())