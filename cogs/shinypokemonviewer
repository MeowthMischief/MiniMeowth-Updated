import discord
from discord.ext import commands
from discord import app_commands
import re
import config
from config import EMBED_COLOR, POKETWO_BOT_ID, GENDER_MALE, GENDER_FEMALE, GENDER_UNKNOWN
from database import db


class ShinyPokemonView(discord.ui.View):
    """Pagination view for shiny Pokemon list"""

    def __init__(self, ctx, pages, total_count, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pages = pages
        self.total_count = total_count
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
            title="✨ Your Shiny Pokemon",
            description=self.pages[self.current_page],
            color=EMBED_COLOR
        )

        footer_text = f"Showing {self.current_page * 20 + 1}–{min((self.current_page + 1) * 20, self.total_count)} out of {self.total_count} • Page {self.current_page + 1}/{len(self.pages)}"
        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your Pokemon list!", ephemeral=True)
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
            await interaction.response.send_message("❌ This is not your Pokemon list!", ephemeral=True)
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


class ShinyPokemonViewer(commands.Cog):
    """View and filter your shiny Pokemon collection"""

    def __init__(self, bot):
        self.bot = bot

    def parse_filters(self, filter_string: str):
        """Parse filter string to extract all options
        Returns: (names, iv_filter, types, region, page)
        """
        names = []
        iv_filter = None
        types = []
        region = None
        page = None

        if not filter_string:
            return names, iv_filter, types, region, page

        args = filter_string.split()

        valid_regions = ['kanto', 'johto', 'hoenn', 'sinnoh', 'unova', 'kalos', 
                         'alola', 'galar', 'hisui', 'paldea', 'unknown', 'missing', 'kitakami']
        valid_types = ['normal', 'fire', 'water', 'grass', 'electric', 'ice',
                       'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
                       'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy', 'missing']

        i = 0
        while i < len(args):
            arg = args[i].lower()

            # Name filter
            if arg in ['--name', '--n']:
                if i + 1 < len(args):
                    name_parts = []
                    i += 1
                    while i < len(args) and not args[i].startswith('--'):
                        name_parts.append(args[i])
                        i += 1
                    if name_parts:
                        names.append(' '.join(name_parts).title())
                else:
                    i += 1
            elif arg.startswith('--name=') or arg.startswith('--n='):
                name_val = arg.split('=', 1)[1]
                if name_val:
                    names.append(name_val.title())
                i += 1

            # IV filter
            elif arg.startswith('--iv'):
                iv_part = arg[4:]  # Get everything after --iv
                if iv_part:
                    iv_filter = self.parse_iv_filter(iv_part)
                i += 1

            # Type filter (max 2)
            elif arg in ['--type', '--t']:
                if i + 1 < len(args) and args[i + 1].lower() in valid_types and len(types) < 2:
                    types.append(args[i + 1].title())
                    i += 2
                else:
                    i += 1
            elif arg.startswith('--type=') or arg.startswith('--t='):
                type_val = arg.split('=', 1)[1].lower()
                if type_val in valid_types and len(types) < 2:
                    types.append(type_val.title())
                i += 1

            # Region filter
            elif arg in ['--region', '--r']:
                if i + 1 < len(args) and args[i + 1].lower() in valid_regions:
                    region = args[i + 1].title()
                    i += 2
                else:
                    i += 1
            elif arg.startswith('--region=') or arg.startswith('--r='):
                region_val = arg.split('=', 1)[1].lower()
                if region_val in valid_regions:
                    region = region_val.title()
                i += 1

            # Page filter
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

        return names, iv_filter, types, region, page

    def parse_iv_filter(self, iv_string: str):
        """Parse IV filter string
        Returns: ('exact', value) or ('gt', value) or ('lt', value) or None
        Examples: 50 -> ('exact', 50.0), >50 -> ('gt', 50.0), <50 -> ('lt', 50.0)
        """
        iv_string = iv_string.strip()

        if iv_string.startswith('>'):
            try:
                value = float(iv_string[1:])
                return ('gt', value)
            except ValueError:
                return None
        elif iv_string.startswith('<'):
            try:
                value = float(iv_string[1:])
                return ('lt', value)
            except ValueError:
                return None
        else:
            try:
                value = float(iv_string)
                return ('exact', value)
            except ValueError:
                return None

    def matches_iv_filter(self, iv_percent: float, iv_filter):
        """Check if IV matches the filter"""
        if not iv_filter:
            return True

        filter_type, filter_value = iv_filter

        if filter_type == 'exact':
            # Match whole number (e.g., 50 matches 50.0-50.99)
            return int(iv_percent) == int(filter_value)
        elif filter_type == 'gt':
            return iv_percent > filter_value
        elif filter_type == 'lt':
            return iv_percent < filter_value

        return True

    def matches_filters(self, pokemon: dict, utils, names: list, iv_filter, types: list, region: str):
        """Check if a Pokemon matches all filters"""
        # Name filter (strict match)
        if names:
            if pokemon['name'] not in names:
                return False

        # IV filter
        if not self.matches_iv_filter(pokemon['iv_percent'], iv_filter):
            return False

        # Type and region filters
        if types or region:
            info = utils.get_pokemon_info(pokemon['name'])
            if not info:
                return False

            if region and info['region'] != region:
                return False

            if types:
                pokemon_types = [info['type1']]
                if info['type2']:
                    pokemon_types.append(info['type2'])

                for type_filter in types:
                    if type_filter not in pokemon_types:
                        return False

        return True

    async def get_user_order(self, user_id: int):
        """Get user's saved order preference"""
        settings = await db.settings.find_one({"user_id": user_id})
        if settings and 'shiny_order' in settings:
            return settings['shiny_order']
        return 'iv-'  # Default: high IV to low IV

    async def set_user_order(self, user_id: int, order: str):
        """Save user's order preference"""
        await db.settings.update_one(
            {"user_id": user_id},
            {"$set": {"shiny_order": order}},
            upsert=True
        )

    def sort_pokemon(self, pokemon_list: list, order: str):
        """Sort Pokemon list based on order preference"""
        if order in ['iv', 'iv-']:
            # High IV to low IV
            return sorted(pokemon_list, key=lambda p: p['iv_percent'], reverse=True)
        elif order == 'iv+':
            # Low IV to high IV
            return sorted(pokemon_list, key=lambda p: p['iv_percent'])
        elif order in ['number', 'number+']:
            # Small ID to large ID
            return sorted(pokemon_list, key=lambda p: p['pokemon_id'])
        elif order == 'number-':
            # Large ID to small ID
            return sorted(pokemon_list, key=lambda p: p['pokemon_id'], reverse=True)
        elif order in ['pokedex', 'pokedex+']:
            # Low dex number to high dex number
            return sorted(pokemon_list, key=lambda p: (p['dex_number'], p['pokemon_id']))
        elif order == 'pokedex-':
            # High dex number to low dex number
            return sorted(pokemon_list, key=lambda p: (p['dex_number'], p['pokemon_id']), reverse=True)
        else:
            # Default: high IV to low IV
            return sorted(pokemon_list, key=lambda p: p['iv_percent'], reverse=True)

    def format_pokemon_line(self, pokemon: dict):
        """Format a single Pokemon line"""
        # Gender emoji from config
        gender_emoji = ""
        if pokemon['gender'] == 'male':
            gender_emoji = config.GENDER_MALE
        elif pokemon['gender'] == 'female':
            gender_emoji = config.GENDER_FEMALE
        else:
            gender_emoji = config.GENDER_UNKNOWN

        # Format: `ID` ✨ Name Gender • Lvl. X • IV%
        return f"`{pokemon['pokemon_id']}`　✨ **{pokemon['name']}**{gender_emoji}　•　Lvl. {pokemon['level']}　•　{pokemon['iv_percent']:.2f}%"

    @commands.hybrid_command(name='pokemon', aliases=['p'])
    @app_commands.describe(filters="Filters: --name, --iv, --type, --region, --page")
    async def pokemon(self, ctx, *, filters: str = None):
        """View your shiny Pokemon with filters"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Parse filters
        names, iv_filter, types, region, page = self.parse_filters(filters)

        # Get all user shinies
        all_shinies = await db.get_all_shinies(user_id)

        if not all_shinies:
            await ctx.send("❌ You don't have any tracked shinies yet!\nUse `?trackshiny` to get started.", 
                          reference=ctx.message, mention_author=False)
            return

        # Check if any name filter is invalid
        if names:
            valid_names = set(s['name'] for s in all_shinies)
            invalid_names = [name for name in names if name not in valid_names]
            if invalid_names:
                await ctx.send(
                    f"❌ The following Pokemon are not known or not in your inventory: {', '.join(invalid_names)}",
                    reference=ctx.message, mention_author=False
                )
                return

        # Apply filters
        filtered_pokemon = []
        for pokemon in all_shinies:
            if self.matches_filters(pokemon, utils, names, iv_filter, types, region):
                filtered_pokemon.append(pokemon)

        if not filtered_pokemon:
            await ctx.send("❌ No Pokemon match your filters!", reference=ctx.message, mention_author=False)
            return

        # Get user's order preference and sort
        order = await self.get_user_order(user_id)
        sorted_pokemon = self.sort_pokemon(filtered_pokemon, order)

        # Create pages
        lines = []
        for pokemon in sorted_pokemon:
            lines.append(self.format_pokemon_line(pokemon))

        # Paginate (20 per page)
        per_page = 20
        pages = []
        for i in range(0, len(lines), per_page):
            page_content = "\n".join(lines[i:i+per_page])
            pages.append(page_content)

        # Create view
        view = ShinyPokemonView(ctx, pages, len(sorted_pokemon))

        # Apply page number if specified
        if page is not None:
            if 1 <= page <= len(pages):
                view.current_page = page - 1
                view.update_buttons()
            else:
                await ctx.send(
                    f"❌ Invalid page number! Valid range: 1-{len(pages)}", 
                    reference=ctx.message, mention_author=False
                )
                return

        message = await ctx.send(embed=view.create_embed(), view=view, reference=ctx.message, mention_author=False)
        view.message = message

    @commands.hybrid_command(name='order', aliases=['or'])
    @app_commands.describe(order_type="Order type: iv/iv+/iv-/number/number+/number-/pokedex/pokedex+/pokedex-")
    async def order(self, ctx, order_type: str = None):
        """Set your preferred Pokemon display order"""
        valid_orders = ['iv', 'iv+', 'iv-', 'number', 'number+', 'number-', 'pokedex', 'pokedex+', 'pokedex-']

        if not order_type:
            current_order = await self.get_user_order(ctx.author.id)
            embed = discord.Embed(
                title="🔄 Pokemon Order Settings",
                description=f"**Current Order:** `{current_order}`\n\n"
                           f"**Available Orders:**\n"
                           f"`iv` / `iv-` - High IV to low IV (default)\n"
                           f"`iv+` - Low IV to high IV\n"
                           f"`number` / `number+` - Small ID to large ID\n"
                           f"`number-` - Large ID to small ID\n"
                           f"`pokedex` / `pokedex+` - Low dex number to high\n"
                           f"`pokedex-` - High dex number to low\n\n"
                           f"Use `?order <type>` to change your order.",
                color=EMBED_COLOR
            )
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            return

        order_type = order_type.lower()

        if order_type not in valid_orders:
            await ctx.send(
                f"❌ Invalid order type!\n"
                f"Please specify either `iv`, `iv+`, `iv-`, `number`, `number+`, `number-`, `pokedex`, `pokedex+` or `pokedex-`",
                reference=ctx.message, mention_author=False
            )
            return

        await self.set_user_order(ctx.author.id, order_type)

        # Get description of the order
        order_descriptions = {
            'iv': 'High IV to low IV',
            'iv-': 'High IV to low IV',
            'iv+': 'Low IV to high IV',
            'number': 'Small ID to large ID',
            'number+': 'Small ID to large ID',
            'number-': 'Large ID to small ID',
            'pokedex': 'Low dex number to high',
            'pokedex+': 'Low dex number to high',
            'pokedex-': 'High dex number to low'
        }

        await ctx.send(
            f"✅ Order set to `{order_type}` - {order_descriptions[order_type]}",
            reference=ctx.message, mention_author=False
        )


async def setup(bot):
    await bot.add_cog(ShinyPokemonViewer(bot))
