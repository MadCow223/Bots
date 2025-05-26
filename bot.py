import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("YOUR_BOT_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="<", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.load_extension("cogs.dynamic_manager")
        await bot.load_extension("cogs.ai_chat")
        await bot.start(TOKEN)

asyncio.run(main())
