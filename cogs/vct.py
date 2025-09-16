import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import requests
from bs4 import BeautifulSoup
import json
import datetime
import traceback
from .utils import match_pic
import pytz

class MatchSelect(discord.ui.Select):
    def __init__(self, match_list):
        self.match_list = match_list
        options = [
            discord.SelectOption(
                label=f"{match['team1']} vs {match['team2']}",
                #description=match['tournament_name'][:100],
                value=str(i)
            )
            for i, match in enumerate(match_list)
        ]

        super().__init__(
            placeholder="選擇一場比賽以查看詳情...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        match = self.match_list[index]
        if 'https://www.vlr.gg' in match['match_page']:
            link = match['match_page']
        else:
            link = f'https://www.vlr.gg' + match['match_page']
            
        try:
            image, match_time = match_pic.gen_pic(match_pic.scrape_major_info(link))
        except Exception as e:
            print(f'error: {e}')

        file = discord.File(image, filename="match.png")

        try:
            match_utc = match['unix_timestamp']
            timezone = pytz.timezone('UTC')
            dt = timezone.localize(datetime.datetime.strptime(match_utc, "%Y-%m-%d %H:%M:%S"))
            timestamp = int(dt.timestamp())
            time_info = f'開始時間：`{match_time}` \n(<t:{timestamp}:R>)'
        except Exception as e:
            print(f'error: {e}')

            time_info = f"開始時間：`{match_time}`"

        result = discord.Embed(
                title = f":{match['flag1']}: {match['team1']} vs :{match['flag2']}: {match['team2']}",
                description= time_info,
                color = discord.Colour.dark_magenta(),
                timestamp= datetime.datetime.now() 
        )
        result.set_footer(text='vlr.gg', icon_url='https://www.vlr.gg/img/vlr/logo_header.png')
        result.set_image(url="attachment://match.png")
        
        # 顯示比賽資訊
        await interaction.response.defer(ephemeral=False)
        loading_message = await interaction.followup.send("🔄 正在獲取資料，請稍候...", wait=True)
        await interaction.followup.send(
            embed= result,
            file=file,
            ephemeral= False
        )
        await loading_message.delete()



class MatchSelectView(discord.ui.View):
    def __init__(self, match_list):
        super().__init__(timeout=None)
        self.add_item(MatchSelect(match_list))

vlrgg_base = "https://vlrggapi.vercel.app"  # unofficial vlr api
    
def format_team_line(flag, team, total_width=21):
    if len(team) > total_width - 4:
        team = team[:total_width - 7] + '...'
    
    line = f":{flag}: {team}"
    return line

class vct(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog loaded\n-----")

    @commands.command()
    async def stringtest(self, ctx, *, msg):
        split_string = msg.split("#", 1)
        tag = split_string[1]
        name = split_string[0]
        name = name.replace(" ", "%20")
        await ctx.send(name)

    @commands.group(
        name="vct", description="統神幫你查VCT賽事資料"
    )
    async def vct(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("缺少或使用錯誤的附加指令!\n請輸入`.vct <附加指令> <參數>`")


    @vct.group(name="match", invoke_without_command=True)
    async def match(self, ctx):
        response = requests.get(f"{vlrgg_base}/match?q=upcoming")
        re = response.json()
        response = requests.get(f"{vlrgg_base}/match?q=live_score")
        re_live = response.json()

        match_data_list = []

        matches = discord.Embed(
            title = '賽事列表', 
            color = discord.Colour.dark_magenta(),
            timestamp= datetime.datetime.now()
            )
        
        if not re_live['data']['segments']:
            matches.add_field(name= f"__正在進行的比賽__", value = '', inline= False)
            matches.add_field(name="", value="`無正在進行中的比賽`", inline=False)
        else:
            matches.add_field(name= f"__正在進行的比賽__", value = '', inline= False)
            for match in re_live['data']['segments']:
                match_data_list.append(match)
                #match['tournament_name'] = 
                team1 = match['team1']
                team2 = match['team2']
                flag1 = match['flag1']
                flag2 = match['flag2']
                score1 = match['score1']
                score2 = match['score2']
                line1 = format_team_line(flag1, team1)
                line2 = format_team_line(flag2, team2)

                matches.add_field(name="", value=f"{line1}\n{line2}", inline=True)
                matches.add_field(name="", value=f"__{score1}__\n__{score2}__", inline=True)
                matches.add_field(name="", value="", inline=False)
        
        matches.add_field(name= f"__即將開始的比賽__", value = '', inline= False)

        match_count = 0
        for match in re['data']['segments']:
            if match_count < 6:
                if match['team1'] == 'TBD' and match['team2'] == 'TBD':  # 若為尚未預備之比賽
                    continue
                else:
                    match_data_list.append(match)
                    match_time = match['time_until_match'].split(" from")[0]
                    matches.add_field(name= f":{match['flag1']}: {match['team1']} vs. :{match['flag2']}: {match['team2']} ({match_time})",
                                    value= f"{match['match_event']} {match['match_series']}", inline= False)
                    match_count += 1
            else:
                break
        
        matches.set_footer(text= 'vlr.gg', icon_url= 'https://www.vlr.gg/img/vlr/logo_header.png')
        #print(match_data_list)
        view = MatchSelectView(match_data_list)
        await ctx.reply(embed = matches, view=view)


    @vct.group(name="result", invoke_without_command=True)
    async def result(self, ctx):
        response = requests.get(f"{vlrgg_base}/match?q=results")
        re = response.json()
        
        matches = discord.Embed(
            title='已完成賽事',
            url='https://www.vlr.gg/matches/results',
            color=discord.Colour.dark_magenta(),
            timestamp=datetime.datetime.now()
        )
        matches.set_footer(text='vlr.gg', icon_url='https://www.vlr.gg/img/vlr/logo_header.png')

        match_data_list = []

        for i in range(6):
            match = re['data']['segments'][i]
            match_data_list.append(match)

            team1 = match['team1']
            team2 = match['team2']
            flag1 = match['flag1']
            flag2 = match['flag2']
            score1 = match['score1']
            score2 = match['score2']
            tourname = match['tournament_name']
            time = match['time_completed']

            line1 = format_team_line(flag1, team1)
            line2 = format_team_line(flag2, team2)

            matches.add_field(name=f'**{tourname}**', value=f'`{time}`', inline=False)
            matches.add_field(name='', value=f"{line1}\n{line2}", inline=True)

            if score1 > score2:
                matches.add_field(name='', value=f"__**{score1}**__\n__{score2}__", inline=True)
            else:
                matches.add_field(name='', value=f"__{score1}__\n__**{score2}**__", inline=True)

            matches.add_field(name='', value='', inline=False)

        # 使用 View 加入選單
        view = MatchSelectView(match_data_list)

        await ctx.reply(embed=matches, view= view)

async def setup(client):
    await client.add_cog(vct(client))

