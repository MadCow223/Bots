import os
import shutil
from datetime import datetime

updates = {
    "dynamic_manager.py": """
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
            if filename.endswith(".py") and filename != "__init__.py":
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

        cog_files = [f[:-3] for f in os.listdir("cogs") if f.endswith(".py") and f[:-3] not in self.exclude and f != "__init__"]
        cogs = [(cog, f"cogs.{cog}" in self.bot.extensions) for cog in cog_files]

        embed = discord.Embed(title="🧠 COG STATUS REPORT", description="Live status of all cogs.", color=discord.Color.blurple())
        embed.set_footer(text="Last updated")
        for cog, is_loaded in sorted(cogs, key=lambda x: (not x[1], x[0])):
            embed.add_field(name=cog, value="✅ Loaded" if is_loaded else "❌ Not Loaded", inline=False)

        view = CogDropdownView(self.bot, cogs)

        try:
            if self.message:
                # Delete all non-pinned messages except the current status message and pinned ones
                async for m in channel.history(limit=50):
                    if m.id != self.message.id and not m.pinned:
                        try:
                            await m.delete()
                        except:
                            pass
        except Exception as e:
            print(f"[DynamicCogManager] Purge failed: {e}")

        if self.message:
            try:
                await self.message.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                # The status message was deleted, reset to None
                self.message = None
        self.message = await channel.send(embed=embed, view=view)
        try:
            if not self.message.pinned:
                await self.message.pin()
        except discord.Forbidden:
            print("[DynamicCogManager] Unable to pin the status message.")

async def setup(bot):
    await bot.add_cog(DynamicCogManager(bot))
""",

    "ai_chat.py": """
import discord
from discord.ext import commands
import openai
import os

AUTHORIZED_ROLES = {1375809453097615470, 1375809454427340840}

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ask")
    async def ask(self, ctx, *, prompt):
        if not self._authorized(ctx):
            return await ctx.send("🚫 You don't have permission to use this.")

        await ctx.typing()
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are MERCURY, a cryptic and tactical AI advisor for a mercenary Discord server."},
                    {"role": "user", "content": prompt}
                ]
            )
            await ctx.send(response.choices[0].message.content)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="edit")
    async def edit_cog(self, ctx, cog: str, *, instruction):
        if not self._authorized(ctx):
            return await ctx.send("🚫 You don't have permission to edit code.")

        file_path = f"cogs/{cog}.py"
        if cog == "__init__" or not os.path.exists(file_path):
            return await ctx.send(f"❌ `{cog}.py` not found.")

        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        prompt = (
            "You are MERCURY, an AI code assistant working with Discord.py.\\n"
            "Update this code based on the user's instruction, return the full Python file:\\n"
            f"\\nINSTRUCTION:\\n{instruction}\\n\\nCURRENT FILE:\\n{original_code}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a precise code editor."}, {"role": "user", "content": prompt}],
                temperature=0.2
            )
            new_code = response.choices[0].message.content.strip()

            preview_message = await ctx.send(f"```python\\n{new_code[:1900]}```\\n✅ Type `<confirm {cog}>` to apply this code.")
            self.bot.generated_cog_preview = {"file": file_path, "code": new_code, "message_id": preview_message.id}

        except Exception as e:
            await ctx.send(f"❌ AI error: {e}")

    @commands.command(name="confirm")
    async def confirm_edit(self, ctx, cog: str):
        if not self._authorized(ctx):
            return await ctx.send("🚫 You don't have permission to confirm code changes.")

        preview = getattr(self.bot, "generated_cog_preview", None)
        if not preview or preview["file"] != f"cogs/{cog}.py":
            return await ctx.send("⚠️ No matching edit preview found.")

        try:
            with open(preview["file"], "w", encoding="utf-8") as f:
                f.write(preview["code"])
        except Exception as e:
            return await ctx.send(f"❌ Failed to write code: {e}")

        try:
            if cog != "__init__":
                await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(f"✅ `{cog}.py` updated and reloaded.")
        except Exception as e:
            await ctx.send(f"❌ Reload failed: {e}")

    @commands.command(name="rollback")
    async def rollback_cog(self, ctx, cog: str):
        if not self._authorized(ctx):
            return await ctx.send("🚫 You don't have permission to roll back code.")

        file_path = f"cogs/{cog}.py"
        try:
            import subprocess
            subprocess.run(["git", "checkout", "HEAD~1", "--", file_path], check=True)
            if cog != "__init__":
                await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(f"↩️ Rolled back `{cog}.py` to the previous commit.")
        except Exception as e:
            await ctx.send(f"❌ Rollback failed: {e}")

    def _authorized(self, ctx):
        return any(role.id in AUTHORIZED_ROLES for role in ctx.author.roles)

async def setup(bot):
    await bot.add_cog(AICog(bot))
"""
}

def backup_file(path):
    import shutil
    from datetime import datetime
    if not os.path.isfile(path):
        print(f"File to backup not found: {path}")
        return False
    backup_path = f"{path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, backup_path)
    print(f"Backup created: {backup_path}")
    return True

def update_cog_file(cogs_folder, filename, new_content):
    filepath = os.path.join(cogs_folder, filename)
    if not os.path.isfile(filepath):
        print(f"Original cog not found: {filepath}")
        return False

    if backup_file(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated cog: {filepath}")
        return True
    else:
        print(f"Skipped updating {filepath} due to backup failure.")
        return False

def main():
    cogs_folder = "cogs"
    for filename, content in updates.items():
        update_cog_file(cogs_folder, filename, content)

if __name__ == "__main__":
    main()
