# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/16 17:48
import os
import subprocess

from runner.tools import Tools


class GetCpuInfo(object):
    def __init__(self, packages, sn="0123456789ABCDEF"):
        self.sn = sn
        self.sn_string = self.sn.replace(":", "_")
        self.packages = packages
        self.result_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "result") #result文件夹所在位置
        self.result_sn_path = os.path.join(self.result_path, self.sn_string)

    def creatpath(self):
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)
        if not os.path.exists(self.result_sn_path):
            os.mkdir(self.result_sn_path)

    def getCupinfo(self, package):
        path = os.path.join(self.result_sn_path, "cupinfo__{}__{}__{}".format(self.sn_string, package, Tools(self.sn).getDeviceTime()))
        cmd = "adb -s {} shell \"top -d 1|grep {}\" > {}".format(self.sn, package, path)
        p = subprocess.Popen(cmd, shell=True)
        return p.pid

    def run(self):
        pis = []
        self.creatpath()
        if isinstance(self.packages, list):
            for package in self.packages:
                pis.append(self.getCupinfo(package))
        else:
            pis.append(self.getCupinfo(self.packages))
        return pis