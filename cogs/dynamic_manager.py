import os
import discord
from discord.ext import commands, tasks
from discord import ui

MANAGED_CHANNEL_ID = 1376007319653187768

class CogDropdown(ui.Select):
    def __init__(self, bot, cogs):
        self.bot = bot
        options = [
            discord.SelectOption(label=cog, description="✅ Loaded" if is_loaded else "❌ Not Loaded")
            for cog, is_loaded in sorted(cogs, key=lambda x: (not x[1], x[0]))
        ]
        super().__init__(placeholder="Select a cog to manage...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        view = CogActionButtons(self.bot, selected)
        await interaction.response.send_message(f"⚙️ Managing `{selected}`:", view=view, ephemeral=True)

class CogActionButtons(ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=30)
        self.add_item(CogButton("Reload", discord.ButtonStyle.blurple, cog, bot))
        self.add_item(CogButton("Unload", discord.ButtonStyle.red, cog, bot))
        self.add_item(CogButton("Load", discord.ButtonStyle.green, cog, bot))

class CogButton(ui.Button):
    def __init__(self, label, style, cog, bot):
        super().__init__(label=label, style=style)
        self.cog = cog
        self.bot = bot
        self.label_type = label

    async def callback(self, interaction: discord.Interaction):
        cog_path = f"cogs.{self.cog}"
        try:
            if self.label_type == "Reload":
                await self.bot.reload_extension(cog_path)
                await interaction.response.send_message(f"✅ Reloaded `{self.cog}`", ephemeral=True)
            elif self.label_type == "Unload":
                await self.bot.unload_extension(cog_path)
                await interaction.response.send_message(f"⚠️ Unloaded `{self.cog}`", ephemeral=True)
            elif self.label_type == "Load":
                await self.bot.load_extension(cog_path)
                await interaction.response.send_message(f"📥 Loaded `{self.cog}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class CogDropdownView(ui.View):
    def __init__(self, bot, cogs):
        super().__init__(timeout=None)
        self.add_item(CogDropdown(bot, cogs))

class DynamicCogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.exclude = {"dynamic_manager"}
        self.message = None
        self.live_updater.start()

    @commands.Cog.listener()
    async def on_ready(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                name = filename[:-3]
                if name not in self.exclude:
                    try:
                        await self.bot.load_extension(f"cogs.{name}")
                        print(f"[DynamicCogManager] Loaded: {name}")
                    except Exception as e:
                        print(f"[DynamicCogManager] Failed to load {name}: {e}")

    @tasks.loop(seconds=1)
    async def live_updater(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(MANAGED_CHANNEL_ID)
        if not channel:
            return

        cog_files = [f[:-3] for f in os.listdir("cogs") if f.endswith(".py") and f[:-3] not in self.exclude]
        cogs = [(cog, f"cogs.{cog}" in self.bot.extensions) for cog in cog_files]

        embed = discord.Embed(title="🧠 COG STATUS REPORT", description="Live status of all cogs.", color=discord.Color.blurple())
        for cog, is_loaded in sorted(cogs, key=lambda x: x[0]):
            embed.add_field(name=cog, value="✅ Loaded" if is_loaded else "❌ Not Loaded", inline=False)

        view = CogDropdownView(self.bot, cogs)

        if self.message:
            try:
                await self.message.edit(embed=embed, view=view)
            except discord.NotFound:
                self.message = await channel.send(embed=embed, view=view)
        else:
            self.message = await channel.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(DynamicCogManager(bot))
