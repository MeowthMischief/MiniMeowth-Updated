import discord
from discord.ext import commands
from discord import app_commands
import io
import unicodedata
import config
from config import EMBED_COLOR
from database import db
from filters import get_filter, get_all_filter_names
from smartlist_utils import build_smartlist_sections
from dex_image_generator import DexImageGenerator


def normalize_string(s):
    """Remove accents from string for comparison"""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


class ShinyDexView(discord.ui.View):
    """Pagination view for shiny dex"""

    def __init__(self, ctx, pages, total_caught, total_pokemon, dex_type="basic", total_shiny_count=0, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pages = pages
        self.total_caught = total_caught
        self.total_pokemon = total_pokemon
        self.dex_type = dex_type
        self.total_shiny_count = total_shiny_count
        self.current_page = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= len(self.pages) - 1)

    def create_embed(self):
        """Create embed for current page"""
        title = f"✨ Your Shiny Dex ({self.dex_type.title()})"
        embed = discord.Embed(title=title, color=EMBED_COLOR)

        # Add count line at the top of description
        count_line = f"You've caught {self.total_caught} out of {self.total_pokemon} pokémons!\n\n"
        embed.description = count_line + self.pages[self.current_page]

        footer_text = f"Page {self.current_page + 1}/{len(self.pages)}"
        if self.total_shiny_count > 0:
            footer_text += f" • Total Shinies: {self.total_shiny_count}"
        embed.set_footer(text=footer_text)

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your shiny dex!", ephemeral=True)
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
            await interaction.response.send_message("❌ This is not your shiny dex!", ephemeral=True)
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


