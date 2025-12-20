import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import config
from config import EMBED_COLOR, POKETWO_BOT_ID
from database import db


class EventDexManagement(commands.Cog):
    """Manage your event shiny Pokémon collection"""

    def __init__(self, bot):
        self.bot = bot
        self.id_pattern = re.compile(r'\*?`\s*(\d+)\s*`\*?')
        self.name_pattern = re.compile(r'✨\s*([^<]+?)(?:\s*<:|$)')
        self.gender_pattern = re.compile(r'<:(male|female|unknown):')
        self.level_pattern = re.compile(r'Lvl\.\s*(\d+)')
        self.iv_pattern = re.compile(r'•\s*([\d.]+)%')

    async def add_event_context_callback(self, interaction: discord.Interaction, message: discord.Message):
        """Context menu command to add event shinies from a message"""
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

        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        all_shinies = []
        processed_shiny_ids = set()
        total_found_in_embed = 0

        embed = message.embeds[0]
        if embed and embed.description:
            lines = embed.description.strip().split('\n')
            page_total = sum(1 for line in lines if '✨' in line)
            total_found_in_embed += page_total

            shinies = self.parse_event_shiny_embed(embed.description, utils)

            for shiny in shinies:
                if shiny['pokemon_id'] not in processed_shiny_ids:
                    all_shinies.append(shiny)
                    processed_shiny_ids.add(shiny['pokemon_id'])

        if total_found_in_embed == 0:
            await interaction.followup.send("❌ No event shinies found to track!")
            return

        new_count = await db.add_event_shinies_bulk(user_id, all_shinies)
        total_in_inventory = await db.count_event_shinies(user_id)

        result_embed = discord.Embed(title="✨ Event Shinies Added", color=EMBED_COLOR)
        result_embed.add_field(
            name="📊 Summary",
            value=f"**Total Event Shinies Tracked:** {total_found_in_embed}\n"
                  f"**Total Event Shinies Added:** {new_count}\n"
                  f"**Currently In Inventory:** {total_in_inventory}",
            inline=False
        )

        await interaction.followup.send(embed=result_embed)

    async def remove_event_context_callback(self, interaction: discord.Interaction, message: discord.Message):
        """Context menu command to remove event shinies from a message"""
        if message.author.id != POKETWO_BOT_ID or not message.embeds:
            await interaction.response.send_message(
                "❌ Please use this on a Pokétwo shiny list message!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        all_ids = []

        embed = message.embeds[0]
        if embed and embed.description:
            lines = embed.description.strip().split('\n')

            for line in lines:
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

        removed_count = await db.remove_event_shinies(user_id, all_ids)
        total_in_inventory = await db.count_event_shinies(user_id)

        result_embed = discord.Embed(title="🗑️ Event Shinies Removed", color=EMBED_COLOR)
        result_embed.add_field(
            name="📊 Summary",
            value=f"**IDs Found in Message:** {len(all_ids)}\n"
                  f"**Event Shinies Removed:** {removed_count}\n"
                  f"**Currently In Inventory:** {total_in_inventory}",
            inline=False
        )

        if removed_count == 0:
            result_embed.add_field(
                name="ℹ️ Note",
                value="None of these IDs were in your tracked event shinies.",
                inline=False
            )

        await interaction.followup.send(embed=result_embed)

    @commands.hybrid_command(name='trackevent', aliases=['addevent'])
    @app_commands.describe(message_ids="Message IDs to track event shinies from (space-separated)")
    async def track_event(self, ctx, *, message_ids: str = None):
        """Track event shinies from Pokétwo --sh embed messages"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        all_shinies = []
        processed_shiny_ids = set()
        monitored_message_id = None
        total_found_in_embed = 0

        async def process_embed(embed):
            nonlocal total_found_in_embed

            if not embed or not embed.description:
                return 0

            lines = embed.description.strip().split('\n')
            page_total = sum(1 for line in lines if '✨' in line)
            total_found_in_embed += page_total

            shinies = self.parse_event_shiny_embed(embed.description, utils)

            count = 0
            for shiny in shinies:
                if shiny['pokemon_id'] not in processed_shiny_ids:
                    all_shinies.append(shiny)
                    processed_shiny_ids.add(shiny['pokemon_id'])
                    count += 1

            return count

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
            await ctx.send("❌ No event shinies found to track!", reference=ctx.message, mention_author=False)
            return

        status_msg = await ctx.send(f"🔄 **Tracking event shinies...**", reference=ctx.message, mention_author=False)

        new_count = await db.add_event_shinies_bulk(user_id, all_shinies)
        total_in_inventory = await db.count_event_shinies(user_id)

        await status_msg.edit(
            content=f"✅ **Event Shiny Tracking In Progress**\n"
                    f"**Total Event Shinies Tracked:** {total_found_in_embed}\n"
                    f"**Total Event Shinies Added:** {new_count}\n"
                    f"**Currently In Inventory:** {total_in_inventory}\n\n"
                    f"💡 Keep clicking pages, I'll auto-detect more!"
        )

        if monitored_message_id:
            def check(before, after):
                return (after.id == monitored_message_id and 
                       after.author.id == POKETWO_BOT_ID and 
                       after.embeds)

            timeout = 300
            start_time = asyncio.get_event_loop().time()
            last_update = start_time

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    wait_time = min(remaining, 30.0)
                    before, after = await self.bot.wait_for('message_edit', timeout=wait_time, check=check)

                    embed = after.embeds[0]
                    page_shinies = []

                    page_total = 0
                    if embed.description:
                        page_lines = embed.description.strip().split('\n')
                        page_total = sum(1 for line in page_lines if '✨' in line)

                    total_found_in_embed += page_total

                    shinies = self.parse_event_shiny_embed(embed.description, utils)

                    for shiny in shinies:
                        if shiny['pokemon_id'] not in processed_shiny_ids:
                            page_shinies.append(shiny)
                            processed_shiny_ids.add(shiny['pokemon_id'])
                            all_shinies.append(shiny)

                    if page_shinies:
                        page_new_count = await db.add_event_shinies_bulk(user_id, page_shinies)
                        new_count += page_new_count
                        last_update = asyncio.get_event_loop().time()
                        total_in_inventory = await db.count_event_shinies(user_id)

                        await status_msg.edit(
                            content=f"✅ **Page detected! Adding more event shinies**\n"
                                    f"**Total Event Shinies Tracked:** {total_found_in_embed}\n"
                                    f"**Total Event Shinies Added:** {new_count}\n"
                                    f"**Currently In Inventory:** {total_in_inventory}\n\n"
                                    f"💡 Keep clicking for more!"
                        )

                except asyncio.TimeoutError:
                    if asyncio.get_event_loop().time() - last_update > 15:
                        break
                    continue

        embed = discord.Embed(title="✨ Event Shiny Tracking Complete", color=EMBED_COLOR)
        total_processed = len(all_shinies)
        duplicates = total_processed - new_count

        summary_text = (
            f"**Total Event Shinies Tracked:** {total_found_in_embed}\n"
            f"**Total Event Shinies Added:** {new_count}\n"
            f"**Currently In Inventory:** {total_in_inventory}\n"
            f"**Duplicates Ignored:** {duplicates}"
        )

        embed.add_field(
            name="📊 Summary",
            value=summary_text,
            inline=False
        )

        await status_msg.edit(content="", embed=embed)

    def parse_event_shiny_embed(self, description: str, utils):
        """Parse Pokétwo shiny embed to extract event shiny data"""
        if not description:
            return []

        shinies = []
        lines = description.strip().split('\n')

        for line in lines:
            if '✨' not in line:
                continue

            try:
                id_match = self.id_pattern.search(line)
                if not id_match:
                    continue
                pokemon_id = int(id_match.group(1).strip())

                name_match = re.search(r'>\s*(.+?)\s*<:(?:male|female|unknown):', line)
                if not name_match:
                    continue

                pokemon_name = name_match.group(1).strip()
                pokemon_name = pokemon_name.replace('<:_:1242455099213877248>', '').strip()
                pokemon_name = pokemon_name.replace('✨', '').strip()
                pokemon_name = re.sub(r'<a?:[^:]*:\d+>', '', pokemon_name).strip()
                pokemon_name = ' '.join(pokemon_name.split()).strip()

                gender_match = self.gender_pattern.search(line)
                gender = gender_match.group(1) if gender_match else 'unknown'

                level_match = self.level_pattern.search(line)
                level = int(level_match.group(1)) if level_match else 1

                iv_match = self.iv_pattern.search(line)
                iv_percent = float(iv_match.group(1)) if iv_match else 0.0

                # Check if it's an event Pokemon
                if not utils.is_event_pokemon(pokemon_name):
                    continue

                shinies.append({
                    'pokemon_id': pokemon_id,
                    'name': pokemon_name,
                    'gender': gender,
                    'level': level,
                    'iv_percent': iv_percent
                })

            except (ValueError, AttributeError):
                continue

        return shinies

    @commands.hybrid_command(name='removeevent', aliases=['rmevent'])
    @app_commands.describe(pokemon_ids="Event Pokemon IDs to remove (space-separated)")
    async def remove_event(self, ctx, *, pokemon_ids: str):
        """Remove event shinies by their IDs"""
        if not pokemon_ids:
            await ctx.send("❌ Please provide Pokemon IDs to remove", reference=ctx.message, mention_author=False)
            return

        try:
            ids = [int(pid) for pid in pokemon_ids.split()]
        except ValueError:
            await ctx.send("❌ Invalid Pokemon IDs provided", reference=ctx.message, mention_author=False)
            return

        count = await db.remove_event_shinies(ctx.author.id, ids)

        if count > 0:
            await ctx.send(f"✅ Removed **{count}** event shinies from tracking", reference=ctx.message, mention_author=False)
        else:
            await ctx.send("❌ No event shinies found with those IDs", reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='clearevent')
    async def clear_event(self, ctx):
        """Clear all tracked event shinies"""
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
            f"⚠️ **WARNING:** Delete ALL tracked event shinies?\n"
            f"⚠️ **IMPORTANT:** This will NOT affect your actual Pokémon in Pokétwo!\n"
            f"Click Confirm or Cancel (30s)",
            reference=ctx.message, mention_author=False, view=view
        )
        await view.wait()

        if view.value is True:
            count = await db.clear_all_event_shinies(user_id)
            await ctx.send(f"🗑️ Cleared **{count}** tracked event shinies")
        elif view.value is False:
            await ctx.send("❌ Clear cancelled")
        else:
            await ctx.send("⏰ Confirmation timed out")

    @commands.hybrid_command(name='eventstats')
    async def event_stats(self, ctx):
        """View statistics about your event shiny collection"""
        user_id = ctx.author.id
        utils = self.bot.get_cog('Utils')

        all_shinies = await db.get_all_event_shinies(user_id)

        if not all_shinies:
            await ctx.send("❌ You haven't tracked any event shinies yet!\nUse `?trackevent` to get started.", 
                          reference=ctx.message, mention_author=False)
            return

        total_tracked = len(all_shinies)

        # Count unique forms
        unique_forms_set = set()
        for shiny in all_shinies:
            name = shiny['name']
            gender = shiny['gender']

            has_gender_diff = utils.has_gender_difference_event(name)

            if has_gender_diff and gender in ['male', 'female']:
                unique_forms_set.add((name, gender))
            else:
                unique_forms_set.add((name, None))

        unique_forms = len(unique_forms_set)

        males = sum(1 for s in all_shinies if s['gender'] == 'male')
        females = sum(1 for s in all_shinies if s['gender'] == 'female')
        unknown = sum(1 for s in all_shinies if s['gender'] == 'unknown')

        ivs = [s['iv_percent'] for s in all_shinies]
        avg_iv = sum(ivs) / len(ivs) if ivs else 0
        max_iv = max(ivs) if ivs else 0
        min_iv = min(ivs) if ivs else 0

        non_zero_ivs = [iv for iv in ivs if iv > 0]
        min_non_zero_iv = min(non_zero_ivs) if non_zero_ivs else 0

        total_event_count = utils.get_total_event_count()
        completion = (unique_forms / total_event_count) * 100 if total_event_count > 0 else 0

        embed = discord.Embed(
            title="✨ Event Shiny Collection Statistics",
            color=EMBED_COLOR
        )

        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )

        embed.add_field(
            name="📊 Collection Overview",
            value=f"**Total Event Shinies:** {total_tracked}\n"
                  f"> **Event Dex:** {unique_forms}/{total_event_count} ({completion:.1f}%)\n"
                  f"> **Males:** {males}\n"
                  f"> **Females:** {females}\n"
                  f"> **Unknown:** {unknown}",
            inline=True
        )

        embed.add_field(
            name="📈 IV Statistics",
            value=f"**Average:** {avg_iv:.2f}%\n"
                  f"> **Highest:** {max_iv:.2f}%\n"
                  f"> **Lowest:** {min_iv:.2f}%\n"
                  f"> **Lowest Non-Zero:** {min_non_zero_iv:.2f}%",
            inline=True
        )

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
    cog = EventDexManagement(bot)

    add_context_menu = app_commands.ContextMenu(
        name="Event Shiny Add",
        callback=cog.add_event_context_callback
    )
    bot.tree.add_command(add_context_menu)

    remove_context_menu = app_commands.ContextMenu(
        name="Event Shiny Remove",
        callback=cog.remove_event_context_callback
    )
    bot.tree.add_command(remove_context_menu)

    await bot.add_cog(cog)
