# the EPW Proj. 3/像素世界项目 第三版 classes.py|类定义
# 反馈：QQ 3629751397、邮箱 WFLing_seaer@163.com
# © 2023-2024 水晴明、凌晚枫 All rights reserved.

# 导入
import math, cmath, os, copy, logging, pickle as _pickle, tkinter as tk, numpy as np

from . import config
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
        _vars = _pickle.load(db)


def warning(*args):
    logging.warning(" ".join([str(c) for c in args]))


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
        self.pic_root = tk.Label(self.win, bg="black")
        self.pic_root.pack(fill="both", expand=1)
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
        self.pic_root.config(image=tkimg)


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
        self.hrZ = hrZ
        self.hbz = hbz
        # 第一个是帧号，然后俩是XY坐标（Z轴是假的，要用frame.Z_map转换为xy偏移量）
        self.position: tuple[int, float, float, int] = (0, 8.0, 8.0, 0)
        self.velocity = 0 + 0j  # 实部为x向右的速度，虚部为y向下的速度
        self.tag = tag
        self.hitclock = False
        self.original_velocity: dict[item, complex] = {}
        self.original_position: dict[item, tuple] = {}

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
        except IndexError as e:
            raise self.FrameNotExistError("尚未创建任何frame") from e
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

    def update(self, _from=None):
        self.hitclock = not _from

        # 定义collide。（其实它返回的不是碰撞而是重叠hhh）
        # 检查日志详见:checklog.md - collide
        def collide(extra_dontcol: list[item] | None = None):
            if not extra_dontcol:
                extra_dontcol = []

            def expand(obj: item):
                exp_array = np.full(self.Frame.size, False, bool)
                exp_array[
                    int(obj.position[1]) : int(obj.position[1]) + obj.hitbox.shape[0],
                    int(obj.position[2]) : int(obj.position[2]) + obj.hitbox.shape[1],
                ] = obj.hitbox
                return exp_array

            self_exp = expand(self)
            check_col_obj: list[item] = []
            now_covering: list[item] = []
            for obj in self.Frame.objs:
                conds = [
                    obj is not self,
                    obj is not _from,
                    obj not in self.donthit,
                    obj in self.onlyhit,
                    obj not in extra_dontcol,
                    obj not in now_covering,
                    obj.hitclock is False,
                ]
                if all(conds):
                    check_col_obj.append(obj)
            return [obj for obj in check_col_obj if (obj is not self) and (expand(obj) & self_exp).any()]

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
        # 检查日志详见:checklog.md - update
        if self.frict == inf or not self.velocity:
            self.velocity = 0j
            return False  # 摩擦力无穷大直接动不了（思考）或者是干脆就没动。

        self.velocity = complex(
            0 if self.velocity.real is nan else self.velocity.real, 0 if self.velocity.imag is nan else self.velocity.imag
        )

        def move(pos, dx, dy):
            ret = (pos[0], pos[1] + dx, pos[2] + dy, pos[3])
            return ret

        def try_move(dx, dy) -> list[item]:
            if not (dx or dy):
                return []
            pos = copy.deepcopy(self.position)
            max_axis_v = max(abs(dx), abs(dy), 1)
            # dx_o、dy_o是速度等比缩放为单轴为1的结果
            dx_o, dy_o = dx / max_axis_v, dy / max_axis_v  # 不怕ZeroDivErr是因为上面直接把可能出0的情况排掉了。
            # 确保对于较大的v不会出现帧间高速穿墙情况
            # while_t是循环次数，为等比缩放比例向下取整的结果。
            while_t = int(max_axis_v)
            ret: list[item] = []
            for _ in range(while_t):
                self.position = move(self.position, dx_o, dy_o)
                ret += collide()
            self.position = move(self.position, dx - dx_o * while_t, dy - dy_o * while_t)
            ret += collide()
            # 还原位置
            self.position = pos
            # 输出时去重
            return list(set(ret))

        def sgn(x):
            return 0 if x == 0 else 1 if x > 0 else -1

        pos_on_start = copy.deepcopy(self.position)

        now_covering = collide()

        direction = (sgn(self.velocity.real), sgn(self.velocity.imag))

        x_col = try_move(self.velocity.real, 0)  # x方向碰撞的物体列表
        col_obj_x = [obj for obj in x_col if (obj.mass != inf) and (obj.frict != inf)]
        y_col = try_move(0, self.velocity.imag)  # y方向碰撞的物体列表
        col_obj_y = [obj for obj in y_col if (obj.mass != inf) and (obj.frict != inf)]
        moveable = (self.velocity.real and col_obj_x == x_col, self.velocity.imag and col_obj_y == y_col)
        col_obj = list(set(col_obj_x + col_obj_y))
        if not col_obj:
            # 没有碰撞
            self.position = move(
                self.position,
                self.velocity.real,
                self.velocity.imag,
            )
            return True
        trying_dv = (0, 0)  # 初始化一下
        if moveable.count(False) == 1:  # 一个轴不能动。moveable的值：0.0没想动，True能动，False动不了。
            x_cant_move = moveable[0] is False  # True是x不能动，False是y不能动。
            stuck_axis_v = self.velocity.real if x_cant_move else self.velocity.imag  # 动不了的轴的速度
            another_axis_v = self.velocity.imag if x_cant_move else self.velocity.real  # 能动的轴的速度
            ssav = sgn(stuck_axis_v)  # Sign of Stuck Axis Velocity(SSAV)
            saav = sgn(another_axis_v)
            fsaav = (_from and sgn(_from.velocity.imag if x_cant_move else _from.velocity.real)) or 0
            trying_move: list[int] = []  # 尝试对角移动的象限。是个列表，因为可能不止一个象限要尝试。
            if x_cant_move:
                if ssav == 1:
                    # 可以尝试的象限有一、四象限。
                    if saav == 1 or fsaav == 1:
                        # or fssav是因为，如果碰撞源有速度分量，那么此时的象限选择也应该有倾向。
                        # 而不是像else里那样两边都试。
                        trying_move.append(1)
                        # 第一象限在渲染时是右下角，而非平面直角坐标系中的右上角。因为对于坐标系统来说向下才是x轴正方向。
                        # （虽然说第一象限的xy取值仍然是x>0 y>0……）
                    elif saav == -1 or fsaav == -1:
                        trying_move.append(4)
                    else:
                        trying_move.extend([4, 1])  # 左上、右上（三四象限）优先。
                else:
                    # 可以尝试的象限有二、三象限。
                    if saav == 1:
                        trying_move.append(2)
                    elif saav == -1:
                        trying_move.append(3)
                    else:
                        trying_move.extend([3, 2])
            else:
                # 是y轴动不了。
                if ssav == 1:
                    # 可以尝试的象限有一、二象限。
                    if saav == 1 or fsaav == 1:
                        trying_move.append(1)
                    elif saav == -1 or fsaav == -1:
                        trying_move.append(2)
                    else:
                        trying_move.extend([1, 2])
                else:
                    # 可以尝试的象限有三、四象限。
                    if saav == 1:
                        trying_move.append(4)
                    elif saav == -1:
                        trying_move.append(3)
                    else:
                        trying_move.extend([4, 3])
            # 经过上面的一堆if，总算是搞出来应该尝试的方向了。对吧……（思考）（放弃思考）
            # 然后，对于可能的方向，直接try_move就行。
            for trying_direction in trying_move:
                trying_dv = ((1, 1), (-1, 1), (-1, -1), (1, -1))[trying_direction - 1]
                try_result = try_move(*trying_dv)
                if [obj for obj in try_result if (obj.mass != inf) and (obj.frict != inf)] == try_result:
                    # 找到一个能动的方向
                    moveable = (True, True)  # 俩true是因为此处尝试的是对角移动。
                    x_col += try_result
                    col_obj_x += try_result
                    y_col += try_result
                    col_obj_y += try_result
                    col_obj = list(set(col_obj + try_result))
                    break
                    # trying_dv会“剩”到外面（因为for循环结束后不会销毁变量，所以循环外的变量就是最后一次循环时的值）

        if any(moveable):  # 能动
            self.position = move(
                self.position,
                self.velocity.real * moveable[0] + trying_dv[0],
                self.velocity.imag * moveable[1] + trying_dv[1],
            )
            for obj in col_obj:
                side_cant = (
                    obj in col_obj_x
                    and not moveable[0]
                    or obj in col_obj_y
                    and not moveable[1]
                    and not (obj in col_obj_x and obj in col_obj_y)
                )
                if side_cant:
                    continue
                # 退，退，退（不是）
                ovs_0, svs_0 = copy.deepcopy(obj.velocity), copy.deepcopy(self.velocity)
                self.original_velocity.update({obj: ovs_0})
                self.original_position.update({obj: obj.position})
                obj.velocity, self.velocity = (
                    2 * self.mass * self.velocity - self.mass * obj.velocity + obj.mass * obj.velocity
                ) / (self.mass + obj.mass), (
                    self.mass * self.velocity - self.mass * obj.velocity + 2 * obj.mass * obj.velocity
                ) / (
                    self.mass + obj.mass
                )
                # 后知后觉（有的物体是单轴碰撞，但上面计算的是双轴碰撞，所以此处该撤回一轴的撤回）
                obj.velocity = complex(
                    (ovs_0.real if not moveable[0] or obj not in col_obj_x else obj.velocity.real),
                    (ovs_0.imag if not moveable[1] or obj not in col_obj_y else obj.velocity.imag),
                )
                self.velocity = complex(
                    (svs_0.real if not moveable[0] or obj not in col_obj_x else self.velocity.real),
                    (svs_0.imag if not moveable[1] or obj not in col_obj_y else self.velocity.imag),
                )
                if not obj.update(self):
                    # 寄了，有个搞不动的
                    self.undo(col_obj_x if obj in col_obj_x else [] + col_obj_y if obj in col_obj_y else [])
                    moveable = (
                        False if obj in col_obj_x else moveable[0],
                        False if obj in col_obj_y else moveable[1],
                    )
        else:
            self.velocity = 0j
            return False

        # 摩擦力的计算。
        # 检查日志详见:checklog.md - update
        velocity = item.to_r_theta(self.velocity)
        velocity, direction = velocity.real, velocity.imag
        velocity = max(velocity - self.frict / max(self.mass, 1), 0)
        self.velocity = item.to_x_y(complex(velocity, direction))
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
        return self.Frame.render().crop((minx, miny, maxx, maxy)).resize(rootsize0)


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
        for obj in self.objs:
            obj.hitclock = False
        return render_base
