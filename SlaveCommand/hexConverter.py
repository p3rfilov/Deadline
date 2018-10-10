'''
Hex to ASCII converter
All credit goes to "Spaceghost"
https://gist.github.com/Spaceghost
'''

import _winreg

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
