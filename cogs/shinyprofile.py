import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor
import aiohttp
import os
import csv
import config
from database import db


class BackgroundSelectView(discord.ui.View):
    """View for selecting background in customize command"""

    def __init__(self, user_id: int, backgrounds: list):
        super().__init__(timeout=60.0)
        self.user_id = user_id
        self.selected_background = None

        # Add background dropdown
        options = []
        for bg in backgrounds:
            # Remove .png extension for display
            display_name = bg.replace('.png', '').replace('_', ' ').title()
            options.append(discord.SelectOption(label=display_name, value=bg))

        self.background_select.options = options

    @discord.ui.select(placeholder="Choose a background...", min_values=1, max_values=1)
    async def background_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your customization menu!", ephemeral=True)
            return

        self.selected_background = select.values[0]
        await interaction.response.send_message(
            f"✅ Background set to: **{select.values[0].replace('.png', '').replace('_', ' ').title()}**. Now click confirm button to save changes.",
            ephemeral=True
        )

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your customization menu!", ephemeral=True)
            return

        if self.selected_background:
            await db.set_user_customization(self.user_id, background=self.selected_background)
            await interaction.response.send_message(
                f"✅ Your background has been saved!",
                ephemeral=True
            )
            self.stop()
        else:
            await interaction.response.send_message("❌ Please select a background first!", ephemeral=True)


