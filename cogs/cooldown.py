import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio
import config
from database import db

class CooldownView(discord.ui.View):
    """View for cooldown list pagination with buttons"""

    def __init__(self, ctx, pokemon_on_cd, pages, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pokemon_on_cd = pokemon_on_cd
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
        embed = discord.Embed(
            title="🔒 Pokemon on Cooldown",
            color=config.EMBED_COLOR
        )

        description_lines = []
        now = datetime.utcnow()

        for p in self.pages[self.current_page]:
            time_left = p['expiry'] - now
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60

            time_str = []
            if days > 0:
                time_str.append(f"{days}d")
            if hours > 0:
                time_str.append(f"{hours}h")
            if minutes > 0 or (days == 0 and hours == 0):
                time_str.append(f"{minutes}m")

            gender_icon = (
                config.GENDER_MALE if p['gender'] == 'male' else 
                config.GENDER_FEMALE if p['gender'] == 'female' else 
                config.GENDER_UNKNOWN
            )

            description_lines.append(
                f"`{p['pokemon_id']}` **{p['name']}** {gender_icon} • {p['iv_percent']}% IV\n"
                f"⏰ {' '.join(time_str)} remaining"
            )

        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • Total: {len(self.pokemon_on_cd)} Pokemon")

        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your cooldown list!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="▶️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ This is not your cooldown list!", ephemeral=True)
            return

        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.defer()

    async def on_timeout(self):
        """Disable all buttons when view times out"""
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass


class ConfirmView(discord.ui.View):
    """Confirmation view for clearing all cooldowns"""

    def __init__(self, ctx):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Not your confirmation!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Not your confirmation!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()


