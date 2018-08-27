# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/8/24 11:46
import copy
import datetime
import logging
import os
import shutil
import subprocess
import time
from multiprocessing.pool import ThreadPool as Pool

import sys
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.styles import colors, PatternFill, Border, Side, Alignment
from openpyxl.styles import numbers

from runner import RUNNER, ROOT
from runner.log import init_log
from runner.parse_log import ParseLog
from runner.tools import Tools

logger = logging.getLogger(__file__)


class Runner(object):
    def __init__(self):
        self.config = Tools.parseConfigJson()
        self.result = os.path.join(ROOT, "result")

    def init(self):
        # del log
        result = self.result
        if os.path.exists(result):
            shutil.rmtree(result)
            time.sleep(1)
        # create log path
        os.mkdir(result)
        time.sleep(1)
        # logger初始化
        init_log()

    def run(self):
        """
        入口函数
        :return:{u'0123456789ABCDEF': {'duration': '0:00:04.237000', 'crash': 2, 'detail': {'01-01 00:12:12.080': ' *** FATAL EXCEPTION IN SYSTEM PROCESS: main\r\n java.lang.NullPointerException\r\n \tat com.android.commands.monkey.MonkeySourceRandom.randomPoint(MonkeySourceRandom.java:324)\r\n', '01-01 00:12:11.070': ' *** FATAL EXCEPTION IN SYSTEM PROCESS: UI\r\n java.lang.NullPointerException\r\n \tat com.android.internal.widget.PointerLocationView.addPointerEvent(PointerLocationView.java:552)\r\n'}, 'anr': 0, 'rom': '03.02.08950.H30.00009'}}
        :rtype:dict
        """
        logger.debug(u"start")
        info = []
        result = {}
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
            self.to_excel(result.update(i.get()))
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
        '''
        获取config配置文件的所有sn号
        :return: 返回含有sn号的生成器
        '''
        sns = [value["sn"] for key, value in self.config.items()]
        logger.debug(u"获取配置文件的设备号{}".format(sns))
        return sns

    def monkey(self, sn, packages, throttle):
        logger.debug(u"{}, monkey测试开始".format(sn))
        sn_string = sn.replace(":", "_") if ":" in sn else sn
        info = {}
        package_string = ""
        starttime = datetime.datetime.now()
        t = starttime.strftime("%Y%m%d%H%M%S")
        logcat_log = "logcat_{}_{}".format(sn_string, t)
        monkey_log = "monkey_{}_{}".format(sn_string, t)
        result_path = os.path.join(ROOT, "result")
        logcat_log_path = os.path.join(result_path, logcat_log)
        monkey_log_path = os.path.join(result_path, monkey_log)
        # rom 版本号
        rom = Tools(sn).getSystemVersion()
        for package in packages[:]:
            package_string += "-p {}".format(package)
        p1 = subprocess.Popen("adb -s {sn} logcat -c && adb -s {sn} logcat -v time > {logcat_log_path}".format(sn=sn,
                                                                                                               logcat_log_path=logcat_log_path),
                              shell=True)
        Tools.execute(
            "adb -s {sn} shell monkey {package_string} --ignore-timeouts --ignore-crashes"
            " --ignore-security-exceptions --kill-process-after-error --monitor-native-crashes"
            " -v -v -v -s 3343 --throttle {throttle} > {mpath}".format(sn=sn, package_string=package_string,
                                                                       throttle=throttle, mpath=monkey_log_path))
        Tools.execute("taskkill /t /f /pid {}".format(p1.pid))
        endtime = datetime.datetime.now()
        duration = str(endtime - starttime)
        # parse log
        log = ParseLog(path=logcat_log_path)
        res = log.parse()
        info[sn] = {"duration": duration, "crash": log.crash, "anr": log.anr, "detail": res, "rom": rom}
        logger.debug(u"{}, monkey执行结果数据:{}".format(sn, info))
        return info

    def to_excel(self, dic):
        logger.debug(u"生成测试结果表格")
        filepath = os.path.join(self.result, "result_{}.xlsx".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
        template_path = os.path.join(RUNNER, "template.xlsx")
        dic = copy.deepcopy(dic)
        shutil.copy(template_path, filepath)
        wb = load_workbook(filepath)
        # 简介页面
        ws = wb["Summary"]
        start_row = 3
        font = Font(name=u"宋体", color=colors.BLACK, size=11)
        fill = PatternFill(fill_type="solid", bgColor="F1E6DC", fgColor="F1E6DC")
        side = Side(border_style="thin", color=colors.BLACK)
        border = Border(left=side, right=side, top=side, bottom=side, outline=side)
        for key, value in dic.items():
            # 行高
            ws.row_dimensions[start_row].height = 30
            for i in ["A", "B", "D", "C", "E", "F"]:
                ws["{}{}".format(i, start_row)].font = font
                ws["{}{}".format(i, start_row)].fill = fill
                ws["{}{}".format(i, start_row)].border = border
                # 设置时间格式为文本
                if i == "D":
                    ws["{}{}".format(i, start_row)].number_format = numbers.FORMAT_TEXT

            ws["A{}".format(start_row)] = value["rom"]
            ws["B{}".format(start_row)] = key
            ws["D{}".format(start_row)] = value["duration"][0:-3]
            ws["E{}".format(start_row)] = value["crash"]
            ws["F{}".format(start_row)] = value["anr"]
            if value["crash"] + value["anr"]:
                result = "FAIL"
                comFont = Font(size=11, bold=True, name=u"宋体", color=colors.RED)
                ws["C{}".format(start_row)].font = comFont
            else:
                result = "PASS"
            ws["C{}".format(start_row)] = result
            start_row += 1
        # 详细页面
        ws = wb["Detail"]
        start_row = 3
        fill2 = PatternFill(fill_type="solid", bgColor="DEF1EB", fgColor="DEF1EB")
        alignment = Alignment(wrap_text=True)
        for key, value in dic.items():
            detail = value["detail"]
            for detail_key, detail_value in detail.items():
                ws.row_dimensions[start_row].height = 50
                for i in ["A", "B", "C"]:

                    ws["{}{}".format(i, start_row)].fill = fill2
                    ws["{}{}".format(i, start_row)].border = border
                    if i == "C":
                        ws["{}{}".format(i, start_row)].alignment = alignment
                    if i == "B":
                        ws["{}{}".format(i, start_row)].number_format = numbers.FORMAT_TEXT
                ws["A{}".format(start_row)] = key
                ws["B{}".format(start_row)] = detail_key
                ws["C{}".format(start_row)] = detail_value.strip()
                start_row += 1
        wb.save(filepath)
        logger.debug(u"测试结束")


if __name__ == "__main__":
    print(sys.path)
    r = Runner()
    r.run()
