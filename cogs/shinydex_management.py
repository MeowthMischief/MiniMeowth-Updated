import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import config
from config import EMBED_COLOR, POKETWO_BOT_ID
from database import db


class ShinyDexManagement(commands.Cog):
    """Manage your shiny Pokémon collection - add, remove, clear, stats"""

    def __init__(self, bot):
        self.bot = bot
        self.id_pattern = re.compile(r'\*?`\s*(\d+)\s*`\*?')
        self.name_pattern = re.compile(r'✨\s*([^<]+?)(?:\s*<:|$)')
        self.gender_pattern = re.compile(r'<:(male|female|unknown):')
        self.level_pattern = re.compile(r'Lvl\.\s*(\d+)')
        self.iv_pattern = re.compile(r'•\s*([\d.]+)%')

    async def add_shiny_context_callback(self, interaction: discord.Interaction, message: discord.Message):
        """Context menu command to add shinies from a message"""
        # Check if message is from Pokétwo
        if message.author.id != POKETWO_BOT_ID or not message.embeds:
            await interaction.response.send_message(
                "❌ Please use this on a Pokétwo shiny list message!",
                ephemeral=True
            )
            return

        utils = self.bot.get_cog('Utils')
        if not utils:
            await interaction.response.send_message("❌ Utils cog not loaded", ephemeral=True)
            return

        # Defer the response as ephemeral (works even in archived threads)
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        all_shinies = []
        processed_shiny_ids = set()
        total_found_in_embed = 0
        event_pokemon_count = 0

        # Process the first embed
        embed = message.embeds[0]
        if embed and embed.description:
            lines = embed.description.strip().split('\n')
            page_total = sum(1 for line in lines if '✨' in line)
            total_found_in_embed += page_total

            shinies = self.parse_shiny_embed(embed.description, utils)
            page_event_count = page_total - len(shinies)
            event_pokemon_count += page_event_count

            for shiny in shinies:
                if shiny['pokemon_id'] not in processed_shiny_ids:
                    all_shinies.append(shiny)
                    processed_shiny_ids.add(shiny['pokemon_id'])

        if total_found_in_embed == 0:
            await interaction.followup.send("❌ No shinies found to track!")
            return

        # Add shinies to database
        new_count = await db.add_shinies_bulk(user_id, all_shinies)
        total_in_inventory = await db.count_shinies(user_id)

        event_note = f"\n⚠️ **Event Pokémon Are Not Counted Towards Dex!**" if event_pokemon_count > 0 else ""

        # Create success embed
        result_embed = discord.Embed(title="✨ Shinies Added", color=EMBED_COLOR)
        result_embed.add_field(
            name="📊 Summary",
            value=f"**Total Shiny Tracked:** {total_found_in_embed} (including {event_pokemon_count} events)\n"
                  f"**Total Shiny Added:** {new_count}\n"
                  f"**Currently In Inventory:** {total_in_inventory}{event_note}",
            inline=False
        )

        await interaction.followup.send(embed=result_embed)

    async def remove_shiny_context_callback(self, interaction: discord.Interaction, message: discord.Message):
        """Context menu command to remove shinies from a message"""
        # Check if message is from Pokétwo
        if message.author.id != POKETWO_BOT_ID or not message.embeds:
            await interaction.response.send_message(
                "❌ Please use this on a Pokétwo shiny list message!",
                ephemeral=True
            )
            return

        # Defer the response as ephemeral (works even in archived threads)
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        all_ids = []

        # Process the embed and extract all Pokemon IDs
        embed = message.embeds[0]
        if embed and embed.description:
            lines = embed.description.strip().split('\n')

            for line in lines:
                # Extract ID using the same pattern
                id_match = self.id_pattern.search(line)
                if id_match:
                    try:
                        pokemon_id = int(id_match.group(1).strip())
                        all_ids.append(pokemon_id)
                    except ValueError:
                        continue

        if not all_ids:
            await interaction.followup.send("❌ No Pokemon IDs found in this message!")
            return

        # Remove the shinies
        removed_count = await db.remove_shinies(user_id, all_ids)
        total_in_inventory = await db.count_shinies(user_id)

        # Create success embed
        result_embed = discord.Embed(title="🗑️ Shinies Removed", color=EMBED_COLOR)
        result_embed.add_field(
            name="📊 Summary",
            value=f"**IDs Found in Message:** {len(all_ids)}\n"
                  f"**Shinies Removed:** {removed_count}\n"
                  f"**Currently In Inventory:** {total_in_inventory}",
            inline=False
        )

        if removed_count == 0:
            result_embed.add_field(
                name="ℹ️ Note",
                value="None of these IDs were in your tracked shinies.",
                inline=False
            )

        await interaction.followup.send(embed=result_embed)

    @commands.hybrid_command(name='trackshiny', aliases=['addshiny'])
    @app_commands.describe(message_ids="Message IDs to track shinies from (space-separated)")
    async def track_shiny(self, ctx, *, message_ids: str = None):
        """Track shinies from Pokétwo --sh embed messages"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        all_shinies = []
        processed_shiny_ids = set()
        monitored_message_id = None
        total_found_in_embed = 0
        event_pokemon_count = 0

        async def process_embed(embed):
            """Parse shiny embed and extract data"""
            nonlocal total_found_in_embed, event_pokemon_count

            if not embed or not embed.description:
                return 0

            # Count all lines with sparkles (including events)
            lines = embed.description.strip().split('\n')
            page_total = sum(1 for line in lines if '✨' in line)
            total_found_in_embed += page_total

            shinies = self.parse_shiny_embed(embed.description, utils)
            page_event_count = page_total - len(shinies)
            event_pokemon_count += page_event_count

            count = 0
            for shiny in shinies:
                if shiny['pokemon_id'] not in processed_shiny_ids:
                    all_shinies.append(shiny)
                    processed_shiny_ids.add(shiny['pokemon_id'])
                    count += 1

            return count

        # Check if replying to a message
        if ctx.message.reference and not message_ids:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)

                if replied_msg.author.id != POKETWO_BOT_ID or not replied_msg.embeds:
                    await ctx.send("❌ Please reply to a Pokétwo shiny list message!", reference=ctx.message, mention_author=False)
                    return

                await process_embed(replied_msg.embeds[0])
                monitored_message_id = replied_msg.id

            except Exception as e:
                await ctx.send(f"❌ Error fetching replied message: {str(e)}", reference=ctx.message, mention_author=False)
                return

        elif message_ids:
            message_ids_list = message_ids.split()
            for msg_id in message_ids_list:
                try:
                    msg = await ctx.channel.fetch_message(int(msg_id))
                    if msg.author.id == POKETWO_BOT_ID and msg.embeds:
                        await process_embed(msg.embeds[0])
                except:
                    continue

        if total_found_in_embed == 0:
            await ctx.send("❌ No shinies found to track!", reference=ctx.message, mention_author=False)
            return

        status_msg = await ctx.send(f"🔄 **Tracking shinies...**", reference=ctx.message, mention_author=False)

        # Add shinies to database
        new_count = await db.add_shinies_bulk(user_id, all_shinies)
        total_in_inventory = await db.count_shinies(user_id)

        event_note = f"\n⚠️ **Event Pokémon Are Not Counted Towards Dex!**" if event_pokemon_count > 0 else ""

        await status_msg.edit(
            content=f"✅ **Shiny Tracking In Progress**\n"
                    f"**Total Shiny Tracked:** {total_found_in_embed} (including {event_pokemon_count} events)\n"
                    f"**Total Shiny Added (excluding events):** {new_count}\n"
                    f"**Currently In Inventory:** {total_in_inventory}{event_note}\n\n"
                    f"💡 Keep clicking pages, I'll auto-detect more!"
        )

        # Monitor for page changes
        if monitored_message_id:
            def check(before, after):
                return (after.id == monitored_message_id and 
                       after.author.id == POKETWO_BOT_ID and 
                       after.embeds)

            timeout = 600
            start_time = asyncio.get_event_loop().time()
            last_update = start_time

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    wait_time = min(remaining, 30.0)
                    before, after = await self.bot.wait_for('message_edit', timeout=wait_time, check=check)

                    embed = after.embeds[0]
                    page_shinies = []

                    # Count total in this page
                    page_total = 0
                    if embed.description:
                        page_lines = embed.description.strip().split('\n')
                        page_total = sum(1 for line in page_lines if '✨' in line)

                    total_found_in_embed += page_total

                    shinies = self.parse_shiny_embed(embed.description, utils)
                    page_event_count = page_total - len(shinies)
                    event_pokemon_count += page_event_count

                    for shiny in shinies:
                        if shiny['pokemon_id'] not in processed_shiny_ids:
                            page_shinies.append(shiny)
                            processed_shiny_ids.add(shiny['pokemon_id'])
                            all_shinies.append(shiny)

                    if page_shinies:
                        page_new_count = await db.add_shinies_bulk(user_id, page_shinies)
                        new_count += page_new_count
                        last_update = asyncio.get_event_loop().time()
                        total_in_inventory = await db.count_shinies(user_id)

                        event_note = f"\n⚠️ **Event Pokémon Are Not Counted Towards Dex!**" if event_pokemon_count > 0 else ""

                        await status_msg.edit(
                            content=f"✅ **Page detected! Adding more shinies**\n"
                                    f"**Total Shiny Tracked:** {total_found_in_embed} (including {event_pokemon_count} events)\n"
                                    f"**Total Shiny Added:** {new_count}\n"
                                    f"**Currently In Inventory:** {total_in_inventory}{event_note}\n\n"
                                    f"💡 Keep clicking for more!"
                        )

                except asyncio.TimeoutError:
                    if asyncio.get_event_loop().time() - last_update > 15:
                        break
                    continue

        # Final summary
        embed = discord.Embed(title="✨ Shiny Tracking Complete", color=EMBED_COLOR)
        total_processed = len(all_shinies)
        duplicates = total_processed - new_count

        summary_text = (
            f"**Total Shiny Tracked:** {total_found_in_embed} (including {event_pokemon_count} events)\n"
            f"**Total Shiny Added:** {new_count}\n"
            f"**Currently In Inventory:** {total_in_inventory}\n"
            f"**Duplicates Ignored:** {duplicates}"
        )

        if event_pokemon_count > 0:
            summary_text += f"\n\n⚠️ **Event Pokémon Are Not Counted Towards Dex!**"

        embed.add_field(
            name="📊 Summary",
            value=summary_text,
            inline=False
        )

        await status_msg.edit(content="", embed=embed)

    def parse_shiny_embed(self, description: str, utils):
        """Parse Pokétwo shiny embed to extract shiny data"""
        if not description:
            return []

        shinies = []
        lines = description.strip().split('\n')

        for line in lines:
            # Skip lines without sparkles emoji
            if '✨' not in line:
                continue

            try:
                # Extract ID
                id_match = self.id_pattern.search(line)
                if not id_match:
                    continue
                pokemon_id = int(id_match.group(1).strip())

                # Extract everything between > and <: (gender emoji)
                name_match = re.search(r'>\s*(.+?)\s*<:(?:male|female|unknown):', line)
                if not name_match:
                    continue

                pokemon_name = name_match.group(1).strip()

                # Remove Gigantamax emoji specifically first
                pokemon_name = pokemon_name.replace('<:_:1242455099213877248>', '').strip()

                # Remove sparkles emoji
                pokemon_name = pokemon_name.replace('✨', '').strip()

                # Remove any other Discord emojis
                pokemon_name = re.sub(r'<a?:[^:]*:\d+>', '', pokemon_name).strip()

                # Clean up extra whitespace
                pokemon_name = ' '.join(pokemon_name.split()).strip()

                # Extract gender
                gender_match = self.gender_pattern.search(line)
                gender = gender_match.group(1) if gender_match else 'unknown'

                # Extract level
                level_match = self.level_pattern.search(line)
                level = int(level_match.group(1)) if level_match else 1

                # Extract IV
                iv_match = self.iv_pattern.search(line)
                iv_percent = float(iv_match.group(1)) if iv_match else 0.0

                # FIXED: Check if Pokemon name exists in the regular dex CSV first
                # This prevents event Pokemon from being added with wrong dex numbers
                if pokemon_name not in utils.dex_data:
                    # Pokemon not in regular dex CSV - skip it (event Pokemon, etc.)
                    continue

                # Get dex number from utils (now safe since we know it exists in CSV)
                dex_number = utils.get_dex_number(pokemon_name)

                shinies.append({
                    'pokemon_id': pokemon_id,
                    'name': pokemon_name,
                    'gender': gender,
                    'level': level,
                    'iv_percent': iv_percent,
                    'dex_number': dex_number
                })

            except (ValueError, AttributeError):
                continue

        return shinies

    @commands.hybrid_command(name='removeshiny', aliases=['rmshiny'])
    @app_commands.describe(pokemon_ids="Shiny Pokemon IDs to remove (space-separated)")
    async def remove_shiny(self, ctx, *, pokemon_ids: str):
        """Remove shinies by their IDs"""
        if not pokemon_ids:
            await ctx.send("❌ Please provide Pokemon IDs to remove", reference=ctx.message, mention_author=False)
            return

        try:
            ids = [int(pid) for pid in pokemon_ids.split()]
        except ValueError:
            await ctx.send("❌ Invalid Pokemon IDs provided", reference=ctx.message, mention_author=False)
            return

        count = await db.remove_shinies(ctx.author.id, ids)

        if count > 0:
            await ctx.send(f"✅ Removed **{count}** shinies from tracking", reference=ctx.message, mention_author=False)
        else:
            await ctx.send("❌ No shinies found with those IDs", reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='clearshiny')
    async def clear_shiny(self, ctx):
        """Clear all tracked shinies"""
        user_id = ctx.author.id

        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30.0)
                self.value = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
            async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ Not your confirmation!", ephemeral=True)
                    return
                self.value = True
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
            async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ Not your confirmation!", ephemeral=True)
                    return
                self.value = False
                self.stop()
                await interaction.response.defer()

        view = ConfirmView()
        await ctx.send(
            f"⚠️ **WARNING:** Delete ALL tracked shinies?\n"
            f"⚠️ **IMPORTANT:** This will NOT affect your actual Pokémon in Pokétwo!\n"
            f"Click Confirm or Cancel (30s)",
            reference=ctx.message, mention_author=False, view=view
        )
        await view.wait()

        if view.value is True:
            count = await db.clear_all_shinies(user_id)
            await ctx.send(f"🗑️ Cleared **{count}** tracked shinies")
        elif view.value is False:
            await ctx.send("❌ Clear cancelled")
        else:
            await ctx.send("⏰ Confirmation timed out")

    @commands.hybrid_command(name='shinystats')
    async def shiny_stats(self, ctx):
        """View statistics about your shiny collection"""
        user_id = ctx.author.id
        utils = self.bot.get_cog('Utils')

        # Get all shinies
        all_shinies = await db.get_all_shinies(user_id)

        if not all_shinies:
            await ctx.send("❌ You haven't tracked any shinies yet!\nUse `?trackshiny` to get started.", 
                          reference=ctx.message, mention_author=False)
            return

        # Calculate stats
        total_tracked = len(all_shinies)

        # Basic Dex: unique dex numbers (count all Pokemon with same dex number)
        unique_dex = len(set(s['dex_number'] for s in all_shinies))

        # Full Dex: Count unique (dex_number, name, gender) combinations based on CSV
        unique_forms_set = set()
        for shiny in all_shinies:
            dex_num = shiny['dex_number']
            name = shiny['name']
            gender = shiny['gender']

            # Check if this specific name has gender difference in CSV
            has_gender_diff = utils.has_gender_difference(name)

            if has_gender_diff and gender in ['male', 'female']:
                # Track with gender
                unique_forms_set.add((dex_num, name, gender))
            else:
                # Track without gender
                unique_forms_set.add((dex_num, name, None))

        unique_forms = len(unique_forms_set)

        # Gender breakdown
        males = sum(1 for s in all_shinies if s['gender'] == 'male')
        females = sum(1 for s in all_shinies if s['gender'] == 'female')
        unknown = sum(1 for s in all_shinies if s['gender'] == 'unknown')

        # IV stats
        ivs = [s['iv_percent'] for s in all_shinies]
        avg_iv = sum(ivs) / len(ivs) if ivs else 0
        max_iv = max(ivs) if ivs else 0
        min_iv = min(ivs) if ivs else 0

        # Non-zero lowest IV
        non_zero_ivs = [iv for iv in ivs if iv > 0]
        min_non_zero_iv = min(non_zero_ivs) if non_zero_ivs else 0

        # Get total counts from CSV
        total_unique_dex = utils.get_total_unique_dex()
        total_forms_count = utils.get_total_forms_count()

        # Completion percentages
        basic_completion = (unique_dex / total_unique_dex) * 100 if total_unique_dex > 0 else 0
        full_completion = (unique_forms / total_forms_count) * 100 if total_forms_count > 0 else 0

        embed = discord.Embed(
            title="✨ Shiny Collection Statistics",
            color=EMBED_COLOR
        )

        # Set author with user's avatar
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )

        # Collection Overview field
        embed.add_field(
            name="📊 Collection Overview",
            value=f"**Total Non-Event Shiny:** {total_tracked}\n"
                  f"> **Basic Dex:** {unique_dex}/{total_unique_dex} ({basic_completion:.1f}%)\n"
                  f"> **Full Dex:** {unique_forms}/{total_forms_count} ({full_completion:.1f}%)\n"
                  f"> **Males:** {males}\n"
                  f"> **Females:** {females}\n"
                  f"> **Unknown:** {unknown}",
            inline=True
        )

        # IV Statistics field - only show "Lowest Non-Zero" if different from "Lowest"
        iv_stats_text = f"**Average:** {avg_iv:.2f}%\n> **Highest:** {max_iv:.2f}%\n> **Lowest:** {min_iv:.2f}%"

        # Only add "Lowest Non-Zero" if it's different from the regular lowest
        if min_non_zero_iv != min_iv:
            iv_stats_text += f"\n> **Lowest Non-Zero:** {min_non_zero_iv:.2f}%"

        embed.add_field(
            name="📈 IV Statistics",
            value=iv_stats_text,
            inline=True
        )

        # Find most common shinies
        from collections import Counter
        name_counts = Counter(s['name'] for s in all_shinies)
        most_common = name_counts.most_common(5)

        if most_common:
            medals = ["> 🥇", "> 🥈", "> 🥉", "> ", "> "]
            common_str = "\n".join(f"{medals[i]}  **{name}:** {count}x" for i, (name, count) in enumerate(most_common))
            embed.add_field(
                name="🏆 Most Collected",
                value=common_str,
                inline=False
            )

        embed.set_footer(text="⚠️ Note: Reindexing in Pokétwo may break ID tracking!")

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)


async def setup(bot):
    cog = ShinyDexManagement(bot)

    # Add context menu commands
    add_context_menu = app_commands.ContextMenu(
        name="Add Shiny",
        callback=cog.add_shiny_context_callback
    )
    bot.tree.add_command(add_context_menu)

    remove_context_menu = app_commands.ContextMenu(
        name="Remove Shiny",
        callback=cog.remove_shiny_context_callback
    )
    bot.tree.add_command(remove_context_menu)

    await bot.add_cog(cog)
