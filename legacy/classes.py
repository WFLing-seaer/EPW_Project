import os

if not os.getcwd().endswith("EPW_Project2"):
    os.chdir("..")

import pickle as _pickle
from . import config as _config
from PIL import Image as _img
from PIL import ImageTk as _itk
from PIL import PngImagePlugin as _png
from PIL import BmpImagePlugin as _bmp
from PIL import GifImagePlugin as _gif
from PIL import JpegImagePlugin as _jpg
from typing import Any, Callable
from threading import Thread

import tkinter as tk
import math
import cmath
import time

_pngtype = _png.PngImageFile
_bmptype = _bmp.BmpImageFile
_giftype = _gif.GifImageFile
_jpgtype = _jpg.JpegImageFile

_imgtype = _img.Image  # _pngtype | _bmptype | _giftype | _jpgtype


def allload():
    with open(_config.DATA, "rb") as db:
        storeddata: dict = _pickle.load(db)
        globals().update(storeddata)


_vars = {}
V_Win = "windows"
V_FRM = "frames"
V_ITM = "items"

inf = float("inf")
nan = float("nan")


dummyImg: _imgtype = _img.open("resources/pict/unknown.png")  # type: ignore

AntiGC = {}


class window:
    """定义tk主窗口。
    每个游戏进程应该有两个window，
    其中一个用以挂载frames，
    另一个用来实现各种奇奇怪怪的效果。
    （但按理来说不会同时存在两个游戏进程就是了……）"""

    def __init__(self):
        self.win: tk.Tk = tk.Tk()
        self.ID = len(_vars.get(V_Win, []))
        _vars[V_Win] = _vars.get(V_Win, []) + [self]


class frame:
    """每帧图片的基础。
    定义了最基础的大小、序号，等等。"""

    basezoom: float = 1.00

    def __init__(self, x, y, win: window, texture: _imgtype = dummyImg, basezoom: float = 1.0) -> None:
        """初始化一个基底图片。
        参数：
        -x,y     左下角坐标。（右上角坐标根据texture大小自动计算）
        -win     窗口。
        -texture 背景图片。"""
        self.x0, self.y0 = x, y
        self.x1, self.y1 = x + texture.width, y + texture.height
        self.root = win.win
        self.tkframe = tk.Frame(win.win, width=texture.width * basezoom, height=texture.height * basezoom)
        self.tkframe.place(x=0, y=0)
        timg = _itk.PhotoImage(texture.resize((int(texture.width * basezoom), int(texture.height * basezoom))))
        sl = tk.Label(self.tkframe, image=timg)
        self.timg = timg
        sl.place(x=0, y=0)
        self.root.update()
        self.sl = sl
        self.texture = texture.convert("RGBA")
        self.ID = len(_vars.get(V_FRM, []))
        _vars[V_FRM] = _vars.get(V_FRM, []) + [self]
        self.hereItems = []
        self.basezoom = basezoom

    def render(self, rxl, ryl, rate=None):
        # rxl、ryl是渲染时的偏移量，也即屏幕左上角相对帧的坐标。
        # rate是缩放比例。
        if rate is None:
            rate = self.basezoom
        self.tkframe.place(x=0, y=0)
        plate = _img.new("RGBA", self.texture.size)
        plate.paste(self.texture, (0, 0))
        for it in reversed(self.hereItems):
            plate.paste(it.charlet, (int(it.x - self.x0), int(it.y - self.y0)))
        pImg = _itk.PhotoImage(plate.resize((int(plate.width * rate), int(plate.height * rate)), resample=5))
        AntiGC["AGC92"] = pImg  # 存起来防垃圾收集，用AGC92做键是因为写这里的时候这行是92行
        self.sl.config(image=pImg)
        self.sl.place(x=-rxl, y=-ryl)


