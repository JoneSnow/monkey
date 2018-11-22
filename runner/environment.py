# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/11/21 10:43
import os
import sys
import time

path = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath(__file__))))
sys.path.append(path)
from runner.tools import Tools


class Environment:
    @staticmethod
    def killAll():
        """
        清除所有残留进程
        """
        Tools.execute("wmic process where name=\"adb.exe\" delete")
        Tools.execute("wmic process where name=\"python.exe\" delete")
        time.sleep(5)

    # @staticmethod
    # def delete():
    #     if os.path.exists(RESULT):
    #         shutil.rmtree(RESULT)

if __name__ == "__main__":
    Environment.killAll()
