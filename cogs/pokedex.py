import discord
from discord.ext import commands
from discord import app_commands
import json
import config
import unicodedata

class PokedexView(discord.ui.View):
    """View with shiny toggle, gender toggle, form dropdowns, and navigation buttons"""

    def __init__(self, ctx, pokemon_data, all_forms, current_form_key, has_gender_diff, all_dex_numbers, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pokemon_data = pokemon_data
        self.all_forms = all_forms  # List of (form_key, form_name) for this dex number
        self.current_form_key = current_form_key
        self.has_gender_diff = has_gender_diff
        self.all_dex_numbers = all_dex_numbers  # Sorted list of all dex numbers
        self.is_shiny = False
        self.is_female = False  # False = male (default), True = female
        self.message = None
        self.current_dropdown_page = 0  # For pagination of form dropdowns

        # Build the view with appropriate components
        self.build_view()

    def build_view(self):
        """Build view components based on Pokemon properties"""
        self.clear_items()

        # Get current dex number
        current_data = self.pokemon_data[self.current_form_key]
        current_dex = current_data.get('dex_number', '0')

        # Row 1: Navigation buttons (Back, Shiny, Gender, Next)
        # Back button
        self.add_item(self.create_dex_back_button(current_dex))

        # Shiny button
        self.add_item(self.create_shiny_button())

        # Gender buttons (if applicable)
        if self.has_gender_diff:
            self.add_item(self.create_male_button())
            self.add_item(self.create_female_button())

        # Next button
        self.add_item(self.create_dex_next_button(current_dex))

        # Row 2 & 3: Form dropdowns (if multiple forms exist)
        if len(self.all_forms) > 1:
            # Calculate how many dropdowns we need (25 options max per dropdown)
            total_pages = (len(self.all_forms) + 24) // 25

            if total_pages > 1:
                # Multiple dropdowns needed - show navigation buttons
                self.add_item(self.create_prev_dropdown_button())
                self.add_item(self.create_next_dropdown_button())

            # Add up to 2 dropdowns for current page
            start_idx = self.current_dropdown_page * 50
            end_idx = min(start_idx + 50, len(self.all_forms))

            # First dropdown (25 forms)
            first_batch_end = min(start_idx + 25, end_idx)
            if start_idx < first_batch_end:
                self.add_item(self.create_form_dropdown(start_idx, first_batch_end, 1))

            # Second dropdown (next 25 forms)
            if first_batch_end < end_idx:
                self.add_item(self.create_form_dropdown(first_batch_end, end_idx, 2))

    def create_dex_back_button(self, current_dex):
        """Create button to go to previous dex number"""
        try:
            current_idx = self.all_dex_numbers.index(current_dex)
            is_first = (current_idx == 0)
        except ValueError:
            is_first = True

        button = discord.ui.Button(
            label="◀",
            style=discord.ButtonStyle.secondary,
            custom_id="dex_back",
            disabled=is_first
        )
        button.callback = self.dex_back_callback
        return button

    def create_dex_next_button(self, current_dex):
        """Create button to go to next dex number"""
        try:
            current_idx = self.all_dex_numbers.index(current_dex)
            is_last = (current_idx == len(self.all_dex_numbers) - 1)
        except ValueError:
            is_last = True

        button = discord.ui.Button(
            label="▶",
            style=discord.ButtonStyle.secondary,
            custom_id="dex_next",
            disabled=is_last
        )
        button.callback = self.dex_next_callback
        return button

    def create_shiny_button(self):
        """Create shiny toggle button"""
        button = discord.ui.Button(
            style=discord.ButtonStyle.primary if self.is_shiny else discord.ButtonStyle.secondary,
            emoji="✨",
            custom_id="toggle_shiny"
        )
        button.callback = self.toggle_shiny_callback
        return button

    def create_male_button(self):
        """Create male button"""
        button = discord.ui.Button(
            label="Male",
            style=discord.ButtonStyle.primary if not self.is_female else discord.ButtonStyle.secondary,
            emoji="♂",
            custom_id="select_male"
        )
        button.callback = self.select_male_callback
        return button

    def create_female_button(self):
        """Create female button"""
        button = discord.ui.Button(
            label="Female",
            style=discord.ButtonStyle.primary if self.is_female else discord.ButtonStyle.secondary,
            emoji="♀",
            custom_id="select_female"
        )
        button.callback = self.select_female_callback
        return button

    def create_prev_dropdown_button(self):
        """Create previous dropdown page button"""
        button = discord.ui.Button(
            label="◀",
            style=discord.ButtonStyle.primary,
            custom_id="prev_dropdown",
            disabled=(self.current_dropdown_page == 0)
        )
        button.callback = self.prev_dropdown_callback
        return button

    def create_next_dropdown_button(self):
        """Create next dropdown page button"""
        total_pages = (len(self.all_forms) + 49) // 50
        button = discord.ui.Button(
            label="▶",
            style=discord.ButtonStyle.primary,
            custom_id="next_dropdown",
            disabled=(self.current_dropdown_page >= total_pages - 1)
        )
        button.callback = self.next_dropdown_callback
        return button

    def create_form_dropdown(self, start_idx, end_idx, dropdown_num):
        """Create dropdown menu for Pokemon forms"""
        options = []
        for i in range(start_idx, end_idx):
            form_key, form_name = self.all_forms[i]
            # Mark current form as default
            is_current = (form_key == self.current_form_key)
            options.append(
                discord.SelectOption(
                    label=form_name[:100],  # Discord limit
                    value=form_key,
                    default=is_current
                )
            )

        select = discord.ui.Select(
            placeholder=f"Select a form ({start_idx + 1}-{end_idx})",
            options=options,
            custom_id=f"form_select_{dropdown_num}"
        )
        select.callback = self.form_select_callback
        return select

    async def dex_back_callback(self, interaction: discord.Interaction):
        """Go to previous dex number"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        current_data = self.pokemon_data[self.current_form_key]
        current_dex = current_data.get('dex_number', '0')

        try:
            current_idx = self.all_dex_numbers.index(current_dex)
            if current_idx > 0:
                # Get previous dex number
                prev_dex = self.all_dex_numbers[current_idx - 1]

                # Get the cog to look up the Pokemon
                cog = self.ctx.bot.get_cog('Pokedex')
                if cog and prev_dex in cog.dex_number_forms:
                    # Get first form of previous dex number
                    prev_form_key, _ = cog.dex_number_forms[prev_dex][0]

                    # Update to new Pokemon
                    self.current_form_key = prev_form_key
                    self.all_forms = cog.dex_number_forms[prev_dex]

                    # Check if new Pokemon has gender difference
                    new_data = self.pokemon_data[prev_form_key]
                    new_pokemon_name = new_data.get('name', '')
                    self.has_gender_diff = new_pokemon_name in config.GENDER_DIFFERENCE_POKEMON

                    # Reset states
                    self.is_female = False
                    self.current_dropdown_page = 0

                    self.build_view()
                    embed = await self.create_embed()
                    await interaction.response.edit_message(embed=embed, view=self)
                    return
        except (ValueError, IndexError):
            pass

        await interaction.response.defer()

    async def dex_next_callback(self, interaction: discord.Interaction):
        """Go to next dex number"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        current_data = self.pokemon_data[self.current_form_key]
        current_dex = current_data.get('dex_number', '0')

        try:
            current_idx = self.all_dex_numbers.index(current_dex)
            if current_idx < len(self.all_dex_numbers) - 1:
                # Get next dex number
                next_dex = self.all_dex_numbers[current_idx + 1]

                # Get the cog to look up the Pokemon
                cog = self.ctx.bot.get_cog('Pokedex')
                if cog and next_dex in cog.dex_number_forms:
                    # Get first form of next dex number
                    next_form_key, _ = cog.dex_number_forms[next_dex][0]

                    # Update to new Pokemon
                    self.current_form_key = next_form_key
                    self.all_forms = cog.dex_number_forms[next_dex]

                    # Check if new Pokemon has gender difference
                    new_data = self.pokemon_data[next_form_key]
                    new_pokemon_name = new_data.get('name', '')
                    self.has_gender_diff = new_pokemon_name in config.GENDER_DIFFERENCE_POKEMON

                    # Reset states
                    self.is_female = False
                    self.current_dropdown_page = 0

                    self.build_view()
                    embed = await self.create_embed()
                    await interaction.response.edit_message(embed=embed, view=self)
                    return
        except (ValueError, IndexError):
            pass

        await interaction.response.defer()

    async def toggle_shiny_callback(self, interaction: discord.Interaction):
        """Toggle between normal and shiny sprite"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        self.is_shiny = not self.is_shiny
        self.build_view()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def select_male_callback(self, interaction: discord.Interaction):
        """Select male sprite"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        if self.is_female:  # Only update if currently showing female
            self.is_female = False
            self.build_view()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def select_female_callback(self, interaction: discord.Interaction):
        """Select female sprite"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        if not self.is_female:  # Only update if currently showing male
            self.is_female = True
            self.build_view()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def toggle_gender_callback(self, interaction: discord.Interaction):
        """Toggle between male and female sprite"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        self.is_female = not self.is_female
        self.build_view()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def prev_dropdown_callback(self, interaction: discord.Interaction):
        """Go to previous dropdown page"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        if self.current_dropdown_page > 0:
            self.current_dropdown_page -= 1
            self.build_view()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_dropdown_callback(self, interaction: discord.Interaction):
        """Go to next dropdown page"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        total_pages = (len(self.all_forms) + 49) // 50
        if self.current_dropdown_page < total_pages - 1:
            self.current_dropdown_page += 1
            self.build_view()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def form_select_callback(self, interaction: discord.Interaction):
        """Handle form selection from dropdown"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your pokedex!", ephemeral=True)
            return

        # Get selected form key
        selected_form_key = interaction.data['values'][0]

        if selected_form_key not in self.pokemon_data:
            await interaction.response.send_message("❌ Form not found!", ephemeral=True)
            return

        # Update current form
        self.current_form_key = selected_form_key

        # Check if new form has gender difference
        new_data = self.pokemon_data[selected_form_key]
        new_pokemon_name = new_data.get('name', '')
        self.has_gender_diff = new_pokemon_name in config.GENDER_DIFFERENCE_POKEMON

        # Reset gender to male when switching forms
        self.is_female = False

        # Reset dropdown page to find the selected form
        for i, (form_key, _) in enumerate(self.all_forms):
            if form_key == selected_form_key:
                self.current_dropdown_page = i // 50
                break

        self.build_view()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        """Create embed for current Pokemon form"""
        data = self.pokemon_data[self.current_form_key]

        # Create title
        title = f"#{data['dex_number']} — {data['name']}"

        # Create embed
        embed = discord.Embed(
            title=title,
            description=data.get('description', 'No description available.'),
            color=discord.Color.from_str(config.EMBED_COLOR) if isinstance(config.EMBED_COLOR, str) else config.EMBED_COLOR
        )

        # Get image URL
        image_url = data['image_url']

        # Apply gender difference (female suffix)
        if self.is_female and self.has_gender_diff:
            # Replace .png with F.png (e.g., 1.png -> 1F.png)
            image_url = image_url.replace('.png', 'F.png')

        # Apply shiny transformation
        if self.is_shiny:
            image_url = image_url.replace('/images/', '/shiny/')

        embed.set_image(url=image_url)

        # Add Evolution field if exists
        evolution_text = self.format_evolution(data)
        if evolution_text:
            embed.add_field(name="Evolution", value=evolution_text, inline=False)

        # Add Types field
        if data.get('types'):
            types_text = '\n'.join(data['types'])
            embed.add_field(name="Types", value=types_text, inline=True)

        # Add Region field
        if data.get('region'):
            embed.add_field(name="Region", value=data['region'], inline=True)

        # Add Catchable field
        if data.get('catchable'):
            embed.add_field(name="Catchable", value=data['catchable'], inline=True)

        # Add Base Stats field
        if data.get('base_stats'):
            stats = data['base_stats']
            total = sum(stats.values())
            stats_text = '\n'.join([
                f"**HP:** {stats.get('HP', 0)}",
                f"**Attack:** {stats.get('Attack', 0)}",
                f"**Defense:** {stats.get('Defense', 0)}",
                f"**Sp. Atk:** {stats.get('Sp. Atk', 0)}",
                f"**Sp. Def:** {stats.get('Sp. Def', 0)}",
                f"**Speed:** {stats.get('Speed', 0)}",
                f"**Total: {total}**"
            ])
            embed.add_field(name="Base Stats", value=stats_text, inline=True)

        # Add Names field
        if data.get('names'):
            names_text = self.format_names(data['names'])
            embed.add_field(name="Names", value=names_text, inline=True)

        # Add Appearance field
        if data.get('appearance'):
            appearance = data['appearance']
            appearance_text = f"Height: {appearance.get('height_m', 'N/A')} m\nWeight: {appearance.get('weight_kg', 'N/A')} kg"
            embed.add_field(name="Appearance", value=appearance_text, inline=True)

        # Add Gender Ratio field
        if data.get('gender_ratio'):
            gender_text = self.format_gender_ratio(data['gender_ratio'])
            embed.add_field(name="Gender Ratio", value=gender_text, inline=True)

        # Add Egg Groups field
        if data.get('egg_groups'):
            egg_groups = data['egg_groups']
            if isinstance(egg_groups, list):
                egg_groups_text = '\n'.join(egg_groups)
            else:
                egg_groups_text = egg_groups
            embed.add_field(name="Egg Groups", value=egg_groups_text, inline=True)

        # Add Hatch Time field
        if data.get('hatch_time'):
            embed.add_field(name="Hatch Time", value=data['hatch_time'], inline=True)

        # Build footer
        footer_parts = []

        if data.get('rarity'):
            footer_parts.append(f"Rarity: {data['rarity']}")

        if self.is_shiny:
            footer_parts.append("✨ Shiny Form")

        if self.is_female and self.has_gender_diff:
            footer_parts.append("♀ Female")
        elif self.has_gender_diff:
            footer_parts.append("♂ Male")

        # Get shiny count for this specific Pokemon (await the coroutine)
        pokemon_name = data.get('name', '')
        user_id = self.ctx.author.id

        # Pass gender info if this Pokemon has gender difference
        gender_filter = None
        if self.has_gender_diff:
            gender_filter = 'female' if self.is_female else 'male'

        # This will be awaited when the embed is created
        shiny_count = await self.get_shiny_count(user_id, pokemon_name, gender_filter)

        footer_parts.append(f"You have {shiny_count} shiny of this pokémon!")

        if footer_parts:
            embed.set_footer(text=" • ".join(footer_parts))

        return embed

    async def get_shiny_count(self, user_id, pokemon_name, gender_filter=None):
        """Get the count of shinies for a specific Pokemon name (and gender if applicable)"""
        try:
            # Import db here to avoid circular imports
            from database import db

            # Get all user's shinies
            all_shinies = await db.get_all_shinies(user_id)

            # Count shinies matching this exact Pokemon name
            if gender_filter:
                # For gender difference Pokemon, count only matching gender
                count = sum(1 for shiny in all_shinies 
                           if shiny['name'] == pokemon_name and shiny['gender'] == gender_filter)
            else:
                # For non-gender difference Pokemon, count all
                count = sum(1 for shiny in all_shinies if shiny['name'] == pokemon_name)

            return count
        except Exception as e:
            print(f"Error getting shiny count: {e}")
            return 0

    def format_evolution(self, data):
        """Format evolution information from fields"""
        fields = data.get('fields', {})
        if 'Evolution' in fields:
            return fields['Evolution']
        return None

    def format_names(self, names_dict):
        """Format Pokemon names in different languages"""
        lines = []
        flag_map = {
            'ja': '🇯🇵',
            'en': '🇬🇧',
            'de': '🇩🇪',
            'fr': '🇫🇷'
        }

        for lang, names in names_dict.items():
            flag = flag_map.get(lang, '🏳️')
            if isinstance(names, list):
                for name in names:
                    lines.append(f"{flag} {name}")
            else:
                lines.append(f"{flag} {names}")

        return '\n'.join(lines) if lines else 'N/A'

    def format_gender_ratio(self, gender_ratio):
        """Format gender ratio with emoji"""
        if gender_ratio == "Genderless":
            return f"{config.GENDER_UNKNOWN} Genderless"

        # If already formatted with emoji from JSON, extract percentages and reformat
        if '<:male:' in gender_ratio or '<:female:' in gender_ratio:
            # Extract numbers from the formatted string
            import re
            numbers = re.findall(r'(\d+\.?\d*)\s*%', gender_ratio)
            if len(numbers) >= 2:
                male_pct = numbers[0]
                female_pct = numbers[1]
                return f"{config.GENDER_MALE} {male_pct}% - {config.GENDER_FEMALE} {female_pct}%"

        # Parse gender ratio (e.g., "87.5% male, 12.5% female")
        if "male" in gender_ratio.lower() and "female" in gender_ratio.lower():
            # Extract percentages
            import re
            numbers = re.findall(r'(\d+\.?\d*)\s*%', gender_ratio)
            if len(numbers) >= 2:
                male_pct = numbers[0]
                female_pct = numbers[1]
                return f"{config.GENDER_MALE} {male_pct}% - {config.GENDER_FEMALE} {female_pct}%"

        return gender_ratio

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass


class Pokedex(commands.Cog):
    """Pokedex information commands"""

    def __init__(self, bot):
        self.bot = bot
        self.pokemon_data = {}
        self.name_index = {}  # Maps all possible names to form keys
        self.dex_number_forms = {}  # Maps dex numbers to list of (form_key, form_name)
        self.load_pokemon_data()

    def normalize_name(self, name):
        """Remove accents and normalize name for searching"""
        # Normalize unicode characters (NFD = decompose accents)
        normalized = unicodedata.normalize('NFD', name)
        # Remove accent marks (combining characters)
        without_accents = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        return without_accents.lower().strip()

    def load_pokemon_data(self):
        """Load Pokemon data from JSON file"""
        try:
            with open('alldata/pokemon_data.json', 'r', encoding='utf-8') as f:
                self.pokemon_data = json.load(f)

            # Build name index and dex number mapping
            for form_key, data in self.pokemon_data.items():
                dex_num = data.get('dex_number', '0')
                pokemon_name = data.get('name', '')

                # Add to dex number forms mapping
                if dex_num not in self.dex_number_forms:
                    self.dex_number_forms[dex_num] = []
                self.dex_number_forms[dex_num].append((form_key, pokemon_name))

                # Index primary name (with and without accents)
                if pokemon_name:
                    self.name_index[pokemon_name.lower()] = form_key
                    normalized = self.normalize_name(pokemon_name)
                    self.name_index[normalized] = form_key

                # Index all alternate names (with and without accents)
                if 'names' in data:
                    for lang, names in data['names'].items():
                        if isinstance(names, list):
                            for name in names:
                                self.name_index[name.lower()] = form_key
                                normalized = self.normalize_name(name)
                                self.name_index[normalized] = form_key
                        else:
                            self.name_index[names.lower()] = form_key
                            normalized = self.normalize_name(names)
                            self.name_index[normalized] = form_key

            print(f"✅ Loaded {len(self.pokemon_data)} Pokemon entries")
            print(f"✅ Indexed {len(self.name_index)} Pokemon names")
            print(f"✅ Mapped {len(self.dex_number_forms)} unique dex numbers")
        except Exception as e:
            print(f"❌ Error loading alldata/pokemon_data.json: {e}")

    @commands.hybrid_command(name='dex', aliases=['d', 'pokedex'])
    @app_commands.describe(pokemon="Name of the Pokemon to look up")
    async def dex_command(self, ctx, *, pokemon: str):
        """
        Look up Pokemon information in the Pokedex
        Usage: m!dex <pokemon name>
        Examples:
          m!dex bulbasaur
          m!dex bisasam (German name)
          m!dex ibui (works for Ībui/Eevee)
          m!dex deoxys
        """
        pokemon_lower = pokemon.lower().strip()

        # Look up Pokemon by name (try exact match first)
        form_key = self.name_index.get(pokemon_lower)

        # If not found, try normalized (accent-removed) version
        if not form_key:
            normalized = self.normalize_name(pokemon)
            form_key = self.name_index.get(normalized)

        if not form_key:
            await ctx.send(f"❌ Pokemon `{pokemon}` not found in Pokedex", reference=ctx.message, mention_author=False)
            return

        if form_key not in self.pokemon_data:
            await ctx.send(f"❌ Pokemon data for `{pokemon}` not found", reference=ctx.message, mention_author=False)
            return

        # Get dex number and all forms for this Pokemon
        data = self.pokemon_data[form_key]
        dex_num = data.get('dex_number', '0')
        all_forms = self.dex_number_forms.get(dex_num, [(form_key, data['name'])])

        # Check if this Pokemon has gender differences
        pokemon_name = data.get('name', '')
        has_gender_diff = pokemon_name in config.GENDER_DIFFERENCE_POKEMON

        # Get sorted list of all dex numbers for navigation
        all_dex_numbers = sorted(self.dex_number_forms.keys(), key=lambda x: int(x) if x.isdigit() else 0)

        # Create view with buttons and dropdowns
        view = PokedexView(ctx, self.pokemon_data, all_forms, form_key, has_gender_diff, all_dex_numbers)
        embed = await view.create_embed()

        message = await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=False)
        view.message = message


async def setup(bot):
    await bot.add_cog(Pokedex(bot))
