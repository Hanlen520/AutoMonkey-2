# Script to start "monkey" on the device, which has a very rudimentary
# shell.
#
version=$(getprop ro.build.version.sdk)
if [ $version -lt 14 ]
then
    echo "is 2.3"
else
    trap "" HUP
    echo "is 4.x"
fi
export CLASSPATH=/data/local/tmp/monkey.jar
exec app_process /data/local/tmp  com.monkey.Monkey "$@"
