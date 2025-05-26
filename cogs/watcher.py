from discord.ext import commands
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class CogReloaderHandler(FileSystemEventHandler):
    def __init__(self, bot):
        self.bot = bot

    def on_modified(self, event):
        if event.src_path.endswith(".py") and "cogs" in event.src_path:
            cog_name = os.path.basename(event.src_path).replace(".py", "")
            if cog_name != "dynamic_manager":
                try:
                    self.bot.reload_extension(f"cogs.{cog_name}")
                    print(f"[Watcher] Reloaded cog: {cog_name}")
                except Exception as e:
                    print(f"[Watcher] Failed to reload {cog_name}: {e}")

class WatcherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.observer = Observer()
        self.event_handler = CogReloaderHandler(bot)
        self.observer.schedule(self.event_handler, path="./cogs", recursive=False)
        self.observer.start()

    def cog_unload(self):
        self.observer.stop()
        self.observer.join()

async def setup(bot):
    await bot.add_cog(WatcherCog(bot))
