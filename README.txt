autoMonkey自动化测试框架之运行篇

写在前面：
1、如何解析日志请参考autoMonkey自动化测试框架之解析篇，运行环境为Python2.7版本
2、流程图请参考：https://www.processon.com/view/link/5b23648be4b0d33dc2f2eb83
3、笔记分享: http://note.youdao.com/noteshare?id=fb942e6a61f94224c24182fa3578d035&sub=B04EA08F00C5477EA75C7162E68F5BE5

简要说明：
	runDmallNativeMonkey.py：google原生monkey的运行主入口
	runNewMonkeydmall.py：自研autoMonkey的运行主入口
	installDmall3.py：提供自动去Jenkins中下载最新版本的方法
	adb.py：封装adb常用方法，提供shell命令执行等
	monkey.jar：基于原生monkey修改并编译生成的jar包，有copyright要求，请不要分享到外部