class Cooldown(commands.Cog):
    """Cooldown management for breeding pairs"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='cooldown', aliases=['cd'])
    @app_commands.describe(
        action="Action to perform: add, remove, list, or clear",
        pokemon_ids="Pokemon IDs separated by spaces"
    )
    async def cooldown_command(self, ctx, action: str, *, pokemon_ids: str = None):
        """
        Manage Pokemon cooldowns
        Usage: 
          cooldown add [ids...] - Add Pokemon to cooldown
          cooldown remove [ids...] - Remove Pokemon from cooldown
          cooldown list - View all Pokemon on cooldown
          cooldown clear - Clear ALL your cooldowns

        Examples:
          m!cd add 123456 789012 345678
          m!cd remove 123456 789012
          m!cd list
          m!cd clear
        """
        action = action.lower()

        if action == 'list':
            await self.list_cooldowns(ctx)
        elif action == 'clear':
            await self.clear_all_cooldowns(ctx)
        elif action in ['add', 'remove']:
            if not pokemon_ids:
                await ctx.send(f"❌ Please provide Pokemon IDs to {action}", reference=ctx.message, mention_author=False)
                return

            try:
                ids = [int(pid) for pid in pokemon_ids.split()]
            except ValueError:
                await ctx.send("❌ Invalid Pokemon IDs provided", reference=ctx.message, mention_author=False)
                return

            if action == 'add':
                await self.add_cooldowns(ctx, ids)
            else:
                await self.remove_cooldowns(ctx, ids)
        else:
            await ctx.send("❌ Invalid action. Use `add`, `remove`, `list`, or `clear`", reference=ctx.message, mention_author=False)

    async def clear_all_cooldowns(self, ctx):
        """Clear all Pokemon cooldowns for the user"""
        user_id = ctx.author.id

        # Defer if slash command to prevent timeout
        if ctx.interaction:
            await ctx.defer()

        # Get current cooldown count first
        cooldowns = await db.get_cooldowns(user_id)

        if not cooldowns:
            await ctx.send("✅ No Pokemon are currently on cooldown", reference=ctx.message, mention_author=False)
            return

        count = len(cooldowns)

        # Ask for confirmation with buttons
        view = ConfirmView(ctx)
        confirm_msg = await ctx.send(
            f"⚠️ **WARNING:** Clear all **{count}** Pokemon from cooldown?\n"
            "Click Confirm or Cancel (30 seconds)",
            reference=ctx.message,
            mention_author=False,
            view=view
        )

        await view.wait()

        if view.value is True:
            # Clear all cooldowns
            cleared_count = await db.clear_all_cooldowns(user_id)

            embed = discord.Embed(
                title="🧹 All Cooldowns Cleared",
                description=f"✅ Cleared **{cleared_count}** Pokemon from cooldown",
                color=config.EMBED_COLOR
            )
            embed.add_field(
                name="Action",
                value=f"All ({cleared_count} Pokemon IDs) cooldowns removed",
                inline=False
            )

            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        elif view.value is False:
            await ctx.send("❌ Clear cancelled", reference=ctx.message, mention_author=False)
        else:
            await ctx.send("⏰ Confirmation timed out. Cooldowns not cleared", reference=ctx.message, mention_author=False)

    async def add_cooldowns(self, ctx, pokemon_ids: list):
        """Add Pokemon to cooldown"""
        user_id = ctx.author.id

        # Defer if slash command to prevent timeout
        if ctx.interaction:
            await ctx.defer()

        # Verify Pokemon exist in inventory
        valid_ids = []
        for pid in pokemon_ids:
            pokemon = await db.get_pokemon_by_id(user_id, pid)
            if pokemon:
                valid_ids.append(pid)

        if not valid_ids:
            await ctx.send("❌ None of the provided IDs exist in your inventory", reference=ctx.message, mention_author=False)
            return

        await db.add_cooldown(user_id, valid_ids)

        embed = discord.Embed(
            title="🔒 Cooldown Added",
            description=f"Added **{len(valid_ids)}** Pokemon to cooldown",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name="Pokemon IDs",
            value=", ".join(f"`{pid}`" for pid in valid_ids),
            inline=False
        )

        embed.add_field(
            name="Duration",
            value=f"**{config.COOLDOWN_DAYS}** days, **{config.COOLDOWN_HOURS}** hour",
            inline=False
        )

        if len(valid_ids) < len(pokemon_ids):
            ignored = len(pokemon_ids) - len(valid_ids)
            embed.set_footer(text=f"{ignored} IDs not found in inventory and were ignored")

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def remove_cooldowns(self, ctx, pokemon_ids: list):
        """Remove Pokemon from cooldown"""
        user_id = ctx.author.id

        # Defer if slash command to prevent timeout
        if ctx.interaction:
            await ctx.defer()

        # Get current cooldowns to verify which IDs are actually on cooldown
        current_cooldowns = await db.get_cooldowns(user_id)

        # Filter to only IDs that are actually on cooldown
        valid_ids = [pid for pid in pokemon_ids if pid in current_cooldowns]
        invalid_ids = [pid for pid in pokemon_ids if pid not in current_cooldowns]

        if not valid_ids:
            await ctx.send("❌ None of the provided IDs are currently on cooldown", reference=ctx.message, mention_author=False)
            return

        # Remove only valid IDs
        await db.remove_cooldown(user_id, valid_ids)

        embed = discord.Embed(
            title="🔓 Cooldown Removed",
            description=f"Removed **{len(valid_ids)}** Pokemon from cooldown",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name="Pokemon IDs Removed",
            value=", ".join(f"`{pid}`" for pid in valid_ids),
            inline=False
        )

        if invalid_ids:
            embed.add_field(
                name="⚠️ Not on Cooldown",
                value=", ".join(f"`{pid}`" for pid in invalid_ids),
                inline=False
            )
            embed.set_footer(text=f"{len(invalid_ids)} IDs were not on cooldown and were ignored")

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def list_cooldowns(self, ctx):
        """List all Pokemon on cooldown - optimized single query"""
        user_id = ctx.author.id

        if ctx.interaction:
            await ctx.defer()

        cooldowns = await db.get_cooldowns(user_id)

        if not cooldowns:
            await ctx.send("✅ No Pokemon are currently on cooldown", 
                          reference=ctx.message, mention_author=False)
            return

        # Load ALL Pokemon data at once (single DB query)
        pokemon_on_cd = []
        for pid, expiry in cooldowns.items():
            pokemon = await db.get_pokemon_by_id(user_id, pid)
            if pokemon:
                pokemon['expiry'] = expiry
                pokemon_on_cd.append(pokemon)

        # Sort by expiry
        pokemon_on_cd.sort(key=lambda x: x['expiry'])

        # Paginate
        per_page = 10
        pages = [pokemon_on_cd[i:i + per_page] 
                 for i in range(0, len(pokemon_on_cd), per_page)]

        # Create view and send
        view = CooldownView(ctx, pokemon_on_cd, pages)
        message = await ctx.send(embed=view.create_embed(), view=view,
                                reference=ctx.message, mention_author=False)
        view.message = message

async def setup(bot):
    await bot.add_cog(Cooldown(bot))
