# -*- coding:utf-8 -*-
# Auther: guofengyang
# Date: 2018/7/17 16:24
import logging
import logging.handlers
import os

from runner import ROOT


def init_log():
    '''log配置初始化'''
    result = os.path.join(ROOT, "result")
    logpath = os.path.join(result, "framework.log")
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M',
                        filename=logpath,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    l = logging.getLogger('')
    l.addHandler(console)
