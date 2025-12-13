import discord
from discord.ext import commands
from discord import app_commands
import config
from config import EMBED_COLOR
from database import db


class StatsView(discord.ui.View):
    """Pagination view for stats"""

    def __init__(self, ctx, pages, stats_type="Type", timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pages = pages
        self.stats_type = stats_type
        self.current_page = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= len(self.pages) - 1)

    def create_embed(self):
        """Create embed for current page"""
        embed = discord.Embed(
            title=f"✨ {self.stats_type} Statistics",
            color=EMBED_COLOR
        )

        embed.set_author(
            name=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url
        )

        # Add fields from current page
        for field in self.pages[self.current_page]:
            embed.add_field(
                name=field['name'],
                value=field['value'],
                inline=False
            )

        # Footer with page info
        total_items = sum(len(page) for page in self.pages)
        start_item = sum(len(self.pages[i]) for i in range(self.current_page)) + 1
        end_item = start_item + len(self.pages[self.current_page]) - 1

        embed.set_footer(text=f"Showing {start_item}–{end_item} out of {total_items}.")

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your stats!", ephemeral=True)
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="▶️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your stats!", ephemeral=True)
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    async def on_timeout(self):
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass


class ShinyDexStats(commands.Cog):
    """Statistics commands for shiny collection - type and region breakdowns"""

    def __init__(self, bot):
        self.bot = bot

        # Type emojis mapping (update these with your actual emoji IDs)
        self.type_emojis = {
            'Normal': '<:white_circle:1449350772759330886>',
            'Fire': '<:fire:1449350556958068736>',
            'Water': '<:droplet:1449350601401045015>',
            'Grass': '<:herb:1449350615548301332>',
            'Electric': '<:zap:1449350683449888989>',
            'Ice': '<:snowflake:1449350748033781841>',
            'Fighting': '<:boxing_glove:1449350710083850324>',
            'Poison': '<:skull_crossbones:1449350785279332372>',
            'Ground': '<:earth_africa:1449350761052901457>',
            'Flying': '<:dove:1449350735664779345>',
            'Psychic': '<:crystal_ball:1449350572737171588>',
            'Bug': '<:bug:1449350643134369792>',
            'Rock': '<:rock:1449350797170053182>',
            'Ghost': '<:ghost:1449350722490728489>',
            'Dragon': '<:dragon:1449350657944457308>',
            'Dark': '<:crescent_moon:1449350670380437737>',
            'Steel': '<:gear:1449350583982100530>',
            'Fairy': '<:fairy:1449350697794408559>',
            'Missing': '<:question:1449363513595400332>'
        }

        # Region emojis mapping
        self.region_emojis = {
            'Kanto': '<:kanto:1449352367756542002>',
            'Johto': '<:johto:1449352435674906625>',
            'Hoenn': '<:hoenn:1449352573810376744>',
            'Sinnoh': '<:sinnoh:1449352646086361300>',
            'Unova': '<:unova:1449352763891912714>',
            'Kalos': '<:kalos:1449356394712010847>',
            'Alola': '<:alola:1449352883987288195>',
            'Galar': '<:galar:1449353475476422726>',
            'Hisui': '<:hisui:1449353533475520572>',
            'Paldea': '<:paldea:1449353594343129128>',
            'Kitakami': '<:kitakami:1449353760206884904>',
            'Unknown': '<:ShinyMissingno:1422092867895033887>',
            'Missing': '❓'
        }

        # Progress bar emojis (Pokétwo style)
        # When quest is COMPLETE (100%)
        self.progress_complete_first = '<:ballot_box_with_check:1449344144156659802>'
        self.progress_complete_middle = '<:ballot_box_with_check:1449341980248113256>'
        self.progress_complete_end = '<:ballot_box_with_check:1449341970639097907>'

        # When quest is INCOMPLETE (<100%)
        self.progress_incomplete_first = '<:black_large_square:1449341999735111690>'
        self.progress_incomplete_middle = '<:black_large_square:1449342009272696903>'
        self.progress_incomplete_empty = '<:black_large_square:1449342009272696903>'
        self.progress_incomplete_end = '<:black_large_square:1449342830777733163>'

    def create_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        """Create a Pokétwo-style progress bar"""
        if total == 0:
            # Empty bar - all incomplete
            return self.progress_incomplete_first + (self.progress_incomplete_empty * (length - 2)) + self.progress_incomplete_end

        # Check if 100% complete
        is_complete = (current >= total)

        if is_complete:
            # All complete - use complete emojis throughout
            return self.progress_complete_first + (self.progress_complete_middle * (length - 2)) + self.progress_complete_end
        else:
            # Partial progress - mix of complete and incomplete
            filled = int((current / total) * length)

            # Ensure at least first emoji is filled if any progress
            if current > 0 and filled == 0:
                filled = 1

            # Build the bar with transition from complete to incomplete
            bar = ""

            for i in range(length):
                if i == 0:
                    # First position - always use first emoji based on progress
                    bar += self.progress_complete_first if filled > 0 else self.progress_incomplete_first
                elif i == length - 1:
                    # Last position - use complete end if fully filled, otherwise incomplete end
                    bar += self.progress_complete_end if filled >= length else self.progress_incomplete_end
                else:
                    # Middle positions - use complete middle if filled, incomplete empty otherwise
                    if i < filled:
                        bar += self.progress_complete_middle
                    else:
                        bar += self.progress_incomplete_empty

            return bar

    def calculate_percentage(self, current: int, total: int) -> float:
        """Calculate percentage with 1 decimal place"""
        if total == 0:
            return 0.0
        return round((current / total) * 100, 1)

    @commands.hybrid_command(name='typestats', aliases=['ts'])
    async def type_stats(self, ctx):
        """View statistics for each Pokémon type in your shiny collection"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Get user's shinies
        user_shinies = await db.get_all_shinies(user_id)

        if not user_shinies:
            await ctx.send("❌ You haven't tracked any shinies yet!\nUse `?trackshiny` to get started.", 
                          reference=ctx.message, mention_author=False)
            return

        # Build user's caught forms by type
        user_forms_by_type = {}

        for shiny in user_shinies:
            name = shiny['name']
            dex_num = shiny['dex_number']
            gender = shiny['gender']

            # Get Pokemon info
            info = utils.get_pokemon_info(name)
            if not info:
                continue

            # Get types
            types = [info['type1']]
            if info['type2']:
                types.append(info['type2'])

            # Check if has gender difference
            has_gender_diff = utils.has_gender_difference(name)

            # Create form key
            if has_gender_diff and gender in ['male', 'female']:
                form_key = (dex_num, name, gender)
            else:
                form_key = (dex_num, name, None)

            # Add to each type
            for ptype in types:
                if ptype not in user_forms_by_type:
                    user_forms_by_type[ptype] = set()
                user_forms_by_type[ptype].add(form_key)

        # Calculate total forms per type from CSV
        all_forms = utils.get_full_dex_entries()
        total_forms_by_type = {}

        for dex_num, pokemon_name, has_gender_diff in all_forms:
            info = utils.get_pokemon_info(pokemon_name)
            if not info:
                continue

            types = [info['type1']]
            if info['type2']:
                types.append(info['type2'])

            # Count forms
            if has_gender_diff:
                form_count = 2  # Male and female
            else:
                form_count = 1

            for ptype in types:
                if ptype not in total_forms_by_type:
                    total_forms_by_type[ptype] = 0
                total_forms_by_type[ptype] += form_count

        # Build stats for each type
        type_stats = []
        for ptype in sorted(total_forms_by_type.keys()):
            caught = len(user_forms_by_type.get(ptype, set()))
            total = total_forms_by_type[ptype]
            progress = self.create_progress_bar(caught, total)

            type_stats.append({
                'type': ptype,
                'caught': caught,
                'total': total,
                'progress': progress
            })

        # Sort by type name
        type_stats.sort(key=lambda x: x['type'])

        # Create pages (10 types per page like Pokétwo quests)
        items_per_page = 10
        pages = []

        for i in range(0, len(type_stats), items_per_page):
            page_stats = type_stats[i:i+items_per_page]
            page_fields = []

            for stat in page_stats:
                type_emoji = self.type_emojis.get(stat['type'], '❓')
                field_name = f"Shiny Progess For {type_emoji} {stat['type']}-type pokémon."
                field_value = f"{stat['progress']} `{stat['caught']}/{stat['total']}`"

                page_fields.append({
                    'name': field_name,
                    'value': field_value
                })

            pages.append(page_fields)

        # Create view and send
        view = StatsView(ctx, pages, "Type")
        message = await ctx.send(embed=view.create_embed(), view=view, reference=ctx.message, mention_author=False)
        view.message = message

    @commands.hybrid_command(name='regionstats', aliases=['rs'])
    async def region_stats(self, ctx):
        """View statistics for each region in your shiny collection"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Get user's shinies
        user_shinies = await db.get_all_shinies(user_id)

        if not user_shinies:
            await ctx.send("❌ You haven't tracked any shinies yet!\nUse `?trackshiny` to get started.", 
                          reference=ctx.message, mention_author=False)
            return

        # Build user's caught forms by region
        user_forms_by_region = {}

        for shiny in user_shinies:
            name = shiny['name']
            dex_num = shiny['dex_number']
            gender = shiny['gender']

            # Get Pokemon info
            info = utils.get_pokemon_info(name)
            if not info:
                continue

            region = info['region']

            # Check if has gender difference
            has_gender_diff = utils.has_gender_difference(name)

            # Create form key
            if has_gender_diff and gender in ['male', 'female']:
                form_key = (dex_num, name, gender)
            else:
                form_key = (dex_num, name, None)

            # Add to region
            if region not in user_forms_by_region:
                user_forms_by_region[region] = set()
            user_forms_by_region[region].add(form_key)

        # Calculate total forms per region from CSV
        all_forms = utils.get_full_dex_entries()
        total_forms_by_region = {}

        for dex_num, pokemon_name, has_gender_diff in all_forms:
            info = utils.get_pokemon_info(pokemon_name)
            if not info:
                continue

            region = info['region']

            # Count forms
            if has_gender_diff:
                form_count = 2  # Male and female
            else:
                form_count = 1

            if region not in total_forms_by_region:
                total_forms_by_region[region] = 0
            total_forms_by_region[region] += form_count

        # Build stats for each region
        region_stats = []

        # Define region order
        region_order = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 
                       'Alola', 'Galar', 'Hisui', 'Paldea', 'Kitakami', 'Unknown', 'Missing']

        for region in region_order:
            if region in total_forms_by_region:
                caught = len(user_forms_by_region.get(region, set()))
                total = total_forms_by_region[region]
                progress = self.create_progress_bar(caught, total)

                region_stats.append({
                    'region': region,
                    'caught': caught,
                    'total': total,
                    'progress': progress
                })

        # Create pages (10 regions per page)
        items_per_page = 10
        pages = []

        for i in range(0, len(region_stats), items_per_page):
            page_stats = region_stats[i:i+items_per_page]
            page_fields = []

            for stat in page_stats:
                region_emoji = self.region_emojis.get(stat['region'], '❓')
                field_name = f"Shiny Progress for {region_emoji} {stat['region']} region"
                field_value = f"{stat['progress']} `{stat['caught']}/{stat['total']}`"

                page_fields.append({
                    'name': field_name,
                    'value': field_value
                })

            pages.append(page_fields)

        # Create view and send
        view = StatsView(ctx, pages, "Region")
        message = await ctx.send(embed=view.create_embed(), view=view, reference=ctx.message, mention_author=False)
        view.message = message


async def setup(bot):
    await bot.add_cog(ShinyDexStats(bot))
