import discord
from discord.ext import commands  
import urllib.request as req 
    
class news(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded\n-----")

    @commands.command(
        name = "news", description = "統神會幫你找新聞!"
    )
    async def news(self, ctx, amount:int):
        url = "https://udn.com/news/breaknews/1"

        if amount <= 15:
            
            
            request = req.Request(url, headers = {
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
            })

            with req.urlopen(request) as response:
                data = response.read().decode("utf-8")

            import bs4
            root = bs4.BeautifulSoup(data, "html.parser")
            titles = root.find_all("div", class_="story-list__text", limit = amount)
            
            hb = discord.Embed(
                title = "新聞 | 即時新聞",
                colour = discord.Colour.gold(),
            )
            hb.set_author(name = "udn聯合新聞網")
            hb.set_thumbnail(url = "https://udn.com/static/img/logo.svg?2020020601")
            hb.set_footer(text = "©Flatha#8726")
            
            for title in titles:
                if title.a != None:
                    text = title.a.string
                    link = "https://udn.com/"+title.a.get("href")
                    hb.add_field(name = text,value = link , inline = False)
            
            await ctx.send(embed = hb)
        else:
            await ctx.send("太多了。吳翼名網路超爛")
    @news.error
    async def argu_error(self,ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("缺少參數!\n格式為`.news <數量>`")


async def setup(client):
    await client.add_cog(news(client))