'''
the EPW Proj./像素世界项目
反馈：QQ 3629751397、邮箱 WFLing_seaer@163.com
水晴明、凌晚枫 © 2023 All rights reserved.
'''
#---------------------------------------
'''
使用说明:
本程序使用API进行调用。
直接运行主程序不会产生任何结果。

API列表：
...

所需库：
config.py
mipmap.py
pickle
typing*
PIL
os

*非必须
'''
#---------------------------------------
#导入所需库
from copy import deepcopy
from math import ceil, floor
import pickle
from random import choice, randint, shuffle
from typing import Any
from PIL import Image
from matplotlib.backend_bases import RendererBase
from config import execution_path,Dumpfile,TDumpfile

'''改变执行位置。'''
import os
execution_path and os.chdir(execution_path);

'''初始化类。'''
class Storage:
    '''所有可存储类的基类。'''
    def flatten(self,cls) -> str:
        res = "{"
        for val in dir(cls):                                                #遍历类内的所有函数/变量/...
            if val[0]==val[1]==val[-2]==val[-1]=='_':continue               #初步筛除私有变量/函数
            xval = getattr(cls,val)                                         #
            sval = str(type(xval))                                          #获取xval的类型
            if sval in ("<class 'function'>","<class 'method'>"):continue   #不保存函数

            res += repr(val) + ':'                                          #写字典键

            def iscontainer(e) -> bool:                                     #是否为容器
                try:
                    assert isinstance(e,str)
                    return False                                      
                except (TypeError,AssertionError):return bool(getattr(e,'__iter__',False))           

            def run(lst,func) -> Any:                                       #对嵌套列表等容器内的每一项执行函数
                print('run run on',lst)
                DCT,TPL=isinstance(lst,dict),isinstance(lst,tuple)
                if DCT:lst=list(lst.items())                                  #将映射、元组展开为列表方便操作
                if TPL:lst=list(lst)
                for ind in range(len(lst)):
                    if iscontainer(lst[ind]):lst[ind] = run(lst[ind],func)
                    else:lst[ind] = func(lst[ind])
                return dict(lst) if DCT else tuple(lst) if TPL else lst
            
            print('val',xval,sval,iscontainer(xval))

            if sval == "<class 'type'>":res += repr(self.flatten(xval))     #展开嵌套类
            elif iscontainer(xval):res += repr(run(xval,str))
            else:res += repr(xval)

            res += ','                                                      #分割字典项
        return '('+repr(repr(cls)[repr(cls).index('.')+1:repr(cls).index(' ')])+','+res[:-1]+'})'#去除多余逗号，并带上类名
    
    def __str__(self) -> str:
        '''用于以字符串形式存储类的实例。'''
        return self.flatten(self)
        
class backup:
    def dump(scope=globals()) -> None:
        with open(Dumpfile,'wb') as dumpfile:pickle.dump(scope,dumpfile)
        with open(TDumpfile,'w') as dumpfile:
            try:dumpfile.write(Storage().flatten(scope))
            except:...
    
    def load(scope=globals()) -> None:
        with open(Dumpfile,'rb') as dumpfile:scope.update(pickle.load(dumpfile))

