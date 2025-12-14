import discord
from discord.ext import commands
from discord import app_commands
import config
from config import EMBED_COLOR
from database import db


class EventDexView(discord.ui.View):
    """Pagination view for event dex"""

    def __init__(self, ctx, pages, total_caught, total_pokemon, dex_type="event", timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pages = pages
        self.total_caught = total_caught
        self.total_pokemon = total_pokemon
        self.dex_type = dex_type
        self.current_page = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= len(self.pages) - 1)

    def create_embed(self):
        """Create embed for current page"""
        title = f"✨ Your Event Dex ({self.dex_type.title()})"
        embed = discord.Embed(title=title, color=EMBED_COLOR)

        count_line = f"You've caught {self.total_caught} out of {self.total_pokemon} event pokémons!\n\n"
        embed.description = count_line + self.pages[self.current_page]

        footer_text = f"Page {self.current_page + 1}/{len(self.pages)}"
        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your event dex!", ephemeral=True)
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
            await interaction.response.send_message("❌ This is not your event dex!", ephemeral=True)
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


class EventDexDisplay(commands.Cog):
    """Display your event shiny Pokémon collection"""

    def __init__(self, bot):
        self.bot = bot

    def parse_filters(self, filter_string: str):
        """Parse filter string to extract options
        Returns: (show_caught, show_uncaught, order, region, types, name_searches, page)
        """
        show_caught = True
        show_uncaught = True
        order = None
        region = None
        types = []
        name_searches = []
        page = None

        if not filter_string:
            return show_caught, show_uncaught, order, region, types, name_searches, page

        args = filter_string.lower().split()

        valid_regions = ['kanto', 'johto', 'hoenn', 'sinnoh', 'unova', 'kalos', 
                         'alola', 'galar', 'hisui', 'paldea', 'unknown', 'missing', 'kitakami']
        valid_types = ['normal', 'fire', 'water', 'grass', 'electric', 'ice',
                       'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
                       'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy', 'shadow', 'missing']

        i = 0
        while i < len(args):
            arg = args[i]

            if arg in ['--caught', '--c']:
                show_uncaught = False
                i += 1
            elif arg in ['--uncaught', '--unc']:
                show_caught = False
                i += 1
            elif arg == '--orderd':
                order = 'desc'
                i += 1
            elif arg == '--ordera':
                order = 'asc'
                i += 1
            elif arg in ['--region', '--r']:
                if i + 1 < len(args) and args[i + 1] in valid_regions:
                    region = args[i + 1].title()
                    i += 2
                else:
                    i += 1
            elif arg.startswith('--region=') or arg.startswith('--r='):
                region_val = arg.split('=', 1)[1]
                if region_val in valid_regions:
                    region = region_val.title()
                i += 1
            elif arg in ['--type', '--t']:
                if i + 1 < len(args) and args[i + 1] in valid_types and len(types) < 2:
                    types.append(args[i + 1].title())
                    i += 2
                else:
                    i += 1
            elif arg.startswith('--type=') or arg.startswith('--t='):
                type_val = arg.split('=', 1)[1]
                if type_val in valid_types and len(types) < 2:
                    types.append(type_val.title())
                i += 1
            elif arg in ['--name', '--n']:
                if i + 1 < len(args):
                    name_parts = []
                    i += 1
                    while i < len(args) and not args[i].startswith('--'):
                        name_parts.append(args[i])
                        i += 1
                    if name_parts:
                        name_searches.append(' '.join(name_parts).title())
                else:
                    i += 1
            elif arg.startswith('--name=') or arg.startswith('--n='):
                name_val = arg.split('=', 1)[1]
                if name_val:
                    name_searches.append(name_val.title())
                i += 1
            elif arg in ['--page', '--p']:
                if i + 1 < len(args):
                    try:
                        page = int(args[i + 1])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1
            elif arg.startswith('--page=') or arg.startswith('--p='):
                try:
                    page_val = arg.split('=', 1)[1]
                    page = int(page_val)
                except ValueError:
                    pass
                i += 1
            else:
                i += 1

        return show_caught, show_uncaught, order, region, types, name_searches, page

    def matches_filters(self, pokemon_name: str, utils, region_filter: str, type_filters: list):
        """Check if a Pokemon matches region and type filters"""
        info = utils.get_pokemon_info(pokemon_name)

        if not info:
            return False

        if region_filter:
            if info['region'] != region_filter:
                return False

        if type_filters:
            pokemon_types = [info['type1']]
            if info['type2']:
                pokemon_types.append(info['type2'])

            for type_filter in type_filters:
                if type_filter not in pokemon_types:
                    return False

        return True

    @commands.hybrid_command(name='eventdex', aliases=['ed'])
    @app_commands.describe(filters="Filters: --caught, --uncaught, --orderd, --ordera, --region, --type, --name, --page")
    async def event_dex(self, ctx, *, filters: str = None):
        """View your event shiny dex (all forms, includes gender differences)"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Parse filters
        show_caught, show_uncaught, order, region_filter, type_filters, name_searches, page = self.parse_filters(filters)

        # Get user's event shinies
        user_shinies = await db.get_all_event_shinies(user_id)

        # Build counts: (name, gender_key) -> count
        form_counts = {}
        for shiny in user_shinies:
            name = shiny['name']
            gender = shiny['gender']

            has_gender_diff = utils.has_gender_difference_event(name)

            if has_gender_diff and gender in ['male', 'female']:
                key = (name, gender)
            else:
                key = (name, None)

            if key not in form_counts:
                form_counts[key] = 0
            form_counts[key] += 1

        # Get all event forms from CSV
        all_forms = utils.get_event_entries()

        # Build filtered list
        form_entries = []
        for pokemon_name, has_gender_diff in all_forms:
            # Apply name search filter
            if name_searches:
                matches_any = any(search.lower() in pokemon_name.lower() for search in name_searches)
                if not matches_any:
                    continue

            # Apply region/type filters
            if region_filter or type_filters:
                if not self.matches_filters(pokemon_name, utils, region_filter, type_filters):
                    continue

            if has_gender_diff:
                # Add male and female entries
                male_count = form_counts.get((pokemon_name, 'male'), 0)
                female_count = form_counts.get((pokemon_name, 'female'), 0)

                form_entries.append((pokemon_name, 'male', male_count))
                form_entries.append((pokemon_name, 'female', female_count))
            else:
                # Add single entry
                count = form_counts.get((pokemon_name, None), 0)
                form_entries.append((pokemon_name, None, count))

        # Apply caught/uncaught filters
        filtered_entries = []
        for entry in form_entries:
            name, gender_key, count = entry
            if count > 0 and not show_caught:
                continue
            if count == 0 and not show_uncaught:
                continue
            filtered_entries.append(entry)

        # Apply ordering
        if order == 'desc':
            filtered_entries.sort(key=lambda x: x[2], reverse=True)
        elif order == 'asc':
            filtered_entries.sort(key=lambda x: x[2])

        if not filtered_entries:
            await ctx.send("❌ No event shinies match your filters!", reference=ctx.message, mention_author=False)
            return

        # Calculate stats
        total_caught = sum(1 for entry in form_entries if entry[2] > 0)
        total_forms = len(form_entries)

        # Create pages
        lines = []
        for name, gender_key, count in filtered_entries:
            icon = f"{config.TICK}" if count > 0 else f"{config.CROSS}"
            sparkles = f"{count} ✨" if count > 0 else "0"

            # Add gender emoji if applicable
            gender_emoji = ""
            if gender_key == 'male':
                gender_emoji = f" {config.GENDER_MALE}"
            elif gender_key == 'female':
                gender_emoji = f" {config.GENDER_FEMALE}"

            lines.append(f"{icon} {name}{gender_emoji} - {sparkles}")

        # Paginate
        per_page = 21
        pages = []
        for i in range(0, len(lines), per_page):
            page_content = "\n".join(lines[i:i+per_page])
            pages.append(page_content)

        # Create view
        filter_text = "event"
        if region_filter:
            filter_text += f" - {region_filter}"
        if type_filters:
            filter_text += f" - {'/'.join(type_filters)}"
        if name_searches:
            filter_text += f" - {', '.join(name_searches)}"

        view = EventDexView(ctx, pages, total_caught, total_forms, filter_text)

        # Apply page number if specified
        if page is not None:
            if 1 <= page <= len(pages):
                view.current_page = page - 1
                view.update_buttons()
            else:
                await ctx.send(f"❌ Invalid page number! Valid range: 1-{len(pages)}", reference=ctx.message, mention_author=False)
                return

        message = await ctx.send(embed=view.create_embed(), view=view, reference=ctx.message, mention_author=False)
        view.message = message


async def setup(bot):
    await bot.add_cog(EventDexDisplay(bot))