class item:
    hitbox: Any  # 边缘图->碰撞箱
    ignorehit: list[type] = None  # type: ignore # 忽略与XX的碰撞。类或者实例；与onlyhit冲突
    onlyhit: list[type] = None  # type: ignore # 只能与XX碰撞。类或者实例；与ignorehit冲突
    x, y = 0, 0
    t0: float = 0.0
    currentframe: frame = None  # type: ignore # 当前所在帧

    def __init__(
        self,
        charlet: _imgtype,
        hitbox: _imgtype,
        hitset: list | tuple | None,
        canbepushed: bool = False,
        mass: float = inf,
        onhit: Callable | None = None,
        oncover: Callable | None = None,
    ) -> None:
        # hitset:list->ignorehit,tuple->onlyhit（我真是个小天才）
        # 一切坐标以左下角为准
        # hitbox是一张黑白图，大小和charlet一样，表示的是碰撞箱。
        # （边缘图纯靠手画，懒得写程序里hhh）
        self.canbepushed = canbepushed
        self.hitbox = hitbox.convert("RGB")
        self.charlet = charlet  #'''.convert('RGBA')'''
        if hitset and not set(hitset).issubset(set(_vars[V_ITM])):
            raise ValueError("hitset不应包含未注册的item")
        if isinstance(hitset, list):
            self.ignorehit = hitset
        elif isinstance(hitset, tuple):
            self.onlyhit = list(hitset)
        self.velocity: complex = 0 + 0j
        self.accleration: complex = 0 + 0j
        self.mass = mass
        self.onhit = onhit
        self.oncover = oncover
        self.update_frame()
        self.ID = len(_vars.get(V_ITM, []))
        _vars[V_ITM] = _vars.get(V_ITM, []) + [self]
        self.hbcolor = [c for c in set(self.hitbox.getdata()) if c < (255, 255, 255)]
        # HitBoxCOLOR，碰撞箱颜色列表。（因为可能会有多碰撞箱）

    @staticmethod
    def to_r_theta(z: complex):
        return complex(abs(z), math.atan2(z.imag, z.real))

    @staticmethod
    def to_x_y(z: complex):
        return complex(z.real * cmath.cos(z.imag), z.real * cmath.sin(z.imag))

    def update_frame(self):
        for aframe in _vars[V_FRM]:
            if aframe.x0 <= self.x <= aframe.x1 and aframe.y0 <= self.y <= aframe.y1:
                self.currentframe = aframe
                aframe.hereItems.append(self)
                break  # 我就不信到时候程序跑起来会有两帧是重叠的，恼。
                # （但还是习惯性break一下）

    def reset_phsc(self):
        self.t0 = time.time()
        self.velocity = 0 + 0j
        self.accleration = 0 + 0j

    def update_phsc(self):
        t1 = time.time()
        self.velocity += self.accleration * (t1 - self.t0)
        self.t0 = t1

    def tp(self, x, y):
        self.x, self.y = x, y
        self.update_frame()

    def collidingItem(
        self,
        testingPx: tuple | None = None,
        collidedPx: list | None = None,
        ignoreItems: list | None = None,
    ) -> list[type]:
        # 返回所有和当前item碰撞的item。
        hmx, hmy = self.hitbox.size  # 相对坐标
        # collidedPx是已经计算完碰撞了的像素颜色。
        # 虽然hitbox理应是黑白图，但是不同的颜色或灰度依然可以用来标识多碰撞箱。
        # 多碰撞箱可以应用于——比如，滑槽——的场景下。
        # testingPx是正在检验的像素颜色。
        colItems = []
        ignoreItems = ignoreItems or []
        for hx in range(hmx):
            for hy in range(hmy):
                pxpos = (hx, hy)  # 相对坐标
                if collidedPx and self.hitbox.getpixel(pxpos) in collidedPx:
                    continue
                if testingPx:
                    if self.hitbox.getpixel(pxpos) != testingPx:
                        continue
                if self.hitbox.getpixel(pxpos) == (255, 255, 255):
                    continue
                canhit: list = self.onlyhit or _vars[V_ITM]
                canhit = list(set(canhit or []) - set(ignoreItems or []) - set(self.ignorehit or []) - {self})
                for aitem in canhit:
                    if aitem.ignorehit and self in aitem.ignorehit:
                        continue
                    if aitem.onlyhit and self not in aitem.onlyhit:
                        continue
                    rahx = self.x + hx - aitem.x
                    # rahx:相对a的x，就是最外面俩for遍历到的碰撞点相对于aitem的坐标
                    rahy = self.y + hy - aitem.y
                    if not (0 <= rahx <= aitem.hitbox.width and 0 <= rahy <= aitem.hitbox.height):
                        continue
                    try:
                        if aitem.hitbox.getpixel((rahx, rahy)) == (255, 255, 255):
                            colItems.append(aitem)
                    except IndexError:
                        pass
        return list(set(colItems))

    def move_vct(self, vector: complex, forced=False):
        dx, dy = vector.real, vector.imag
        x, y = self.x, self.y
        ret = 0  # 返回值
        # 函数返回值:0执行成功 1因为被阻挡只能向x方向移动 2因为被阻挡只能向y方向移动
        # 3因为被阻挡不能移动 4因为出帧而不能移动 5强制移动
        if not (
            self.currentframe.x0 <= x + dx <= self.currentframe.x1 and self.currentframe.y0 <= y + dy <= self.currentframe.y1
        ):
            return 4  # 确保不会出帧。出帧的唯一方法是tp。（所以整个函数里没有update_frame。）
        if not forced:
            nowcolliding = []
            for hitcolor in self.hbcolor:
                while True:
                    colliding = self.collidingItem(hitcolor, ignoreItems=nowcolliding)
                    if colliding:
                        nowcolliding.extend(colliding)
                    else:
                        break
                self.x += dx  # 假设移动了
                col_x = self.collidingItem(hitcolor, ignoreItems=nowcolliding)
                if col_x:
                    for col_itm in col_x:
                        if col_itm.canbepushed:
                            col_itm.accleration = 1j * vector.imag
                    ret += 1
                self.x -= dx  # 恢复假设前的位置
                self.y += dy
                col_y = self.collidingItem(hitcolor, ignoreItems=nowcolliding)
                if col_y:
                    ret += 2
                self.y -= dy
                # ret返回3说明因为被阻挡而彻底不能移动，
                # 返回1或2表示因为被阻挡而只能向其中一个方向移动。
            if ret % 2 == 0:
                self.x += dx
            if ret // 2 == 0:
                self.y += dy
            # 根据ret的结果移动，不在上面直接移动了是因为上面一段套在for里了，
            # 在上面移动的话会移动过头
            return ret
        else:
            self.x += dx
            self.y += dy
            return 5

    def render(self):
        rfrmpos = (self.x - self.currentframe.x0, self.y - self.currentframe.y0)
        # 相对于帧的坐标,related-to-frame-position
        cfrmpos = (
            self.currentframe.tkframe.winfo_x(),
            self.currentframe.tkframe.winfo_y(),
        )
        # 帧坐标,current-frame-...（懒的写（摆
        rwinpos = (cfrmpos[0] + rfrmpos[0], cfrmpos[1] + rfrmpos[1])  # 相对于窗口的坐标
        winx, winy = self.currentframe.root.size()
        frmx, frmy = self.currentframe.tkframe.size()
        nx, ny = cfrmpos
        if winx // 4 > rwinpos[0] and nx < 0:
            nx, ny = (cfrmpos[0] + rwinpos[0] - winx // 4, cfrmpos[1])
        elif winx * 3 // 4 < rwinpos[0] and nx > winx - frmx:
            nx, ny = (cfrmpos[0] + rwinpos[0] - winx * 3 // 4, cfrmpos[1])
        if winy // 4 > rwinpos[1] and ny > 0:
            nx, ny = (cfrmpos[0], cfrmpos[1] + rwinpos[1] - winy // 4)
        elif winy * 3 // 4 < rwinpos[1] and ny > winy - frmy:
            nx, ny = (cfrmpos[0], cfrmpos[1] + rwinpos[1] - winy * 3 // 4)
        # 上面这八行，一坨代码，都是保证玩家位置在中央50%的……hhh
        self.currentframe.render(-nx, -ny, 1)
