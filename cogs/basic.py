import discord
from discord.ext import commands  
import urllib.request as req 
from datetime import datetime

class Basic(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded\n-----")

    @commands.command(
        name = "hello", description = "統神跟你打招呼!"
    )
    async def hello(self,ctx):
        await ctx.send(f"hello, {ctx.author.mention} :capy:")    

    
    @commands.command()
    async def time(self,ctx):
        timestamp = datetime.now()
        currentTime = timestamp.strftime(r"%I:%M %p")
        await ctx.send(f"現在時間是 {currentTime}")

async def setup(client):
    await client.add_cog(Basic(client))