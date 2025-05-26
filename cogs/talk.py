from discord.ext import commands

class TalkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello from the Talk Cog!")

async def setup(bot):
    await bot.add_cog(TalkCog(bot))
