# python3
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24
# @Author  : lhc
# @Email   : 2743218818@qq.com
# @File    : 综合.py
# @Software: PyCharm
import json
import logging
import random
import urllib
import time
import hashlib
import requests
import nonebot
from nonebot.rule import Rule
from nonebot import on_command, on_startswith, on_keyword, on_fullmatch, on_message
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER, GROUP_MEMBER
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.params import ArgPlainText, CommandArg, ArgStr
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, \
    MessageSegment, Message, GroupMessageEvent, Event, escape


def dbqchecker():
    async def _checker(bot: Bot, event: Event, state: T_State) -> bool:
        s = str(event.get_event_description())
        if 'type=sticker' in s or 'subType=1' in s or 'subType=2' in s:  # 在这个位置写入你的判断代码
            return True  # 记住，返回值一定要是个bool类型的值！
        return False

    return Rule(_checker)


dbq = on_message(rule=dbqchecker())


@dbq.handle()
async def _dbq(event: Event):
    s = str(event.get_event_description())
    if 'subType=1' in s:
        await dbq.send('这是表情包')
    elif 'subType=2' in s:
        await dbq.send('这是特殊表情')
    else:
        await dbq.send('这是大表情')


wettr = on_command('q')


@wettr.handle()
async def _handle(matcher: Matcher, city: Message = CommandArg()):
    if city.extract_plain_text() and city.extract_plain_text()[0] != '_':
        matcher.set_arg('city', city)


@wettr.got('city', prompt='你想夸赞谁呢？')
async def _(city: str = ArgPlainText('city')):
    if city in ['lhc', '你', 'LHC']:
        await wettr.send(f'{city}太菜了')
    else:
        await wettr.send(f'{city}tql!')


w = on_fullmatch('七七')


@w.handle()
async def _handle():
    await w.send('我在')


w = on_command('reply', block=True)


@w.handle()
async def _handle(bot: Bot, event: MessageEvent):
    a = f'{str(event.reply.sender.user_id)}:"{event.reply.message}"'
    await w.send(str(a))


w = on_keyword({'今日人品', '今日运势'}, priority=5)


@w.handle()
async def _handle(bot: Bot, event: MessageEvent):
    qq = event.get_user_id()
    t1 = time.time() // 10000
    replay = int(hashlib.md5((str(qq) + str(t1)).encode()).hexdigest(), 16) % 42 + 61
    msg = '你今天的人品值为：' + str(replay)
    await w.send(msg, at_sender=True)


w = on_keyword({'原神'}, priority=5)
lt = 0


@w.handle()
async def _handle(bot: Bot, event: MessageEvent):
    global lt
    t = time.time()
    try:
        if t - lt > 10:
            await w.send(random.choices(['启动！', '原神？'], [0.8, 0.2])[0])
        else:
            await w.send(random.choices(['已经启动了，请耐心等待', '启动启动，就知道启动！'], [0.2, 0.8])[0])
    except:
        pass
    finally:
        lt = t


pp = on_command('匹配', priority=5)


@pp.handle()
async def handle_first_receive(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["city"] = arg.extract_plain_text().strip()


@pp.got("city", prompt="你要测试和谁的匹配程度呢？")
async def handle_city(bot: Bot, event: MessageEvent, city: str = ArgStr("city")):
    user = event.get_user_id()
    if str(user) in ['3174143625', 'none']:
        return
    replay = int(hashlib.md5((str(user) + str(city)).encode()).hexdigest(), 16) % 135 - 5
    l = ['七七', '77', '强']
    for i in l:
        if i in city:
            replay = int((replay + 100) / 1.9)
            break
    msg = '嗨呀，你和' + str(city) + '的相匹配程度竟然是' + str(replay) + '%呀！'
    await pp.finish(message=msg, at_sender=True)


abstract = on_command("wa", priority=5, block=True)


@abstract.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["abstract"] = arg.extract_plain_text().strip()


@abstract.got("abstract", prompt="你想查询什么数学问题？")
async def _(bot: Bot, event: Event, target_text: str = ArgStr("abstract")):
    await abstract.send(f"https://mnihyc.com/test/wolframalpha/query.php?q={urllib.parse.quote(target_text)}&mag=1",
                        at_sender=True)


matcher = on_command("whoami")


@matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    str = f"{event.get_event_name().replace('.', '_')}" + ':' + event.get_user_id() + '|'
    if await GROUP_ADMIN(bot, event):
        await matcher.send(str + "管理员")
    elif await GROUP_OWNER(bot, event):
        await matcher.send(str + "群主")
    elif await GROUP_MEMBER(bot, event):
        await matcher.send(str + "群员")
    else:
        await matcher.send(str + "私聊")

    # str=event.get_log_string()+event.get_event_description()+event.get_user_id()
    # await matcher.send(str)


abstract = on_command("raw", priority=5, block=True)


@abstract.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["abstract"] = arg.extract_plain_text().strip()


@abstract.got("abstract", prompt="你想显示什么消息的源码？")
async def _(bot: Bot, event: Event, target_text: str = ArgStr("abstract")):
    # target_text += str(event.get_event_description())
    # if ',type=sticker' in str(event.get_message()):
    #     await abstract.send('大表情')
    await abstract.send(target_text, at_sender=True)


w = on_command('reply', block=True)


@w.handle()
async def _handle(bot: Bot, event: MessageEvent):
    a = f'{str(event.reply.sender.user_id)}:"{event.reply.message}"'
    await w.send(a)


abstract = on_command("tts", priority=5, block=True)


@abstract.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["abstract"] = arg.extract_plain_text().strip()


@abstract.got("abstract", prompt="你想让我说什么？")
async def _(bot: Bot, event: Event, text: str = ArgStr("abstract")):
    msg = f"[CQ:tts,text={text}]"
    await abstract.send(Message(msg))


picture = on_command('pic')


@picture.handle()
async def handle_receive(bot: Bot, state: T_State):
    pic = await get_picture()
    await picture.send(MessageSegment.image(pic))


async def get_picture():
    url = 'https://api.vvhan.com/api/bing?type=json&rand=sj'
    res = requests.get(url)
    result = json.loads(res.text)
    img = result['data']['url']
    title = result['data']['title']
    date = result['data']['date']
    print(date, title)
    image = f"[CQ:image,file={img}]"
    return img

# 获取列表
matcher = on_command("friendlist")


@matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    s = await bot.get_friend_list()
    await matcher.send(str(s))

matcher = on_command("groupinfo")


@matcher.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    s = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    await matcher.send(str(s))


# 多参数输入实例
abstract = on_command("test", priority=5, block=True)


@abstract.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["a1"] = arg.extract_plain_text().strip()


@abstract.got("abstract", prompt="a1=？")
async def _(bot: Bot, event: Event, a1: str = ArgStr("a1")):
    await abstract.send(a1, at_sender=True)


@abstract.got("a2", prompt="a2=？")
async def _(bot: Bot, event: Event, a2: str = ArgStr("a2")):
    await abstract.send(a2, at_sender=True)


@abstract.got("a3", prompt="a3=？")
async def _(bot: Bot, event: Event, a3: str = ArgStr("a3")):
    await abstract.finish(a3, at_sender=True)
