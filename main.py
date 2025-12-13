import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import signal
import sys
import config
from database import db
import re

load_dotenv()

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# Custom prefix function to handle bot mentions and strip spaces
def get_prefix(bot, message):
    """
    Custom prefix handler that:
    1. Allows bot mentions as prefix
    2. Allows configured prefixes from config
    3. Strips whitespace after prefix
    """
    # Get bot mentions as prefixes
    mention_prefixes = [f'<@{bot.user.id}> ', f'<@!{bot.user.id}> ']

    # Combine with config prefixes
    prefixes = mention_prefixes + config.PREFIX

    # Check each prefix
    for prefix in prefixes:
        if message.content.startswith(prefix):
            # Find where the actual command starts (skip whitespace after prefix)
            remaining = message.content[len(prefix):]
            stripped = remaining.lstrip()
            # Calculate how much whitespace was stripped
            whitespace_len = len(remaining) - len(stripped)
            # Return the prefix + whitespace so discord.py can parse the command
            return prefix + ' ' * whitespace_len

    # If no prefix matched, return the list for discord.py to handle
    return prefixes

# Bot setup
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None,  
    case_insensitive=True
)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} ({bot.user.id})')
    print(f'📝 Prefix: {config.PREFIX} + <@{bot.user.id}>')
    print(f'🎨 Embed Color: #{config.EMBED_COLOR:06x}')

    # Connect to database
    await db.connect()

    # Load cogs
    cogs = [
        'cogs.utils',
        'cogs.shinydexstats',
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

    # Load Jishaku
    try:
        await bot.load_extension('jishaku')
        print(f'✅ Loaded extension: jishaku')
    except Exception as e:
        print(f'❌ Failed to load jishaku: {e}')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

    # Set streaming activity
    try:
        activity = discord.Streaming(
            name="Team Rocket's Adventures",
            url="https://www.twitch.tv/discord"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)
        print(f'✅ Activity set: {activity.name}')
    except Exception as e:
        print(f'❌ Failed to set activity: {e}')

    print('🚀 Bot is ready!')

@bot.event
async def on_message(message):
    """Process commands from messages with space handling"""
    if message.author.bot:
        return

    # Custom processing to handle spaces after prefix
    content = message.content

    # Check for bot mention prefix
    mention_patterns = [f'<@{bot.user.id}>', f'<@!{bot.user.id}>']
    for pattern in mention_patterns:
        if content.startswith(pattern):
            # Remove mention and strip spaces
            remaining = content[len(pattern):].lstrip()
            if remaining:
                # Reconstruct message content with single space after mention
                message.content = f'{pattern} {remaining}'
            break
    else:
        # Check for regular prefixes
        for prefix in config.PREFIX:
            if content.startswith(prefix):
                # Remove prefix and strip spaces
                remaining = content[len(prefix):].lstrip()
                if remaining:
                    # Reconstruct message content with no space after prefix
                    message.content = f'{prefix}{remaining}'
                break

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Process commands from edited messages"""
    if after.author.bot:
        return

    # Only process if the content actually changed
    if before.content != after.content:
        # Apply same space handling as on_message
        content = after.content

        mention_patterns = [f'<@{bot.user.id}>', f'<@!{bot.user.id}>']
        for pattern in mention_patterns:
            if content.startswith(pattern):
                remaining = content[len(pattern):].lstrip()
                if remaining:
                    after.content = f'{pattern} {remaining}'
                break
        else:
            for prefix in config.PREFIX:
                if content.startswith(prefix):
                    remaining = content[len(prefix):].lstrip()
                    if remaining:
                        after.content = f'{prefix}{remaining}'
                    break

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

    # Set Jishaku environment variables (optional customization)
    os.environ["JISHAKU_NO_UNDERSCORE"] = "True"  # Disables underscore prefix requirement
    os.environ["JISHAKU_HIDE"] = "True"  # Hides jishaku from help command

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
