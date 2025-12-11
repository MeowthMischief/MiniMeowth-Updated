import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import config
from database import db

class InventoryView(discord.ui.View):
    """View with pagination buttons and inventory dropdown"""

    def __init__(self, ctx, category: str, category_name: str, filters_str: str, pokemon_list, cooldowns, pages, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.category = category
        self.category_name = category_name
        self.filters_str = filters_str
        self.pokemon_list = pokemon_list
        self.cooldowns = cooldowns
        self.pages = pages
        self.current_page = 0
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        self.previous_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= len(self.pages) - 1)

    def create_embed(self):
        """Create embed for current page"""
        title = f"Your {self.category_name} Pokémon Inventory"
        embed = discord.Embed(title=title, color=config.EMBED_COLOR)

        lines = []
        for p in self.pages[self.current_page]:
            cd = "🔒" if p['pokemon_id'] in self.cooldowns else ""
            g = config.GENDER_MALE if p['gender'] == 'male' else config.GENDER_FEMALE if p['gender'] == 'female' else config.GENDER_UNKNOWN
            lines.append(f"`{p['pokemon_id']}` {cd} **{p['name']}** {g} • {p['iv_percent']}% IV")

        embed.description = "\n".join(lines)

        footer = [f"Page {self.current_page + 1}/{len(self.pages)}", f"Total: {len(self.pokemon_list)} Pokémon"]
        embed.set_footer(text=" • ".join(footer))
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
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
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.select(
        placeholder="Switch Inventory",
        options=[
            discord.SelectOption(label="Normal Inventory", value="normal", emoji="📦"),
            discord.SelectOption(label="TripMax Inventory", value="tripmax", emoji="⬆️"),
            discord.SelectOption(label="TripZero Inventory", value="tripzero", emoji="⬇️")
        ]
    )
    async def inventory_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        await interaction.response.defer()

        category_map = {
            'normal': (config.NORMAL_CATEGORY, 'Normal'),
            'tripmax': (config.TRIPMAX_CATEGORY, 'TripMax'),
            'tripzero': (config.TRIPZERO_CATEGORY, 'TripZero')
        }
        new_cat, new_name = category_map[select.values[0]]

        inv_cog = self.ctx.bot.get_cog('Inventory')
        if inv_cog:
            await inv_cog._reload_inventory_view(interaction, self.ctx, new_cat, new_name, self.filters_str, self.message)

    async def on_timeout(self):
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='add')
    @app_commands.describe(message_ids="Message IDs to add Pokemon from (space-separated)")
    async def add_command(self, ctx, *, message_ids: str = None):
        await self._add_to_category(ctx, config.NORMAL_CATEGORY, message_ids)

    @commands.hybrid_command(name='addtripmax')
    @app_commands.describe(message_ids="Message IDs to add Pokemon from (space-separated)")
    async def add_tripmax_command(self, ctx, *, message_ids: str = None):
        await self._add_to_category(ctx, config.TRIPMAX_CATEGORY, message_ids)

    @commands.hybrid_command(name='addtripzero')
    @app_commands.describe(message_ids="Message IDs to add Pokemon from (space-separated)")
    async def add_tripzero_command(self, ctx, *, message_ids: str = None):
        await self._add_to_category(ctx, config.TRIPZERO_CATEGORY, message_ids)

    async def _add_to_category(self, ctx, category: str, message_ids_str: str):
        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        all_pokemon = []
        processed_pokemon_ids = set()
        monitored_message_id = None

        async def process_embed(embed):
            if not embed or not embed.description:
                return 0
            pokemon_list = utils.parse_embed_content(embed.description)
            count = 0
            for p in pokemon_list:
                if p['pokemon_id'] not in processed_pokemon_ids:
                    egg_groups = p.get('egg_groups', ['Undiscovered'])
                    if 'Undiscovered' not in egg_groups:
                        all_pokemon.append(p)
                        processed_pokemon_ids.add(p['pokemon_id'])
                        count += 1
            return count

        if ctx.message.reference and not message_ids_str:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if not replied_msg.embeds:
                    await ctx.send("❌ Please reply to a Poketwo message with embeds!", reference=ctx.message, mention_author=False)
                    return
                await process_embed(replied_msg.embeds[0])
                monitored_message_id = replied_msg.id
            except Exception as e:
                await ctx.send(f"❌ Error fetching replied message: {str(e)}", reference=ctx.message, mention_author=False)
                return
        elif message_ids_str:
            message_ids = message_ids_str.split()
            for msg_id in message_ids:
                try:
                    embed = await utils.fetch_embed_by_id(ctx, int(msg_id))
                    await process_embed(embed)
                except:
                    continue

        category_names = {
            config.NORMAL_CATEGORY: "Normal",
            config.TRIPMAX_CATEGORY: "TripMax",
            config.TRIPZERO_CATEGORY: "TripZero"
        }
        category_display = category_names.get(category, category)

        if not all_pokemon:
            await ctx.send("❌ No valid Pokemon found to add", reference=ctx.message, mention_author=False)
            return

        initial_count = len(all_pokemon)
        status_msg = await ctx.send(
            f"🔄 **Adding {initial_count} Pokemon to {category_display} inventory...**",
            reference=ctx.message, mention_author=False
        )

        new_count = await db.add_pokemon_bulk(user_id, all_pokemon, category)
        total = await db.count_pokemon(user_id, category=category)
        await status_msg.edit(
            content=f"✅ **Added {new_count} Pokemon to {category_display}!**\n"
                    f"💡 Keep clicking pages, I'll auto-detect more!\n📊 Total in inventory: {total}"
        )

        if monitored_message_id:
            def check(before, after):
                return (after.id == monitored_message_id and after.embeds)

            timeout = 60
            start_time = asyncio.get_event_loop().time()
            last_update = start_time

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    wait_time = min(remaining, 30.0)
                    before, after = await self.bot.wait_for('message_edit', timeout=wait_time, check=check)

                    embed = after.embeds[0]
                    page_pokemon = []
                    pokemon_list = utils.parse_embed_content(embed.description)
                    for p in pokemon_list:
                        if p['pokemon_id'] not in processed_pokemon_ids:
                            egg_groups = p.get('egg_groups', ['Undiscovered'])
                            if 'Undiscovered' not in egg_groups:
                                page_pokemon.append(p)
                                processed_pokemon_ids.add(p['pokemon_id'])

                    if page_pokemon:
                        page_new_count = await db.add_pokemon_bulk(user_id, page_pokemon, category)
                        new_count += page_new_count
                        last_update = asyncio.get_event_loop().time()
                        total = await db.count_pokemon(user_id, category=category)
                        await status_msg.edit(
                            content=f"✅ **Page detected! Added {page_new_count} more Pokemon**\n"
                                    f"📊 Total added: {new_count} | Inventory total: {total}\n💡 Keep clicking for more!"
                        )
                except asyncio.TimeoutError:
                    if asyncio.get_event_loop().time() - last_update > 15:
                        break
                    continue

        embed = discord.Embed(title=f"✅ {category_display} Inventory Updated", color=config.EMBED_COLOR)
        total_processed = len(all_pokemon)
        duplicates = total_processed - new_count
        embed.add_field(name="📊 Summary", value=f"**{new_count}** new Pokemon added\n**{duplicates}** duplicates ignored\n**{total_processed}** total processed", inline=False)
        total = await db.count_pokemon(user_id, category=category)
        embed.set_footer(text=f"Total Pokemon in {category_display} inventory: {total}")
        await status_msg.edit(content="", embed=embed)

    @commands.hybrid_command(name='remove', aliases=['rm'])
    @app_commands.describe(pokemon_ids="Pokemon IDs to remove (space-separated)")
    async def remove_command(self, ctx, *, pokemon_ids: str):
        if not pokemon_ids:
            await ctx.send("❌ Please provide Pokemon IDs to remove", reference=ctx.message, mention_author=False)
            return
        try:
            ids = [int(pid) for pid in pokemon_ids.split()]
        except ValueError:
            await ctx.send("❌ Invalid Pokemon IDs provided", reference=ctx.message, mention_author=False)
            return
        count = await db.remove_pokemon(ctx.author.id, ids)
        if count > 0:
            await ctx.send(f"✅ Removed **{count}** Pokemon from inventory", reference=ctx.message, mention_author=False)
        else:
            await ctx.send("❌ No Pokemon found with those IDs", reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='clear')
    @app_commands.describe(category="Which inventory to clear: inv, tripmax, tripzero, or all")
    async def clear_command(self, ctx, category: str = None):
        if not category:
            await ctx.send(f"❌ Please specify which inventory to clear:\n• `{config.PREFIX}clear inv`\n• `{config.PREFIX}clear tripmax`\n• `{config.PREFIX}clear tripzero`\n• `{config.PREFIX}clear all`", reference=ctx.message, mention_author=False)
            return

        category = category.lower()
        category_map = {
            'inv': (config.NORMAL_CATEGORY, 'Normal'),
            'normal': (config.NORMAL_CATEGORY, 'Normal'),
            'tripmax': (config.TRIPMAX_CATEGORY, 'TripMax'),
            'tripzero': (config.TRIPZERO_CATEGORY, 'TripZero'),
            'all': (None, 'ALL')
        }

        if category not in category_map:
            await ctx.send("❌ Invalid category. Use: `inv`, `tripmax`, `tripzero`, or `all`", reference=ctx.message, mention_author=False)
            return

        db_category, display_name = category_map[category]

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
        await ctx.send(f"⚠️ **WARNING:** Delete {display_name} Pokemon?\nClick Confirm or Cancel (30s)", reference=ctx.message, mention_author=False, view=view)
        await view.wait()

        if view.value is True:
            count = await db.clear_inventory(ctx.author.id, db_category)
            await ctx.send(f"🗑️ Cleared **{count}** Pokemon from {display_name} inventory")
        elif view.value is False:
            await ctx.send("❌ Clear cancelled")
        else:
            await ctx.send("⏰ Confirmation timed out")

    @commands.hybrid_command(name='inventory', aliases=['inv'])
    @app_commands.describe(filters="Optional filters (e.g., '--g male --gmax --n pikachu --cd')")
    async def view_inventory(self, ctx, *, filters: str = None):
        await self._view_category_inventory(ctx, config.NORMAL_CATEGORY, "Normal", filters)

    @commands.hybrid_command(name='invtripmax')
    @app_commands.describe(filters="Optional filters (e.g., '--g male --gmax --n pikachu --cd')")
    async def view_tripmax_inventory(self, ctx, *, filters: str = None):
        await self._view_category_inventory(ctx, config.TRIPMAX_CATEGORY, "TripMax", filters)

    @commands.hybrid_command(name='invtripzero')
    @app_commands.describe(filters="Optional filters (e.g., '--g male --gmax --n pikachu --cd')")
    async def view_tripzero_inventory(self, ctx, *, filters: str = None):
        await self._view_category_inventory(ctx, config.TRIPZERO_CATEGORY, "TripZero", filters)

    async def _view_category_inventory(self, ctx, category: str, category_name: str, filters_str: str):
        user_id = ctx.author.id
        args = filters_str.split() if filters_str else []
        gender_filter = None
        gmax_filter = False
        regional_filter = False
        cooldown_filter = None  # None = show all, True = only cooldown, False = only no cooldown
        name_filters = []  # List of names to filter

        i = 0
        while i < len(args):
            arg = args[i].lower()
            if arg in ['--g', '--gender']:
                if i + 1 < len(args):
                    gender_value = args[i + 1].lower()
                    if gender_value in ['male', 'female', 'unknown']:
                        gender_filter = gender_value
                        i += 2
                        continue
                    else:
                        await ctx.send(f"❌ Invalid gender: `{args[i + 1]}`", reference=ctx.message, mention_author=False)
                        return
                else:
                    await ctx.send("❌ `--g` requires gender", reference=ctx.message, mention_author=False)
                    return
            elif arg in ['--gmax', '--gigantamax', '--gm']:
                gmax_filter = True
                i += 1
            elif arg in ['--regional', '--regionals', '--reg']:
                regional_filter = True
                i += 1
            elif arg == '--cd':
                cooldown_filter = True
                i += 1
            elif arg in ['--nocd', '--b']:
                cooldown_filter = False
                i += 1
            elif arg in ['--n', '--name']:
                if i + 1 < len(args):
                    name_filters.append(args[i + 1])
                    i += 2
                else:
                    await ctx.send("❌ `--n` requires a name", reference=ctx.message, mention_author=False)
                    return
            else:
                i += 1

        db_filters = {}
        if gender_filter:
            db_filters['gender'] = gender_filter
        if gmax_filter:
            db_filters['is_gmax'] = True
        if regional_filter:
            db_filters['is_regional'] = True

        pokemon_list, cooldowns = await asyncio.gather(
            db.get_pokemon(user_id, db_filters, category),
            db.get_cooldowns(user_id)
        )

        # Apply name filters (OR logic - match any of the names)
        if name_filters:
            pokemon_list = [
                p for p in pokemon_list 
                if any(name.lower() in p['name'].lower() for name in name_filters)
            ]

        # Apply cooldown filter
        if cooldown_filter is not None:
            if cooldown_filter:  # --cd: only show Pokemon on cooldown
                pokemon_list = [p for p in pokemon_list if p['pokemon_id'] in cooldowns]
            else:  # --nocd: only show Pokemon not on cooldown
                pokemon_list = [p for p in pokemon_list if p['pokemon_id'] not in cooldowns]

        if not pokemon_list:
            await ctx.send(f"❌ No Pokemon found in {category_name} inventory", reference=ctx.message, mention_author=False)
            return

        pokemon_list.sort(key=lambda x: x['iv_percent'], reverse=True)
        per_page = 20
        pages = [pokemon_list[i:i + per_page] for i in range(0, len(pokemon_list), per_page)]

        view = InventoryView(ctx, category, category_name, filters_str, pokemon_list, cooldowns, pages)
        message = await ctx.send(embed=view.create_embed(), view=view, reference=ctx.message, mention_author=False)
        view.message = message

    async def _reload_inventory_view(self, interaction, ctx, category: str, category_name: str, filters_str: str, message):
        user_id = ctx.author.id
        args = filters_str.split() if filters_str else []
        gender_filter = gmax_filter = regional_filter = None
        cooldown_filter = None
        name_filters = []

        i = 0
        while i < len(args):
            arg = args[i].lower()
            if arg in ['--g', '--gender'] and i + 1 < len(args):
                if args[i + 1].lower() in ['male', 'female', 'unknown']:
                    gender_filter = args[i + 1].lower()
                i += 2
            elif arg in ['--gmax', '--gigantamax', '--gm']:
                gmax_filter = True
                i += 1
            elif arg in ['--regional', '--regionals', '--reg']:
                regional_filter = True
                i += 1
            elif arg == '--cd':
                cooldown_filter = True
                i += 1
            elif arg in ['--nocd', '--b']:
                cooldown_filter = False
                i += 1
            elif arg in ['--n', '--name'] and i + 1 < len(args):
                name_filters.append(args[i + 1])
                i += 2
            else:
                i += 1

        db_filters = {}
        if gender_filter:
            db_filters['gender'] = gender_filter
        if gmax_filter:
            db_filters['is_gmax'] = True
        if regional_filter:
            db_filters['is_regional'] = True

        pokemon_list, cooldowns = await asyncio.gather(
            db.get_pokemon(user_id, db_filters, category),
            db.get_cooldowns(user_id)
        )

        # Apply name filters
        if name_filters:
            pokemon_list = [
                p for p in pokemon_list 
                if any(name.lower() in p['name'].lower() for name in name_filters)
            ]

        # Apply cooldown filter
        if cooldown_filter is not None:
            if cooldown_filter:
                pokemon_list = [p for p in pokemon_list if p['pokemon_id'] in cooldowns]
            else:
                pokemon_list = [p for p in pokemon_list if p['pokemon_id'] not in cooldowns]

        if not pokemon_list:
            await interaction.followup.send(f"❌ No Pokemon in {category_name} inventory", ephemeral=True)
            return

        pokemon_list.sort(key=lambda x: x['iv_percent'], reverse=True)
        pages = [pokemon_list[i:i + 20] for i in range(0, len(pokemon_list), 20)]

        view = InventoryView(ctx, category, category_name, filters_str, pokemon_list, cooldowns, pages)
        view.message = message
        await message.edit(embed=view.create_embed(), view=view)

    @commands.hybrid_command(name='stats')
    async def inventory_stats(self, ctx):
        user_id = ctx.author.id
        total_normal, total_tripmax, total_tripzero, total, males, females, unknown, gmax_count, cooldowns = await asyncio.gather(
            db.count_pokemon(user_id, category=config.NORMAL_CATEGORY),
            db.count_pokemon(user_id, category=config.TRIPMAX_CATEGORY),
            db.count_pokemon(user_id, category=config.TRIPZERO_CATEGORY),
            db.count_pokemon(user_id),
            db.count_pokemon(user_id, {'gender': 'male'}),
            db.count_pokemon(user_id, {'gender': 'female'}),
            db.count_pokemon(user_id, {'gender': 'unknown'}),
            db.count_pokemon(user_id, {'is_gmax': True}),
            db.get_cooldowns(user_id)
        )

        on_cooldown = len(cooldowns)
        embed = discord.Embed(title="📊 Inventory Statistics", color=config.EMBED_COLOR)
        embed.add_field(name="📦 Inventories", value=f"**Normal:** {total_normal}\n**TripMax:** {total_tripmax}\n**TripZero:** {total_tripzero}\n**Total Unique:** {total}", inline=True)
        embed.add_field(name="⏱️ Availability", value=f"**On Cooldown:** {on_cooldown}\n**Available:** {total - on_cooldown}", inline=True)
        embed.add_field(name="⚥ Genders", value=f"{config.GENDER_MALE} **Males:** {males}\n{config.GENDER_FEMALE} **Females:** {females}\n{config.GENDER_UNKNOWN} **Unknown:** {unknown}", inline=True)
        embed.add_field(name="<:gigantamax:1420708122267226202> Gigantamax", value=f"**{gmax_count}**", inline=True)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

async def setup(bot):
    await bot.add_cog(Inventory(bot))
