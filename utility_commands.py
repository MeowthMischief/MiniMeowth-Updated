import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
from config import EMBED_COLOR

# Emoji Configuration (centralized for easy changes)
EMOJI_INCENSE = "<:incense:1450840364499075164>"
EMOJI_REDEEM = "<:redeem:1450840362288414821>"
EMOJI_POKECOINS = "<:pokecoins:1450840388100292689>"
EMOJI_SHARDS = "<:shards:1450840370039488524>"
EMOJI_POKEBALL = "<a:pokeball:1450840367552532510>"
EMOJI_TICK = "<:white_check_mark:1449749985057964094>"
EMOJI_CROSS = "<:cross_mark:1449750002388959377>"
EMOJI_GREEN_DOT = "<:green_dot:1450840704153686139>"

# Global variables to track active commands
active_track_commands = {}

class UtilityCommands(commands.Cog):
    """Utility commands for text formatting and currency conversion"""

    def __init__(self, bot):
        self.bot = bot

    # ==================== Event Listeners ====================

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle responses from Pokétwo for track command"""
        if message.author.id != 716390085896962058:  # Pokétwo bot ID
            return

        channel_id = message.channel.id

        if channel_id not in active_track_commands:
            return

        command_data = active_track_commands[channel_id]

        if command_data.get('status') != 'sending':
            return

        # Check for the "currently running another command" error
        if message.embeds:
            for embed in message.embeds:
                if embed.description and "You are currently running another command" in embed.description:
                    return

        if message.content and "You are currently running another command" in message.content:
            return

        # Handle next command in sequence
        command_data['current_index'] += 1

        if command_data['current_index'] < len(command_data['pokemon_ids']):
            await self._send_next_track_command(message.channel, command_data)
        else:
            await self._finish_track_sequence(message.channel, command_data)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reactions to start sending tracked commands"""
        if user.bot or str(reaction.emoji) != '✅':
            return

        channel_id = reaction.message.channel.id
        if channel_id not in active_track_commands:
            return

        command_data = active_track_commands[channel_id]

        if (command_data.get('status') != 'tracking' or
            user.id != command_data['user_id'] or
            reaction.message.id != command_data['tracking_message_id']):
            return

        await self._start_track_sending(reaction.message.channel, command_data)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Handle message edits to update tracked Pokemon IDs"""
        await self._handle_track_update(after)

    # ==================== Track Command ====================

    @commands.command(name='track')
    async def track(self, ctx, *, command_template: str):
        """
        Track Pokemon IDs from an editing list and send commands when ready
        Usage: ?track <command with (id) placeholder>
        Example: ?track p!select (id)

        Reply to a Pokétwo list message, then react with ✅ when done editing.
        """
        if not ctx.message.reference:
            return await self._send_error(ctx, "Please reply to a Pokétwo list message!")

        if ctx.channel.id in active_track_commands:
            return await self._send_error(ctx, "There's already an active track command in this channel! Use `?stoptrack` first.")

        if '(id)' not in command_template:
            return await self._send_error(ctx, "Command template must contain `(id)` placeholder!\nExample: `?track p!select (id)`")

        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            if not await self._validate_poketwo_message(replied_message, "pokémon", check_description=True):
                return await self._send_error(ctx, "Please reply to a Pokétwo pokémon list message!")

            # Extract initial Pokemon IDs
            pokemon_ids = self._extract_pokemon_ids(replied_message.embeds[0].description)

            # Create tracking message
            embed = discord.Embed(
                description=f"{EMOJI_TICK} Started tracking! React with ✅ when done editing.\nCommand: `{command_template}`\nIDs collected: {len(pokemon_ids)}",
                color=EMBED_COLOR
            )
            tracking_msg = await ctx.reply(embed=embed, mention_author=False)
            await tracking_msg.add_reaction('✅')

            # Store track command data
            active_track_commands[ctx.channel.id] = {
                'pokemon_ids': pokemon_ids.copy(),
                'template': command_template,
                'user_id': ctx.author.id,
                'monitoring_message_id': replied_message.id,
                'tracking_message_id': tracking_msg.id,
                'status': 'tracking',
                'current_index': 0,
                'total_count': 0
            }

            # Set timeout
            asyncio.create_task(self._track_timeout(ctx.channel.id, tracking_msg))

        except Exception as e:
            await self._send_error(ctx, f"An error occurred: {str(e)}")

    @commands.command(name='stoptrack')
    async def stoptrack(self, ctx):
        """Stop the active track command in this channel"""
        if ctx.channel.id in active_track_commands:
            del active_track_commands[ctx.channel.id]
            await self._send_success(ctx, "Stopped active track command!")
        else:
            await self._send_error(ctx, "No active track command in this channel!")

    # ==================== Prefix Command ====================

    @commands.command(name='prefix')
    async def prefix_command(self, ctx, pattern: str, *, items: str):
        """
        Add a prefix pattern to comma-separated items
        Usage: ?prefix "<pattern>" item1, item2, item3
        Example: ?prefix "--n" abra, kadabra, alakazam
        Result: --n abra --n kadabra --n alakazam

        The pattern in quotes will replace each comma.
        Extra spaces are automatically normalized.
        """
        # Split by comma and strip whitespace from each item
        item_list = [item.strip() for item in items.split(',') if item.strip()]

        if not item_list:
            return await self._send_error(ctx, "No items found! Use format: `?prefix \"--n\" item1, item2, item3`")

        # Build result with pattern before each item
        result = ' '.join([f"{pattern} {item}" for item in item_list])

        # Send result (split if too long)
        await self._send_long_message(ctx, result)

    # ==================== Convert Slash Command ====================

    @app_commands.command(name="convert", description="Convert between PC, Shards, Redeems, and Incenses")
    @app_commands.describe(
        choice="What currency to convert from",
        amount="Amount to convert"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="PC", value="pc"),
        app_commands.Choice(name="Shards", value="shards"),
        app_commands.Choice(name="Redeems", value="redeems"),
        app_commands.Choice(name="Incenses", value="incenses")
    ])
    async def convert_command(self, interaction: discord.Interaction, 
                              choice: app_commands.Choice[str], amount: int):
        """Convert between different currencies"""

        if amount <= 0:
            await interaction.response.send_message(
                "Amount must be greater than 0!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{EMOJI_POKEBALL} Currency Converter", 
            color=EMBED_COLOR
        )
        embed.add_field(name="Input", value=f"{amount:,} {choice.name}", inline=False)

        if choice.value == "pc":
            shards = amount // 200
            redeems = shards // 200
            incenses = amount // 10000

            embed.add_field(name=f"{EMOJI_SHARDS} Shards", value=f"{shards:,}", inline=True)
            embed.add_field(name=f"{EMOJI_REDEEM} Redeems", value=f"{redeems:,}", inline=True)
            embed.add_field(name=f"{EMOJI_INCENSE} Incenses", value=f"{incenses:,}", inline=True)

        elif choice.value == "shards":
            pc = amount * 200
            redeems = amount // 200
            incenses = amount // 50

            embed.add_field(name=f"{EMOJI_POKECOINS} PC", value=f"{pc:,}", inline=True)
            embed.add_field(name=f"{EMOJI_REDEEM} Redeems", value=f"{redeems:,}", inline=True)
            embed.add_field(name=f"{EMOJI_INCENSE} Incenses", value=f"{incenses:,}", inline=True)

        elif choice.value == "redeems":
            shards_standard = amount * 200
            shards_discounted = (amount * 38000) // 200
            pc_standard = shards_standard * 200
            pc_discounted = amount * 38000
            incenses_standard = shards_standard // 50
            incenses_discounted = shards_discounted // 50

            embed.add_field(
                name=f"{EMOJI_SHARDS} Shards (Standard Rate)",
                value=f"{shards_standard:,}",
                inline=True
            )
            embed.add_field(
                name=f"{EMOJI_SHARDS} Shards (Discounted Rate)",
                value=f"{shards_discounted:,}",
                inline=True
            )
            embed.add_field(name="\u200b", value="\u200b", inline=False)

            embed.add_field(
                name=f"{EMOJI_POKECOINS} PC (Standard Rate)",
                value=f"{pc_standard:,}",
                inline=True
            )
            embed.add_field(
                name=f"{EMOJI_POKECOINS} PC (Discounted Rate)",
                value=f"{pc_discounted:,}",
                inline=True
            )
            embed.add_field(name="\u200b", value="\u200b", inline=False)

            embed.add_field(
                name=f"{EMOJI_INCENSE} Incenses (Standard Rate)",
                value=f"{incenses_standard:,}",
                inline=True
            )
            embed.add_field(
                name=f"{EMOJI_INCENSE} Incenses (Discounted Rate)",
                value=f"{incenses_discounted:,}",
                inline=True
            )

            embed.add_field(
                name=f"{EMOJI_GREEN_DOT} Note",
                value="Standard: 1 Redeem = 200 Shards = 40,000 PC\nDiscounted: 1 Redeem = 190 Shards = 38,000 PC",
                inline=False
            )

        elif choice.value == "incenses":
            pc = amount * 10000
            shards = amount * 50
            redeems = shards // 200

            embed.add_field(name=f"{EMOJI_POKECOINS} PC", value=f"{pc:,}", inline=True)
            embed.add_field(name=f"{EMOJI_SHARDS} Shards", value=f"{shards:,}", inline=True)
            embed.add_field(name=f"{EMOJI_REDEEM} Redeems", value=f"{redeems:,}", inline=True)

        embed.set_footer(
            text="Rates: 1 Shard = 200 PC | 1 Redeem = 200 Shards | 1 Incense = 50 Shards = 10,000 PC"
        )

        await interaction.response.send_message(embed=embed)

    # ==================== Replace Slash Command ====================

    @app_commands.command(name="replace", description="Replace or remove phrases from text")
    @app_commands.describe(
        old_word="The phrase to find and replace/remove",
        text="The text to search in",
        new_word="The phrase to replace with (leave empty to remove)"
    )
    async def replace_slash(self, interaction: discord.Interaction, 
                           old_word: str, text: str, new_word: str = None):
        """Replace or remove phrases from text"""

        replacement = new_word if new_word is not None else ""
        escaped_old = re.escape(old_word)

        is_word_only = bool(re.match(r'^\w+(\s+\w+)*$', old_word))

        if is_word_only:
            pattern = re.compile(r'\b' + escaped_old + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(escaped_old, re.IGNORECASE)

        if not pattern.search(text):
            await interaction.response.send_message(
                f'"{old_word}" was not found in the text', ephemeral=False)
            return

        result = pattern.sub(replacement, text)
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()

        if not result:
            result = "(empty)"

        if len(result) <= 2000:
            await interaction.response.send_message(result)
        else:
            await interaction.response.send_message(result[:2000])
            remaining = result[2000:]
            while remaining:
                chunk = remaining[:2000]
                await interaction.followup.send(chunk)
                remaining = remaining[2000:]

    # ==================== Helper Methods ====================

    async def _validate_poketwo_message(self, message, title_keyword: str = None, 
                                       check_description: bool = False) -> bool:
        """Validate if message is from Pokétwo with proper embed"""
        if message.author.id != 716390085896962058 or not message.embeds:
            return False

        embed = message.embeds[0]

        if title_keyword and (not embed.title or title_keyword.lower() not in embed.title.lower()):
            return False

        if check_description and not embed.description:
            return False

        return True

    def _extract_pokemon_ids(self, description: str) -> list:
        """Extract Pokemon IDs from embed description"""
        pokemon_ids = []
        for line in description.split('\n'):
            if '•' in line:
                id_part = line.split('　')[0] if '　' in line else line.split()[0]
                id_match = id_part.replace('**', '').replace('`', '').strip()
                pokemon_ids.append(id_match)
        return pokemon_ids

    async def _handle_track_update(self, message: discord.Message):
        """Handle updates to tracked messages"""
        for channel_id, track_data in list(active_track_commands.items()):
            if (track_data.get('monitoring_message_id') != message.id or 
                track_data.get('status') != 'tracking'):
                continue

            if message.author.id != 716390085896962058 or not message.embeds:
                continue

            embed = message.embeds[0]
            if not embed.title or "pokémon" not in embed.title.lower() or not embed.description:
                continue

            new_ids = self._extract_pokemon_ids(embed.description)

            # Add only new IDs
            added_count = 0
            for pokemon_id in new_ids:
                if pokemon_id not in track_data['pokemon_ids']:
                    track_data['pokemon_ids'].append(pokemon_id)
                    added_count += 1

            # Update tracking message
            if added_count > 0:
                try:
                    tracking_msg = await self.bot.get_channel(channel_id).fetch_message(
                        track_data['tracking_message_id'])
                    embed = discord.Embed(
                        description=f"{EMOJI_TICK} Started tracking! React with ✅ when done editing.\nCommand: `{track_data['template']}`\nIDs collected: {len(track_data['pokemon_ids'])}",
                        color=EMBED_COLOR
                    )
                    await tracking_msg.edit(embed=embed)
                except:
                    pass

    async def _start_track_sending(self, channel, command_data):
        """Start sending tracked commands"""
        if not command_data['pokemon_ids']:
            embed = discord.Embed(
                description=f"{EMOJI_CROSS} No Pokemon IDs were collected!",
                color=EMBED_COLOR
            )
            await channel.send(embed=embed)
            del active_track_commands[channel.id]
            return

        command_data['status'] = 'sending'
        command_data['current_index'] = 0
        command_data['total_count'] = len(command_data['pokemon_ids'])

        first_id = command_data['pokemon_ids'][0]
        command = command_data['template'].replace('(id)', first_id)
        await channel.send(f"```{command}```")

        embed = discord.Embed(
            description=f"{EMOJI_TICK} Started sending commands! Total IDs: {len(command_data['pokemon_ids'])}",
            color=EMBED_COLOR
        )
        await channel.send(embed=embed)

    async def _send_next_track_command(self, channel, command_data):
        """Send the next command in track sequence"""
        next_id = command_data['pokemon_ids'][command_data['current_index']]
        template = command_data['template']
        command = template.replace('(id)', next_id)
        await channel.send(f"```{command}```")

    async def _finish_track_sequence(self, channel, command_data):
        """Finish track command sequence and cleanup"""
        total = command_data['total_count']
        await channel.send(f"{EMOJI_TICK} All commands completed! Total: {total}")
        del active_track_commands[channel.id]

    async def _track_timeout(self, channel_id: int, tracking_message: discord.Message):
        """Cancel track command after 3 minutes"""
        await asyncio.sleep(180)

        if channel_id in active_track_commands and active_track_commands[channel_id].get('status') == 'tracking':
            embed = discord.Embed(
                description="⏱️ Track command timed out after 3 minutes!",
                color=EMBED_COLOR
            )
            try:
                await tracking_message.edit(embed=embed)
            except:
                pass
            del active_track_commands[channel_id]

    async def _send_long_message(self, ctx, text: str):
        """Send long text, splitting if necessary"""
        if len(text) <= 1900:
            await ctx.channel.send(text)
        else:
            # Find a good split point
            mid_point = len(text) // 2
            while mid_point < len(text) and text[mid_point] != ' ':
                mid_point += 1

            part1 = text[:mid_point]
            part2 = text[mid_point:].strip()

            await ctx.channel.send(part1)
            await ctx.channel.send(part2)

    async def _send_error(self, ctx, message: str):
        """Send error embed"""
        embed = discord.Embed(description=f"{EMOJI_CROSS} {message}", color=EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    async def _send_success(self, ctx, message: str):
        """Send success embed"""
        embed = discord.Embed(description=f"{EMOJI_TICK} {message}", color=EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))
