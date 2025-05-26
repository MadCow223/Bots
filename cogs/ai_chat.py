
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
            "You are MERCURY, an AI code assistant working with Discord.py.\n"
            "Update this code based on the user's instruction, return the full Python file:\n"
            f"\nINSTRUCTION:\n{instruction}\n\nCURRENT FILE:\n{original_code}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a precise code editor."}, {"role": "user", "content": prompt}],
                temperature=0.2
            )
            new_code = response.choices[0].message.content.strip()

            preview_message = await ctx.send(f"```python\n{new_code[:1900]}```\n✅ Type `<confirm {cog}>` to apply this code.")
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
