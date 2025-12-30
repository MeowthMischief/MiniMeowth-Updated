from PIL import Image, ImageDraw, ImageFont, ImageColor
import aiohttp
from io import BytesIO
import os


class DexImageGenerator:
    """Generate visual dex images with Pokemon sprites"""

    def __init__(self, bot):
        self.bot = bot
        self.fonts_folder = 'shinystats/fonts'
        self.emojis_folder = 'shinystats/emojis'

        # GitHub repository details
        self.github_user = 'cynthiaofpower'
        self.github_repo = 'meowthfonts'
        self.github_branch = 'main'

        # Gender symbol URLs
        self.gender_symbols = {
            'male': 'https://cdn.discordapp.com/emojis/1207734081585152101.png',
            'female': 'https://cdn.discordapp.com/emojis/1207734084210532483.png'
        }

        # Glass panel settings (matching shinystatsimage.py)
        self.glass_color = (20, 20, 40, 180)
        self.border_color = (255, 255, 255, 80)

        # Layout settings - INCREASED to 6x5 = 30 Pokemon per page
        self.cols = 6
        self.rows = 5
        self.max_pokemon = 30

        # Cell dimensions
        self.cell_width = 180
        self.cell_height = 200
        self.padding = 15

        # Header settings
        self.header_height = 80
        self.header_padding = 20

        # Image dimensions (with header)
        self.img_width = (self.cell_width * self.cols) + (self.padding * (self.cols + 1))
        self.img_height = self.header_height + (self.cell_height * self.rows) + (self.padding * (self.rows + 1))

        # Gender symbol size
        self.gender_symbol_size = 24

        # Initialize font and emoji download on cog load
        self.bot.loop.create_task(self.download_fonts())
        self.bot.loop.create_task(self.download_gender_symbols())

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

    async def download_file_from_url(self, url: str, save_path: str):
        """Download a file from a direct URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        content = await resp.read()

                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                        with open(save_path, 'wb') as f:
                            f.write(content)
                        print(f"✅ Downloaded gender symbol: {os.path.basename(save_path)}")
                        return True
                    else:
                        print(f"❌ Failed to download from {url}: Status {resp.status}")
                        return False
        except Exception as e:
            print(f"❌ Error downloading from {url}: {e}")
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
        print("📥 Downloading fonts for dex images from GitHub...")

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

        print("✅ Font download complete for dex images!")

    async def download_gender_symbols(self):
        """Download gender symbol images from Discord CDN"""
        print("📥 Downloading gender symbols for dex images...")

        # Create emojis directory
        os.makedirs(self.emojis_folder, exist_ok=True)

        # Download each gender symbol
        for gender, url in self.gender_symbols.items():
            local_path = os.path.join(self.emojis_folder, f"{gender}.png")

            # Skip if already exists
            if os.path.exists(local_path):
                print(f"⏭️ Gender symbol already exists: {gender}.png")
                continue

            await self.download_file_from_url(url, local_path)

        print("✅ Gender symbol download complete for dex images!")

    def load_gender_symbol(self, gender: str):
        """Load gender symbol from local file"""
        try:
            symbol_path = os.path.join(self.emojis_folder, f"{gender}.png")
            if os.path.exists(symbol_path):
                img = Image.open(symbol_path).convert('RGBA')
                # Resize to desired size
                img.thumbnail((self.gender_symbol_size, self.gender_symbol_size), Image.Resampling.LANCZOS)
                return img
        except Exception as e:
            print(f"❌ Error loading gender symbol for {gender}: {e}")
        return None

    async def fetch_pokemon_image(self, cdn_number: int, gender_key: str = None, has_gender_diff: bool = False):
        """Fetch Pokemon image from Poketwo CDN"""
        # Add 'F' suffix for female gender difference Pokemon
        if has_gender_diff and gender_key == 'female':
            url = f"https://cdn.poketwo.net/shiny/{cdn_number}F.png"
        else:
            url = f"https://cdn.poketwo.net/shiny/{cdn_number}.png"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data)).convert('RGBA')
            except Exception as e:
                print(f"Error fetching image for CDN {cdn_number} (gender: {gender_key}): {e}")
        return None

    def make_dark_silhouette(self, img: Image.Image):
        """Create silhouette using the previous background color and remove background."""

        # This was your original bg color: (100, 110, 130)
        silhouette_color = (100, 110, 130, 255)

        # Start with transparent image
        silhouette = Image.new('RGBA', img.size, (0, 0, 0, 0))

        pixels = img.load()
        sil_pixels = silhouette.load()

        for y in range(img.size[1]):
            for x in range(img.size[0]):
                r, g, b, a = pixels[x, y]

                # If the Pokemon pixel exists, color it
                if a > 0:
                    sil_pixels[x, y] = silhouette_color

        return silhouette
        
    def draw_header(self, draw, overlay_draw, header_info: dict, page_info: dict = None):
        """Draw header with filter information
        header_info: dict with keys 'dex_type', 'types', 'regions', 'filter_name'
        page_info: dict with 'current_page', 'total_pages', 'total_count'
        """
        # Load header font
        try:
            title_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Bold.ttf'), 28)
            filter_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 18)
            page_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 15)
        except:
            title_font = ImageFont.load_default()
            filter_font = ImageFont.load_default()
            page_font = ImageFont.load_default()

        # Draw header background (rounded rectangle)
        header_x = self.padding
        header_y = self.padding
        header_w = self.img_width - (self.padding * 2)
        header_h = self.header_height - self.padding

        overlay_draw.rounded_rectangle(
            [(header_x, header_y), (header_x + header_w, header_y + header_h)],
            radius=15,
            fill=self.glass_color
        )
        overlay_draw.rounded_rectangle(
            [(header_x, header_y), (header_x + header_w, header_y + header_h)],
            radius=15,
            outline=self.border_color,
            width=3
        )

        # Build header text
        dex_type = header_info.get('dex_type', 'Full Shiny Dex')
        filter_name = header_info.get('filter_name')
        types = header_info.get('types', [])
        regions = header_info.get('regions', [])

        # Main title (unchanged size and style)
        if filter_name:
            main_text = f"Filter - {filter_name}"
        else:
            main_text = dex_type

        # Build filter text separately
        filter_text = None
        filter_parts = []
        if types:
            types_text = ", ".join(types)
            filter_parts.append(f"Types: {types_text}")
        if regions:
            regions_text = ", ".join(regions)
            filter_parts.append(f"Regions: {regions_text}")

        if filter_parts:
            filter_text = " | ".join(filter_parts)

        # Build page text for right side
        page_text = None
        if page_info:
            current_page = page_info.get('current_page', 1)
            total_pages = page_info.get('total_pages', 1)
            total_count = page_info.get('total_count', 0)

            if total_pages > 1:
                page_text = f"Page {current_page}/{total_pages} • {total_count} Total"
            else:
                page_text = f"{total_count} Pokémon"

        # Calculate text positions
        title_bbox = draw.textbbox((0, 0), main_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]

        # If there's filter text, calculate total width for centering
        if filter_text:
            filter_bbox = draw.textbbox((0, 0), f" | {filter_text}", font=filter_font)
            filter_width = filter_bbox[2] - filter_bbox[0]
            total_width = title_width + filter_width
            title_x = header_x + (header_w - total_width) // 2
        else:
            title_x = header_x + (header_w - title_width) // 2

        title_y = header_y + 12

        # Draw main title (will be drawn after overlay composite)
        return main_text, filter_text, title_x, title_y, title_font, filter_font, header_x, header_w, page_text, page_font

    async def create_dex_image(self, pokemon_entries: list, utils, header_info: dict = None, page_info: dict = None):
        """
        Create dex image with Pokemon sprites
        pokemon_entries: list of tuples (dex_num, name, gender_key, count)
        header_info: dict with 'dex_type', 'types', 'regions', 'filter_name'
        page_info: dict with 'current_page', 'total_pages', 'total_count'
        Limited to first 30 entries (6x5 grid)
        """
        # Limit to 30 Pokemon
        pokemon_entries = pokemon_entries[:self.max_pokemon]

        if not pokemon_entries:
            return None

        # Default header info
        if header_info is None:
            header_info = {'dex_type': 'Full Shiny Dex'}

        # Calculate dynamic grid dimensions based on actual Pokemon count
        num_pokemon = len(pokemon_entries)

        # Determine optimal rows (always use full 6 columns width)
        actual_rows = (num_pokemon + self.cols - 1) // self.cols  # Ceil division
        actual_rows = max(1, min(actual_rows, self.rows))  # Clamp between 1 and max_rows

        # Calculate dynamic image height based on actual rows needed
        dynamic_img_height = self.header_height + (self.cell_height * actual_rows) + (self.padding * (actual_rows + 1))

        # Create background with dynamic height
        bg = Image.new('RGBA', (self.img_width, dynamic_img_height), (40, 40, 60, 255))

        # Create overlay for glass panels with dynamic height
        overlay = Image.new('RGBA', (self.img_width, dynamic_img_height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Load fonts
        try:
            dex_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-Bold.ttf'), 16)
            count_font = ImageFont.truetype(os.path.join(self.fonts_folder, 'Poppins-SemiBold.ttf'), 18)
        except:
            dex_font = ImageFont.load_default()
            count_font = ImageFont.load_default()

        # Draw header and get text info
        draw_temp = ImageDraw.Draw(bg)
        header_data = self.draw_header(draw_temp, overlay_draw, header_info, page_info)
        main_text, filter_text, title_x, title_y, title_font, filter_font, header_x, header_w, page_text, page_font = header_data

        # Process each Pokemon
        for idx, (dex_num, name, gender_key, count) in enumerate(pokemon_entries):
            row = idx // self.cols
            col = idx % self.cols

            # Calculate position (offset by header height)
            x = self.padding + (col * (self.cell_width + self.padding))
            y = self.header_height + self.padding + (row * (self.cell_height + self.padding))

            # Draw glass panel
            overlay_draw.rounded_rectangle(
                [(x, y), (x + self.cell_width, y + self.cell_height)],
                radius=12,
                fill=self.glass_color
            )
            overlay_draw.rounded_rectangle(
                [(x, y), (x + self.cell_width, y + self.cell_height)],
                radius=12,
                outline=self.border_color,
                width=2
            )

            # Draw dex number badge (top right)
            has_gender_diff = utils.has_gender_difference(name)

            # Add gender suffix for gender difference Pokemon
            if has_gender_diff and gender_key:
                dex_text = f"#{dex_num}{gender_key[0].upper()}"
            else:
                dex_text = f"#{dex_num}"

            # Calculate badge size
            bbox = overlay_draw.textbbox((0, 0), dex_text, font=dex_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            badge_padding = 8
            badge_width = text_width + (badge_padding * 2)
            badge_height = text_height + (badge_padding * 2)

            badge_x = x + self.cell_width - badge_width - 8
            badge_y = y + 3

            # Draw badge circle/oval
            overlay_draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                radius=badge_height // 2,
                fill=(0, 0, 0, 200)
            )
            overlay_draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
                radius=badge_height // 2,
                outline=(255, 215, 0, 255),
                width=2
            )

        # Composite overlay onto background
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)

        # Draw header text (after composite)
        draw.text((title_x, title_y), main_text, font=title_font, fill=(255, 255, 255))

        # Draw filter text next to main title if it exists
        if filter_text:
            title_bbox = draw.textbbox((0, 0), main_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            filter_x = title_x + title_width
            # Align filter text vertically with main title (slightly lower to match baseline)
            filter_y = title_y + 8
            draw.text((filter_x, filter_y), f" | {filter_text}", font=filter_font, fill=(200, 200, 220))

        # Draw page info in top right of header if provided
        if page_text:
            page_bbox = draw.textbbox((0, 0), page_text, font=page_font)
            page_text_width = page_bbox[2] - page_bbox[0]
            page_text_height = page_bbox[3] - page_bbox[1]

            # Position in top right of header with padding
            page_badge_padding = 10
            page_badge_width = page_text_width + (page_badge_padding * 2)
            page_badge_height = page_text_height + (page_badge_padding * 2)

            page_badge_x = header_x + header_w - page_badge_width - 12
            page_badge_y = self.padding + 12

            # Draw glass-style badge
            draw.rounded_rectangle(
                [(page_badge_x, page_badge_y), 
                 (page_badge_x + page_badge_width, page_badge_y + page_badge_height)],
                radius=8,
                fill=(20, 20, 40, 200)
            )
            draw.rounded_rectangle(
                [(page_badge_x, page_badge_y), 
                 (page_badge_x + page_badge_width, page_badge_y + page_badge_height)],
                radius=8,
                outline=(255, 255, 255, 100),
                width=2
            )

            # Draw page text
            page_text_x = page_badge_x + page_badge_padding
            page_text_y = page_badge_y + page_badge_padding - 2
            draw.text((page_text_x, page_text_y), page_text, font=page_font, fill=(200, 200, 220))

        # Now add Pokemon images and text
        for idx, (dex_num, name, gender_key, count) in enumerate(pokemon_entries):
            row = idx // self.cols
            col = idx % self.cols

            x = self.padding + (col * (self.cell_width + self.padding))
            y = self.header_height + self.padding + (row * (self.cell_height + self.padding))

            # Get CDN number
            cdn_number = utils.get_cdn_number(name)
            has_gender_diff = utils.has_gender_difference(name)

            # Fetch Pokemon image
            poke_img = await self.fetch_pokemon_image(cdn_number, gender_key, has_gender_diff)

            if poke_img:
                # If uncaught, make it dark silhouette
                if count == 0:
                    poke_img = self.make_dark_silhouette(poke_img)

                # Resize to fit in cell (leave room for count at bottom)
                sprite_max_size = 120
                poke_img.thumbnail((sprite_max_size, sprite_max_size), Image.Resampling.LANCZOS)

                # Center horizontally, place in upper portion
                poke_w, poke_h = poke_img.size
                poke_x = x + (self.cell_width - poke_w) // 2
                poke_y = y + 32

                # Paste Pokemon image
                bg.paste(poke_img, (poke_x, poke_y), poke_img)

            # Add gender symbol for gender difference Pokemon (top left corner, inside rectangle)
            if has_gender_diff and gender_key:
                gender_symbol = self.load_gender_symbol(gender_key)
                if gender_symbol:
                    # Position in top left corner with small padding from edge
                    symbol_x = x + 8
                    symbol_y = y + 8
                    bg.paste(gender_symbol, (symbol_x, symbol_y), gender_symbol)

            # Draw count below Pokemon
            if count > 0:
                count_text = f"x{count}"
                count_color = (100, 200, 255)
            else:
                count_text = "x0"
                count_color = (120, 120, 120)

            # Center count text
            bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = bbox[2] - bbox[0]
            count_x = x + (self.cell_width - count_width) // 2
            count_y = y + self.cell_height - 35

            draw.text((count_x, count_y), count_text, font=count_font, fill=count_color)

            # Draw dex number text on badge
            has_gender_diff = utils.has_gender_difference(name)
            if has_gender_diff and gender_key:
                dex_text = f"#{dex_num}{gender_key[0].upper()}"
            else:
                dex_text = f"#{dex_num}"

            bbox = draw.textbbox((0, 0), dex_text, font=dex_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            badge_padding = 8
            badge_width = text_width + (badge_padding * 2)
            badge_height = text_height + (badge_padding * 2)

            badge_x = x + self.cell_width - badge_width - 8
            badge_y = y + 4

            text_x = badge_x + badge_padding
            text_y = badge_y + badge_padding - 2

            draw.text((text_x, text_y), dex_text, font=dex_font, fill=(255, 215, 0))

        return bg
