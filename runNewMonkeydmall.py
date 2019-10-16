# coding=utf-8
'''
Created on 2016-3-30
@author: shoubo.wang

'''

import os, time
import adb
#import deviceSerial
import random
import config
import installDmall3
#import re
#import multiprocessing

LOCAL_DIR_ANDROID = "/data/local/tmp"
MONKEY_PATH_ANDROID = "%s/monkey" % LOCAL_DIR_ANDROID
LOG_PATH_ANDROID = "%s/MTlog/" % LOCAL_DIR_ANDROID

LOCAL_DIR_PC = os.path.dirname(__file__)
MONKEY_PATH_PC = os.path.join(LOCAL_DIR_PC, "monkey")
MONKEYJAR_PATH_PC = os.path.join(LOCAL_DIR_PC,"monkey.jar")

class RunMonkey():
    def __init__(self,device):
        self.device=device
        if not self.has_monkey():
            self.init_monkey()
            
    def has_logDir(self,LOG_PATH_ANDROID):
        if not os.path.exists(LOG_PATH_ANDROID):
            self.device.runRootShellCmd("mkdir %s" % LOG_PATH_ANDROID)
        self.device.runRootShellCmd("chmod -R 777 %s" % LOG_PATH_ANDROID)
            
    def has_monkey(self):
        res = self.device.runRootShellCmd("ls %s" % LOCAL_DIR_ANDROID)
        #print "has_monkey is running"
        if str(res).find("monkey") >= 0 and str(res).find("monkey.jar")>=0:
            return True
        return False
    
    def init_monkey(self):
        self.device.pushFile(MONKEY_PATH_PC, LOCAL_DIR_ANDROID)
        self.device.pushFile(MONKEYJAR_PATH_PC, LOCAL_DIR_ANDROID)
#        print "init_monkey is running"
        self.device.runRootShellCmd("chmod 777 %s" % MONKEY_PATH_ANDROID)
        self.device.runRootShellCmd("chmod -R 777 %s" % LOG_PATH_ANDROID)
        
    def push_dumpFile(self):   
        while True:
            res = self.device.runRootShellCmd("ls /sdcard/")
            if str(res).find("dump.hprof") >= 0:
                ts = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
                res = self.device.runRootShellCmd("mv /sdcard/dump.hprof /sdcard/dump{}.hprof".format(ts))
                time.sleep(120)
         
    def start_monkey(self, app, branch, server, version, jenkinsBuildID, times, logcat=False):

        self.has_logDir(LOG_PATH_ANDROID)
        deviceNo = self.device.get_serialNo()
        param = []
        param.append("--throttle 400 ")
        param.append("-s {} ".format(random.randint(10, 100000)))
        package = "{}".format("com.wm.dmall" if "release" in server else "com.wm.dmall.debug")
        param.append("-p {} ".format(package))
        #param.append("--forbidactivity-list com.sgiggle.app.settings.SettingsPreferenceModernActivity ")
        param.append("--ignore-crashes ")
        param.append("--ignore-native-crashes ")
        param.append("--ignore-timeouts ")
        #param.append("--monitor-native-crashes ")
        param.append("--ignore-security-exceptions ")
        param.append("--pct-ui 40 ")
        param.append("--pct-touch 30 ")
        param.append("--pct-syskeys 2 ")
        param.append("--pct-anyevent 0 ")
        param.append("--bugreport ")
        param.append("-v -v")
        
        log_suffix = "dmall" + "-" + branch + "-" + str(jenkinsBuildID) + "-" + version + server + "-" + deviceNo + "-" + time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
        #print log_suffix
        logFile = "%s.log" % log_suffix
        fullLogFile = "> %s%s 2>&1 &" % (LOG_PATH_ANDROID, logFile)
        #start = time.time()
        self.device.runRootShellCmd("%s %s %s %s" % (MONKEY_PATH_ANDROID, "".join(param), times, fullLogFile),3,False)

        if logcat:
            logFile_logcat = "logcat-" + logFile
            logcat_cmd = "logcat -v time > "
            self.device.runRootShellCmd("%s%s" %(logcat_cmd, logFile_logcat), 3, True)
        

    def stop_monkey(self):
#        if self.is_monkey_running():
#        print self.processId
        self.device.runRootShellCmd("kill %s"%self.processId)
#       else:
#            pass

    def is_monkey_running(self):
        processList=self.device.list_process()
        for process in processList:
            if process["pid"]==self.processId:
                return True
        return False
    
    def get_monkey_pid(self):
        Retry = 5
        while Retry > 0:
            processList = self.device.list_process()
            for process in processList:
                if process["processname"]=="com.tencent.monkey":
                    return process["pid"]
            time.sleep(0.3)
            Retry -= 1   
        return None
    
    def get_package_pid(self, package):
        Retry = 5
        while Retry > 0:
            processList = self.device.list_process()
            for process in processList:
                if process["processname"]==package:
                    return process["pid"]
            time.sleep(0.3)
            Retry -= 1   
        return None
    
def setEvents(msg, default=2000000):
    try:
        times = input(msg)
        if times != "":
            default = int(times)
    except:
        raise ValueError
    
    finally:
        return str(default)

def runMonkey(app, branch, server, version, jenkinsBuildID):
    monkey = RunMonkey(device)
    #monkey.init_monkey()
    times=setEvents("Type the count of events to start Monkey testing. Press Enter for the default value 1,500,000.")
    monkey.start_monkey(app, branch, server, version, jenkinsBuildID, times, False)
    print("DMall New Monkey is running!")
    print("Press ctrl+c to stop")
    
    while monkey.is_monkey_running:
        try:
            if monkey.get_monkey_pid()==None:
                print('Monkey finished!')
                break
            time.sleep(0.5)
        except KeyboardInterrupt:
            #monkey.stop_monkey()
            print('Monkey has stopped')          
            break

if __name__=="__main__":
    device = adb.AdbDevice()
    #device = adbdevice_in.AdbDevice()
    need_auto_upgrade = False
    pureInstall = False

    if need_auto_upgrade:
        (app, version, env) = ("com.wm.dmall", "4.1.0", "-dmtest")
        (jenkinsBuildID, downloadURL) = installDmall3.getDownloadURL(config.uriForStore["jenkins"], version, env)
        print jenkinsBuildID
        print downloadURL
        if downloadURL:
            apkFile = installDmall3.isReadyForInstall(downloadURL)
            if apkFile:
                print apkFile
                
                if pureInstall:
                    print u"你选择了全新安装，安装之前会自动卸载手机上已安装的多点App。"
                    device.uninstall_package(app)
                    
                else:
                    print u"你选择了覆盖安装，安装包已经就绪，马上安装。"
                    
                appInstall = device.install_package(apkFile)
                
                if appInstall:
                    print u"APP安装成功，测试马上进行。"
                    revision = apkFile.split("-")[2]
                    runMonkey(app, version, env, revision, jenkinsBuildID)
                    
                else:
                    print u"安装失败。"
                    
            else:
                print u"APP下载失败。"
                
        else:
            print u"Jenkins服务不可用。"
         
    else:
        print u"不使用Jenkins上的最新APP进行测试。"
        #runMonkey("com.wm.dmall", "V3.8.8", "release-okhttp","c33849360-","okhttp")
        runMonkey("com.wm.dmall", "V4.1.0", "dmtest","82e2229-","3832")
            