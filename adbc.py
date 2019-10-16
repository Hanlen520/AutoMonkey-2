# -*- coding: utf-8 -*-  
'''
Created on 2016年4月2日

@author: shoubo.wang

'''
import time
import subprocess
import os
import thread
#import thread for python 2.x
import sys
import logging
#from log import logger

class AdbDevice():
    def __init__(self,Type=None,serialNumber=None):
        self.adbType=self.getadbType(Type,serialNumber)
        self._NeedQuote=None
        self._isRooted=None
    
    def getadbType(self,Type,serialNumber):    
        adbType="adb "
        if  serialNumber:
            adbType+="-s %s "%serialNumber
        elif Type:
            adbType+=Type+" "
        return adbType
        
    def timer(self,process,TimeOut):
        num=0
        while process.poll()==None and num<TimeOut*10:
            num+=1
            time.sleep(0.1)
        if process.poll()==None:
            os.system("taskkill /T /F /PID %d"%process.pid)
            print process.pid
            logging.log(logging.WARN,u"%d进程超时，被强行关闭！"%process.pid)
            
        thread.exit_thread()

    def runShellCmd(self,Cmd,TimeOut=3,returnSub=False):
#        print Cmd
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
    
    def runCmd(self,Cmd,TimeOut=5,returnSub=False,Retry=3):
        while Retry>0:
            try:
                return self.runCmdOnce(Cmd, TimeOut, returnSub)
            except RuntimeError:
                pass
            Retry-=1
            
    def runCmdOnce(self,Cmd,TimeOut=3,returnSub=False):

        process=subprocess.Popen(self.adbType+Cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        if not returnSub:
            thread.start_new_thread(self.timer,(process,TimeOut))  
            #output,Error=process.communicate()
            res=process.stdout.read()
            process.wait()
            if process.poll() != 0:
                error=process.stderr.read()
                logging.log(logging.WARN,error)
                logging.log(logging.WARN,u"adb执行出错或超时，命令是：")
                logging.log(logging.WARN,self.adbType+Cmd)
                if "killing" in error:
                    logging.log(logging.WARN,"请结束所有管理手的软件，尝试adb shell 是否能运行")
                    sys.exit(1)
                if ("device not found" in res) or ("device not found" in error) or ("offline" in error) or ("offline" in error):
                    logging.log(logging.WARN,"设备未找到，或离线，请先保证adb shell能运行")
    #                 sys.exit(1)
                if "Android Debug Bridge version" in (res or error):
                    logging.log(logging.WARN,"adb命令有错误！")
                    sys.exit(1)
                if "more than one" in (res or error):
                    logging.log(logging.WARN,"多台设备连接电脑，请在调用时使用选项-s serialnumber，详细查看说明！")
                    sys.exit(1)
                raise RuntimeError("adb执行出错或超时，命令是："+self.adbType+Cmd)
            
            res=res.replace("\r\n","\n").splitlines()
            
#             print res
            if len(res)==0:
                return None
            return res
        
        else:
            return process
    
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
            print("adb等待超时")

    def install_package(self,path,TimeOut=120):
        res=self.runCmd("install \"%s\""%path, TimeOut)
        if res==None or "Failure" in res[1]:
            logging.log(logging.WARN,"安装文件不成功！")
            return False
        logging.log(logging.WARN,"安装：%s"%path)
        return True
    
    def uninstall_package(self,package,TimeOut=30):
        if self.runCmd("uninstall %s"%package, TimeOut)==None:
            logging.log(logging.WARN,"卸载文件不成功！")
            return False
        logging.log(logging.WARN,"卸载：%s"%package)
        return True
    
    def start_activity(self,activityname):
        self.runCmd("shell am start %s"%activityname)
    
    def stop_package(self,package):
        self.runCmd("shell am force-stop %s"%package)
    
    def clear_package(self,package):
        self.runCmd("shell pm clear %s"%package)
        
    def input(self,string):
        self.runCmd("shell input text %s"%string)
        
    def press_keyevent(self,keyname):
        self.runCmd("shell input keyevent %s"%keyname)
    
if __name__=="__main__":
    device=AdbDevice()
    print(device.list_process())
