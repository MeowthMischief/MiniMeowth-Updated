import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import signal
import sys
import config
from database import db

load_dotenv()

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Bot setup
bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,  
    case_insensitive=True
)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} ({bot.user.id})')
    print(f'📝 Prefix: {config.PREFIX}')
    print(f'🎨 Embed Color: #{config.EMBED_COLOR:06x}')

    # Connect to database
    await db.connect()

    # Load cogs
    cogs = [
        'cogs.utils',
        'cogs.shinydex_display',
        'cogs.shinydex_management',
        'cogs.event_display',
        'cogs.event_management',
        'cogs.breeding',
        'cogs.cooldown',
        'cogs.help',
        'cogs.inventory',
        'cogs.settings'
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'✅ Loaded cog: {cog}')
        except Exception as e:
            print(f'❌ Failed to load cog {cog}: {e}')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

    # Set streaming activity
    try:
        activity = discord.Streaming(
            name="MeowthMischief★'s Adventures",
            url="https://www.twitch.tv/discord"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)
        print(f'✅ Activity set: {activity.name}')
    except Exception as e:
        print(f'❌ Failed to set activity: {e}')

    print('🚀 Bot is ready!')

@bot.event
async def on_message(message):
    """Process commands from messages"""
    if message.author.bot:
        return

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Process commands from edited messages"""
    if after.author.bot:
        return

    # Only process if the content actually changed
    if before.content != after.content:
        await bot.process_commands(after)

@bot.event
async def on_disconnect():
    """Handle Discord disconnections - DO NOT close database here!"""
    print("⚠️ Discord disconnected (will attempt to reconnect...)")
    # Database stays open - Discord will reconnect automatically

@bot.event
async def on_resumed():
    """Handle Discord reconnection"""
    print("✅ Discord connection resumed")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided")
    elif isinstance(error, commands.HybridCommandError):
        # Unwrap the original error
        original = error.original if hasattr(error, 'original') else error
        await ctx.send(f"❌ An error occurred: {str(original)}")
        print(f"Hybrid command error: {original}")
        import traceback
        traceback.print_exception(type(original), original, original.__traceback__)
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        print(f"Error: {error}")
        import traceback
        traceback.print_exception(type(error), error, error.__traceback__)

async def shutdown():
    """Properly shutdown bot and database"""
    print("\n🛑 Shutting down bot...")
    try:
        await db.close()
        await bot.close()
        print("✅ Shutdown complete")
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals (Ctrl+C, kill, etc.)"""
    print(f"\n⚠️ Received signal {signum}")
    # Create a task to shutdown gracefully
    asyncio.create_task(shutdown())
    sys.exit(0)

# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        sys.exit(1)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Kill command

    try:
        print("🚀 Starting bot...")
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("\n⚠️ KeyboardInterrupt detected")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure database is closed on exit
        print("🧹 Cleaning up...")
        if db.client:
            try:
                # Run the async close in a new event loop since bot.run() has closed its loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(db.close())
                loop.close()
            except Exception as e:
                print(f"⚠️ Error closing database: {e}")

        print("👋 Bot stopped")