class ShinyStatsImage(commands.Cog):
    """Generate visual shiny statistics cards"""

    def __init__(self, bot):
        self.bot = bot
        self.backgrounds_folder = 'shinystats/backgrounds'
        self.fonts_folder = 'shinystats/fonts'

        # GitHub repository details
        self.github_user = 'cynthiaofpower'
        self.github_repo = 'meowthfonts'
        self.github_branch = 'main'  # or 'master' - adjust if needed

        # Cache for Pokemon name to CDN number mapping
        self.pokemon_cdn_mapping = {}
        self.load_pokemon_mapping()

        # Predefined solid colors
        self.solid_colors = {
            'red.png': '#8B0000',
            'blue.png': '#00008B',
            'green.png': '#006400',
            'purple.png': '#4B0082',
            'orange.png': '#FF8C00',
            'pink.png': '#FF1493',
            'cyan.png': '#008B8B',
            'yellow.png': '#FFD700',
            'black.png': '#000000',
            'gray.png': '#2F4F4F'
        }

        # Initialize resource download on cog load
        self.bot.loop.create_task(self.initialize_resources())

    async def initialize_resources(self):
        """Download fonts and backgrounds from GitHub on startup"""
        await self.download_fonts()
        await self.download_backgrounds()

    async def download_file_from_github(self, file_path: str, save_path: str):
        """Download a single file from GitHub repository"""
        url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/{self.github_branch}/{file_path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        content = await resp.read()

                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                        with open(save_path, 'wb') as f:
                            f.write(content)
                        print(f"✅ Downloaded: {file_path}")
                        return True
                    else:
                        print(f"❌ Failed to download {file_path}: Status {resp.status}")
                        return False
        except Exception as e:
            print(f"❌ Error downloading {file_path}: {e}")
            return False

    async def get_github_directory_contents(self, directory: str):
        """Get list of files in a GitHub directory"""
        url = f"https://api.github.com/repos/{self.github_user}/{self.github_repo}/contents/{directory}?ref={self.github_branch}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        contents = await resp.json()
                        return [item['name'] for item in contents if item['type'] == 'file']
                    else:
                        print(f"❌ Failed to fetch directory contents: Status {resp.status}")
                        return []
        except Exception as e:
            print(f"❌ Error fetching directory contents: {e}")
            return []

    async def download_fonts(self):
        """Download all fonts from GitHub repository"""
        print("📥 Downloading fonts from GitHub...")

        # Create fonts directory
        os.makedirs(self.fonts_folder, exist_ok=True)

        # Get list of font files
        font_files = await self.get_github_directory_contents('fonts')

        if not font_files:
            print("⚠️ No fonts found in repository")
            return

        # Download each font
        for font_file in font_files:
            if font_file.endswith('.ttf') or font_file.endswith('.otf'):
                github_path = f"fonts/{font_file}"
                local_path = os.path.join(self.fonts_folder, font_file)

                # Skip if already exists
                if os.path.exists(local_path):
                    print(f"⏭️ Font already exists: {font_file}")
                    continue

                await self.download_file_from_github(github_path, local_path)

        print("✅ Font download complete!")

    async def download_backgrounds(self):
        """Download all backgrounds from GitHub repository"""
        print("📥 Downloading backgrounds from GitHub...")

        # Create backgrounds directory
        os.makedirs(self.backgrounds_folder, exist_ok=True)

        # Get list of background files
        background_files = await self.get_github_directory_contents('backgrounds')

        if not background_files:
            print("⚠️ No backgrounds found in repository")
            return

        # Download each background
        for bg_file in background_files:
            if bg_file.endswith('.png') or bg_file.endswith('.jpg') or bg_file.endswith('.jpeg'):
                github_path = f"backgrounds/{bg_file}"
                local_path = os.path.join(self.backgrounds_folder, bg_file)

                # Skip if already exists
                if os.path.exists(local_path):
                    print(f"⏭️ Background already exists: {bg_file}")
                    continue

                await self.download_file_from_github(github_path, local_path)

        print("✅ Background download complete!")

    def load_pokemon_mapping(self):
        """Load Pokemon name to CDN number mapping from CSV file"""
        mapping_file = 'data/pokemon_cdn_mapping.csv'  # You can change this path

        if not os.path.exists(mapping_file):
            print(f"⚠️ Warning: Pokemon CDN mapping file not found at {mapping_file}")
            return

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Assuming CSV has columns: 'name' and 'cdn_number'
                    # Adjust column names based on your actual CSV structure
                    pokemon_name = row.get('name', '').strip()
                    cdn_number = row.get('cdn_number', '').strip()

                    if pokemon_name and cdn_number:
                        # Store both lowercase and original case for flexible matching
                        self.pokemon_cdn_mapping[pokemon_name.lower()] = int(cdn_number)

            print(f"✅ Loaded {len(self.pokemon_cdn_mapping)} Pokemon CDN mappings")
        except Exception as e:
            print(f"❌ Error loading Pokemon CDN mapping: {e}")

    def get_cdn_number(self, pokemon_name: str) -> int:
        """Get CDN number for a Pokemon name"""
        # Try exact match (case-insensitive)
        cdn_number = self.pokemon_cdn_mapping.get(pokemon_name.lower())

        if cdn_number is None:
            print(f"⚠️ Warning: No CDN mapping found for '{pokemon_name}'")
            # Return 0 or some default value if not found
            return 0

        return cdn_number

    def get_available_backgrounds(self):
        """Get list of available background files"""
        backgrounds = []

        # Add image backgrounds from folder
        if os.path.exists(self.backgrounds_folder):
            for file in os.listdir(self.backgrounds_folder):
                if file.endswith('.png') and file != 'default.png':
                    backgrounds.append(file)

        # Add gray as default first
        backgrounds.insert(0, 'black.png')

        # Add solid color backgrounds
        for color_name in self.solid_colors.keys():
            if color_name not in backgrounds:
                backgrounds.append(color_name)

        return backgrounds

    def create_background(self, background_name: str, width: int, height: int):
        """Create or load background image"""
        # Check if it's a solid color
        if background_name in self.solid_colors:
            bg = Image.new('RGBA', (width, height), ImageColor.getrgb(self.solid_colors[background_name]))
            return bg

        # Load image background
        bg_path = os.path.join(self.backgrounds_folder, background_name)
        if os.path.exists(bg_path):
            bg = Image.open(bg_path).convert('RGBA')
            bg = bg.resize((width, height), Image.Resampling.LANCZOS)
            return bg

        # Fallback to gray (default)
        return Image.new('RGBA', (width, height), ImageColor.getrgb(self.solid_colors['gray.png']))

    async def fetch_pokemon_image(self, pokemon_name: str):
        """Fetch Pokemon image from Poketwo CDN using Pokemon name"""
        cdn_number = self.get_cdn_number(pokemon_name)

        if cdn_number == 0:
            return None

        url = f"https://cdn.poketwo.net/shiny/{cdn_number}.png"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data))
            except Exception as e:
                print(f"Error fetching image for {pokemon_name} (CDN: {cdn_number}): {e}")
        return None

    async def fetch_user_avatar(self, user: discord.User):
        """Fetch user's avatar"""
        async with aiohttp.ClientSession() as session:
            try:
                avatar_url = user.display_avatar.url
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data))
            except:
                pass
        return None

    async def create_stats_image(self, user: discord.User, stats_data: dict, background_name: str, user_title: str):
        """Create the shiny stats image"""
        # Image dimensions: 1024x576
        width, height = 1024, 576

        # Load/create background
        bg = self.create_background(background_name, width, height)

        # Create overlay for glass panels
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Split point (moved slightly more right to give left side more room)
        split_x = 570

        # Glass panel settings
        glass_color = (20, 20, 40, 180)  # Dark with transparency
        border_color = (255, 255, 255, 80)  # Subtle white border

        # === LEFT SIDE: Two Panels ===
        left_margin = 20
        panel_width = split_x - (2 * left_margin)

        # PANEL 1: Profile (User avatar + username + title)
        profile_panel_y = 20
        profile_panel_height = 100

        overlay_draw.rounded_rectangle(
            [(left_margin, profile_panel_y), 
             (left_margin + panel_width, profile_panel_y + profile_panel_height)],
            radius=15,
            fill=glass_color
        )
        overlay_draw.rounded_rectangle(
            [(left_margin, profile_panel_y), 
             (left_margin + panel_width, profile_panel_y + profile_panel_height)],
            radius=15,
            outline=border_color,
            width=2
        )

        # PANEL 2: Stats (bigger panel below profile)
        stats_panel_y = profile_panel_y + profile_panel_height + 15
        stats_panel_height = height - stats_panel_y - 20

        overlay_draw.rounded_rectangle(
            [(left_margin, stats_panel_y), 
             (left_margin + panel_width, stats_panel_y + stats_panel_height)],
            radius=15,
            fill=glass_color
        )
        overlay_draw.rounded_rectangle(
            [(left_margin, stats_panel_y), 
             (left_margin + panel_width, stats_panel_y + stats_panel_height)],
            radius=15,
            outline=border_color,
            width=2
        )

        # === RIGHT SIDE: Pokemon Panel ===
        right_margin = 20
        pokemon_panel_x = split_x + 10
        pokemon_panel_y = 20
        pokemon_panel_width = width - pokemon_panel_x - right_margin
        pokemon_panel_height = height - 40

        overlay_draw.rounded_rectangle(
            [(pokemon_panel_x, pokemon_panel_y), 
             (pokemon_panel_x + pokemon_panel_width, pokemon_panel_y + pokemon_panel_height)],
            radius=15,
            fill=glass_color
        )
        overlay_draw.rounded_rectangle(
            [(pokemon_panel_x, pokemon_panel_y), 
             (pokemon_panel_x + pokemon_panel_width, pokemon_panel_y + pokemon_panel_height)],
            radius=15,
            outline=border_color,
            width=2
        )

        # Composite overlay onto background
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # Load fonts
        try:
            username_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 24)
            title_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Regular.ttf'), 16)
            header_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Bold.ttf'), 25)
            stat_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Medium.ttf'), 23)
            value_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 23)
        except:
            username_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            stat_font = ImageFont.load_default()
            value_font = ImageFont.load_default()

        # Colors
        text_white = (255, 255, 255)
        text_gold = (255, 215, 0)
        text_cyan = (100, 200, 255)
        text_gray = (180, 180, 180)
        text_coral = (255, 123, 137)
        text_silver = (192, 192, 192)
        text_royalblue = (128, 0, 128)

        # === PANEL 1 CONTENT: Profile ===
        # Fetch and draw user avatar
        avatar_size = 70
        avatar_x = left_margin + 15
        avatar_y = profile_panel_y + 15

        avatar_img = await self.fetch_user_avatar(user)
        if avatar_img:
            avatar_img = avatar_img.convert('RGBA').resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

            # Create circular mask for avatar
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (avatar_size, avatar_size)], fill=255)

            # Apply mask and paste
            bg.paste(avatar_img, (avatar_x, avatar_y), mask)

        # Username and title next to avatar
        username_x = avatar_x + avatar_size + 15
        username_y = profile_panel_y + 25
        draw.text((username_x, username_y), user.display_name, font=username_font, fill=text_white)

        # User title below username
        title_y = username_y + 28
        draw.text((username_x, title_y), user_title, font=title_font, fill=text_gray)

        # === PANEL 2 CONTENT: Stats ===
        stats_x = left_margin + 20
        stats_y = stats_panel_y + 20
        line_height = 32

        # Column positions - adjusted for better spacing
        col1_x = stats_x
        col2_x = stats_x + 260  # Increased from 220 to 260 for more separation

        # Header
        draw.text((col1_x, stats_y), "Collection Stats", font=header_font, fill=text_gold)
        draw.text((col2_x, stats_y), "Pokédex Progress", font=header_font, fill=text_gold)
        stats_y += 40

        # Left column stats
        left_stats = [
            ("Non-Event Shiny:", stats_data.get('total_non_event', 0)),
            ("Event Shinies:", stats_data.get('event_shinies', 0)),
            ("Rare Shinies:", stats_data.get('rare_shinies', 0)),
            ("Regional Shinies:", stats_data.get('regional_shinies', 0)),
            ("Mint Shinies:", stats_data.get('mint_shinies', 0))
        ]

        current_y = stats_y
        for label, value in left_stats:
            draw.text((col1_x, current_y), label, font=stat_font, fill=text_white)

            # Get the width of the label text to position value right after it
            bbox = draw.textbbox((0, 0), label, font=stat_font)
            label_width = bbox[2] - bbox[0]

            # Add small padding (5 pixels) after the label
            value_x = col1_x + label_width + 5
            draw.text((value_x, current_y), str(value), font=value_font, fill=text_silver)
            current_y += line_height

        # Right column stats
        right_stats = [
            ("Basic Dex:", f"{stats_data.get('basic_dex', 0)}/{stats_data.get('total_unique_dex', 0)}"),
            ("Full Dex:", f"{stats_data.get('full_dex', 0)}/{stats_data.get('total_forms', 0)}")
        ]

        current_y = stats_y
        for label, value in right_stats:
            draw.text((col2_x, current_y), label, font=stat_font, fill=text_white)

            # Get the width of the label text
            bbox = draw.textbbox((0, 0), label, font=stat_font)
            label_width = bbox[2] - bbox[0]

            # Add small padding after the label
            value_x = col2_x + label_width + 5
            draw.text((value_x, current_y), value, font=value_font, fill=text_silver)
            current_y += line_height

        # === TOP 5 MOST COLLECTED POKEMON ===
        top_5_y = stats_panel_y + stats_panel_height - 150

        # Draw separator line
        separator_y = top_5_y - 10
        draw.line([(stats_x, separator_y), (stats_x + panel_width - 40, separator_y)], 
                  fill=(255, 255, 255, 100), width=1)

        # Header
        draw.text((stats_x, top_5_y), "Top 5 Most Collected", font=header_font, fill=text_gold)
        top_5_y += 30

        # Get top 5 most collected pokemon
        top_pokemon = stats_data.get('top_5_pokemon', [])

        if top_pokemon:
            # Display in horizontal row
            pokemon_size = 70
            spacing = 95  # Increased spacing slightly
            start_x = stats_x + 10

            for i, (name, count) in enumerate(top_pokemon):
                if i >= 5:
                    break

                poke_x = start_x + (i * spacing)
                poke_y = top_5_y + 15

                # Fetch and draw pokemon image using name
                poke_img = await self.fetch_pokemon_image(name)
                if poke_img:
                    poke_img = poke_img.convert('RGBA')
                    poke_img.thumbnail((pokemon_size, pokemon_size), Image.Resampling.LANCZOS)

                    # Create circular mask
                    mask = Image.new('L', (pokemon_size, pokemon_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([(0, 0), (pokemon_size, pokemon_size)], fill=255)

                    # Create white circle background
                    circle_bg = Image.new('RGBA', (pokemon_size, pokemon_size), (255, 255, 255, 30))
                    circle_draw = ImageDraw.Draw(circle_bg)
                    circle_draw.ellipse([(0, 0), (pokemon_size, pokemon_size)], 
                                       outline=(255, 255, 255, 150), width=2)

                    bg.paste(circle_bg, (poke_x, poke_y), mask)
                    bg.paste(poke_img, (poke_x, poke_y), poke_img)

                # Draw count badge below pokemon
                count_text = f"x{count}"
                try:
                    count_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Bold.ttf'), 17)
                except:
                    count_font = ImageFont.load_default()

                # Center the count text
                bbox = draw.textbbox((0, 0), count_text, font=count_font)
                count_width = bbox[2] - bbox[0]
                count_x = poke_x + (pokemon_size - count_width) // 2
                count_y = poke_y + pokemon_size + 5

                # Draw count with background
                padding = 4
                draw.rounded_rectangle(
                    [(count_x - padding, count_y - padding), 
                     (count_x + count_width + padding, count_y + 16)],
                    radius=8,
                    fill=(0, 0, 0, 180)
                )
                draw.text((count_x, count_y), count_text, font=count_font, fill=text_cyan)

        # === RIGHT PANEL CONTENT: Showcase Pokemon ===
        # Header: "My Favorite Shiny" (removed sparkle emoji)
        showcase_header_y = pokemon_panel_y + 20
        showcase_text = "Display Pokémon"

        # Center the header text
        bbox = draw.textbbox((0, 0), showcase_text, font=header_font)
        header_width = bbox[2] - bbox[0]
        header_x = pokemon_panel_x + (pokemon_panel_width - header_width) // 2
        draw.text((header_x, showcase_header_y), showcase_text, font=header_font, fill=text_gold)

        

        # Showcase pokemon data
        showcase_data = stats_data.get('showcase_pokemon')

        if showcase_data:
            # Nickname (above image)
            nickname_y = showcase_header_y + 40
            nickname = showcase_data.get('nickname', 'No Nickname')

            try:
                nickname_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-MediumItalic.ttf'), 22)
            except:
                try:
                    nickname_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Medium.ttf'), 22)
                except:
                    nickname_font = stat_font

            # Center nickname
            bbox = draw.textbbox((0, 0), f'"{nickname}"', font=nickname_font)
            nick_width = bbox[2] - bbox[0]
            nick_x = pokemon_panel_x + (pokemon_panel_width - nick_width) // 2
            draw.text((nick_x, nickname_y), f'"{nickname}"', font=nickname_font, fill=(200, 200, 255))

            # Pokemon Image - use name instead of dex_number
            pokemon_img = await self.fetch_pokemon_image(showcase_data['name'])
            if pokemon_img:
                pokemon_img = pokemon_img.convert('RGBA')

                # Resize to fit in panel
                max_size = 300
                pokemon_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                # Center the pokemon
                poke_w, poke_h = pokemon_img.size
                poke_x = pokemon_panel_x + (pokemon_panel_width - poke_w) // 2
                poke_y = nickname_y + 50

                bg.paste(pokemon_img, (poke_x, poke_y), pokemon_img)

                # Pokemon name (below image)
                name_y = poke_y + poke_h + 15
                pokemon_name = showcase_data['name']

                try:
                    name_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 24)
                except:
                    name_font = username_font

                # Center the name
                bbox = draw.textbbox((0, 0), pokemon_name, font=name_font)
                name_width = bbox[2] - bbox[0]
                name_x = pokemon_panel_x + (pokemon_panel_width - name_width) // 2
                draw.text((name_x, name_y), pokemon_name, font=name_font, fill=text_white)

                # Level and IV (below name)
                level = showcase_data['level']
                iv = showcase_data['iv_percent']
                gender = showcase_data['gender']

                # Gender symbol (using text symbols that PIL can render)
                gender_symbol = ""
                if gender == 'male':
                    gender_symbol = "M"
                elif gender == 'female':
                    gender_symbol = "F"
                else:
                    gender_symbol = "-"

                stats_text = f"{gender_symbol} | Level {level}  •  {iv:.2f}% IV"

                try:
                    info_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Regular.ttf'), 18)
                except:
                    info_font = stat_font

                # Center the stats
                bbox = draw.textbbox((0, 0), stats_text, font=info_font)
                stats_width = bbox[2] - bbox[0]
                stats_x = pokemon_panel_x + (pokemon_panel_width - stats_width) // 2
                stats_y = name_y + 35
                draw.text((stats_x, stats_y), stats_text, font=info_font, fill=text_coral)
        else:
            # No showcase pokemon set - show placeholder
            placeholder_y = pokemon_panel_y + (pokemon_panel_height // 2) - 50
            placeholder_text = "No Pokémon Showcased"
            placeholder_hint = "Use m!setfavorite <id> to set"

            # Center placeholder text
            bbox = draw.textbbox((0, 0), placeholder_text, font=username_font)
            placeholder_width = bbox[2] - bbox[0]
            placeholder_x = pokemon_panel_x + (pokemon_panel_width - placeholder_width) // 2
            draw.text((placeholder_x, placeholder_y), placeholder_text, font=username_font, fill=(150, 150, 150))

            bbox = draw.textbbox((0, 0), placeholder_hint, font=stat_font)
            hint_width = bbox[2] - bbox[0]
            hint_x = pokemon_panel_x + (pokemon_panel_width - hint_width) // 2
            draw.text((hint_x, placeholder_y + 40), placeholder_hint, font=stat_font, fill=(120, 120, 120))

        return bg

    @commands.hybrid_command(name='shinystatsimg', aliases=['ssimg','pf','profile'])
    async def shiny_stats_image(self, ctx):
        """Generate a visual card of your shiny collection statistics"""
        await ctx.defer()

        user_id = ctx.author.id
        utils = self.bot.get_cog('Utils')

        # Get all shinies
        all_shinies = await db.get_all_shinies(user_id)

        if not all_shinies:
            if ctx.interaction:
                await ctx.send("❌ You haven't tracked any shinies yet!\nUse `m!trackshiny` to get started.")
            else:
                await ctx.send("❌ You haven't tracked any shinies yet!\nUse `m!trackshiny` to get started.", 
                              reference=ctx.message, mention_author=False)
            return

        # Get user customization
        customization = await db.get_user_customization(user_id)
        background_name = customization['background']
        user_title = customization['user_title']

        # Get user settings for showcase pokemon
        user_data = await db.get_user_data(user_id)
        showcase_id = user_data.get('settings', {}).get('showcase_pokemon_id')

        # Get showcase pokemon data
        showcase_pokemon = None
        if showcase_id:
            showcase_pokemon = await db.get_shiny_by_id(user_id, showcase_id)

        # Get event shinies count
        event_shinies_count = await db.count_event_shinies(user_id)

        # Calculate stats using utils
        total_tracked = len(all_shinies)
        unique_dex = len(set(s['dex_number'] for s in all_shinies))

        # Full Dex calculation
        unique_forms_set = set()
        for shiny in all_shinies:
            dex_num = shiny['dex_number']
            name = shiny['name']
            gender = shiny['gender']

            has_gender_diff = utils.has_gender_difference(name)

            if has_gender_diff and gender in ['male', 'female']:
                unique_forms_set.add((dex_num, name, gender))
            else:
                unique_forms_set.add((dex_num, name, None))

        unique_forms = len(unique_forms_set)

        # Get totals
        total_unique_dex = utils.get_total_unique_dex()
        total_forms_count = utils.get_total_forms_count()

        # Calculate special counts using utils
        rare_count = utils.count_rare_shinies(all_shinies)
        regional_count = utils.count_regional_shinies(all_shinies)
        mint_count = utils.count_mint_shinies(all_shinies)

        # Most common Pokemon and Top 5
        from collections import Counter
        name_counts = Counter(s['name'] for s in all_shinies)

        # Get top 5 most collected - NOW ONLY PASSING NAME AND COUNT
        top_5_pokemon = []
        for name, count in name_counts.most_common(5):
            top_5_pokemon.append((name, count))

        # Prepare stats data
        stats_data = {
            'total_non_event': total_tracked,
            'event_shinies': event_shinies_count,
            'rare_shinies': rare_count,
            'regional_shinies': regional_count,
            'mint_shinies': mint_count,
            'basic_dex': unique_dex,
            'full_dex': unique_forms,
            'total_unique_dex': total_unique_dex,
            'total_forms': total_forms_count,
            'top_5_pokemon': top_5_pokemon,
            'showcase_pokemon': showcase_pokemon
        }

        # Create the image
        try:
            # For slash commands, send a followup message; for prefix commands, send a status message
            if ctx.interaction:
                await ctx.send("🎨 Generating your shiny stats card...")
            else:
                status_msg = await ctx.send("🎨 Generating your shiny stats card...")

            img = await self.create_stats_image(ctx.author, stats_data, background_name, user_title)

            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            file = discord.File(img_bytes, filename='shinystats.png')

            # Check if it's a slash command (interaction) or prefix command
            if ctx.interaction:
                await ctx.send(file=file)
            else:
                await status_msg.delete()
                await ctx.send(file=file, reference=ctx.message, mention_author=False)

        except Exception as e:
            error_msg = f"❌ Error generating image: {str(e)}"
            if ctx.interaction:
                await ctx.send(error_msg)
            else:
                await status_msg.edit(content=error_msg)
            print(f"Error in shiny stats image: {e}")

    @commands.hybrid_command(name='customize')
    async def customize_card(self, ctx):
        """Customize your stats card (background and title)"""
        user_id = ctx.author.id

        # Get current customization
        customization = await db.get_user_customization(user_id)
        current_bg = customization['background']
        current_title = customization['user_title']

        # Get available backgrounds
        backgrounds = self.get_available_backgrounds()

        # Create embed showing current settings
        embed = discord.Embed(
            title="🎨 Customize Your Stats Card",
            description=f"**Current Background:** {current_bg.replace('.png', '').replace('_', ' ').title()}\n"
                       f"**Current Title:** {current_title}",
            color=config.EMBED_COLOR
        )
        embed.add_field(
            name="How to Customize",
            value="1️⃣ Select a background from the dropdown below\n"
                  "2️⃣ Click Confirm to save\n"
                  "3️⃣ Use `m!settitle <your title>` to change your title",
            inline=False
        )

        # Create view with background selector
        view = BackgroundSelectView(user_id, backgrounds)

        if ctx.interaction:
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='settitle')
    @app_commands.describe(title="Your custom title (max 50 characters)")
    async def set_title(self, ctx, *, title: str):
        """Set your custom title on the stats card"""
        user_id = ctx.author.id

        if len(title) > 50:
            if ctx.interaction:
                await ctx.send("❌ Title too long! Maximum 50 characters.")
            else:
                await ctx.send("❌ Title too long! Maximum 50 characters.", 
                              reference=ctx.message, mention_author=False)
            return

        await db.set_user_customization(user_id, user_title=title)

        if ctx.interaction:
            await ctx.send(f'✅ Your title has been set to: **{title}**')
        else:
            await ctx.send(f'✅ Your title has been set to: **{title}**', 
                          reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='setfavorite', aliases=['setshowcase'])
    @app_commands.describe(pokemon_id="Pokemon ID to showcase", nickname="Optional nickname")
    async def set_favorite(self, ctx, pokemon_id: int, *, nickname: str = None):
        """Set your favorite Pokemon to showcase (optionally set nickname too)"""
        user_id = ctx.author.id

        # Check if pokemon exists in user's shinies
        shiny = await db.get_shiny_by_id(user_id, pokemon_id)

        if not shiny:
            if ctx.interaction:
                await ctx.send("❌ Pokemon not found in your shiny collection!")
            else:
                await ctx.send("❌ Pokemon not found in your shiny collection!", 
                              reference=ctx.message, mention_author=False)
            return

        # Update settings with showcase pokemon
        updates = {'showcase_pokemon_id': pokemon_id}

        # Set nickname if provided
        if nickname:
            if len(nickname) > 50:
                if ctx.interaction:
                    await ctx.send("❌ Nickname too long! Maximum 50 characters.")
                else:
                    await ctx.send("❌ Nickname too long! Maximum 50 characters.", 
                                  reference=ctx.message, mention_author=False)
                return
            await db.set_pokemon_nickname(user_id, pokemon_id, nickname)

        await db.update_settings(user_id, updates)

        nickname_msg = f' with nickname "{nickname}"' if nickname else ""

        if ctx.interaction:
            await ctx.send(f"✅ Set **{shiny['name']}** (ID: {pokemon_id}) as your favorite Pokemon{nickname_msg}!")
        else:
            await ctx.send(f"✅ Set **{shiny['name']}** (ID: {pokemon_id}) as your favorite Pokemon{nickname_msg}!", 
                          reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='setnickname', aliases=['nick'])
    @app_commands.describe(pokemon_id="Pokemon ID", nickname="Nickname for your Pokemon")
    async def set_nickname(self, ctx, pokemon_id: int, *, nickname: str):
        """Set or change a Pokemon's nickname (doesn't affect showcase)"""
        user_id = ctx.author.id

        # Check if pokemon exists
        shiny = await db.get_shiny_by_id(user_id, pokemon_id)

        if not shiny:
            if ctx.interaction:
                await ctx.send("❌ Pokemon not found in your shiny collection!")
            else:
                await ctx.send("❌ Pokemon not found in your shiny collection!", 
                              reference=ctx.message, mention_author=False)
            return

        if len(nickname) > 50:
            if ctx.interaction:
                await ctx.send("❌ Nickname too long! Maximum 50 characters.")
            else:
                await ctx.send("❌ Nickname too long! Maximum 50 characters.", 
                              reference=ctx.message, mention_author=False)
            return

        await db.set_pokemon_nickname(user_id, pokemon_id, nickname)

        if ctx.interaction:
            await ctx.send(f'✅ Set nickname "{nickname}" for **{shiny["name"]}** (ID: {pokemon_id})!')
        else:
            await ctx.send(f'✅ Set nickname "{nickname}" for **{shiny["name"]}** (ID: {pokemon_id})!', 
                          reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='refreshresources', aliases=['updateresources'])
    @commands.is_owner()
    async def refresh_resources(self, ctx):
        """Refresh fonts and backgrounds from GitHub (Owner only)"""
        await ctx.send("🔄 Refreshing resources from GitHub...")

        await self.download_fonts()
        await self.download_backgrounds()

        await ctx.send("✅ Resources refreshed successfully!")


async def setup(bot):
    await bot.add_cog(ShinyStatsImage(bot))
