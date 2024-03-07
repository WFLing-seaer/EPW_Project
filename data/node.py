import math, cmath, tkinter as tk


class node:
    """定义图或树的节点。"""

    istree: bool
    related: dict

    def __init__(
        self,
        related: dict | list | type | None = None,
        parent: type | None = None,
        data=None,
    ) -> None:
        """定义图或树的节点。
        related  : {node:weight}或list[node]（等价于{n1:0,n2:0,...}或node（等价于{n:0}）
        parent   : node

        注，下文叙述时，将related视作一个节点时，指的是其中的每一个节点。

        如果只定义了parent：
        -此节点为叶子节点，当且仅当parent为树节点。
        -否则，为图节点。
        如果只定义了related：
        -此节点为树节点，当且仅当related皆为根节点。
        -否则，为图节点。
        -如有需要，related所在树将被修改为图。
        同时定义related和parent时：
        -如parent为树节点、related皆为根节点：
        *节点也为树节点，其为parent的一个子树的根节点，其子树以related为根节点。
        -否则：
        *将parent所在树修改为图（如需要）。
        *将related所在树修改为图（如需要）。
        *此节点为连接parent与related的图节点。
        *parent侧的权值将被设为0。
        *parent与related将被合并。
        如果related与parent都未定义：
        -此节点为树的根节点。

        当此节点是树节点时：
        -以此节点为根结点的树是parent（如有）的子树。
        当此节点是图节点时：
        -各边的权值由映射决定。如related不是映射，则权值默认为0。"""
        dfn = (parent is not None) * 2 + (related is not None)
        # dfn=define 0:None None;1:None 东西;2:东西 None;3:东西 东西

        if isinstance(related, dict):
            pass
        elif isinstance(related, list):
            related = dict(zip(related, [0] * len(related)))
        else:
            related = {related: 0}

        self.data = data

        if dfn == 0:  # 用习惯了switch之后……（恼）
            self.istree: bool = True  # T:树节点;F:图节点
            self.parent: None = None  # type: ignore
            self.related: dict = {}
        elif dfn == 1:
            self.istree: bool = all([n.istree for n in related])
            self.parent: None = None  # type: ignore
            self.related: dict = related
            if self.istree:
                if any([n.parent for n in related]):
                    self.istree = False
                    for rel, weight in related.items():
                        rel.tograph()
                        rel.related.update({self: weight})
                else:
                    for rel in related:
                        rel.parent = self
        elif dfn == 2:
            self.istree: bool = parent.istree  # type: ignore
            self.parent: type = parent if self.istree else None  # type: ignore
            self.related: dict = {} if self.istree else {parent: 0}
            self.parent.related.update({self: 0})  # type: ignore
        elif dfn == 3:
            self.istree: bool = all([n.istree for n in related]) and parent.istree  # type: ignore
            self.parent: type = parent if self.istree else None  # type: ignore
            self.related: dict = related
            if self.parent:
                self.parent.related.update({self: 0})  # type: ignore
            if self.istree:
                if any([n.parent for n in related]):
                    parent.tograph()  # type: ignore
                    for rel, weight in related.items():
                        rel.tograph()
                        rel.related.update({self: weight})
                else:
                    for rel in related:
                        rel.parent = self
            else:
                self.related.update({parent: 0})

    def __iter__(self):
        if self.istree:
            if self.related:
                subs = [self]
                for n in self.related:
                    subs += list(n)
                return iter(subs)
            else:
                return iter([self])
        else:
            return iter([])

    def __bool__(self):
        return bool(self.data)

    def __add__(self, val):
        n = node(dict(list(self.related.items()) + [(val, 0)]), self.parent, self.data)
        if self.istree:
            if val.parent:
                self.tograph()
                val.tograph()
                val.related.update({n: 0})
            else:
                val.parent = n
        else:
            val.related.update({n: 0})
        return n

    def __radd__(self, val):
        return val.__add__(self)

    @staticmethod
    def show_graph(nodes):
        win = tk.Tk("图:" + __name__)
        canvas = tk.Canvas(win)
        canvas.config(width=1024, height=1024)
        canvas.pack()
        lnodes = len(nodes)
        dnode = {}
        for i, n in enumerate(nodes):
            x, y = cmath.sin(2 * math.pi * i / lnodes), cmath.cos(2 * math.pi * i / lnodes)
            canvas.create_oval(
                512 + x * 64 * lnodes**0.5 - 128 / lnodes,
                512 + y * 64 * lnodes**0.5 - 128 / lnodes,
                512 + x * 64 * lnodes**0.5 + 128 / lnodes,
                512 + y * 64 * lnodes**0.5 + 128 / lnodes,
            )
            canvas.create_text(
                512 + x * 64 * lnodes**0.5,
                512 + y * 64 * lnodes**0.5,
                font='"星汉等宽 CN normal" ' + str(int(128 / lnodes)),
                text=str(n.data),
            )
            dnode[n] = (512 + x * 64 * lnodes**0.5, 512 + y * 64 * lnodes**0.5)
        for n in nodes:
            dn = dnode[n]
            for rn, weight in n.related.items():
                try:
                    x00, y00, x01, y01, r = dnode[n] + dnode[rn] + (128 / lnodes,)
                    θ = math.atan2(y01 - y00, x01 - x00)
                    dx, dy = r * cmath.cos(θ), r * cmath.sin(θ)
                    x10, y10, x11, y11 = x00 + dx, y00 + dy, x01 - dx, y01 - dy
                    canvas.create_line(x10, y10, x11, y11)
                    canvas.create_text(
                        (dn[0] + dnode[rn][0]) / 2,
                        (dn[1] + dnode[rn][1]) / 2,
                        font='"星汉等宽 CN normal" 16',
                        text=str(weight),
                    )
                except KeyError:
                    pass
        canvas.focus_set()

    def tograph(self):
        if self.istree:
            self.istree = False
            if self.parent:
                self.related.update({self.parent: 0})
            [n.tograph() for n in self.related]
