# the EPW Proj. 3/像素世界项目 第三版 classes.py|类定义
# 反馈：QQ 3629751397、邮箱 WFLing_seaer@163.com
# © 2023-2024 水晴明、凌晚枫 All rights reserved.

# 导入
from __future__ import annotations
import math, time, cmath, os, copy, logging, threading as trd, pickle as _pickle, tkinter as tk, numpy as np

from . import config, node
from PIL import Image as _img, ImageTk as _itk
from typing import Any, Callable, Type

# 常量
V_WIN: str = "WINDOWS"
V_FRM: str = "FRAMES"
V_ITM: str = "ITEMS"

inf: float = float("inf")
nan: float = float("nan")

Imgtype = _img.Image


def _pass(*_):
    pass


# 全局变量
_vars: dict[str, Any] = {}


# 全局函数
def dump():
    with os.fdopen(os.open(config.DATA, 32768, 769), "wb") as db:
        _pickle.dump(_vars, db)


def load():
    with open(config.DATA, "rb") as db:
        global _vars
        _vars = _pickle.load(db)


def warning(*args):
    string = " ".join([str(c) for c in args])
    logging.warning(string)


# 类定义
class window:
    """定义tkinter主窗口。
    每个游戏进程可能不止一个window。
    （当然此处表述不严谨，原则上同设备不允许同时开俩游戏进程）"""

    # 挂载于此窗口的对象列表，其索引为ID。
    objs: list[Type[Any]] = []

    def __init__(self, size: tuple[int, int] | None = None):
        """size - 窗口大小，留空(None)表示全屏"""
        # 创建窗口。
        self.win: tk.Tk = tk.Tk()
        if size is None:
            self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.config(background="#000000")
        self.win.attributes("-transparentcolor", "#000000")
        if size is None:
            self.win.overrideredirect(True)
        # ID。
        self.ID = len(_vars.get(V_WIN, []))
        # 注册。（对于任何类，注册都是必须的。）
        _vars[V_WIN] = _vars.get(V_WIN, []) + [self]
        # 窗口的显示区。不想用Canvas（摆）
        self.size = size or (
            self.win.winfo_screenwidth(),
            self.win.winfo_screenheight(),
        )
        self.win.geometry(str(self.size[0]) + "x" + str(self.size[1]))
        self.win.wm_resizable(False, False)
        self.pic = _itk.PhotoImage(
            _img.new(
                "RGBA",
                self.size,
            )
        )
        self.pic_root = tk.Canvas(self.win, bg="black")
        self.pic_root.pack(fill="both", expand=True)
        self.win.update()

    def __del__(self):
        # 销毁窗口。
        for obj in self.objs:
            try:
                del obj
            except AttributeError:
                pass
        self.win.destroy()

    def append(self, cls):
        # 注册一个类实例为此窗口挂载的对象。（不同于上面__init__里那个注册）
        self.objs.append(cls)
        return len(self.objs) - 1

    def remove(self, cls):
        # 从挂载的对象中注销一个类实例。
        try:
            self.objs.remove(cls)
        except ValueError as e:
            raise ValueError("试图注销尚未注册的实例") from e

    def render(self, img: Imgtype):
        tkimg = _itk.PhotoImage(image=img)
        # 防垃圾收集
        self.pic = tkimg
        self.pic_root.create_image((0, 0), image=tkimg, anchor="nw")
        self.win.update()


