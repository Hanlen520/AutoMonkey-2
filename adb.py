# -*- coding: utf-8 -*-
import time,os,sys
import subprocess
import logging
import thread
import platform

def adb_path():
    cur_path = os.path.dirname(os.path.abspath(__file__))
    osName = platform.system()
    if osName == "Windows":
        return os.path.join(cur_path, 'windows', 'adb.exe ')
    elif osName == "Linux":
        return os.path.join(cur_path, 'linux', 'adb ')
    elif osName == "Darwin":
        return os.path.join(cur_path, 'mac', 'adb ')
    else:
        print "unknown system" 
        return
    
class AdbDevice():
    def __init__(self, adbArgv=None):
        """
        @param adbArgv:adb
        @author: shwang
        @sample: 
        adbd = AdbCommands("-s 015F3EE203017013")
        """
        self.adb=adb_path()
        if adbArgv:
            self.adb = self.adb + adbArgv + " "
        self._NeedQuote=None
        self._isRooted=None
        
    
    def get_serialNo(self):
        return self.runCmdOnce("get-serialno")[0]
        
    def timer(self,process,timeout):
        num=0
        while process.poll()==None and num<timeout*10:
            num+=1
            time.sleep(0.1)
        if process.poll()==None:
            #os.system("taskkill /T /F /PID %d"%process.pid)
            print "%d process timeout ,be killed！"%process.pid
        thread.exit_thread()

    def runShellCmd(self,Cmd,TimeOut=3,returnSub=False):
        return self.runCmd("shell \"%s\" "%Cmd, TimeOut,returnSub)
    
    def _check_need_quote(self):#不同版本的su，不一样，有些需要引号，有些不需要
        cmd = "su -c ls -l /data/data"
        result = self.runShellCmd(cmd)
        if result==None:
            return
        for line in result:
            if 'com.android.phone' in line:
                self._NeedQuote = False
        if self._NeedQuote==None:
            self._NeedQuote = True
    
    def is_rooted(self):
        result = str(self.runShellCmd('id'))
        return result.find('uid=0(root)') >= 0
    
    def runRootShellCmd(self,Cmd,TimeOut=3,returnSub=False):
        if self._isRooted==None:
            self._isRooted=self.is_rooted()
        if self._isRooted:
            return self.runShellCmd(Cmd, TimeOut, returnSub)
        if self._NeedQuote==None:
            self._check_need_quote()
        if self._NeedQuote:
            return self.runShellCmd("""su -c '%s'"""%Cmd, TimeOut,returnSub)
        else:
