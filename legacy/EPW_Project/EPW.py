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
copy
math
typing
PIL
os
random
'''
#---------------------------------------
#导入所需库
from copy import deepcopy#遇事不决deepcopy（）
from math import floor ,ceil, lcm#我哪知道为啥不用int()？（悲）
import pickle#这玩意太难篡改了……
from random import choice, randint, random ,seed#遇事不决量子力学
from typing import Any#强迫症发作想写类型声明的后果
from PIL import Image,ImageDraw,ImageFont#好用得嘞
from config import execution_path,Dumpfile,TDumpfile#各种路径（但是只有三个变量为啥我还要单开一个文件声明了啊……）

'''改变执行位置。'''
import os#哦！斯！
execution_path and os.chdir(execution_path)#传统艺能cd（）

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
        

class world(Storage):
    users={}#用户，ID对类映射
    players={}#玩家，同上
    items={}#物品，同
    places={}#地点，同

    class user(Storage):
        def __init__(self,UID:int,players:list[int]=[]) -> None:
            self.UID = UID                                              #UID                    （整型）
            self.players = players                                      #此账户的像素点列表     （player类列表）
            world.users[UID]=self#注册

    class player(Storage):
        def __init__(self,ID:int,name:str,color:tuple[int,int,int],pos:int=0,stag:list[str]=[],tag:list[str]=[],ivt:dict={}) -> None:
            self.ID = ID                                                #ID                     （整型）
            self.name = name                                            #名称                   （字符串）
            self.color = color                                          #颜色                   （RGB三元组）
            self.pos = pos                                              #位置                   （整型）
            self.stag = stag                                            #特殊标签               （字符串列表）
            self.tag = tag                                              #标签                   （字符串列表）
            self.ivt = ivt                                              #背包                   （物品名称-数量映射）
            world.players[ID]=self#注册
            self.baseimg = Image.frombytes("RGB",(1,1),b'0000')#创建一个1x1的空图片作为基础
            self.baseimg.putpixel((0,0),color)#根据刚才的基础图片生成这个像素点
            world.places[pos].herepixel.append(self)#注册到地点

        class RenderError(Exception):...
        class InventoryError(Exception):...
        class UnknownPlaceError(Exception):...
        class UnknownObjectError(Exception):...
        class UnknownTargetError(Exception):...
        class InvalidPlaceError(Exception):...

        def render(self,shiver=None) -> Image:
            RESAMPLE = Image.NEAREST#统一重采样方法
            MIPMAP = 0#还没有做画质选项的打算，所以MIPMAP就固定为0了。不过以后可以直接从这扩展。
            hpsize=-1
            while True:
                try:
                    herepixel = world.places[self.pos].herepixel#在此的像素点
                    pixelpopularity = min((sum([plc[2][0]*plc[2][1] for plc in world.places[self.pos].pixels])//len(herepixel)),min([min(plc[2][0],plc[2][1]) for plc in world.places[self.pos].pixels])**2/4)#计算像素点密度（懒得搞二维均衡了，偷懒按照正方形计算了）（悲）
                    pixelplates = deepcopy(world.places[self.pos].pixels)#能塞(sei)像素点的地方
                    prt={}#像素点偏移量
                    if shiver and len(shiver)/len(herepixel)!=2:raise self.RenderError('无法渲染像素点：无效的抖动帧')#shiver长度不对就抛错
                    for ignore in range(len(herepixel)):
                        seed(tuple(prt))
                        plate = choice(pixelplates)#瞎选一个，这里用seed的原因是要保证渲染各帧的时候像素点不会乱串（因为每次渲染的时候所有变量都一样所以不会串）
                        prt[plate]=prt.get(plate,(0,0))#获取偏移量，或者设置默认值0,0
                        if hpsize == -1:hpsize = floor(pixelpopularity**0.5)
                        psize=hpsize#计算像素点的大小
                        if psize < 2:raise self.RenderError('无法渲染像素点：密度过大')#检验
                        pgrid=plate[2][0]//psize
                        phgrid=plate[2][1]//psize#这两行是计算一片区域内排像素点的行列数
                        prt[plate] = (prt[plate][0]+1,prt[plate][1])#下一个格点
                        if prt[plate][0] >= pgrid:prt[plate]=(0,prt[plate][1]+1)#同上
                        try:
                            if prt[plate][1] >= phgrid:pixelplates.remove(plate)#塞满一个之后就不要塞了
                        except ValueError:raise self.RenderError('无法渲染全部像素点：可渲染面积不足')#所有plate都塞满了像素点还没排完
                    break
                except IndexError:
                    #print('dec size:',hpsize)
                    hpsize-=1
            BG=Image.new('RGB',world.places[self.pos].BGimg.size,(0,0,0))#创建一个背景图的空副本（因为deepcopy不能复制图像迫不得已才出此下策）
            BG.paste(world.places[self.pos].BGimg,(0,0))#给副本粘上背景图
            [BG.paste(item[0].mipmap[MIPMAP].resize((int(item[0].mipmap[MIPMAP].size[0]*item[3]),int(item[0].mipmap[MIPMAP].size[1]*item[3])),resample=RESAMPLE),item[1:3],None) for item in world.places[self.pos].items]#粘物品
            herepixel = world.places[self.pos].herepixel#在此的像素点
            pixelpopularity = min((sum([plc[2][0]*plc[2][1] for plc in world.places[self.pos].pixels])//len(herepixel)),min([min(plc[2][0],plc[2][1]) for plc in world.places[self.pos].pixels])**2/4)#计算像素点密度（懒得搞二维均衡了，偷懒按照正方形计算了）（悲）
            iherepixel = iter(herepixel)#开个迭代器
            pixelplates = deepcopy(world.places[self.pos].pixels)#能塞(sei)像素点的地方
            prt={}#像素点偏移量
            if shiver and len(shiver)/len(herepixel)<2:raise self.RenderError('无法渲染像素点：无效的抖动帧')#shiver长度不对就抛错
            elif shiver:shiver = shiver[:len(herepixel)*2]
            _shiver = iter(shiver or [randint(0,5) for ignore in range(2*len(herepixel))])#没有shiver就弄个空shiver上去（shiver的格式是，每两个值表示一个像素点的抖动，因为在渲染的时候herepixel不会变，所以不用担心对不齐的问题）
            while True:
                seed(tuple(prt))
                plate = choice(pixelplates)#瞎选一个，这里用seed的原因是要保证渲染各帧的时候像素点不会乱串（因为每次渲染的时候所有变量都一样所以不会串）
                prt[plate]=prt.get(plate,(0,0))#获取偏移量，或者设置默认值0,0
                psize=hpsize#计算像素点的大小
                if psize < 2:raise self.RenderError('无法渲染像素点：密度过大')#检验
                try:
                    pxlb=next(iherepixel)
                    pxl=pxlb.baseimg.resize((psize-2,psize-2),resample=RESAMPLE)
                    ImageDraw.Draw(pxl).text((0,0),pxlb.name,tuple((c+128 if c<=127 else c-128 for c in pxlb.color)),ImageFont.truetype('MAE.ttf',max(2,min(psize//len(pxlb.name),psize//6))))
                    BG.paste(pxl,(int(plate[0]+prt[plate][0]*psize+(psize*next(_shiver)/100)),int(plate[1]+prt[plate][1]*psize-(psize*next(_shiver)/100))),None)#粘像素点，-2是为了抖动
                except StopIteration:break#粘完了就出循环
                pgrid=plate[2][0]//psize
                phgrid=plate[2][1]//psize#这两行是计算一片区域内排像素点的行列数
                prt[plate] = (prt[plate][0]+1,prt[plate][1])#下一个格点
                if prt[plate][0] >= pgrid:prt[plate]=(0,prt[plate][1]+1)#同上
                try:
                    if prt[plate][1] >= phgrid:pixelplates.remove(plate)#塞满一个之后就不要塞了
                except ValueError:raise self.RenderError('无法渲染全部像素点：可渲染面积不足')#所有plate都塞满了像素点还没排完
            return BG

        def GIFrender(self):
            import anim
            def seedfrom(k):
                seed(k)
                while True:
                    o=random()
                    seed(o)
                    yield(o)
            anims = anim.anim
            anim_length=lcm(*[len(a) for a in anims])
            anims = [iter(a*ceil(2*anim_length*len(world.places[self.pos].herepixel)/len(a))) for a in anims]
            output=[]
            for i in range(anim_length):
                sf=seedfrom(tuple(world.places.items()))
                shiver=[]
                for ig in range(len(world.places[self.pos].herepixel)):
                    seed(next(sf))
                    t = choice(anims)
                    shiver +=[next(t)+next(sf)*20-10,next(t)+next(sf)*20-10]
                output.append(self.render(shiver))
                print('成功渲染一帧:',i)
            output[0].save('~$tmp.gif',save_all=True,append_images=output[1:], duration=int(1000/8), loop=0, disposal=2)
            return Image.open('~$tmp.gif')
        def move(self,to,forced=False) -> None:
            if not (to in world.places.keys()):raise self.UnknownPlaceError
            if not (forced or (to in world.places[self.pos].conn)):raise self.InvalidPlaceError
            try:
                print('TRK201',repr(self.pos))
                world.places[self.pos].herepixel = set(world.places[self.pos].herepixel)
                world.places[self.pos].herepixel = list(world.places[self.pos].herepixel)
                world.places[self.pos].herepixel.remove(self)
            except ValueError:
                print('TRK205')
                for aplace in world.places.values():
                    try:
                        aplace.herepixel = set(aplace.herepixel)
                        aplace.herepixel = list(aplace.herepixel)
                        aplace.herepixel.remove(self)
                        print('TRK210')
                    except Exception as e:aplace.herepixel = list(aplace.herepixel);print('TRK211',repr(e))
            except Exception as e:print('TRK',repr(e))
            print('TRK212')
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

class backup:
    def dump() -> None:
        with open(Dumpfile,'wb+') as dumpfile:pickle.dump((world.players,world.places,world.users,world.items),dumpfile)
        '''with open(TDumpfile,'w') as dumpfile:
            try:dumpfile.write(Storage().flatten(scope))
            except:...'''
    
    def load() -> None:
        with open(Dumpfile,'rb+') as dumpfile:world.players,world.places,world.users,world.items=pickle.load(dumpfile)