class item:
    """item类表示的是物体。一切物体，除了背景以外的一切物体，都是item。"""

    class SizeNotFitError(ValueError):
        pass

    class FrameNotExistError(ValueError):
        pass

    def __init__(
        self,
        charlet: Imgtype,
        hitbox: Imgtype,
        name: str = "未命名的物体",
        onhit: Callable = _pass,
        oncover: Callable = _pass,
        extradata: dict | None = None,
        mass: float = 10,
        frict: float = 10,
        e: float = 1.0,
        hrZ: int = 0,
        hbz: int = 1,
        animation: str = "",
        tag: str = "item",
    ):
        """charlet - 贴图。
        hitbox - 碰撞框。（黑白）
        name - 物体名称。
        onhit - 物体与其他物体碰撞碰撞时的回调函数。
         -应当接受两个位置参数为(this:item,other:item)
        oncover - 物体与其他物体重叠时的回调函数。
         -应当接受两个位置参数为(this:item,other:list[item])
        extradata - 额外的数据。
        mass - 质量。
        frict - 摩擦因数。
        hrZ - 当其他物体与hrZ不为0的物体重叠时，其Z轴会被设为hrZ。
        hbz - 此物体的碰撞箱能碰撞到的Z层级数。
        animation - 动画文件(.ias)路径。
        tag - 物品类型，"item" "background"之一。
        注：重力加速度取值固定为1。
        其中：
        "onlyhit"   : list[item] - 指定此物品只会与特定物品碰撞。
        "donthit"   : list[item] - 指定此物品不会与特定物品碰撞。
        "oninteract": dict[str,Callable] - 物体进行交互时的回调函数字典。
         -键为交互项名称，值为交互时的回调函数。
         -每个函数应当接受一个位置参数为i:item。
        "onupdate"  : Callable   - 物体进行物理更新时的回调函数。
         -应当接受一个位置参数为i:item。
        同时定义onlyhit和donthit时，这两个列表同时生效，
        此时碰撞对象为在onlyhit且不在donthit内的物品。
        另外，新的item在创建之后默认挂载到frame 0的(8,8)位。
        如果未创建任何frame，则会抛出FrameNotExist异常。"""

        self.size = charlet.size

        if hitbox.size != self.size:
            raise self.SizeNotFitError("碰撞箱必须与贴图等大")

        self.hitbox: np.ndarray = np.array(hitbox.convert("L")) != np.full(self.size, 255)
        self.charlet = charlet.convert("RGBA")
        self.name = name
        self.extradata = extradata
        self.onhit = onhit
        self.oncover = oncover
        self.mass = mass
        self.frict = frict
        self.e_phy = e  # 这命名足够直观了吧……恢复系数！hhh（加个phy是为了防止混淆）
        self.hrZ = hrZ
        self.hbz = hbz
        # 第一个是帧号，然后俩是XY坐标（Z轴是假的，要用frame.Z_map转换为xy偏移量）
        self.position: tuple[int, float, float, int] = (0, 8.0, 8.0, 0)
        self.velocity = 0 + 0j  # 实部为速率，虚部为方向（弧度，范围[0,2pi)）
        self.tag = tag
        self.original_velocity: dict[item, complex] = {}
        self.original_position: dict[item, tuple] = {}
        self.hit_node = node.node(data=self)

        if animation:
            with open(animation, "r") as file:
                cmd = file.readlines()
        else:
            cmd = []

        def anim():
            while True:
                for a in cmd or ["_pass()"]:
                    yield a

        self.anim = anim()

        # ID。
        self.ID = len(_vars.get(V_ITM, []))
        # 注册。
        _vars[V_ITM] = _vars.get(V_ITM, []) + [self]
        try:
            self.Frame: frame = _vars[V_FRM][0]
            self.RID = self.Frame.append(self)
        except IndexError as _e:
            raise self.FrameNotExistError("尚未创建任何frame") from _e
        if min(self.Frame.size) < 9 + max(self.size):
            raise self.SizeNotFitError("帧尺寸过小，无法初始化物体")
        extradata = extradata or {
            "onlyhit": self.Frame.objs,
            "donthit": [],
            "oninteract": _pass,
            "onupdate": _pass,
        }
        self.onlyhit: list[item]
        self.donthit: list[item]
        self.oninteract: Callable
        self.onupdate: Callable
        self.onlyhit, self.donthit, self.oninteract, self.onupdate = (
            extradata.get("onlyhit", self.Frame.objs),
            extradata.get("donthit", []),
            extradata.get("oninteract", _pass),
            extradata.get("onupdate", _pass),
        )

    @staticmethod
    def to_r_theta(z: complex):
        return complex(abs(z), cmath.phase(z))

    @staticmethod
    def to_x_y(z: complex):
        return complex(z.real * cmath.cos(z.imag), z.real * cmath.sin(z.imag))

    @staticmethod
    def inrange(value: float, _min: float, _max: float):
        return max(min(value, _max), _min)

    @staticmethod
    def lsub(lst1: list, lst2: list):
        return [i for i in lst1 if i not in lst2]

    @staticmethod
    def land(lst1: list, lst2: list):
        return [i for i in lst1 if i in lst2]

    def undo(self, select=None):
        self.velocity = self.original_velocity.get(self, self.velocity)
        self.position = self.original_position.get(self, self.position)
        [k.undo() for k in self.original_position if not select or k in select]

    def collide_update(
        self, exclude: None | list = None, hit_chain: None | node.node = None, request: bool = False
    ) -> tuple[float, float] | bool:
        # 这个函数其实就是把以前的update中有关于碰撞的东西单拎出来了。
        # 现在update只负责更新摩擦力之类的东西。令行禁止，无需磨叽。
        # 至于能不能动、动多少的问题，交给这个函数来干。
        # 返回值：实际能动的偏移量，直角坐标表示法。
        # 如果request为真，则返回“能不能动”（主要是为了节省资源hhh）

        if not (self.velocity.real or request):
            return 0, 0

        exclude = exclude or []

        hit_chain = (
            hit_chain or self.hit_node
        )  # hit_chain其实是一个node，其父节点及祖节点表示碰撞来源，子节点表示碰撞进行的方向

        hp = hit_chain.parents()
        if self.hit_node in hp:
            # 此节点已经参与过碰撞
            self.hit_node = hp[hp.index(self.hit_node)]

        # 定义collide。返回值为字典，{item:[(int,int)]}，键为发生碰撞的物体，值为碰撞点坐标
        # 检查日志详见:checklog.md - collide
        def collide(pos=None, _exclude: list[item] | None = None) -> dict[item, list[tuple[int, int]]]:
            # pos是“假定当前物体在pos”的意思

            if not _exclude:
                _exclude = []

            def expand(obj: item, pos: tuple[float, float] | None = None):
                # 把物体的碰撞箱扩展到帧的大小方便进行碰撞
                exp_array = np.full(self.Frame.size, False, bool)
                xx = pos[0] if pos else obj.position[1]
                yy = pos[1] if pos else obj.position[2]
                exp_array[
                    int(xx) : int(xx) + obj.hitbox.shape[0],
                    int(yy) : int(yy) + obj.hitbox.shape[1],
                ] = obj.hitbox
                return exp_array

            self_exp = expand(self, pos)
            now_covering: list[item] = []

            result = {}

            for obj in self.Frame.objs:
                conds = [
                    obj is not self,
                    obj not in exclude,
                    obj not in self.donthit,
                    obj in self.onlyhit,
                    obj not in _exclude,
                    obj not in now_covering,
                ]
                if all(conds):
                    ands = np.argwhere(expand(obj) & self_exp).tolist()
                    ands = [tuple(pos) for pos in ands]
                    if len(ands) >= 2:
                        result[obj] = ands

            return result

        def theta(points):
            # 返回拟合直线的斜角。范围：[0,pi)
            points = np.array(points, int)
            if np.all(points[:, 0] == points[0, 0]):
                angle = math.pi / 2
            else:
                slope, _ = np.polyfit(points[:, 0], points[:, 1], 1)
                angle = math.tan(abs(slope))
                if slope < 0:
                    angle = math.pi - angle
            return angle

        target_length = self.velocity.real  # 计划在一次更新内内移动的距离

        moved = 0  # 已经移动的距离

        now_moving_to = self.position[1:3]

        def move_rt(pos: tuple, v: complex):
            v_xy = item.to_x_y(v)
            return (pos[0] + v_xy.real, pos[1] + v_xy.imag)

        v_per_cycle = complex(1, self.velocity.imag)

        dont_collide = [o.data for o in [hit_chain.parent] + list(hit_chain.related.keys()) if o]

        moveable = True  # 初始化

        while True:
            # 循环，直到下列二者之一：
            # 1. 到达目标位置
            # 2. 无法继续前进
            will_collide = collide(move_rt(now_moving_to, v_per_cycle), dont_collide)

            print("wc", self.name, [w.name for w in will_collide], file=open("W:\\log.log", "w"))

            moveable = not will_collide or all([obj.collide_update(request=True) for obj in will_collide])

            if moved >= target_length:
                # 直接返回速度的直角坐标表示
                v_x_y = item.to_x_y(self.velocity)
                return v_x_y.real, v_x_y.imag
            if not moveable:
                break

            moved += 1  # 每次直线移动1，这样就能确保xy两轴上的分量都<=1。

            if request:
                continue

            for obj in will_collide:
                # 上面的if已经确保了所有的obj都推得动

                # 接下来进行一大坨的碰撞计算……（悲）
                # 最佳拟合直线：
                col_angle = theta(will_collide[obj])
                # 计算两物体在法线上的速度分量。t是碰撞面的倾斜角，把它加上pi/2再对pi取余就是法线的倾斜角。
                norm_angle = (col_angle + math.pi / 2) % (math.pi)
                # 计算碰撞的时候用整体速率而不用逐帧速率。
                v10_on_norm = self.velocity.real * math.cos(self.velocity.imag - norm_angle)
                # v10是此物体初速度分量，v20是obj初速度分量。
                v20_on_norm = obj.velocity.real * math.cos(obj.velocity.imag - norm_angle)
                # 碰撞。
                v1_on_norm = v10_on_norm - obj.mass * (1 + self.e_phy) * (v10_on_norm - v20_on_norm) / (self.mass + obj.mass)
                v2_on_norm = v20_on_norm - self.mass * (1 + obj.e_phy) * (v10_on_norm - v20_on_norm) / (self.mass + obj.mass)
                # 计算碰撞后角度。
                angle_10 = self.velocity.imag
                angle_20 = obj.velocity.imag
                angle_1 = 2 * col_angle - angle_10 + 2 * math.pi
                angle_2 = 2 * col_angle - angle_20 + 2 * math.pi
                # 将法线速度还原为沿运动方向的速度。
                v1_on_direction = v1_on_norm * math.cos(angle_1 - norm_angle)
                v2_on_direction = v2_on_norm * math.cos(angle_2 - norm_angle)
                # 最后一步，合成最终的速度。
                self.velocity = complex(v1_on_direction, angle_1)
                obj.velocity = complex(v2_on_direction, angle_2)
                # 碰撞完成，剩下的活obj负责。
                obj.collide_update(hit_chain=hit_chain)
        if request:
            return moveable
        m_x_y = item.to_x_y(complex(moved, self.velocity.imag))
        return m_x_y.real, m_x_y.imag

    def update(self):
        pos_on_start = copy.deepcopy(self.position)
        # 切帧。
        # 检查日志详见:checklog.md - update
        if self.Frame.ID != self.position[0]:
            self.Frame.remove(self)
            try:
                self.Frame: frame = _vars[V_FRM][self.position[0]]
            except IndexError as e:
                raise self.FrameNotExistError("当前positon没有对应的frame") from e
            self.RID = self.Frame.append(self)

        # 碰撞计算。
        # 原碰撞计算已移交try_update函数处理。
        warning(self.velocity)
        dx, dy = self.collide_update()  # type: ignore
        warning(dx, dy)
        self.position = (self.position[0], self.position[1] + dx, self.position[2] + dy, self.position[3])
        # 摩擦力的计算。
        # 检查日志详见:checklog.md - update
        velocity, direction = self.velocity.real, self.velocity.imag
        velocity = max(velocity - self.frict / max(self.mass, 1), 0)
        self.velocity = complex(velocity, direction)
        exec(next(self.anim), {"target": self, "_pass": _pass})
        return self.position != pos_on_start

    def render(self):
        x, y = self.position[1:3]
        rootsize = self.Frame.win.size
        rootsize0 = rootsize
        framesize = self.Frame.size
        scale = 1
        if framesize[0] < rootsize[0] or framesize[1] < rootsize[1]:
            scale = max(rootsize[0] / framesize[0], rootsize[1] / framesize[1])
            rootsize = (int(rootsize[0]) / scale, int(rootsize[1] / scale))
        minx, miny, maxx, maxy = (
            x - rootsize[0] / 2,
            y - rootsize[1] / 2,
            x + rootsize[0] / 2,
            y + rootsize[1] / 2,
        )
        if x <= rootsize[0]:
            minx = 0
            maxx = rootsize[0]
        if y <= rootsize[1]:
            miny = 0
            maxy = rootsize[1]
        if framesize[0] - x <= rootsize[0]:
            minx = framesize[0] - rootsize[0]
            maxx = framesize[0]
        if framesize[1] - y <= rootsize[1]:
            miny = framesize[1] - rootsize[1]
            maxy = framesize[1]
        minx, miny, maxx, maxy = int(minx), int(miny), int(maxx), int(maxy)

        ret = self.Frame.render().crop((minx, miny, maxx, maxy)).resize(rootsize0)
        return ret


