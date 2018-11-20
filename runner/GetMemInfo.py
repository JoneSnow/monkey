# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/16 17:48
import csv
import multiprocessing
import os
import re
import sys
import time

from runner.Runner import Runner

path = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
sys.path.append(path)
from runner.tools import Tools


class GetMemInfo(object):
    """
    获取指定sn手机下的指定应用包的性能数据
    """
    def __init__(self, packages, sn):
        self.sn = "" if sn is None else sn
        self.sn_string = self.sn.replace(":", "_")
        self.packages = packages
        self.result_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "result")  # result文件夹所在位置
        self.path = os.path.join(self.result_path, self.sn_string) # sn文件夹所在文职
        self.csv_path = os.path.join(self.path, "meminfo__{}.csv".format(Tools(self.sn).getDeviceTime()))

    def getMeminfo(self, package):
        res = Tools.execute("adb -s {} shell \"dumpsys meminfo {} |grep TOTAL|busybox awk '{{print $2}}'\"".format(self.sn, package))
        res = self.getNumber(res)
        return res

    def run(self):
        self.creatpath()
        header = [self.sn + "__" + package for package in self.packages]
        self.toCsv(header)
        while True:
            if isinstance(self.packages, list):
                row = []
                for package in self.packages:
                    row.append(self.getMeminfo(package))
                self.toCsv(row)
            else:
                res = self.getMeminfo(self.packages)
                self.toCsv([res])
            time.sleep(1)

    def getNumber(self, s):
        number_string = "".join(re.findall(r"\d+", s))
        return number_string

    def toCsv(self, data):
        with open(self.csv_path, 'ab') as infile:
            writer = csv.writer(infile, delimiter=',')
            writer.writerow(data)

    def creatpath(self):
        if not os.path.exists(self.result_path):
            os.mkdir(self.result_path)
        if not os.path.exists(self.path):
            os.mkdir(self.path)

def worker(packages, sn):
    GetMemInfo(packages, sn).run()

if __name__ == "__main__":
    '''cmd script'''
    Runner().checkDevices()
    pool = []
    config = Tools.parseConfigJson()
    for device, content in config.items():
        sn = content["sn"]
        packages = content["packages"]
        p = multiprocessing.Process(target=worker, args=(packages, sn))
        p.daemon = True
        pool.append(p)
    for item in pool:
        item.start()
        item.join()
    print "done!"

