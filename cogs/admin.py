import discord
from discord.ext import commands
import os
from pathlib import Path
import datetime

class  Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def load(self,ctx, extension):
        try:
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f'`<{extension}> loaded.`')
            return
        except Exception as e:
            await ctx.send(f'`<{extension}> is already loaded!`')

    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f'`<{extension}> unloaded.`')
            return
        except Exception as e:
            await ctx.send(f'`<{extension}> is not loaded!`')

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f'`<{extension}> reloaded.`')
            return
        except Exception as e:
            await ctx.send("`Could not reload cog.`")   

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def clear(self,ctx, amount : int):
        await ctx.channel.purge(limit = amount+1)
        await ctx.send(f"`{amount} 則訊息已清除`")
    #clear_cmd_error
    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("請輸入要刪除的訊息數量")
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("你沒有權限呦 :lock:")

    @commands.command()
    async def stop(self, ctx):
        for i in range(100):
            await ctx.send("-skip")
            

async def setup(bot):
    await bot.add_cog(Admin(bot))