class frame:
    """每个frame是一个区域，游戏内所有活动都在区域内进行。
    frame之间不能直接跨越。同时，渲染时也只会渲染本frame。"""

    # 挂载于此frame的对象列表，其索引为ID。
    objs: list[item] = []

    def __init__(self, root: window, texture: Imgtype, Z_map: Callable | None = None):
        """root - window实例，frame所在窗口。
        texture - 帧背景。"""
        # 创建frame。
        self.frame: tk.Frame = tk.Frame()
        # ID。
        self.ID = len(_vars.get(V_FRM, []))
        # 注册。
        _vars[V_FRM] = _vars.get(V_FRM, []) + [self]
        self.RID = root.append(self)
        self.win = root
        self.root = root.win
        self.texture = texture.convert("RGBA")
        self.size = texture.size
        self.Z_map = Z_map or (lambda z: (-z, -2 * z))

    def append(self, cls):
        # 注册一个类实例为此帧挂载的对象。
        self.objs.append(cls)
        return len(self.objs) - 1

    def remove(self, cls):
        # 从挂载的对象中注销一个类实例。
        try:
            self.objs.remove(cls)
        except ValueError as e:
            raise ValueError("试图注销尚未注册的实例") from e

    def update(self):
        for obj in self.objs:
            obj.update()

    def render(self):
        render_base = self.texture.convert("RGBA").copy()
        for obj in self.objs:
            render_base.paste(
                obj.charlet,
                (
                    int(self.Z_map(obj.position[3])[0] + obj.position[1]),
                    int(self.Z_map(obj.position[3])[1] + obj.position[2]),
                ),
                mask=obj.charlet,
            )
        return render_base