class world(Storage):
    users={}
    players={}
    items={}
    places={}

    class user(Storage):
        def __init__(self,UID:int,players:list[int]=[]) -> None:
            self.UID = UID                                              #UID                    （整型）
            self.players = players                                      #此账户的像素点列表     （player类列表）
            world.users[UID]=self

    class player(Storage):
        def __init__(self,ID:int,name:str,color:tuple[int,int,int],pos:int=0,stag:list[str]=[],tag:list[str]=[],ivt:dict={}) -> None:
            self.ID = ID                                                #ID                     （整型）
            self.name = name                                            #名称                   （字符串）
            self.color = color                                          #颜色                   （RGB三元组）
            self.pos = pos                                              #位置                   （整型）
            self.stag = stag                                            #特殊标签               （字符串列表）
            self.tag = tag                                              #标签                   （字符串列表）
            self.ivt = ivt                                              #背包                   （物品名称-数量映射）
            world.players[ID]=self
            self.baseimg = Image.frombytes("RGB",(1,1),b'0000')
            self.baseimg.putpixel((0,0),color)
            world.places[pos].herepixel.append(self)

        class RenderError(Exception):...
        class InventoryError(Exception):...
        class UnknownPlaceError(Exception):...
        class UnknownObjectError(Exception):...
        class UnknownTargetError(Exception):...
        class InvalidPlaceError(Exception):...

        def render(self) -> Image:
            from PIL import Image

            RESAMPLE = Image.NEAREST
            MIPMAP = 0

            BG=Image.new('RGB',world.places[self.pos].BGimg.size,(0,0,0))
            BG.paste(world.places[self.pos].BGimg,(0,0))
            [BG.paste(item[0].mipmap[MIPMAP].resize((item[0].mipmap[MIPMAP].size[0]*item[3],item[0].mipmap[MIPMAP].size[1]*item[3]),resample=RESAMPLE),item[1:3],None) for item in world.places[self.pos].items]
            herepixel = world.places[self.pos].herepixel
            pixelpopularity = min((sum([plc[2][0]*plc[2][1] for plc in world.places[self.pos].pixels])//len(herepixel)),min([min(plc[2][0],plc[2][1]) for plc in world.places[self.pos].pixels])**2/4)
            iherepixel = iter(herepixel)
            pixelplates = deepcopy(world.places[self.pos].pixels)
            prt={}
            while True:
                plate = choice(pixelplates)
                prt[plate]=prt.get(plate,(0,0))
                psize=floor(pixelpopularity**0.5)
                try:
                    BG.paste(next(iherepixel).baseimg.resize((psize-2,psize-2),resample=RESAMPLE),(plate[0]+prt[plate][0]*psize+randint(0,2),plate[1]+prt[plate][1]*psize+randint(0,2)),None)
                except StopIteration:break
                pgrid=plate[2][0]//psize
                phgrid=plate[2][1]//psize
                prt[plate] = (prt[plate][0]+1,prt[plate][1])
                if prt[plate][0] >= pgrid:prt[plate]=(0,prt[plate][1]+1)
                try:
                    if prt[plate][1] >= phgrid:pixelplates.remove(plate)
                except ValueError:raise self.RenderError('无法渲染全部像素点：可渲染面积不足')
                
            return BG

        def move(self,to,forced=False) -> None:
            if not (to in world.places.keys()):raise self.UnknownPlaceError
            if not (forced or (to in world.places[self.pos].conn)):raise self.InvalidPlaceError
            try:
                world.places[self.pos].herepixel.remove(self)
            except ValueError:
                for aplace in world.places:
                    try:aplace.herepixel.remove(self) 
                    finally:...
            self.pos = to
            world.places[self.pos].herepixel.append(self)

        def interact(self,target,oper) -> Any:
            tt=[item[0] for item in world.places[self.pos].items if item[0].ID == target]
            if not tt:raise self.UnknownObjectError
            return getattr(tt[0].oper,oper)(self)
        
        def give(self,target,item,quality,forced=False) -> None:
            if not forced:
                if not ((self.ivt.get(item,0) > quality) and (quality > 0)):raise ValueError
                self.ivt[item] -= quality
            world.players[target].ivt[item] = world.players[target].ivt.get(item,0)+abs(quality)



    class item(Storage):
        def __init__(self,ID:int,desc:str='未命名物品|暂无简介',oper:type=None,mipmapID:str='unknown') -> None:
            from mipmap import mipmaps
            self.ID = ID                                                #ID                     （整型）
            self.desc = desc                                            #名称|描述              （字符串）
            self.oper = oper                                            #可执行的操作           （类）
            self.mipmap = mipmaps[mipmapID]                             #mipmap贴图             （图片列表【mipmap】）
            world.items[ID]=self

    class place(Storage):
        import mipmap
        def __init__(self,ID:int,desc:str='未命名地点|暂无简介',BGimg:Image=mipmap.mipmaps['unknown'],conn:list[int]=[],pixels:list[tuple[int,int,tuple[int,int]]]=[(0,0,(128,128))],items:list[tuple[type,int,int,int]]=[]) -> None:
            self.ID = ID                                                #ID                     （整型）
            self.desc = desc                                            #名称|描述              （字符串）
            self.BGimg = BGimg                                          #背景图                 （Image实例）
            self.conn = conn                                            #可前往的地点           （地点ID列表）
            self.pixels = pixels                                        #可渲染像素点的空地     （x、y、最大尺寸三元组的列表）
            self.items = items                                          #场景内的物品           （物品ID、x、y、缩放四元组的列表）
            world.places[ID]=self
            self.herepixel=[]
