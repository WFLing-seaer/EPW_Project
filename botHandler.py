import botpy
import EPW

class FUNC:
    def me(info):

class main(botpy.Client):
    async def on_at_message_create(self, message:botpy.message.Message) -> None:
        try:
            func=getattr(FUNC,message.content[message.content.index('/')+1:message.content.index(' ')+message.content[message.content.index(' ')+1:].index(' ')+1])
            args=message.content[message.content.index(' ')+message.content[message.content.index(' ')+1:].index(' ')+2:].split()
        except:func=(lambda *args:'E5:指令错误')
        await message.reply(content=func(*args))

intents = botpy.Intents(public_guild_messages=True) 
client = main(intents=intents)
client.run(appid='102078532', token='t5JlsgR4uCMsuid9LWXp5bcSdLSuflod')