#            print Cmd
            return self.runShellCmd("""su -c %s"""%Cmd, TimeOut,returnSub)
    
    def runCmdOnce(self,Cmd,TimeOut=3):
        print Cmd
        process=subprocess.Popen(self.adb+Cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        thread.start_new_thread(self.timer,(process,TimeOut))   
        #res=process.stdout.read() + process.stderr.read()
        res=process.stdout.read()
        process.communicate()
        process.wait()
        """
        if process.poll() != 0:
            error=process.stderr.read()
            print error
            if "killing" in (res or error):
                print 
                sys.exit(1)
            if ("device not found" or "offline") in (res or error):
                print 'Please confirm you phone have connect to PC!!!'
                #sys.exit(1)
            if "Android Debug Bridge version" in (res or error):
                print 'Adb cmd error!!!! Please check you adb cmd!!!'
                sys.exit(1)
            if "more than one" in (res or error):
                print 'More then one device, Please set -d option '
                sys.exit(1)
            #sys.exit(1)
            """
        res=res.replace("\r\n","\n").splitlines()
        return res
        
    def runCmd(self,Cmd,TimeOut=3,Retry=3):
        while Retry>=0:
            res=self.runCmdOnce(Cmd, TimeOut)
            if res!=None:
                break
            Retry-=1
        return res
        
    def install_package(self,path,TimeOut=30):
        res=self.runCmd("install -r \"%s\""%path, TimeOut)
        
        if res == []:
            logging.log(logging.WARN,"Install on Android 7.x above.")
            return True
        
        if res==None or "Failure" in res[1]:
            logging.log(logging.WARN,"Failed to install application.")
            return False
        else:
            logging.log(logging.WARN,"Install:%s successfully"%path)
            return True
    
    def uninstall_package(self,package,TimeOut=30):
        if self.runCmd("uninstall %s"%package, TimeOut)==None:
            logging.log(logging.WARN,"Failed to uninstall application.")
            return False
        logging.log(logging.WARN,"Uninstall:%s"%package)
        return True
    
    def list_process(self):
        '''获取进程列表
        '''
        processList=[]
        result = self.runShellCmd("/system/bin/ps")#防止使用的busybox的ps
        for line in result[1:]:
#             logging.log(logging.ERROR, line)
            line=line.split()
            processList.append({"processname":line[-1],"pid":line[1]})
        return processList
    
    def getProcessPId(self,ProcessName):
        processList=self.list_process()
#         logger.debug(processList)
        PidList=[]
        for process in processList:
            if process["processname"]==ProcessName:
                PidList.append(process["pid"])
#         print "####################################################"
#         logging.log(logging.WARN,PidList)
        return PidList
    
    def startNetcap(self,capfile):
        self.pushFile("tcpdump", "./data/tcpdump",4)
        self.runCmd("shell chmod 555 ./data/tcpdump")
        self.netcap=subprocess.Popen(self.adbType+'shell "./data/tcpdump  -l -X -n -s 0 -p -w ./data/%s >>/dev/null"'%capfile,shell=True)
    
    def stopNetcap(self):
        self.runCmd("shell pkill -2 tcpdump")
        time.sleep(1)
        
    def killProcess(self,pid=None,processname=None):
        if pid:
            self.runRootShellCmd("kill %s"%pid)
        elif processname:
            pidList=self.getProcessPId(processname)
            for pid in pidList:
                self.runRootShellCmd("kill %s"%pid)
        else:
            raise RuntimeError('killProcess方法使用错误' )

    def pushFile(self,src,dst,timeout=30):
        self.runCmd("push "+src+" "+dst,timeout)

    def pullFile(self,src,dst,timeout=30):
        self.runRootShellCmd("chmod 777"+" "+src)
        return self.runCmd("pull "+src+" "+dst,timeout)
        
    def adbRoot(self):
        if not self.runCmd("root"):
            logging.log(logging.WARN,"ROOT失败！请按ReadMe教程获取adb root权限！")
            return False
        return True

    def logcat(self):
        if not self.runCmd("logcat -d"):
            logging.log(logging.WARN,"获取日志失败！")
    
    def remount(self):
        self.runCmd("remount")

    def get_state(self):
        res=self.runCmd(self.adbType+"get-state")
        if not res:
            logging.log(logging.WARN,"终端连接中断！")
            return
        return res.readline()[0]

    def wait_for_device(self,timeOut=120):
        if not self.runCmd(self.adbType+"wait-for-device",timeOut):
            print "adb等待超时"
            
    def start_video(self, filepath="/sdcard/MTlog/", filename=".mp4", 
                    videoWidth=480, videoHeight=720, bitRate=250000):
        #t = settings.tparams["test_timestamp"]
        TimeStamp = time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
        # time format for file names > "MM_DD_YYYY__HH_MM_SS"
        #testTimeStamp = "_{0}_{1}_{2}__{3}_{4}_{5}_".format(t.month, t.day, t.year, t.hour, t.minute, t.second)
        #filename = filename.split(".")
        #filename.insert(1, testTimeStamp)
        #filename.insert(len(filename)-1, ".")
        #filename = "".join(filename)
        filename += TimeStamp

        cmd="adb shell screenrecord {0}{1} ".format(filepath, filename)
        # custom resolution parameters, to reduce file size
        cmd+="--size {0}x{1} --bit-rate {2}".format(videoWidth, videoHeight, bitRate)
        print("Recording video: " + cmd)
        try:
            self.stop_video()
        except:
            print sys.exc_info()[0]
            #print(sys.exec_info()[0])
        subprocess.Popen(shlex.split(cmd))
        return filename
    
    def stop_video(self):
        pid = self.find_process_by_name("screenrecord")
        if pid == "":
            print "screenrecord is not running, no need to kill process"
            return
        else:
            print("screenrecord PID found: " + str(pid))
            cmd = "adb shell kill -2 " + str(pid)
            print(cmd)
            subprocess.Popen(shlex.split(cmd))
            time.sleep(10) #video file needs some time to get completed before calling pull_video()
            
        
class AndroidDevice(AdbDevice):
    
    def __init__(self,serialNumber = None):
        if serialNumber:
            AdbDevice.__init__(self,"-s %s"%self.serialNumber)
        else:
            AdbDevice.__init__(self)

    
    