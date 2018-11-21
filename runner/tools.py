# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/7/13 15:46
import json
import logging
import os
import re
import subprocess
import time

from runner import RUNNER

logger = logging.getLogger(__name__)


class Tools(object):
    """通用方法类"""

    def __init__(self, sn=None):
        """
        :param sn: 设备号
        """
        self.sn = Tools.device() if sn is None else sn

    @staticmethod
    def devices():
        """
        获取所有连接的设备sn号， 返回一个sn的列表。 如果未查到任何设备， 将抛出ValueError异常
        :exception:  未查找的任何设备，函数抛出ValueError异常
        :return(list):  返回sn列表。 如[sn1, sn2]
        """
        logger.debug(u"获取所有连接状态的设备号")
        res = os.popen("adb devices")
        res = res.read().split()
        devices = [item for item in res if len(item) >= 16]
        if len(devices) == 0:
            logger.error(u"Can't find any devices", exc_info=True)
            raise ValueError(u"Can't find any devices")
        logger.debug(u"获取所有连接状态的设备号:{}".format(devices))
        return devices

    @staticmethod
    def device():
        """
        获取连接设备的第一个sn好，返回一个str。 如果未查找到任何设备， 将抛出ValueError异常
        :exception: 未查找的任何设备，函数抛出ValueError异常
        :return(str): 返回第一个sn号， 如： "1111111111111111"
        """
        devices = Tools.devices()
        logger.debug(u"获取连接状态的第一个设备号:{}".format(devices[0]))
        return devices[0]

    @staticmethod
    def execute(cmd):
        """
        执行命令行命令
        :param cmd: 执行命令行命令
        :return: 命令返回结果， 如果报错返回报错信息
        """
        try:
            res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            logger.debug("execute {} success. result: {}".format(cmd, res))
        except subprocess.CalledProcessError as e:
            res = "execute function error, returncode:{}, cmd:{}, output:{}".format(e.returncode, e.cmd, e.output)
            logger.error(res)
        return res

    def clearApp(self, appName):
        """
        清除应用缓存
        :param appName: 应用名
        """
        res = Tools.execute("adb -s {sn} shell pm clear {appName}".format(sn=self.sn, appName=appName))
        return res

    def stopApp(self, appName):
        """
        关闭app
        :param appName: 应用包名
        :return:执行结果
        """
        res = Tools.execute("adb -s {sn} shell am force-stop {appName}".format(sn=self.sn, appName=appName))
        time.sleep(2)
        return res

    def startApp(self, appname, activity):
        """
        adb命令开启应用

        :param appname:应用包名
        :type appname:str
        :param activity: 应用activity名
        :type activity:str
        :return: 执行结果
        :rtype: str
        """
        res = Tools.execute("adb -s {sn} shell am start -n {appname}/{activity}".format(sn=self.sn, appname=appname,
                                                                                        activity=activity))
        time.sleep(1)
        return res

    def clickByCmd(self, x, y):
        """adb命令点击屏幕坐标点"""
        res = Tools.execute("adb -s {sn} shell input tap {x} {y}".format(sn=self.sn, x=x, y=y))
        return res

    def crashInfo(self):
        """
        crash信息
        :return: {'system_app_strictmode@1532518894868.txt.gz': '2018-07-25_19:41'}
        """
        key = {}
        res = Tools.execute(
            "adb -s {} shell \"ls -al /data/system/dropbox |busybox awk \'{{print $5, $6, $7}}\'\"".format(self.sn))
        if "permission" not in res.lower():
            res = res.split("\r\r\n")
            for item in res:
                if item:
                    item = item.split()
                    time = item[0] + "_" + item[1]
                    name = item[2]
                    key[name] = time
            return key

    def anrInfo(self):
        """
        anr信息
        :return:  {'trace.txt': '2018-07-25_19:41'}
        """
        key = {}
        res = Tools.execute(
            "adb -s {} shell \"ls -al /data/anr |busybox awk \'{{print $5, $6, $7}}\'\"".format(self.sn))
        res = res.split("\r\r\n")
        for item in res:
            if item:
                item = item.split()
                time = item[0] + "_" + item[1]
                name = item[2]
                key[name] = time
        return key

    def getDeviceTime(self):
        """
        获取设备当前时间
        :return: 当前时间字符串，如"2018-07-25 10:50:32"
        """
        res = Tools.execute('adb -s {} shell "date +\\"%Y%m%d_%H%M%S\\""'.format(self.sn)).replace("\r\r\n", "").strip()
        return res

    @staticmethod
    def parseConfigJson():
        """
        解析config.json为字典
        :return: 字典数据
        """
        path = os.path.join(RUNNER, "config.json")
        with open(path) as f:
            dic = json.load(f)
        return dic

    @staticmethod
    def getConfigDevices():
        """
        获取config.json配置文件中services配置的uuid号
        :return: 包好uuid值的list
        """
        sns = []
        dic = Tools.parseConfigJson()
        services = dic["services"]
        for service in sorted(services):
            sn = Tools.parseConfigJson()["services"][service]["desired_caps"]["udid"]
            sns.append(sn)
        return sns

    def getSystemVersion(self):
        """
        获取系统ROM版本号

        :return: 返回系统版本号，如"03.02.08950.H30.00009"
        :rtype: str
        """
        if os.name == "nt":
            cmd = "adb -s {sn} shell getprop |findstr ro.build.display.id".format(sn=self.sn)
        else:
            cmd = "adb -s {sn} shell getprop |grep ro.build.display.id".format(sn=self.sn)
        res = Tools.execute(cmd)
        version = res.split(":")[-1]
        if version:
            version = version.strip().lstrip("[").rstrip("]")
        else:
            version = ""
        return version

    @staticmethod
    def getNumber(s):
        """
        过滤字符中的数字
        :param s: 字符串
        :return: 含有数字的字符串
        :type s: str
        :rtype: str
        """
        number_string = "".join(re.findall(r"\d+", s))
        return number_string