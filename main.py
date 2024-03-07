# the EPW Proj. 3/像素世界项目 第三版 main.py|主程序
# 反馈：QQ 3629751397、邮箱 WFLing_seaer@163.com
# © 2023-2024 水晴明、凌晚枫 All rights reserved.
from data import classes as cls
from PIL import Image
import keyboard as kbo

info = cls.info

win = cls.window((1920, 1080))
frm = cls.frame(win, Image.open("resources/pict/backboard.png"))
item0 = cls.item(
    Image.open("resources/pict/DEMO-001_sprt.png"),
    Image.open("resources/pict/DEMO-001_hbox.png"),
    "test1",
    lambda a, b: info("撞击", a.name, [(b.name) for b in b]),
    lambda a, b: info("重叠", a.name, [b.name for b in b]),
)
item1 = cls.item(
    Image.open("resources/pict/SLIDE-001_sprt.png"),
    Image.open("resources/pict/SLIDE-001_hbox.png"),
    "test2",
    lambda a, b: info("撞击", a.name, [(b.name) for b in b]),
    lambda a, b: info("重叠", a.name, [b.name for b in b]),
    mass=20,
    frict=2,
)
item3 = cls.item(
    Image.open("resources/pict/SLOT-001_sprt.png"),
    Image.open("resources/pict/SLOT-001_hbox.png"),
    "test3",
    mass=32,  # float("inf"),
    frict=float("inf"),
    extradata={"onlyhit": [item1]},
)
item1.position = (0, 250, 100, 0)
item3.position = (0, 100, 100, 0)
item0.position = (0, 220, 100, 0)
while True:
    v = 0j
    if kbo.is_pressed("w"):
        v = complex(v.real, -5)
    elif kbo.is_pressed("s"):
        v = complex(v.real, 5)
    if kbo.is_pressed("a"):
        v = complex(-5, v.imag)
    elif kbo.is_pressed("d"):
        v = complex(5, v.imag)
    elif kbo.is_pressed("esc"):
        del win
        break
    item0.velocity = v
    frm.update()
    win.render(item0.render())
    win.win.update()