class ShinyDexDisplay(commands.Cog):
    """Display your shiny Pokémon collection - view dex, filters"""

    def __init__(self, bot):
        self.bot = bot
        self.image_generator = DexImageGenerator(bot)

    def parse_filters(self, filter_string: str):
        """Parse filter string to extract options
        Returns: (show_caught, show_uncaught, order, region, types, name_searches, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female)
        """
        show_caught = True
        show_uncaught = True
        order = None
        region = None
        types = []
        name_searches = []
        page = None
        show_list = False
        show_smartlist = False
        ignore_gender = False
        exclude_names = []
        show_image = False
        ignore_male = False
        ignore_female = False

        if not filter_string:
            return show_caught, show_uncaught, order, region, types, name_searches, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female

        args = filter_string.lower().split()

        valid_regions = ['kanto', 'johto', 'hoenn', 'sinnoh', 'unova', 'kalos', 
                         'alola', 'galar', 'hisui', 'paldea', 'unknown', 'missing', 'kitakami']
        valid_types = ['normal', 'fire', 'water', 'grass', 'electric', 'ice',
                       'fighting', 'poison', 'ground', 'flying', 'psychic', 'bug',
                       'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy', 'missing']

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
            elif arg == '--list':
                show_list = True
                i += 1
            elif arg in ['--smartlist', '--slist']:
                show_smartlist = True
                i += 1
            elif arg in ['--image', '--img']:
                show_image = True
                i += 1
            elif arg in ['--nogender', '--ng', '--ignoregender', '--ig']:
                ignore_gender = True
                i += 1
            elif arg in ['--ignoremale', '--im']:
                ignore_male = True
                i += 1
            elif arg in ['--ignorefemale', '--if']:
                ignore_female = True
                i += 1
            elif arg in ['--exclude', '--ex', '--exc']:
                if i + 1 < len(args):
                    exclude_parts = []
                    i += 1
                    while i < len(args) and not args[i].startswith('--'):
                        exclude_parts.append(args[i])
                        i += 1
                    if exclude_parts:
                        exclude_names.append(' '.join(exclude_parts).title())
                else:
                    i += 1
            elif arg.startswith('--exclude=') or arg.startswith('--ex=') or arg.startswith('--exc='):
                exclude_val = arg.split('=', 1)[1]
                if exclude_val:
                    exclude_names.append(exclude_val.title())
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

        return show_caught, show_uncaught, order, region, types, name_searches, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female

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

    def is_excluded(self, pokemon_name: str, exclude_names: list):
        """Check if a Pokemon should be excluded based on exclude filters"""
        if not exclude_names:
            return False

        normalized_pokemon = normalize_string(pokemon_name.lower())

        for exclude_name in exclude_names:
            normalized_exclude = normalize_string(exclude_name.lower())
            if normalized_exclude in normalized_pokemon:
                return True

        return False

    async def send_pokemon_list_simple(self, ctx, pokemon_names: list):
        """Send simple Pokemon names as --n formatted list (text or file)"""
        formatted_list = " ".join([f"--n {name.lower()}" for name in pokemon_names])

        total_count = len(pokemon_names)
        list_text = f"**total pokemon: {total_count}**. use --smartlist/--slist for better list!\n\n{formatted_list}"

        if len(list_text) <= 1900:
            await ctx.send(list_text, reference=ctx.message, mention_author=False)
        else:
            file = discord.File(
                io.BytesIO(formatted_list.encode('utf-8')),
                filename='pokemon_list.txt'
            )
            await ctx.send(
                f"**total: {total_count} pokemon**\n📝 list is too long! here's a file:",
                file=file,
                reference=ctx.message,
                mention_author=False
            )

    async def send_pokemon_smartlist(self, ctx, pokemon_data: list, utils):
        """Send Pokemon names as smartlist with gender differences and categories
        pokemon_data: list of tuples (name, gender_key, count)
        """
        sections, total_count, gender_diff_count = build_smartlist_sections(pokemon_data, utils)

        # Join sections with blank lines
        list_text = "\n\n".join(sections)

        # If list is short enough, send as message
        if len(list_text) <= 1900:
            await ctx.send(list_text, reference=ctx.message, mention_author=False)
        else:
            # Create a text file
            file = discord.File(
                io.BytesIO(list_text.encode('utf-8')),
                filename='pokemon_smartlist.txt'
            )
            await ctx.send(
                f"**total: {total_count} pokemon** ({gender_diff_count} species with gender differences)\n📝 list is too long! here's a file:",
                file=file,
                reference=ctx.message,
                mention_author=False
            )

    async def send_dex_image(self, ctx, pokemon_entries: list, utils, page: int = 1, header_info: dict = None):
        """Generate and send dex image"""
        # Calculate which 30 Pokemon to show based on page
        start_idx = (page - 1) * 30
        end_idx = start_idx + 30
        page_entries = pokemon_entries[start_idx:end_idx]

        if not page_entries:
            await ctx.send("❌ No Pokémon on this page!", reference=ctx.message, mention_author=False)
            return

        # Generate image
        status_msg = await ctx.send("🎨 Generating dex image...", reference=ctx.message, mention_author=False)

        try:
            # Build page info
            total_pages = (len(pokemon_entries) + 29) // 30  # Round up
            page_info = {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': len(pokemon_entries)
            }

            img = await self.image_generator.create_dex_image(page_entries, utils, header_info, page_info)

            if img:
                # Save to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)

                file = discord.File(img_bytes, filename='shinydex.png')

                await status_msg.delete()
                await ctx.send(file=file, reference=ctx.message, mention_author=False)
            else:
                await status_msg.edit(content="❌ Failed to generate image!")

        except Exception as e:
            await status_msg.edit(content=f"❌ Error generating image: {str(e)}")
            print(f"Error in dex image generation: {e}")

    @commands.hybrid_command(name='shinydex', aliases=['sd','basicdex','bd'])
    @app_commands.describe(filters="Filters: --caught, --uncaught, --orderd, --ordera, --region, --type, --name, --exclude, --page, --list, --smartlist, --image, --ignoremale, --ignorefemale")
    async def shiny_dex(self, ctx, *, filters: str = None):
        """View your basic shiny dex (one Pokemon per dex number, counts all forms)"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Parse filters
        show_caught, show_uncaught, order, region_filter, type_filters, name_searches, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female = self.parse_filters(filters)

        # Check conflicting flags
        if show_image and (show_list or show_smartlist):
            await ctx.send("❌ Cannot use --image with --list or --smartlist!", reference=ctx.message, mention_author=False)
            return

        # Get user's shinies
        user_shinies = await db.get_all_shinies(user_id)

        # Build dex number -> count map (count ALL shinies with that dex number)
        dex_counts = {}
        for shiny in user_shinies:
            dex_num = shiny['dex_number']
            if dex_num not in dex_counts:
                dex_counts[dex_num] = 0
            dex_counts[dex_num] += 1

        # Get all dex entries from CSV (one per dex number - the first/top one)
        all_dex_entries = utils.get_basic_dex_entries()

        # Build filtered list
        dex_entries = []
        for dex_num, pokemon_name in all_dex_entries:
            # Apply exclude filter first
            if self.is_excluded(pokemon_name, exclude_names):
                continue

            # Apply name search filter with accent-insensitive matching
            if name_searches:
                normalized_pokemon = normalize_string(pokemon_name.lower())
                matches_any = any(normalize_string(search.lower()) in normalized_pokemon for search in name_searches)
                if not matches_any:
                    continue

            # Apply region/type filters
            if region_filter or type_filters:
                if not self.matches_filters(pokemon_name, utils, region_filter, type_filters):
                    continue

            count = dex_counts.get(dex_num, 0)
            dex_entries.append((dex_num, pokemon_name, count))

        # Apply caught/uncaught filters
        filtered_entries = []
        for dex_num, name, count in dex_entries:
            if count > 0 and not show_caught:
                continue
            if count == 0 and not show_uncaught:
                continue
            filtered_entries.append((dex_num, name, count))

        # Apply ordering
        if order == 'desc':
            filtered_entries.sort(key=lambda x: x[2], reverse=True)
        elif order == 'asc':
            filtered_entries.sort(key=lambda x: x[2])

        if not filtered_entries:
            await ctx.send("❌ No shinies match your filters!", reference=ctx.message, mention_author=False)
            return

        # If --image flag is set, generate image
        if show_image:
            # Convert to format expected by image generator (dex_num, name, gender_key, count)
            image_entries = [(dex_num, name, None, count) for dex_num, name, count in filtered_entries]

            # Build header info
            header_info = {'dex_type': 'Basic Shiny Dex'}
            if type_filters:
                header_info['types'] = type_filters
            if region_filter:
                header_info['regions'] = [region_filter]

            await self.send_dex_image(ctx, image_entries, utils, page or 1, header_info)
            return

        # If --list flag is set, send simple list format
        if show_list:
            pokemon_names = [name for _, name, _ in filtered_entries]
            await self.send_pokemon_list_simple(ctx, pokemon_names)
            return

        # If --smartlist flag is set, send smartlist format
        if show_smartlist:
            # For basic dex, we don't track gender, so just mark all as no gender diff
            pokemon_data = [(name, None, count) for _, name, count in filtered_entries]
            await self.send_pokemon_smartlist(ctx, pokemon_data, utils)
            return

        # Calculate stats
        total_caught = sum(1 for _, _, count in dex_entries if count > 0)
        total_pokemon = len(dex_entries)
        total_shiny_count = sum(count for _, _, count in filtered_entries)

        # Create pages
        lines = []
        for dex_num, name, count in filtered_entries:
            icon = f"{config.TICK}" if count > 0 else f"{config.CROSS}"
            sparkles = f"{count} ✨" if count > 0 else "0"
            lines.append(f"{icon} **#{dex_num}** {name} - {sparkles}")

        # Paginate
        per_page = 21
        pages = []
        for i in range(0, len(lines), per_page):
            page_content = "\n".join(lines[i:i+per_page])
            pages.append(page_content)

        # Create view with only region and type filters in display name
        filter_text = "basic"
        if region_filter:
            filter_text += f" - {region_filter}"
        if type_filters:
            filter_text += f" - {'/'.join(type_filters)}"

        view = ShinyDexView(ctx, pages, total_caught, total_pokemon, filter_text, total_shiny_count)

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

    @commands.hybrid_command(name='shinydexfull', aliases=['sdf','fulldex','fd','fullshinydex','fsd'])
    @app_commands.describe(filters="Filters: --caught, --unc, --orderd, --ordera, --region, --type, --name, --exclude, --page, --list, --smartlist, --image, --ignoremale, --ignorefemale")
    async def shiny_dex_full(self, ctx, *, filters: str = None):
        """View your full shiny dex (all forms, includes gender differences)"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id

        # Parse filters
        show_caught, show_uncaught, order, region_filter, type_filters, name_searches, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female = self.parse_filters(filters)

        # Check conflicting flags
        if show_image and (show_list or show_smartlist):
            await ctx.send("❌ Cannot use --image with --list or --smartlist!", reference=ctx.message, mention_author=False)
            return

        # Get user's shinies
        user_shinies = await db.get_all_shinies(user_id)

        # Build counts: (dex_num, name, gender_key) -> count
        form_counts = {}
        for shiny in user_shinies:
            dex_num = shiny['dex_number']
            name = shiny['name']
            gender = shiny['gender']

            has_gender_diff = utils.has_gender_difference(name)

            if has_gender_diff and gender in ['male', 'female']:
                key = (dex_num, name, gender)
            else:
                key = (dex_num, name, None)

            if key not in form_counts:
                form_counts[key] = 0
            form_counts[key] += 1

        # Get all forms from CSV
        all_forms = utils.get_full_dex_entries()

        # Build filtered list
        form_entries = []
        for dex_num, pokemon_name, has_gender_diff in all_forms:
            # Apply exclude filter first
            if self.is_excluded(pokemon_name, exclude_names):
                continue

            # Apply name search filter with accent-insensitive matching
            if name_searches:
                normalized_pokemon = normalize_string(pokemon_name.lower())
                matches_any = any(normalize_string(search.lower()) in normalized_pokemon for search in name_searches)
                if not matches_any:
                    continue

            # Apply region/type filters
            if region_filter or type_filters:
                if not self.matches_filters(pokemon_name, utils, region_filter, type_filters):
                    continue

            if has_gender_diff:
                # Add male and female entries (unless explicitly ignored)
                if not ignore_male:
                    male_count = form_counts.get((dex_num, pokemon_name, 'male'), 0)
                    form_entries.append((dex_num, pokemon_name, 'male', male_count))
                
                if not ignore_female:
                    female_count = form_counts.get((dex_num, pokemon_name, 'female'), 0)
                    form_entries.append((dex_num, pokemon_name, 'female', female_count))
            else:
                # Add single entry
                count = form_counts.get((dex_num, pokemon_name, None), 0)
                form_entries.append((dex_num, pokemon_name, None, count))

        # Apply caught/uncaught filters
        filtered_entries = []
        for entry in form_entries:
            dex_num, name, gender_key, count = entry
            if count > 0 and not show_caught:
                continue
            if count == 0 and not show_uncaught:
                continue
            filtered_entries.append(entry)

        # Apply ordering
        if order == 'desc':
            filtered_entries.sort(key=lambda x: x[3], reverse=True)
        elif order == 'asc':
            filtered_entries.sort(key=lambda x: x[3])

        if not filtered_entries:
            await ctx.send("❌ No shinies match your filters!", reference=ctx.message, mention_author=False)
            return

        # If --image flag is set, generate image
        if show_image:
            # Build header info
            header_info = {'dex_type': 'Full Shiny Dex'}
            if type_filters:
                header_info['types'] = type_filters
            if region_filter:
                header_info['regions'] = [region_filter]

            await self.send_dex_image(ctx, filtered_entries, utils, page or 1, header_info)
            return

        # If --list flag is set, send simple list format
        if show_list:
            pokemon_names = [name for _, name, _, _ in filtered_entries]
            # Remove duplicates while preserving order
            seen = set()
            unique_names = []
            for name in pokemon_names:
                if name not in seen:
                    seen.add(name)
                    unique_names.append(name)
            await self.send_pokemon_list_simple(ctx, unique_names)
            return

        # If --smartlist flag is set, send smartlist format
        if show_smartlist:
            pokemon_data = [(name, gender_key, count) for _, name, gender_key, count in filtered_entries]
            await self.send_pokemon_smartlist(ctx, pokemon_data, utils)
            return

        # Calculate stats
        total_caught = sum(1 for entry in form_entries if entry[3] > 0)
        total_forms = len(form_entries)
        total_shiny_count = sum(entry[3] for entry in filtered_entries)

        # Create pages
        lines = []
        for dex_num, name, gender_key, count in filtered_entries:
            icon = f"{config.TICK}" if count > 0 else f"{config.CROSS}"
            sparkles = f"{count} ✨" if count > 0 else "0"

            # Add gender emoji if applicable
            gender_emoji = ""
            if gender_key == 'male':
                gender_emoji = f" {config.GENDER_MALE}"
            elif gender_key == 'female':
                gender_emoji = f" {config.GENDER_FEMALE}"

            lines.append(f"{icon} **#{dex_num}** {name}{gender_emoji} - {sparkles}")

        # Paginate
        per_page = 21
        pages = []
        for i in range(0, len(lines), per_page):
            page_content = "\n".join(lines[i:i+per_page])
            pages.append(page_content)

        # Create view with only region and type filters in display name
        filter_text = "full"
        if region_filter:
            filter_text += f" - {region_filter}"
        if type_filters:
            filter_text += f" - {'/'.join(type_filters)}"

        view = ShinyDexView(ctx, pages, total_caught, total_forms, filter_text, total_shiny_count)

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

    @commands.hybrid_command(name='filter', aliases=['f'])
    @app_commands.describe(
        filter_name="Filter name (e.g., eevos, starters, legendaries)",
        options="Options: --caught, --uncaught, --orderd, --ordera, --region, --type, --exclude, --nogender, --page, --list, --smartlist, --image, --ignoremale, --ignorefemale"
    )
    async def filter_dex(self, ctx, filter_name: str = None, *, options: str = None):
        """View your shiny dex with custom filters"""
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        # If no filter name provided, show available filters
        if not filter_name:
            available_filters = get_all_filter_names()
            filter_list = ", ".join([f"`{f}`" for f in available_filters])
            embed = discord.Embed(
                title="📋 Available Filters",
                description=f"Use `filter <name>` to view a filtered dex.\n\n**Available filters:**\n{filter_list}",
                color=EMBED_COLOR
            )
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            return

        # Get the filter
        filter_data = get_filter(filter_name)
        if not filter_data:
            available_filters = get_all_filter_names()
            filter_list = ", ".join([f"`{f}`" for f in available_filters])
            await ctx.send(
                f"❌ Filter `{filter_name}` not found!\n\n**Available filters:** {filter_list}",
                reference=ctx.message, mention_author=False
            )
            return

        user_id = ctx.author.id

        # Parse options
        show_caught, show_uncaught, order, region_filter, type_filters, _, page, show_list, show_smartlist, ignore_gender, exclude_names, show_image, ignore_male, ignore_female = self.parse_filters(options)

        # Check conflicting flags
        if show_image and (show_list or show_smartlist):
            await ctx.send("❌ Cannot use --image with --list or --smartlist!", reference=ctx.message, mention_author=False)
            return

        # Get user's shinies
        user_shinies = await db.get_all_shinies(user_id)

        # Get filter Pokemon set and apply region/type/exclude filters
        filter_pokemon_set = set()
        for pokemon_name in filter_data['pokemon']:
            # Apply exclude filter first
            if self.is_excluded(pokemon_name, exclude_names):
                continue

            # Apply region/type filters
            if region_filter or type_filters:
                if not self.matches_filters(pokemon_name, utils, region_filter, type_filters):
                    continue
            filter_pokemon_set.add(pokemon_name)

        # If no Pokemon match the filters, return early
        if not filter_pokemon_set:
            await ctx.send("❌ No Pokémon in this filter match your region/type filters!", reference=ctx.message, mention_author=False)
            return

        # Build counts
        form_counts = {}
        for shiny in user_shinies:
            dex_num = shiny['dex_number']
            name = shiny['name']
            gender = shiny['gender']

            # Only process if name is in filter
            if name not in filter_pokemon_set:
                continue

            has_gender_diff = utils.has_gender_difference(name)

            # If ignore_gender is True, combine all genders into one entry
            if ignore_gender or not has_gender_diff:
                key = (dex_num, name, None)
            elif has_gender_diff and gender in ['male', 'female']:
                key = (dex_num, name, gender)
            else:
                key = (dex_num, name, None)

            if key not in form_counts:
                form_counts[key] = 0
            form_counts[key] += 1

        # Build entries from filter list
        dex_entries = []
        for pokemon_name in filter_pokemon_set:
            dex_num = utils.get_dex_number(pokemon_name)
            if dex_num is None:
                continue

            has_gender_diff = utils.has_gender_difference(pokemon_name)

            # If ignore_gender is True, create single entry with combined count
            if ignore_gender:
                # Combine male and female counts
                male_count = form_counts.get((dex_num, pokemon_name, 'male'), 0)
                female_count = form_counts.get((dex_num, pokemon_name, 'female'), 0)
                combined_count = form_counts.get((dex_num, pokemon_name, None), 0)
                total_count = male_count + female_count + combined_count

                dex_entries.append((dex_num, pokemon_name, None, total_count))
            elif has_gender_diff:
                # Add male entry (unless ignored)
                if not ignore_male:
                    male_count = form_counts.get((dex_num, pokemon_name, 'male'), 0)
                    dex_entries.append((dex_num, pokemon_name, 'male', male_count))
                
                # Add female entry (unless ignored)
                if not ignore_female:
                    female_count = form_counts.get((dex_num, pokemon_name, 'female'), 0)
                    dex_entries.append((dex_num, pokemon_name, 'female', female_count))
            else:
                count = form_counts.get((dex_num, pokemon_name, None), 0)
                dex_entries.append((dex_num, pokemon_name, None, count))

        # Sort by dex number by default
        dex_entries.sort(key=lambda x: x[0])

        # Apply caught/uncaught filters
        filtered_entries = []
        for entry in dex_entries:
            dex_num, name, gender_key, count = entry
            if count > 0 and not show_caught:
                continue
            if count == 0 and not show_uncaught:
                continue
            filtered_entries.append(entry)

        # Apply ordering
        if order == 'desc':
            filtered_entries.sort(key=lambda x: x[3], reverse=True)
        elif order == 'asc':
            filtered_entries.sort(key=lambda x: x[3])

        if not filtered_entries:
            await ctx.send("❌ No shinies match your filters!", reference=ctx.message, mention_author=False)
            return

        # If --image flag is set, generate image
        if show_image:
            # Build header info
            header_info = {'filter_name': filter_data['name']}
            if type_filters:
                header_info['types'] = type_filters
            if region_filter:
                header_info['regions'] = [region_filter]

            await self.send_dex_image(ctx, filtered_entries, utils, page or 1, header_info)
            return

        # If --list flag is set, send simple list format
        if show_list:
            pokemon_names = [name for _, name, _, _ in filtered_entries]
            # Remove duplicates while preserving order
            seen = set()
            unique_names = []
            for name in pokemon_names:
                if name not in seen:
                    seen.add(name)
                    unique_names.append(name)
            await self.send_pokemon_list_simple(ctx, unique_names)
            return

        # If --smartlist flag is set, send smartlist format
        if show_smartlist:
            pokemon_data = [(name, gender_key, count) for _, name, gender_key, count in filtered_entries]
            await self.send_pokemon_smartlist(ctx, pokemon_data, utils)
            return

        # Calculate stats
        total_caught = sum(1 for entry in dex_entries if entry[3] > 0)
        total_pokemon = len(dex_entries)
        total_shiny_count = sum(entry[3] for entry in filtered_entries)

        # Create pages
        lines = []
        for dex_num, name, gender_key, count in filtered_entries:
            icon = f"{config.TICK}" if count > 0 else f"{config.CROSS}"
            sparkles = f"{count} ✨" if count > 0 else "0"

            gender_emoji = ""
            if gender_key == 'male':
                gender_emoji = f" {config.GENDER_MALE}"
            elif gender_key == 'female':
                gender_emoji = f" {config.GENDER_FEMALE}"

            lines.append(f"{icon} **#{dex_num}** {name}{gender_emoji} - {sparkles}")

        # Paginate
        per_page = 21
        pages = []
        for i in range(0, len(lines), per_page):
            page_content = "\n".join(lines[i:i+per_page])
            pages.append(page_content)

        # Create view with filters in display name
        filter_display_name = filter_data['name']
        if region_filter:
            filter_display_name += f" - {region_filter}"
        if type_filters:
            filter_display_name += f" - {'/'.join(type_filters)}"

        view = ShinyDexView(ctx, pages, total_caught, total_pokemon, filter_display_name, total_shiny_count)

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
    await bot.add_cog(ShinyDexDisplay(bot))
