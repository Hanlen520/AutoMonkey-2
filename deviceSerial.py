'''

@author: user
'''
import os

devices = {"HC34PW101233"       :"HTCs720e",
           "f84697d2"           :"SamsungS5",
           "7eac292"            :"OnePlus",
           "HT4ABJT06089"       :"Nexus9",
           "016B7FFD1601201C"   :"Nexus",
           "BY2QUX14AU046007"   :"HonorL01",
           "4d00d6223a3570d5"   :"SamsungNoteII",
           "4df109d22ae0af0b"   :"SamsungNote2",
           "23d7c686"           :"MiNote"}

def get_Device():
    ret = os.popen("adb devices").readlines()
    if len(ret) == 1:
        print("No device detected")
        
    else:
        print ret
        serial = ret[1].strip().split("device")[0].strip()
        
    return serial

def get_devices():
    serialList = []
    
    ret = os.popen("adb devices").readlines()
    print ret
    if len(ret) == 1:
        print("No device detected")
    
    else:
        print("Totally {0} device{1} detected.".format(len(ret)-2, "s" if len(ret)>3 else ""))
        for i in range(1, len(ret)):
            serial = ret[i].strip().split("device")[0].strip()
            serialList.append(serial)
            if serial:
                if serial in devices.keys():
                    print(devices[serial] + " is connected successfully")
                else:
                    print("Unknown device " + serial + " is connected")
                    
    return serialList


print get_devices()