# python3
# -*- coding: utf-8 -*-
# @Time    : 2023/11/25
# @Author  : lhc
# @Email   : 2743218818@qq.com
# @File    : eval.py
# @Software: PyCharm

import urllib, requests, psutil, builtins
from urllib import parse
from nonebot.rule import to_me
from math import *
import sympy
from sympy import integrate as sh, diff as d, limit as lim, series as se, summation as s, product as p, solve as es, \
    dsolve as ds, symbols, Function, I, oo
import time, threading, nonebot, inspect
import random
import re
import pickle
from nonebot.permission import SUPERUSER
from nonebot import on_command, on_startswith, on_keyword, on_fullmatch
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment, escape
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER


def help():
    help = [
        """
    基本指令：
        1.加(+)减(-)乘(*)除(/)乘方(**)取余(%)整除(//)e(6.02e23)括号(())
        2.当然也包括六种比较运算(==,!=,<,>,<=,>=)
        3.还有六种位运算(&:与,|:或,^:异或,~:非(相反数减一),<<:左移,>>:右移)
        """,
        """
    高级指令：
        常用函数：
        fact(x) 分解质因数+因式分解 lcm(x,y) 最小公倍数 gcd(x,y) 最大公约数
        exp(x)  e的x次幂(e**x)
        factorial(x) x的阶乘
        log(x) 自然对数 log10(x) 常用对数 log(x,y) 对数
        sqrt(x) 平方根
        三角函数：
        sin(x) cos(x) tan(x)
        asin(x) acos(x) atan(x) atan2(y,x)
        sinh(x) cosh(x) tanh(x)
        asinh(x) acosh(x) atanh(x)
        辅助指令：
        科学常数：e,pi,I(虚数单位）,oo(正无穷大)
        ceil(x) floor(x) 向上,下取整
        fabs(x) x的绝对值
    """,
        """
    高等指令：
    ! 当表达式中使用到前面这些函数时，需要用单引号括起来。
    ! 可用数学变量：x,y,z,m,n.函数变量：f,g,h(用于微分方程求解)
        求和：
            s((1/2)**n,(n,0,oo)):对表达式中n从零到正无穷求和
            s(n,(n,0,m),(m,1,100)):对n从零到m求和,其中m又分别从1到100.
        求积：
            p((1/2)**n,(n,0,2)):对表达式中n从零到2求和
            p(n,(n,1,m),(m,1,100)):对n从1到m求积,其中m又分别从1到100.
        积分：
            不定积分：
                sh('log(x)'):对表达式log(x)不定积分
            定积分：
                sh(x**2,(x,0,1)):对x**2中的x在0到1积分
                无穷区间反常积分:
                sh(x**-2, (x, -oo, -1)):对表达式x**-2中的x从负无穷到-1积分
                无界函数反常积分:
                sh('log(x)', (x, 0, 1))
        导数/微分：
            d('log(x)/x') d(1) d(x) d('tan(x)'):对表达式微分
            d(x**5,x,5):对表达式求5阶导
        求极限：
            lim((1+1/n)**n,n,oo):求1加n分之一和的n次方在n趋于正无穷时的极限    
            lim('sin(x)/x', x, 0):求x趋于0时表达式的极限(注意英文单引号)
        求泰勒级数：
            se('sin(x)'):求表达式的5阶(默认)麦克劳林公式
            se('tan(x)',x,-1,4):求表达式在x=-1带皮亚诺余项的3阶泰勒公式(也就是求到O((x-1)**4))
            !最后O((x + 1)**4, (x, -1))表示(x-1)**4的同阶无穷小,在x趋近于1时
        解普通方程：(Equation Solve)
        ! 几乎输入任何正常的方程都能解
            es(x*9-6)：解关于x方程“x*9-6=0”
            线性方程(组):
            es([3*y+5*y-19,4*x-3*y-6])：解关于[x,y]的方程“3*y+5*y-19=0&&4*x-3*y-6=0”
            es([x+y+z-2,2*x-y+z+1,x+2*y+2*z-3],[x,y,z]):解关于[x,y,z]的方程
            当r<n时：
            es([x+y+z-2,2*x-y+z+1],[x,y,z]):无穷多解以后面的变量表示前面的
            es([x+y+z-2,x+y+z-3,x-2],[x,y,z]):r<r(增广),无解
            高次方程：
            es(x**4+4):解关于x方程“x**4+4=0”，几次方程有几个根
            多元多次方程:
            es([y**2-1,4*x-3*y-6])：表示为元组的列表
        解微分方程：(Differential equation Solve)
            ds(f(x).diff(x,4)-2*f(x).diff(x,3)+5*f(x).diff(x,2)):解f''''-2f'''+5f''=0
            ds(f(x).diff(x)-x):解f‘(x)-x=0
        注意乘方在python是**，括号引号必须英文"""]
    return '\n'.join(help)


