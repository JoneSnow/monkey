# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/16 17:48
import os
import subprocess

from runner.tools import Tools


class GetCpuInfo(object):
    """
    获取CPU占有率类
    """
    def __init__(self, packages, sn="0123456789ABCDEF"):
        """
        :param packages: 包名,可接受字符串app，也接受数列为参数。如:["ecarx.settings", "com.ecarx.eline"] 或者 "com.ecar.eline"
        :param sn: 设备串号
        :type packages: str|list
        :type sn: str
        """
        self.sn = sn
        self.sn_string = self.sn.replace(":", "_")
        self.packages = packages
        self.result_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "result") #result文件夹所在位置
        self.result_sn_path = os.path.join(self.result_path, self.sn_string)

    def creatpath(self):
        """
        创建数据归档路径
        """
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)
        if not os.path.exists(self.result_sn_path):
            os.mkdir(self.result_sn_path)

    def getcpuinfo(self, package):
        """
        获取cpu占有率
        :param package: 应用包名
        :return: 进程ID
        :type package: str
        :rtype: int
        """
        path = os.path.join(self.result_sn_path, "cpuinfo__{}__{}__{}".format(self.sn_string, package, Tools(self.sn).getDeviceTime()))
        cmd = "adb -s {} shell \"top -d 1|grep {}\" > {}".format(self.sn, package, path)
        p = subprocess.Popen(cmd, shell=True)
        return p.pid

    def run(self):
        """
        入口函数
        :return: 返回包含子进程ID的元组
        :rtype: tuple
        """
        pis = []
        self.creatpath()
        if isinstance(self.packages, list):
            for package in self.packages:
                pis.append(self.getcpuinfo(package))
        else:
            pis.append(self.getcpuinfo(self.packages))
        return pis