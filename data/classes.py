import pickle as _pickle
from . import config as _config
from PIL import Image as _img
from PIL import ImageTk as _itk
from PIL import PngImagePlugin as _png
from PIL import BmpImagePlugin as _bmp
from PIL import GifImagePlugin as _gif
from PIL import JpegImagePlugin as _jpg

import tkinter as tk
import math

_pngtype = _png.PngImageFile
_bmptype = _bmp.BmpImageFile
_giftype = _gif.GifImageFile
_jpgtype = _jpg.JpegImageFile

_imgtype = _pngtype | _bmptype | _giftype | _jpgtype

def allload():
    with open(_config.DATA,'rb') as db:
        storeddata:dict=_pickle.load(db)
        globals().update(storeddata)

VARS = {}
Vwin='windows'
Vfrm='frames'
Vitm='items'

dummyImg:_imgtype=_img.open('../pict/unknown.png') # type: ignore

class window:
    '''定义tk主窗口。每个游戏进程应该有两个window，其中一个用以挂载frames，另一个用来实现各种奇奇怪怪的效果。（但按理来说不会同时存在两个游戏进程就是了……）'''
    def __init__(self):
        self.win:tk.Tk = tk.Tk()
        self.ID = len(VARS.get(Vwin,[]))
        VARS[Vwin] = VARS.get(Vwin,[])+[self]
class frame:
    '''每帧图片的基础。
    定义了最基础的大小、序号，等等。'''
    def __init__(self,x,y,win:window=VARS[Vwin][0],texture:_imgtype=dummyImg) -> None:
        '''初始化一个基底图片。
        参数：
        -x,y     左下角坐标。（右上角坐标根据texture大小自动计算）
        -win     窗口。
        -texture 背景图片。'''
        self.x0,self.y0 = x,y
        self.x1,self.y1 = x+texture.width,y+texture.height
        self.root = win.win
        self.tkframe = tk.Frame(win.win,width=texture.width,height=texture.height)
        self.tkframe.place(x=0,y=0)
        tk.Label(self.tkframe,image=texture).place(x=0,y=0)#type:ignore
        self.texture = texture
        self.ID=len(VARS.get(Vfrm,[]))
        VARS[Vfrm] = VARS.get(Vfrm,[])+[self]
        self.hereItems=[]
    def render(self,rxl,ryl,rate):
        #rxl、ryl是渲染时的偏移量，也即屏幕左上角相对帧的坐标。rate是缩放比例。
        self.tkframe.place(x=0,y=0)
        plate = self.texture
        for it in self.hereItems:
            plate.paste(it.charlet,(it.x-self.x0,it.y-self.y0))
        pImg=_itk.PhotoImage(plate.resize((int(plate.width*rate),int(plate.height*rate)),resample=5))
        self.tkframe.config(image=pImg)#type:ignore
        self.tkframe.place(x=-rxl,y=-ryl)
