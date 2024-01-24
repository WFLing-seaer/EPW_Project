#the EPW Proj. 2/像素世界项目 第二版 main.py|主程序
#反馈：QQ 3629751397、邮箱 WFLing_seaer@163.com
#© 2023-2024 水晴明、凌晚枫 All rights reserved.
from data import config
from data import classes as cls

try:
    import os,sys,time,random,jieba,ik
    import tkinter as tk
    import logging as log
    import keyboard as kb
    import subprocess
    log=log.Logger(__name__)
except ImportError as ie:
    ie=str(ie)[17:-1]
    log.critical('E01:运行所需库“'+ie+'”缺失。')
    if input('可能为您自动安装缺失的库。输入"y"以进行安装。').lower()=='y':
        if subprocess.run(['cmd','/c','pip install '+ie]).returncode:
            log.error('E02:安装缺失的库“'+ie+'”失败。请稍后再试，或自行手动安装。')
        else:
            log.warning('成功安装库“'+ie+'”。请重启程序以应用更改。')
    exit(1)
ik.other.random
