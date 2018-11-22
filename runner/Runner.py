# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/8/24 11:46
import datetime
import gzip
import logging
import os
import subprocess
import sys
import time
from itertools import islice
from multiprocessing.pool import ThreadPool as Pool

# 添加包路径
import pygal

path = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
sys.path.append(path)

from runner.GetCpuInfo import GetCpuInfo
from runner.ParsePerformanceData import ParsePerformanceData

from runner import ROOT
from runner.log import init_log
from runner.tools import Tools

logger = logging.getLogger(__file__)
import os.path

class Runner(object):
    def __init__(self):
        self.config = Tools.parseConfigJson()
        self.result = os.path.join(ROOT, "result")

    def init(self):
        result = self.result
        # create log path
        if not os.path.exists(result):
            os.mkdir(result)
            time.sleep(1)
        # logger初始化
        init_log()

    def run(self):
        """
        入口函数,
        :rtype: dict
        :return:返回monkey统计数据，
        {"0123456789ABCDEF":  #设备串号
            "detail":[{       #各个错误文件详细信息
                "anr":1，     # 出现anr次数
                "crash":0，   #出现crash次数
                "filename": 'system_app_anr@1542696522720.txt.gz'， #log中对应的文件名
                "msg": "",  #错误详细信息
                "package": 'ecarx.voiceservice v3190 (1.6.0)', #错误应用
                "strictmode": 0，#出现strictmode次数
                "other": 0      #其他错误出现次数
            }],
            "detail_package_summary":{  #基于应用的错误统计
                "ecarx.news": {         #应用名称
                    "anr":0,            #anr出现次数
                    "crash":0,          #crash出现次数
                    "other":0,          #其他错误出现次数
                    "strictmode":1,     #标准模式
                }
            },
            "duration": 0:00:28.766000, #测试持续时间
            "rom": '18.00.11.84552.00000', #系统版本号
            "summary":{                 #全部错误数量统计
                "anr":1, "crash": 0, "other": 0, "strictmode":7
            }
        }
        :rtype:dict
        """
        logger.debug(u"start")
        info = []
        result = {}
        Tools.execute("adb kill-server")
        Tools.execute("adb start-server")
        self.checkDevices()
        self.init()
        pool = Pool(processes=len(self.config))
        for key, value in self.config.items():
            sn = value["sn"]
            packages = value["packages"]
            throttle = value["throttle"]
            info.append(pool.apply_async(self.monkey, (sn, packages, throttle,)))
        pool.close()
        pool.join()
        for i in info:
            result.update(i.get())
        self.toBar(result)
        self.to_html(result)
        ParsePerformanceData().run()
        return result

    def checkDevices(self):
        """
        检查配置文件中的sn号是否存在于已连接的设备中
        :raise: ValueError
        """
        # 连接网络设备
        logger.debug(u"链接网络设备")
        config_devices = self.getConfigDevices()
        for device in config_devices:
            if ":" in device:
                Tools.execute("adb connect {ip}".format(ip=device))
        logger.debug(u"检查配置文件中的设备是否在链接状态")
        results = []
        connect_devices = Tools.devices()
        config_devices = self.getConfigDevices()
        for item in config_devices:
            if item not in connect_devices:
                results.append(item)
        if results:
            logger.error(u"检查设备链接状态失败", exc_info=True)
            raise ValueError(
                u"can't find config devices {} in connect devices, please check config.json".format(results))

    def getConfigDevices(self):
        """
        获取config配置文件的所有sn号
        :return: 返回含有sn号的生成器
        """
        sns = [value["sn"] for key, value in self.config.items()]
        logger.debug(u"获取配置文件的设备号{}".format(sns))
        return sns

    def monkey(self, sn, packages, throttle):
        """
        执行monkey测试
        :param sn: 设备串口号
        :param packages: app包名
        :param throttle: 测试频率
        :type sn: str
        :type packages: str
        :type throttle: str
        :rtype: dict
        :return: 返回monkey测试数据， 如:
        {"0123456789ABCDEF":  #设备串号
            "detail":[{       #各个错误文件详细信息
                "anr":1，     # 出现anr次数
                "crash":0，   #出现crash次数
                "filename": 'system_app_anr@1542696522720.txt.gz'， #log中对应的文件名
                "msg": "",  #错误详细信息
                "package": 'ecarx.voiceservice v3190 (1.6.0)', #错误应用
                "strictmode": 0，#出现strictmode次数
                "other": 0      #其他错误出现次数
            }],
            "detail_package_summary":{  #基于应用的错误统计
                "ecarx.news": {         #应用名称
                    "anr":0,            #anr出现次数
                    "crash":0,          #crash出现次数
                    "other":0,          #其他错误出现次数
                    "strictmode":1,     #标准模式
                }
            },
            "duration": 0:00:28.766000, #测试持续时间
            "rom": '18.00.11.84552.00000', #系统版本号
            "summary":{                 #全部错误数量统计
                "anr":1, "crash": 0, "other": 0, "strictmode":7
            }
        }
        """
        logger.debug(u"{}, monkey测试开始".format(sn))
        #delete log
        self.delete_log(sn)
        sn_string = sn.replace(":", "_") if ":" in sn else sn
        info = {}
        package_string = ""
        starttime = datetime.datetime.now()
        t = starttime.strftime("%Y%m%d%H%M%S")
        logcat_log = "logcat_{}_{}".format(sn_string, t)
        monkey_log = "monkey_{}_{}".format(sn_string, t)
        result_path = os.path.join(ROOT, "result")
        log_path = os.path.join(result_path, sn_string)
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        logcat_log_path = os.path.join(log_path, logcat_log)
        monkey_log_path = os.path.join(log_path, monkey_log)
        # rom 版本号
        rom = Tools(sn).getSystemVersion()
        for package in packages[:]:
            package_string += "-p {} ".format(package)
        pis = []
        try:
            #收集log
            p_log = subprocess.Popen("adb -s {sn} logcat -c && adb -s {sn} logcat -v time > {logcat_log_path}".format(
                sn=sn,logcat_log_path=logcat_log_path),shell=True)
            #收集cpu占有率信息
            p_cpuinfo = GetCpuInfo(packages=packages[:], sn=sn).run()
            time.sleep(2)
            Tools.execute(
                "adb -s {sn} shell monkey {package_string} --ignore-timeouts --ignore-crashes"
                " --ignore-security-exceptions --kill-process-after-error --monitor-native-crashes"
                " --pct-syskeys 0 -v -v -v -s 3343 --throttle {throttle} > {mpath}".format(sn=sn, package_string=package_string,
                                                                                           throttle=throttle, mpath=monkey_log_path))
            pis.append(p_log.pid)
            pis.extend(p_cpuinfo)
        finally:
            for p in pis:
                Tools.execute("taskkill /t /f /pid {}".format(p))
        #get log
        self.get_log(sn, log_path)
        #prase log
        endtime = datetime.datetime.now()
        duration = endtime - starttime
        # parse log
        detail = []
        summary = { "anr":0, "crash":0, "strictmode":0, "other":0}
        detail_package_summary = {}
        for item in self.parse_log(log_path):
            detail.append(item)
            packagename = item.get("package", None)
            if packagename:
                if packagename not in  detail_package_summary:
                    detail_package_summary.update({packagename:{"anr": 0, "crash":0, "strictmode":0, "other":0}})
                if item["anr"]:
                    detail_package_summary[packagename]["anr"] += 1
                elif item["crash"]:
                    detail_package_summary[packagename]["crash"] += 1
                elif item["strictmode"]:
                    detail_package_summary[packagename]["strictmode"] += 1
                elif item["other"]:
                    detail_package_summary[packagename]["other"] += 1
            if item["anr"]:
                summary["anr"] += 1
            elif item["crash"]:
                summary["crash"] += 1
            elif item["strictmode"]:
                summary["strictmode"] += 1
            elif item["other"]:
                summary["other"] += 1
        info[sn] = {"duration": duration, "rom": rom, "detail": detail, "summary": summary, "detail_package_summary": detail_package_summary }
        logger.debug(u"{}, monkey执行结果数据:{}".format(sn, info))
        return info

    def to_html(self, dic):
        """
        数据转为html
        :param dic: monkey测试完的数据， self.monkey返回的字典数据
        :type dic: dict
        """
        from jinja2 import PackageLoader, Environment

        env = Environment(loader=PackageLoader("runner", 'templates'))  # 创建一个包加载器对象

        template = env.get_template('template.html')  # 获取一个模板文件
        s = template.render(dict = dic)
        with open("../result/report.html", "w") as f:
            f.write(s)

    def toBar(self, dic):
        """
        系统错误的APP分布直方图
        :param dic: monkey测试完的数据， self.monkey返回的字典数据
        :type dic: dict
        """
        bar_chart = pygal.Bar()
        bar_chart.title = u"系统错误的APP分布"
        for key, value in dic.items():
            for key1, value1 in value["detail_package_summary"].items():
                bar_chart.add(key1, [value1["crash"] + value1["anr"] + value1["strictmode"] + value1["other"]])
        path = os.path.join(os.path.join(ROOT, "result"), "bar.svg")
        bar_chart.render_to_file(path)
        
    def parse_log(self, path):
        """
        解析log
        :param path:  log所在路径
        :return: 生成器
        """
        dropbox = os.path.join(path, "dropbox")
        for filename in os.listdir(dropbox):
            filepath = os.path.join(dropbox, filename)
            yield self.get_info(filename, filepath)

    def get_info(self, filename, filepath):
        """
        获取filepath中的文件详细错误信息
        :param filename: 文件名
        :param filepath: 文件所在路径
        :return: dict
        """
        info = {
            "filename": filename,
            "anr": 0,
            "crash": 0,
            "strictmode": 0,
            "other": 0
        }
        if filename.startswith("system_app") or filename.startswith("data_app"):
            for item in [".txt", ".gz"]:
                detail = self.get_info_detail(filepath, item)
                if detail:
                    package, msg = detail
                    info["msg"] = msg
                    info["package"] = package
        if "app_anr" in filename:
            info["anr"] += 1
        elif "app_crash" in filename:
            info["crash"] += 1
        elif filename.startswith("system_app_strictmode"):
            info["strictmode"] += 1
        else:
            info["other"] += 1
        return info

    def get_info_detail(self, filepath, filetype=".txt"):
        """
        文件内容中的详细错误信息
        :param filepath: 文件所在路径
        :param filetype: 文件类型，可选参数: ".txt", ".gz"
        :return:包含包名和想起错误的元素
        :rtype: tuple
        """
        if filepath.endswith(filetype):
            package = []
            if filetype == ".txt":
                with open(filepath, "r") as f:
                    msg = islice(f, 0, 10)
                    msg = list(msg)
                    for i in msg:
                        if "Package" in i:
                            package.append(i.split(":")[1].strip())
                    package = ",".join(package)
                    msg = "<br>".join(msg)
                    return (package, msg)
            elif filetype == ".gz":
                with gzip.open(filepath, "r") as f:
                    msg = islice(f, 0, 10)
                    msg = list(msg)
                    for i in msg:
                        if "Package" in i:
                            package.append(i.split(":")[1].strip())
                    package = ",".join(package)
                    msg = "<br>".join(msg)
                    return (package, msg)

    def delete_log(self, sn):
        """
        清除设备log
        :param sn: 设备串号
        :type sn: str
        """
        Tools.execute("adb -s {sn} shell rm -rf /data/system/dropbox/*".format(sn=sn))
        Tools.execute("adb -s {sn} shell rm -rf /data/anr/*".format(sn=sn))
        Tools.execute("adb -s {sn} shell rm -rf /data/tombstone/*".format(sn=sn))
        Tools.execute("adb -s {sn} shell rm -rf /data/kernel_log/*".format(sn=sn))
        Tools.execute("adb -s {sn} shell rm -rf /sdcard/AmapAutoLog/*".format(sn=sn))

    def get_log(self, sn, log_path):
        """
        获取设备log
        :param sn: 设备串号
        :param log_path: log归档地址
        :type sn: str
        :type log_path: str
        """
        Tools.execute("adb -s {sn} pull /data/system/dropbox/ {log_path}".format(sn=sn, log_path=log_path))
        Tools.execute("adb -s {sn} pull /data/anr/ {log_path}".format(sn=sn, log_path=log_path))
        Tools.execute("adb -s {sn} pull /data/tombstone {log_path}".format(sn=sn, log_path=log_path))
        Tools.execute("adb -s {sn} pull /data/kernel_log {log_path}".format(sn=sn, log_path=log_path))
        Tools.execute("adb -s {sn} pull /sdcard/AmapAutoLog {log_path}".format(sn=sn, log_path=log_path))

    # def kill_all(self):
    #     Tools.execute("wmic process where name=\"node.exe\" delete")

if __name__ == "__main__":
    r = Runner()
    r.run()
