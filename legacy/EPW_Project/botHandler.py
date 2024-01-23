import botpy
import EPW
import requests
import hashlib
import pickle

current_pixel=pickle.load(open('~$pxtmp','rb+'));
EPW.backup.load()
class FUNC:
    def me(msg,*info):
        if '-s' in info:
            try:
                img=current_pixel[int(msg.author.id)].render();
            except IndexError as e:
                return 'E14:未注册的用户或无效像素点'+repr(e)
            except Exception as e:
                return 'E17:渲染错误:'+str(e)
            img.resize((512,512)).save('~$tmp.png','png')
        else:
            current_pixel[int(msg.author.id)].GIFrender()
        return ('infos:'+str(info),'~$tmp'+('.png' if '-s' in info else'.gif'))
    def 前往(msg,*info):
        if info:
            try:
                current_pixel[int(msg.author.id)].move(int(info[0]))
                EPW.backup.dump()
            except IndexError as e:
                return 'E26:未注册的用户或无效地点'+repr(e)
            except ValueError as e:
                return 'E30:地点编号需作为第一个参数传入且必须为非负整数'+repr(e)
            except Exception as e:
                return 'E32:未知的地点操作错误:'+repr(e)
            return FUNC.me(msg,('操作成功',))
        else:
            return '当前您位于'+'（'.join(EPW.world.places[current_pixel[int(msg.author.id)].pos].desc.split('|'))+'）\n当前可以前往的地点列表:\n编号\t地点\n'+'\n'.join([str(k)+'\t'+EPW.world.places[k].desc.split('|')[0] for k in EPW.world.places[current_pixel[int(msg.author.id)].pos].conn])

    def 注册(msg,*info):
        if not info:
            return '''欢迎注册像素世界。在注册之前，请您确认您已经阅读了公告。
确认之后，请您输入“/注册 （像素点1编号）【像素点2编号】【像素点3编号】……”进行注册。
像素点编号格式为“#XXXXXX”，如“#CCFCFC”，字母大写，多个编号之间以空格分隔。
例：/注册 #FCCCFC #CCFCFC
注意：注册时将会从像素点.cn查询像素点信息，可能需要一分钟左右时间，请耐心等待。'''
        else:
            #info = info.split(' ')
            print('注册 info：',repr(info))
            if not all([len(c)==7 and c[0]=='#' and all(['0'<=ch<='9' or 'A'<=ch<='F' for ch in c[1:]]) for c in info]):
                return '您的像素点格式有误！'
            pixels=[p[1:] for p in info]
            output='请检查您的像素点列表：\n'
            pxs=[]
            txts=[]
            for pixel in pixels:
                try:
                    txt=requests.get('https://xn--o1qx19eeqi.cn/i/x/'+pixel+'.json')
                    print('获取信息成功。')
                    if not txt.ok:raise Exception
                    txt=txt.text.split('／')
                    if txt[0] in [str(hex((a.color[0]<<16)+(a.color[1]<<8)+a.color[2]))[2:] for a in EPW.world.players.values()]:
                        return 'E32:像素点已经注册'
                    txts.append((txt,pixel))
                    output+='像素点'+txt[0]+'（领养人：'+txt[1]+'）；\n'
                except Exception as e:
                    return 'E25:不存在的像素点'+repr(e)
            for txt in reversed(txts):
                print(repr(txt),'txt')
                current_pixel.update({int(msg.author.id):EPW.world.player(int(hashlib.md5(str(txt[0][0]).encode()).hexdigest(),base=16),txt[0][0],(int(txt[1][0:2],base=16),int(txt[1][2:4],base=16),int(txt[1][4:],base=16)))})
                pxs.append(current_pixel[int(msg.author.id)])
            
            if int(msg.author.id) in EPW.world.users:
                [user for user in EPW.world.users.values() if user.UID==int(msg.author.id)][0].players += pxs
            else:
                EPW.world.user(int(msg.author.id),pxs)
            EPW.backup.dump()
            pickle.dump(current_pixel,open('~$pxtmp','wb+'))
            return output+'上述像素点成功注册。'
    def 切换像素点(msg,*info):
        if not info:
            return '切换像素点：请输入像素点编号（需为您注册的，井号打头，大写字母）以切换到对应像素点。\n例：/切换像素点 #E4E4FC'
        else:
            if info[0].lstrip('#') in [str(hex((p.color[0]<<16)+(p.color[1]<<8)+p.color[2]))[2:].upper() for p in EPW.world.users[int(msg.author.id)].players]:
                current_pixel[int(msg.author.id)] = [p for p in EPW.world.users[int(msg.author.id)].players if str(hex((p.color[0]<<16)+(p.color[1]<<8)+p.color[2]))[2:] == info[0].lstrip('#').lower()][0]
                pickle.dump(current_pixel,open('~$pxtmp','wb+'))
                return '已切换到像素点'+info[0]
            else:
                return 'E85:像素点不存在或不是您领养的'
class main(botpy.Client):
    async def on_at_message_create(self, message:botpy.message.Message) -> None:
        ERR=''
        """if not message.content.startswith('<@!7774168355917134191> /'):
            print(message.content)
            try:
                await self.api.recall_message(message.channel_id, message.id, hidetip=True)
            except botpy.errors.AuthenticationFailedError:
                ERR='E46:机器人权限不足'"""
        try:
            func=getattr(FUNC,message.content[message.content.index('/')+1:message.content.index(' ')+message.content[message.content.index(' ')+1:].index(' ')+1])
            args=message.content[message.content.index(' ')+message.content[message.content.index(' ')+1:].index(' ')+2:].split()
        except Exception as e:
            await message.reply(content='E5:指令错误:'+repr(e))
            return
        #try:
        output=func(message,*args)
        #except Exception as e:
            #output='E16:参数错误:'+repr(e)
        
        await message.reply(content=ERR or (output if isinstance(output,str) else output[0]),file_image=output[1] if isinstance(output,tuple) else None)

intents = botpy.Intents(public_guild_messages=True) 
client = main(intents=intents)
print(globals())
client.run(appid='102078532', token='t5JlsgR4uCMsuid9LWXp5bcSdLSuflod')