class node:
    '''定义图或树的节点。'''
    istree:bool
    related:dict
    def __init__(self,
                 related:dict|list|type|None=None,
                 parent:type|None=None,
                 data=None) -> None:
        '''定义图或树的节点。
        related  : {node:weight} 或 list[node]（等价于{node1:0,node2:0,...}） 或  node（等价于{node:0}）
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
        -各边的权值由映射决定。如related不是映射，则权值默认为0。  '''
        dfn = (parent is not None)*2+(related is not None)#dfn=define 0:None None;1:None 东西;2:东西 None;3:东西 东西

        if isinstance(related,dict):pass
        elif isinstance(related,list):related=dict(zip(related,[0]*len(related)))
        else:related={related:0}

        self.data = data

        if   dfn==0:#用习惯了switch之后……（恼）
            self.istree  :bool = True#T:树节点;F:图节点
            self.parent  :None = None # type: ignore
            self.related :dict = {}
        elif dfn==1:
            self.istree  :bool = all([n.istree for n in related])
            self.parent  :None = None # type: ignore
            self.related :dict = related
            if self.istree:
                if any([n.parent for n in related]):
                    self.istree=False
                    for rel,weight in related.items():
                            rel.tograph()
                            rel.related.update({self:weight})
                else:
                    for rel in related:
                            rel.parent=self
        elif dfn==2:
            self.istree  :bool = parent.istree # type: ignore
            self.parent  :type = parent if self.istree else None # type: ignore
            self.related :dict = {} if self.istree else {parent:0}
            self.parent.related.update({self:0}) # type: ignore
        elif dfn==3:
            self.istree  :bool = all([n.istree for n in related]) and parent.istree # type: ignore
            self.parent  :type = parent if self.istree else None # type: ignore
            self.related :dict = related
            if self.parent:self.parent.related.update({self:0}) # type: ignore
            if self.istree:
                if any([n.parent for n in related]):
                    parent.tograph() # type: ignore
                    for rel,weight in related.items():
                            rel.tograph()
                            rel.related.update({self:weight})
                else:
                    for rel in related:
                            rel.parent=self
            else:
                 self.related.update({parent:0})
    def __iter__(self):
        if self.istree:
            if self.related:
                subs=[self]
                for n in self.related:
                    subs += list(n)
                return iter(subs)
            else:
                return iter([self])
        else:
            return iter([])
    def __bool__(self):
        return bool(self.data)
    def __add__(self,val):
        n=node(dict(list(self.related.items())+[(val,0)]),self.parent,self.data)
        if self.istree:
            if val.parent:
                self.tograph()
                val.tograph()
                val.related.update({n:0})
            else:
                val.parent=n
        else:
            val.related.update({n:0})
        return n
    def __radd__(self,val):
        return val.__add__(self)
    @staticmethod
    def show_graph(nodes):
        win=tk.Tk('图:'+__name__)
        canvas=tk.Canvas(win)
        canvas.config(width=1024,height=1024)
        canvas.pack()
        lnodes=len(nodes)
        dnode={}
        for i,n in enumerate(nodes):
            x,y=math.sin(2*math.pi*i/lnodes),math.cos(2*math.pi*i/lnodes)
            canvas.create_oval(512+x*64*lnodes**0.5-128/lnodes,512+y*64*lnodes**0.5-128/lnodes,512+x*64*lnodes**0.5+128/lnodes,512+y*64*lnodes**0.5+128/lnodes)
            canvas.create_text(512+x*64*lnodes**0.5,512+y*64*lnodes**0.5,font='"星汉等宽 CN normal" '+str(int(128/lnodes)),text=str(n.data))
            dnode[n]=(512+x*64*lnodes**0.5,512+y*64*lnodes**0.5)
        for n in nodes:
            dn=dnode[n]
            for rn,weight in n.related.items():
                try:
                    x00,y00,x01,y01,r=dnode[n]+dnode[rn]+(128/lnodes,)
                    θ=math.atan2(y01-y00,x01-x00)
                    dx,dy=r*math.cos(θ),r*math.sin(θ)
                    x10,y10,x11,y11=x00+dx,y00+dy,x01-dx,y01-dy
                    canvas.create_line(x10,y10,x11,y11)
                    canvas.create_text((dn[0]+dnode[rn][0])/2,(dn[1]+dnode[rn][1])/2,font='"星汉等宽 CN normal" 16',text=str(weight))
                except KeyError:
                    pass
        canvas.focus_set()
    def tograph(self):
        if self.istree:
            self.istree = False
            if self.parent:
                self.related.update({self.parent:0})
            [n.tograph() for n in self.related]
