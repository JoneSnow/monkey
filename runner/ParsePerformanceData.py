# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/20 12:02
import csv
import os
from collections import defaultdict

import pygal

from runner import RESULT


class ParsePerformanceData:
    def __init__(self):
        self.result = defaultdict(dict)

    def getFilepath(self):
        paths = defaultdict(list)
        for root, dirs, files in os.walk(top=RESULT, topdown=True):
            for name in files:
                if name.startswith("cpuinfo"):
                    filepath = os.path.join(root, name)
                    paths["cpu"].append(filepath)
                elif name.startswith("meminfo"):
                    filepath = os.path.join(root, name)
                    paths["mem"].append(filepath)
        return paths

    def getCpuinfo(self, filepath):
        """
        读取cpu占有率数据
        :param filepath:
        :return:
        """
        dic = defaultdict(list)
        path, filename = os.path.split(filepath)
        _, sn, package, time = filename.split("__")
        dic["package"] = package
        dic["sn"] = sn
        dic["time"] = time
        with open(filepath, "rb") as f:
            for item in f:
                if item:
                    dic["cpu"].append(item.split()[2])
        return dic

    def getMeminfo(self, filepath):
        dic = {}
        path, filename = os.path.split(filepath)
        time = filename.split(".")[0].split("__")[1]
        dic["mem_time"] = time
        mem, le = [], 0

        with open(filepath, "rb") as f:
            reader = csv.reader(f)
            for num,item in enumerate(reader):
                if num == 0:
                    le = len(item)
                    f.seek(0)
                    break
            for num in range(le):
                mem.append(self.getCol(reader, num))
                f.seek(0)
        self.dealMeminfo(mem, time)

    def run(self):
        paths = self.getFilepath()
        for key, value in paths.items():
            if key == "cpu":
                for item in value:
                    dic = self.getCpuinfo(item)
                    self.dealDic(dic)
            else:
                for item in value:
                    self.getMeminfo(item)
        self.toLine(mode="mem")
        self.toLine(mode="cpu")

    def dealDic(self, dic):
        sn = dic["sn"]
        package = dic["package"]
        cpu = [self.percentToFloat(item) for item in dic["cpu"]]
        mem = dic["mem"]
        time = dic["time"]
        if sn not in self.result:
            if cpu:
                self.result[sn] = {
                    dic[package]:{
                        dic["cpu"]: cpu,
                        dic["cpu_time"]: time
                    }
                }
            else:
                self.result[sn] = {
                    dic[package]:{
                        dic["mem"]:mem,
                        dic["mem_time"]: time
                    }
                }
        elif package not in self.result[sn]:
            if cpu:
                self.result[sn][package] = {
                    dic["cpu"]: cpu,
                    dic["cpu_time"]: time
                }
            else:
                self.result[sn][package] = {
                    dic["cpu"]: cpu,
                    dic["mem_time"]: time
                }
        elif "cpu" not in self.result[sn][package] and cpu:
            self.result[sn][package]["cpu"] = cpu
            self.result[sn][package]["cpu_time"] = time
        elif "mem" not in self.result[sn][package] and mem:
            self.result[sn][package]["mem"] = mem
            self.result[sn][package]["mem_time"] = time

    def getCol(self, data, i):
        col = [eachLine[i] for eachLine in data]
        return col

    def dealMeminfo(self, mem, t):
        for eachMem in mem:
            mem_list = []
            for num, item in enumerate(eachMem):
                if num == 0:
                    sn, package = item.split("__")
                    if sn not in self.result:
                        self.result[sn] = {package:{}}
                    elif package not in self.result[sn]:
                        self.result[sn][package] = {}
                else:
                    mem_list.append(float(item))
            self.result[sn][package]["mem"] = mem_list
        self.result[sn][package]["mem_time"] = t

    def percentToFloat(self, s):
        return int(s.strip("%"))

    def toLine(self, mode="mem"):
        for sn, content in self.result.items():
            date_chart = pygal.Line(x_label_rotation=20)
            s =u"内存" if mode == "mem" else u"CPU占有率"
            date_chart.title = u"{}统计图".format(s)
            for key, value in content.items():
                date_chart.add(key+" " + mode, value[mode])
            path = os.path.join(RESULT, "{}_{}.svg".format(sn, mode))
            date_chart.render_to_file(path)

if __name__ == "__main__":
    ParsePerformanceData().run()


