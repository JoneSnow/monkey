# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/20 12:02
import csv
import os
from collections import defaultdict

import pygal

from runner import RESULT
from runner.tools import Tools


class ParsePerformanceData:
    """解析性能数据类"""
    def __init__(self):
        self.result = defaultdict(dict)

    def getFilepath(self):
        """
        获取log中所有的cpu，内存数据文档所在路径
        :return: {
            "cpu":[],  #cpu数据文档路径
            "mem":[]   #内存数据文档路径 
        }
        :rtype: dict 
        """
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
        :param filepath: cpu数据文档所在路径
        :type filepath: str
        :return: {
            "package": "com.ecarx.settings",#应用包名
            "sn": "0123456789ABCDEF",       #设备串号
            "time": "20191120_172551",      #记录开始时间
            "cpu": []                       #cpu占有率list
        } 
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
        """
        获取内存信息
        :param filepath: 内存文档所在路径 
        """
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
        """
        入口函数
        """
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
        """
        数据转换至self.result
        :param dic:  self.getCpuinfo方法所返回的数据
        """
        sn = dic["sn"]
        package = dic["package"]
        cpu = [self.percentToInt(item) for item in dic["cpu"]]
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
        """
        获取二维数据中的某列数据
        :param data: 二位数列
        :param i:  第几列
        :return: 某列数据
        :type data: list
        :type i: int
        :rtype: list
        """
        col = [eachLine[i] for eachLine in data]
        return col

    def dealMeminfo(self, mem, t):
        """
        转换内存数据信息至self.result
        """
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
                    mem_list.append(self.strToFloat(item))
            self.result[sn][package]["mem"] = mem_list
        self.result[sn][package]["mem_time"] = t

    def percentToInt(self, s):
        """
        转换百分比字符串数据至int
        :param s: 百分比字符串
        :return: int
        :type s: str
        :rtype: int
        """
        return int(s.strip("%"))

    def toLine(self, mode="mem"):
        """
        数据转为折线图
        :param mode: 转换模式，可选参数: "mem" 或者 "cpu"
        """
        for sn, content in self.result.items():
            date_chart = pygal.Line(x_label_rotation=20)
            s =u"内存" if mode == "mem" else u"CPU占有率"
            date_chart.title = u"{}统计图".format(s)
            for key, value in content.items():
                date_chart.add(key+" " + mode, value[mode])
            path = os.path.join(RESULT, "{}_{}.svg".format(sn, mode))
            date_chart.render_to_file(path)

    def strToFloat(self, s):
        s = Tools.getNumber(s)
        if s == "":
            return 0
        return float(s)

if __name__ == "__main__":
    ParsePerformanceData().run()


