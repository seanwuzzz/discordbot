import discord
import os
from pathlib import Path
from discord.ext import commands
import asyncio
import tracemalloc
import traceback

tracemalloc.start()
    
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 確定你有打開 Developer Portal 裡的 intent


client = commands.Bot(command_prefix='.', intents=intents)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="So Cute | .help"))
    print("===============")
    print("統神好可愛 Online")
    print("===============")

async def load_cogs():
    cwd = str(Path(__file__).parents[0])
    for filename in os.listdir(f"{cwd}/cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

async def on_command_error(ctx, error):
    # 在 console 印出錯誤完整堆疊
    print(f"指令 '{ctx.command}' 執行錯誤:")
    traceback.print_exception(type(error), error, error.__traceback__)
    
    # 你可以選擇回覆使用者
    await ctx.send(f"發生錯誤: {error}")


async def main():
    await load_cogs()
    await client.start('TOKEN')  # 放入自己的Token

if __name__ == "__main__":
    asyncio.run(main())