def fact(num):
    if 'x' in str(num):
        return sympy.factor(str(num))
    list = []
    i = 2
    while i <= sqrt(num):
        if num % i == 0:
            list.append(str(i))
            num /= i
            continue  # 优化
        i += 1
        # 优化
        if i > sqrt(num):
            break
    if num > 1:
        list.append(str(int(num)))
    return '*'.join(list)


class MyThread(threading.Thread):
    def __init__(self, target, args=()):
        """
        why: 因为threading类没有返回值,因此在此处重新定义MyThread类,使线程拥有返回值
        """
        super(MyThread, self).__init__()
        self.func = target
        self.args = args

    def run(self):
        # 接受返回值
        self.result = self.func(*self.args)

    def get_result(self):
        # 线程不结束,返回值为None
        try:
            return self.result
        except Exception:
            return None


# 为了限制真实请求时间或函数执行时间的装饰器
def limit_decor(limit_time):
    """
    :param limit_time: 设置最大允许执行时长,单位:秒
    :return: 未超时返回被装饰函数返回值,超时则返回 None
    """

    def functions(func):
        # 执行操作
        def run(*params: object) -> object:
            thre_func = MyThread(target=func, args=params)
            # 主线程结束(超出时长),则线程方法结束
            thre_func.daemon = True
            thre_func.start()
            # 计算分段沉睡次数
            sleep_num = int(limit_time // 1)
            sleep_nums = round(limit_time % 1, 1)
            # 多次短暂沉睡并尝试获取返回值
            for i in range(sleep_num):
                time.sleep(1)
                infor = thre_func.get_result()
                if infor:
                    return infor
            time.sleep(sleep_nums)
            # 最终返回值(不论线程是否已结束)
            if thre_func.get_result():
                return thre_func.get_result()
            else:
                return "计算超时，自己算去吧"  # 超时返回  可以自定义

        return run

    return functions


@limit_decor(3)
def supereval(string):
    # with open(r'data\leveldb\var.var', 'rb') as f:
    # names = pickle.load(f)

    # if string in names.keys():
    # return str(names[string])
    # if re.search(r'\*\*.{4,}', string):
    #     return '命令过长'
    # 下面适用于不知道代码的
    pattern = re.compile('\*\*\s*([0-9a-fA-Fx*]*)')
    result = pattern.findall(string)
    for i in result:
        if len(i) > 6:
            return '命令过长'
    try:
        forbiddenlist = [':', 'wr', 'exe', 'sys', 'op', 'cmd', '__']
        for i in forbiddenlist:
            if i in string:
                return '非计算命令'  # (ACCESS_DENIED)
        if str(string).isdigit():
            return fact(int(string))
        result = str(eval(str(string)))
        if len(result) > 2400:
            return f'超出2400截断({len(result)}){result[:2400]}'
        else:
            return result
    except Exception as e:
        return f'语法错误:{e}'
        # try:
        #     return supereval(str(string) + ')')
        # except:
        #     try:
        #         return supereval(str(string) + '))')
        #     except:
        #         return f'语法错误:{e}'


if __name__ == '__main__':
    print(supereval('1 - 1'))

last_user = 0
wettr = on_command("e", priority=5)

x, y, z, m, n = symbols('x y z m n')
f = Function('f')
g = Function('g')
h = Function('h')


@wettr.handle()
async def _handle(matcher: Matcher, event: MessageEvent, city: Message = CommandArg()):
    userid = event.get_user_id()
    if userid in [2849721306] or '0000000' in userid:
        return
    if city.extract_plain_text():
        matcher.set_arg('city', city)


@wettr.got('city', prompt='你想执行什么算式？')
async def _(event: MessageEvent, city: str = ArgPlainText('city')):
    global last_user
    userid = event.get_user_id()
    if "'" in city or "/e" in city:
        await wettr.send('->' + str(supereval(city)))

    elif userid != last_user:
        last_user = userid
        await wettr.send(str(supereval(city)), at_sender=True)
    else:
        await wettr.send(str(supereval(city)))