class item:
    hitbox:_imgtype #边缘图->碰撞箱
    ignorehit:list[type] = None# type: ignore #忽略与XX的碰撞。类或者实例；与onlyhit冲突
    onlyhit:list[type] = None# type: ignore #只能与XX碰撞。类或者实例；与ignorehit冲突
    x,y=0,0
    currentframe:frame = None# type: ignore #当前所在帧
    def __init__(self,charlet:_imgtype,hitbox:_imgtype,hitset:list|tuple,canbepushed:bool=False) -> None:
        #hitset:list->ignorehit,tuple->onlyhit（我真是个小天才）
        #一切坐标以左下角为准
        #hitbox是一张黑白图，大小和charlet一样，表示的是碰撞箱。（边缘图纯靠手画，懒得写程序里hhh）
        self.canbepushed = canbepushed
        self.hitbox = hitbox
        self.charlet = charlet
        if hitset and not set(hitset).issubset(set(VARS[Vitm])):raise ValueError('hitset无论何种情况下都不应包含未注册的item')
        if isinstance(hitset,list):
            self.ignorehit = hitset
        elif isinstance(hitset,tuple):
            self.onlyhit = list(hitset)
        self.velocity = 0
        self.update_frame()
        self.ID=len(VARS.get(Vitm,[]))
        VARS[Vitm] = VARS.get(Vitm,[])+[self]
        self.hbcolor = [c for c in set(hitbox.getdata()) if c<(255,255,255)]#HitBoxCOLOR，碰撞箱颜色列表。（因为可能会有多碰撞箱）
    def update_frame(self):
        for aframe in VARS[Vfrm]:
            if aframe.x0 <= self.x <= aframe.x1 and aframe.y0 <= self.y <= aframe.y1:
                self.currentframe = aframe
                aframe.hereItems.append(self)
                break#我就不信到时候程序跑起来会有两帧是重叠的，恼。（但还是习惯性break一下）
    def tp(self,x,y):
        self.x,self.y=x,y
        self.update_frame()
    def collidingItem(self,testingPx:tuple|None=None,collidedPx:list|None=None,ignoreItems:list|None=None):
        #返回所有和当前item碰撞的item。
        hmx,hmy = self.hitbox.size#相对坐标
        #collidedPx是已经计算完碰撞了的像素颜色。虽然hitbox理应是黑白图，但是不同的颜色或灰度依然可以用来标识多碰撞箱。多碰撞箱可以应用于——比如，滑槽——的场景下。
        #testingPx是正在检验的像素颜色。
        colItems=[]
        ignoreItems = ignoreItems or []
        for hx in range(hmx):
            for hy in range(hmy):
                pxpos=(hx,hy)#相对坐标
                if collidedPx and self.hitbox.getpixel(pxpos) in collidedPx:continue
                if testingPx:
                    if self.hitbox.getpixel(pxpos) != testingPx:continue
                else:
                    if self.hitbox.getpixel(pxpos) < (255,255,255):continue
                canhit:list=self.onlyhit or VARS[Vitm]
                canhit=list(set(canhit)-set(ignoreItems)-set(self.ignorehit)-{self})
                for aitem in canhit:
                    if aitem.ignorehit and self in aitem.ignorehit:continue
                    if aitem.onlyhit and self not in aitem.onlyhit:continue
                    rahx = self.x+hx-aitem.x#rahx:相对a的x，就是最外面俩for遍历到的碰撞点相对于aitem的坐标
                    rahy = self.y+hy-aitem.y
                    if not (0<=rahx<=aitem.hitbox.width and 0<=rahy<=aitem.hitbox.height):continue
                    if aitem.hitbox.getpixel((rahx,rahy)) == (255,255,255):colItems.append(aitem)
        return colItems
    def move_vct(self,vector:complex,forced=False):
        dx,dy=vector.real,vector.imag
        x,y=self.x,self.y
        ret=0#返回值
        #函数返回值:0执行成功 1因为被阻挡只能向x方向移动 2因为被阻挡只能向y方向移动 3因为被阻挡不能移动 4因为出帧而不能移动 5强制移动
        if not (self.currentframe.x0<=x+dx<=self.currentframe.x1 and self.currentframe.y0<=y+dy<=self.currentframe.y1):
            return 4#确保不会出帧。出帧的唯一方法是tp。（所以整个函数里没有update_frame。）
        if not forced:
            nowcolliding = []
            for hitcolor in self.hbcolor:
                while True:
                    colliding = self.collidingItem(hitcolor,ignoreItems=nowcolliding)
                    if colliding:nowcolliding.extend(colliding)
                    else:break
                self.x += dx#假设移动了
                if self.collidingItem(hitcolor,ignoreItems=nowcolliding):
                    ret+=1
                self.x -= dx#恢复假设前的位置
                self.y += dy
                if self.collidingItem(hitcolor,ignoreItems=nowcolliding):
                    ret+=2
                self.y -= dy
                #ret返回3说明因为被阻挡而彻底不能移动，返回1或2表示因为被阻挡而只能向其中一个方向移动。
            if ret%2==0:self.x += dx
            if ret//2==0:self.y += dy#根据ret的结果移动，不在上面直接移动了是因为上面一段套在for里了，在上面移动的话会移动过头
            return ret
        else:
            self.x += dx
            self.y += dy
            return 5
    def render(self):
        rfrmpos=(self.x-self.currentframe.x0,self.y-self.currentframe.y0)#相对于帧的坐标,related-to-frame-position
        cfrmpos=self.currentframe.tkframe.winfo_x(),self.currentframe.tkframe.winfo_y()#帧坐标,current-frame-...（懒的写（摆
        rwinpos=(cfrmpos[0]+rfrmpos[0],cfrmpos[1]+rfrmpos[1])#相对于窗口的坐标
        winx,winy = self.currentframe.root.size()
        frmx,frmy=self.currentframe.tkframe.size()
        nx,ny=cfrmpos
        if winx//4 > rwinpos[0] and nx<0:
            nx,ny=(cfrmpos[0]+rwinpos[0]-winx//4,cfrmpos[1])
        elif winx*3//4 < rwinpos[0] and nx>winx-frmx:
            nx,ny=(cfrmpos[0]+rwinpos[0]-winx*3//4,cfrmpos[1])
        if winy//4 > rwinpos[1] and ny>0:
            nx,ny=(cfrmpos[0],cfrmpos[1]+rwinpos[1]-winy//4)
        elif winy*3//4 < rwinpos[1] and ny>winy-frmy:
            nx,ny=(cfrmpos[0],cfrmpos[1]+rwinpos[1]-winy*3//4)
        #上面这八行，一坨代码，都是保证玩家位置在中央50%的……hhh
        self.currentframe.render(-nx,-ny,1)
