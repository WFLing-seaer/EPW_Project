from __future__ import annotations
from typing import Any


class node:
    """定义图或树的节点。"""

    istree: bool
    related: dict[node, int]
    parent: node

    auto_convert = False
    exclusive = True

    def __init__(
        self,
        related: dict[node, int] | list[node] | node | None = None,
        parent: node | None = None,
        data: Any = None,
    ):
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
        elif isinstance(related, node):
            related = {related: 0}
        else:
            related = {}

        self.data = data

        if dfn == 0:  # 用习惯了switch之后……（恼）
            self.istree: bool = True  # T:树节点;F:图节点
            self.parent: None = None  # type: ignore
            self.related: dict[node, int] = {}
        elif dfn == 1:
            self.istree: bool = all([n.istree for n in related])
            self.parent: None = None  # type: ignore
            self.related: dict[node, int] = related
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
            self.parent: node = parent if self.istree else None  # type: ignore
            self.related: dict[node, int] = {} if self.istree else {parent: 0} if parent else {}
            self.parent.related.update({self: 0})  # type: ignore
        elif dfn == 3:
            self.istree: bool = all([n.istree for n in related]) and parent.istree  # type: ignore
            self.parent: node = parent if self.istree else None  # type: ignore
            self.related: dict[node, int] = related
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
                self.related.update({parent: 0} if parent else {})

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

    def __eq__(self, val):
        return self.data == val.data if self.exclusive else vars(self) == vars(val)

    def __hash__(self):
        return hash(self.data) if self.exclusive else hash(vars(self))

    def tograph(self):
        if self.istree and self.auto_convert:
            self.istree = False
            if self.parent:
                self.related.update({self.parent: 0})
            [n.tograph() for n in self.related]

    def parents(self):
        # 此节点的所有父节点以及祖节点。
        if not self.parent:
            return []
        result = [self.parent]
        result += self.parent.parents()
        return result
