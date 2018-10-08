'''
All credit goes to "Spaceghost"
https://gist.github.com/Spaceghost
'''

import _winreg

# wID = '''a4,00,00,00,03,00,00,00,30,30,33,37,31,2d,4f,45,4d,2d,\
#   39,30,34,36,31,36,32,2d,30,38,33,37,32,00,b4,00,00,00,58,31,35,2d,33,37,33,\
#   36,32,00,00,00,00,00,00,00,cd,dd,a4,ab,08,20,50,ac,01,29,9d,1d,ff,80,01,00,\
#   00,00,00,00,e0,92,bd,57,fa,8a,bf,fa,02,00,00,00,00,00,00,00,00,00,00,00,00,\
#   00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
#   00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,\
#   00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,00,29,52,73,82'''
# 
# s = wID.replace(',','').replace(' ','')
#
# result = s.decode("hex")
# print(result)

################################################################################

def DecodeKey(rpk):
    '''
    Returns a decoded product key.
    Input: list of strings
    Output: string
    '''
    rpkOffset = 52
    i = 28
    szPossibleChars = "BCDFGHJKMPQRTVWXY2346789"
    szProductKey = ""
    
    while i >= 0:
        dwAccumulator = 0
        j = 14
        while j >= 0:
            dwAccumulator = dwAccumulator * 256
            d = rpk[j+rpkOffset]
            if isinstance(d, str):
                d = ord(d)
            dwAccumulator = d + dwAccumulator
            rpk[j+rpkOffset] =  (dwAccumulator / 24) if (dwAccumulator / 24) <= 255 else 255 
            dwAccumulator = dwAccumulator % 24
            j = j - 1
        i = i - 1
        szProductKey = szPossibleChars[dwAccumulator] + szProductKey
        
        if ((29 - i) % 6) == 0 and i != -1:
            i = i - 1
            szProductKey = "-" + szProductKey
            
    return szProductKey

def GetKeyFromRegLoc(key, value="DigitalProductID"):
    try:
        key = _winreg.OpenKey(
        _winreg.HKEY_LOCAL_MACHINE,key)
    
        value, type = _winreg.QueryValueEx(key, value)
        
        return DecodeKey(list(value))
    except:
        return ''
    
def GetXPKey():
    return GetKeyFromRegLoc("SOFTWARE\Microsoft\Windows NT\CurrentVersion")

# print "XP: %s" % GetXPKey()
