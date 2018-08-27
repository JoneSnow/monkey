# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/8/22 19:18
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


class ParseLog(object):
    def __init__(self, path=None):
        self.path = os.path.join(ROOT, "logcat.txt") if path is None else path
        #解析匹配关键字
        self.crashInfo = [
            "FATAL EXCEPTION",
            "ANR"
        ]
        self.crash = 0
        self.anr = 0

    def parse(self):
        result = []
        crash_start_line = 0
        with open(self.path, "r") as f:
            for line, eachLine in enumerate(f):
                for i in self.crashInfo:
                    if i.upper() in eachLine.upper():
                        if i == u"FATAL EXCEPTION":
                            self.crash += 1
                        else:
                            self.anr += 1
                        crash_start_line = line
                        crash_time = eachLine[0:18].strip()
                        detail = eachLine.split("):")[-1]
                        result.append([crash_time, detail])
                    else:
                        if crash_start_line != 0 and 1 <= line - crash_start_line <= 2:
                            detail = eachLine.split("):")[-1]
                            if detail not in result[-1][-1]:
                                result[-1][-1] = result[-1][-1] + detail
        return dict(result)


if __name__ == "__main__":
    '''cmd script'''
    import argparse

    parser = argparse.ArgumentParser("parse log")
    parser.add_argument("--path", "-p", action="store", required=False, default="logcat.txt", help="excel path")

    args = parser.parse_args()
    result = ParseLog(args.path).parse()
    for key, value in result.items():
        print("+++++++++++++++++++++++++++++++++++")
        print(key)
        print
        print(value)
        print("+++++++++++++++++++++++++++++++++++")
