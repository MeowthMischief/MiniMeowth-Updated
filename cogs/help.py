import discord
from discord.ext import commands
from discord import app_commands
import config

# ===== HELP SYSTEM CONFIG =====
HELP_PREFIX = "m!"  # Change this to update prefix everywhere in help

class HelpDropdown(discord.ui.Select):
    """Dropdown menu for selecting help categories"""

    def __init__(self, help_cog):
        self.help_cog = help_cog

        options = [
            discord.SelectOption(
                label="Home",
                description="Main help menu",
                value="home",
                emoji="🏠"
            ),
            discord.SelectOption(
                label="Inventory",
                description="Manage your Pokemon inventory",
                value="inventory",
                emoji="📦"
            ),
            discord.SelectOption(
                label="Breeding",
                description="Generate breeding pairs",
                value="breeding",
                emoji="💕"
            ),
            discord.SelectOption(
                label="Cooldown",
                description="Manage breeding cooldowns",
                value="cooldown",
                emoji="🔒"
            ),
            discord.SelectOption(
                label="Settings",
                description="Configure preferences",
                value="settings",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Shiny Dex",
                description="Track your shinies",
                value="shinydex",
                emoji="✨"
            ),
            discord.SelectOption(
                label="Pokedex",
                description="Look up Pokemon info",
                value="pokedex",
                emoji="🔍"
            ),
            discord.SelectOption(
                label="List Tools",
                description="Compare and manage Pokemon lists",
                value="listtools",
                emoji="📋"
            ),
            discord.SelectOption(
                label="Utility",
                description="Helpful utility commands",
                value="utility",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Context Menu",
                description="Right-click message commands",
                value="context",
                emoji="📱"
            )
        ]

        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return

        category = self.values[0]

        embed_map = {
            "home": self.help_cog.get_home_embed,
            "inventory": self.help_cog.get_inventory_embed,
            "breeding": self.help_cog.get_breeding_embed,
            "cooldown": self.help_cog.get_cooldown_embed,
            "settings": self.help_cog.get_settings_embed,
            "shinydex": self.help_cog.get_shinydex_embed,
            "pokedex": self.help_cog.get_pokedex_embed,
            "listtools": self.help_cog.get_listtools_embed,
            "utility": self.help_cog.get_utility_embed,
            "context": self.help_cog.get_context_embed
        }

        embed = embed_map[category]()
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    """View with navigation buttons and dropdown"""

    def __init__(self, ctx, help_cog):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.help_cog = help_cog
        self.message = None

        # Add dropdown
        self.add_item(HelpDropdown(help_cog))

    @discord.ui.button(label="📦Inventory", style=discord.ButtonStyle.primary, row=1)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_inventory_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="💕Breeding", style=discord.ButtonStyle.primary, row=1)
    async def breeding_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_breeding_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚙️Settings", style=discord.ButtonStyle.primary, row=1)
    async def settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_settings_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="✨Shiny Dex", style=discord.ButtonStyle.success, row=2)
    async def shinydex_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_shinydex_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛠️Utility", style=discord.ButtonStyle.success, row=2)
    async def utility_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_utility_embed()
        await interaction.response.edit_message(embed=embed, view=self)


    @discord.ui.button(label="📋List Tools", style=discord.ButtonStyle.success, row=2)
    async def listtools_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_listtools_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🏠Home", style=discord.ButtonStyle.secondary, row=2)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your help menu!", ephemeral=True)
            return
        embed = self.help_cog.get_home_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except:
                pass


class HelpCommands(commands.Cog):
    """Enhanced help system with interactive menus"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='help', aliases=['h'])
    @app_commands.describe(command="Specific command to get help for")
    async def help_command(self, ctx, *, command: str = None):
        """
        Display help menu or get info about a specific command

        __Usage:__
        > `m!help` - Show interactive help menu
        > `m!help <command>` - Get detailed info about a command

        __Examples:__
        > `m!help breed`
        > `m!help trackshiny`
        """
        # If specific command requested
        if command:
            await self.show_command_help(ctx, command)
            return

        # Show interactive menu
        view = HelpView(ctx, self)
        embed = self.get_home_embed()
        message = await ctx.send(embed=embed, view=view, reference=ctx.message if hasattr(ctx.message, 'reference') else None, mention_author=False)
        view.message = message

    async def show_command_help(self, ctx, command_name: str):
        """Show detailed help for a specific command"""
        cmd = self.bot.get_command(command_name.lower())

        if not cmd:
            await ctx.send(f"Command `{command_name}` not found! Use `{HELP_PREFIX}help` to see all commands.", 
                          reference=ctx.message if hasattr(ctx.message, 'reference') else None, mention_author=False)
            return

        # Check if it's a hybrid command
        is_hybrid = isinstance(cmd, commands.HybridCommand)
        is_slash = is_hybrid or hasattr(cmd, 'app_command')

        # Build description
        description_parts = []

        # Get command help text
        if cmd.help:
            description_parts.append(cmd.help.split('\n\n')[0])  # First paragraph only
        else:
            description_parts.append("_No description available_")

        description_parts.append("")  # Empty line

        # Command availability
        if is_hybrid:
            description_parts.append("__Available as:__")
            description_parts.append(f"> Prefix command: `{HELP_PREFIX}{cmd.name}`")
            description_parts.append(f"> Slash command: `/{cmd.name}`")
        elif is_slash:
            description_parts.append(f"__Available as:__ Slash command only `/{cmd.name}`")
        else:
            description_parts.append(f"__Available as:__ Prefix command `{HELP_PREFIX}{cmd.name}`")

        embed = discord.Embed(
            title=f"Command: {cmd.name}",
            description="\n".join(description_parts),
            color=config.EMBED_COLOR
        )

        # Aliases (only for prefix commands)
        if cmd.aliases:
            aliases_text = " ".join([f"`{alias}`" for alias in cmd.aliases])
            embed.add_field(
                name="__Aliases__",
                value=aliases_text,
                inline=False
            )

        # Usage
        usage_lines = []
        if cmd.signature:
            usage_lines.append(f"> `{HELP_PREFIX}{cmd.name} {cmd.signature}`")
            if is_hybrid or is_slash:
                clean_sig = cmd.signature.replace('[', '').replace(']', '').replace('<', '').replace('>', '')
                usage_lines.append(f"> `/{cmd.name} {clean_sig}`")
        else:
            usage_lines.append(f"> `{HELP_PREFIX}{cmd.name}`")
            if is_hybrid or is_slash:
                usage_lines.append(f"> `/{cmd.name}`")

        embed.add_field(
            name="__Usage__",
            value="\n".join(usage_lines),
            inline=False
        )

        # Parameters (if any)
        if cmd.clean_params:
            param_lines = []
            for param_name, param in cmd.clean_params.items():
                # Determine if required or optional
                is_required = param.default == param.empty

                if is_required:
                    param_lines.append(f"> `{param_name}` - Required")
                else:
                    param_lines.append(f"> `{param_name}` - Optional")

            if param_lines:
                embed.add_field(
                    name="__Parameters__",
                    value="\n".join(param_lines),
                    inline=False
                )

        # Examples from docstring
        if cmd.help and ("__Examples:__" in cmd.help or "__Usage:__" in cmd.help):
            examples = []
            lines = cmd.help.split('\n')
            in_example_section = False

            for line in lines:
                if "__Examples:__" in line or "__Usage:__" in line:
                    in_example_section = True
                    continue
                if in_example_section:
                    if line.strip().startswith('>'):
                        # Extract the example
                        example = line.strip()[1:].strip()
                        if example.startswith('`') and example.endswith('`'):
                            examples.append(example)
                    elif line.strip() and not line.strip().startswith('>'):
                        # Hit next section
                        break

            if examples:
                embed.add_field(
                    name="__Examples__",
                    value="\n".join([f"> {ex}" for ex in examples[:3]]),
                    inline=False
                )

        # Footer with category info
        cog_name = cmd.cog.qualified_name if cmd.cog else "General"
        embed.set_footer(text=f"Category: {cog_name}")

        await ctx.send(embed=embed, reference=ctx.message if hasattr(ctx.message, 'reference') else None, mention_author=False)

    def get_home_embed(self):
        """Main help menu"""
        embed = discord.Embed(
            title="🎮 Bot Help Menu",
            description=(
                f"Welcome to the Pokétwo assistant bot!\n\n"
                f"__📚 Quick Navigation__\n"
                f"- Use the dropdown menu below to explore categories\n"
                f"- Use `{HELP_PREFIX}help <command>` for detailed info\n\n"
                f"__💬 Command Types__\n"
                f"- **Prefix** - Use `{HELP_PREFIX}` before command\n"
                f"- **Slash** - Use `/` before command\n"
                f"- **Context** - Right-click messages (see Context Menu page)"
            ),
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name="__📂 Categories__",
            value=(
                "- 📦 **Inventory** - Pokemon management\n"
                "- 💕 **Breeding** - Generate breeding pairs\n"
                "- 🔒 **Cooldown** - Track breeding cooldowns\n"
                "- ⚙️ **Settings** - Configure preferences\n"
                "- ✨ **Shiny Dex** - Track shiny collection\n"
                "- 🔍 **Pokedex** - Look up Pokemon info\n"
                "- 🛠️ **Utility** - Helper commands\n"
                "- 📱 **Context Menu** - Message actions"
            ),
            inline=False
        )

        embed.set_footer(text=f"Use {HELP_PREFIX}help <command> for details • Menu timeout: 3 minutes")

        return embed

    def get_inventory_embed(self):
        """Inventory commands help"""
        embed = discord.Embed(
            title="📦 __Inventory Commands__",
            description="Manage your Pokemon inventory across multiple categories",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}add` `{HELP_PREFIX}addtripmax` `{HELP_PREFIX}addtripzero`",
            value=(
                "> Add Pokemon to inventories\n"
                "> Reply to Pokétwo message or provide message IDs\n"
                "> Auto-detects page changes for 60 seconds"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}inv` `{HELP_PREFIX}invtripmax` `{HELP_PREFIX}invtripzero`",
            value=(
                "> View your Pokemon inventories\n"
                "> **Filters:** `--g male/female`, `--gmax`, `--regional`, `--n <name>`, `--cd`, `--nocd`"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}stats`",
            value="> View statistics for all inventories",
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}remove` `{HELP_PREFIX}clear`",
            value=(
                "> Remove Pokemon by ID or clear entire inventory\n"
                "> **Clear options:** `inv`, `tripmax`, `tripzero`, `all`"
            ),
            inline=False
        )

        embed.set_footer(text=f"Example: {HELP_PREFIX}inv --g female --gmax")

        return embed

    def get_breeding_embed(self):
        """Breeding commands help"""
        embed = discord.Embed(
            title="💕 __Breeding Commands__",
            description="Generate optimal breeding pairs based on your settings",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"__🎲 Generate Pairs__",
            value=(
                f"`{HELP_PREFIX}breed [count]` `/breed [count]`\n"
                f"- Generate 1-2 breeding pairs\n"
                f"- Automatically adds Pokemon to cooldown\n"
                f"- Uses your configured settings"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__⚙️ Basic Settings__",
            value=(
                f"`{HELP_PREFIX}settings`\n"
                f"- View all current settings\n"
                f"- Configure mode, target, and display preferences"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🎯 Pairing Mode__",
            value=(
                f"`{HELP_PREFIX}settings mode <selective/notselective>`\n"
                f"- **Selective:** Pairs old IDs with new IDs\n"
                f"- **Not Selective:** Pairs any compatible Pokemon"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🎯 Breeding Targets__",
            value=(
                f"`{HELP_PREFIX}settings target <targets>`\n"
                f"- **Options:** `all`, `gmax`, `regionals`, `tripmax`, `tripzero`, `mychoice`\n"
                f"- Or specify Pokemon names: `pikachu, eevee`"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🔢 ID Overrides__",
            value=(
                f"`{HELP_PREFIX}setid` `{HELP_PREFIX}setnew` `{HELP_PREFIX}setold`\n"
                f"- Override ID categorization for selective mode\n"
                f"- Supports bulk operations and ranges"
            ),
            inline=False
        )

        embed.set_footer(text=f"💡 Example: {HELP_PREFIX}settings target gmax")

        return embed

    def get_cooldown_embed(self):
        """Cooldown commands help"""
        embed = discord.Embed(
            title="🔒 __Cooldown Commands__",
            description=f"Manage breeding cooldowns ({config.COOLDOWN_DAYS}d {config.COOLDOWN_HOURS}h duration)",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}cd list` `{HELP_PREFIX}cooldown list`",
            value=(
                "> View all Pokemon on cooldown\n"
                "> Shows time remaining and Pokemon details"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}cd add <ids>` `{HELP_PREFIX}cd remove <ids>`",
            value=(
                "> Manually manage cooldowns\n"
                "> Space-separated Pokemon IDs"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}cd clear`",
            value=(
                "> Clear ALL cooldowns\n"
                "> Requires confirmation"
            ),
            inline=False
        )

        embed.add_field(
            name="Note",
            value=(
                f"> Pokemon are automatically added to cooldown when using `{HELP_PREFIX}breed`\n"
                "> Cooldowns are global across all inventories"
            ),
            inline=False
        )

        embed.set_footer(text=f"Example: {HELP_PREFIX}cd add 123456 789012")

        return embed

    def get_settings_embed(self):
        """Settings commands help"""
        embed = discord.Embed(
            title="⚙️ __Settings Commands__",
            description="Configure your breeding preferences and behavior",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"__📊 View Settings__",
            value=(
                f"`{HELP_PREFIX}settings`\n"
                f"- View all current settings and available options"
            ),
            inline=False
        )

        embed.add_field(
            name="__🎯 Mode Configuration__",
            value=(
                f"`{HELP_PREFIX}settings mode <selective/notselective>`\n"
                f"- **Selective:** Pairs old IDs (≤271800) with new IDs (≥271900)\n"
                f"- **Not Selective:** Pairs any compatible Pokemon"
            ),
            inline=False
        )

        embed.add_field(
            name="__🎯 Target Configuration__",
            value=(
                f"`{HELP_PREFIX}settings target <targets>`\n"
                f"- `all` - Breed everything\n"
                f"- `gmax` - Gigantamax only\n"
                f"- `regionals` - Regional forms\n"
                f"- `tripmax` - High IV inventory\n"
                f"- `tripzero` - Low IV inventory\n"
                f"- `mychoice` - Custom pairing\n"
                f"- `pikachu, eevee` - Specific Pokemon"
            ),
            inline=False
        )

        embed.add_field(
            name="__💝 MyChoice Configuration__",
            value=(
                f"`{HELP_PREFIX}settings setmale <species>` - Set male species\n"
                f"`{HELP_PREFIX}settings setfemale <species>` - Set female species"
            ),
            inline=False
        )

        embed.add_field(
            name="__ℹ️ Display Configuration__",
            value=(
                f"`{HELP_PREFIX}settings info <detailed/simple/off>`\n"
                f"- **Detailed:** Full information with IVs and reasons\n"
                f"- **Simple:** Basic info only\n"
                f"- **Off:** Command only"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🔄 Reset Settings__",
            value=(
                f"`{HELP_PREFIX}reset-settings`\n"
                f"- Reset all settings to defaults"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Settings are saved per user")

        return embed

    def get_shinydex_embed(self):
        """Shiny Dex commands help"""
        embed = discord.Embed(
            title="✨ __Shiny Dex Commands__",
            description="Track and view your shiny Pokemon collection",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}trackshiny [msg_ids]`",
            value=(
                "> Track shinies from Pokétwo `--sh` messages\n"
                "> Reply to message or provide IDs\n"
                "> Auto-detects page changes for 5 minutes"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}shinydex` `{HELP_PREFIX}shinydexfull`",
            value=(
                "> **Basic dex** (`sd`) - One per dex number\n"
                "> **Full dex** (`sdf`) - All forms and genders"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}eventdex` `{HELP_PREFIX}pokemon`",
            value=(
                "> **Event dex** (`ed`) - Event Pokemon collection\n"
                "> **Pokemon list** (`p`) - Detailed list with filters"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}filter <name> <other filters like --t, --r, --ng>` `{HELP_PREFIX}order <type>`",
            value=(
                "> **Filter** - Use custom filters (eevos, starters, etc.)\n"
                "> **Order** - Set display order (iv, number, pokedex)"
            ),
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}shinystats` `{HELP_PREFIX}typestats` `{HELP_PREFIX}regionstats`",
            value="> View collection statistics and progress",
            inline=False
        )

        embed.add_field(
            name=f"`{HELP_PREFIX}removeshiny` `{HELP_PREFIX}clearshiny`",
            value="> Remove shinies by ID or clear all tracked shinies",
            inline=False
        )

        embed.add_field(
            name="Available Filters",
            value=(
                "> `--caught` `--uncaught` `--orderd` `--ordera`\n"
                "> `--region <name>` `--type <name>` `--name <search>`\n"
                "> `--page <number>` `--list` `--smartlist`"
            ),
            inline=False
        )

        embed.set_footer(text=f"Example: {HELP_PREFIX}shinydex --region kanto --caught")

        return embed

    def get_pokedex_embed(self):
        """Pokedex commands help"""
        embed = discord.Embed(
            title="🔍 __Pokedex Commands__",
            description="Look up detailed Pokemon information",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"__🔎 Lookup Command__",
            value=(
                f"`{HELP_PREFIX}dex <pokemon>` `{HELP_PREFIX}pokedex <pokemon>`\n"
                f"- Look up any Pokemon by name or dex number\n"
                f"- Supports all languages (EN, JP, DE, FR)\n"
                f"- Works with forms and alternate names"
            ),
            inline=False
        )

        embed.add_field(
            name="__🎮 Interactive Features__",
            value=(
                f"- Toggle between normal and shiny sprites\n"
                f"- View gender differences (male/female)\n"
                f"- Browse all forms via dropdown menu\n"
                f"- Navigate between dex numbers\n"
                f"- See your shiny count for that Pokemon"
            ),
            inline=False
        )

        embed.add_field(
            name="__📊 Information Displayed__",
            value=(
                f"- Base stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed)\n"
                f"- Types, region, and catchability\n"
                f"- Evolution line and methods\n"
                f"- Egg groups and hatch time\n"
                f"- Gender ratio and appearance\n"
                f"- Names in multiple languages"
            ),
            inline=False
        )

        embed.add_field(
            name="__💡 Examples__",
            value=(
                f"- `{HELP_PREFIX}dex bulbasaur` - Look up by name\n"
                f"- `{HELP_PREFIX}dex #25` - Look up by dex number\n"
                f"- `{HELP_PREFIX}dex deoxys` - Browse all forms\n"
                f"- `{HELP_PREFIX}dex pikachu` - See gender differences"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Supports accent-insensitive search")

        return embed

    def get_utility_embed(self):
        """Utility commands help"""
        embed = discord.Embed(
            title="🛠️ __Utility Commands__",
            description="Helpful commands for various tasks",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"__📝 Track Command__",
            value=(
                f"`{HELP_PREFIX}track <command template>`\n"
                f"- Track Pokemon IDs from an editing list\n"
                f"- Reply to message, edit it, then react with ✅\n"
                f"- **Example:** `{HELP_PREFIX}track p!select (id)`\n"
                f"- Monitors for 3 minutes"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__✏️ Format Command__",
            value=(
                f"`{HELP_PREFIX}format \"<pattern>\" <items>`\n"
                f"- Add prefix pattern to comma-separated items\n"
                f"- **Example:** `{HELP_PREFIX}format \"--n\" abra, kadabra`\n"
                f"- **Result:** `--n abra --n kadabra`"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__💰 Convert Command__",
            value=(
                f"`/convert <currency> <amount>`\n"
                f"- Convert between Pokétwo currencies\n"
                f"- **Currencies:** PC, Shards, Redeems, Incenses\n"
                f"- Slash command only"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🔄 Replace Command__",
            value=(
                f"`/replace <old> <new> <text>`\n"
                f"- Replace or remove phrases from text\n"
                f"- Leave `new` empty to remove phrase\n"
                f"- Slash command only"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__📊 Order Command__",
            value=(
                f"`{HELP_PREFIX}order <type>`\n"
                f"- Set Pokemon display order\n"
                f"- **Types:** `iv`, `iv+`, `iv-`, `number`, `number+`, `number-`, `pokedex`, `pokedex+`, `pokedex-`"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Track command auto-sends commands on Pokétwo response")

        return embed

    def get_context_embed(self):
        """Context menu commands help"""
        embed = discord.Embed(
            title="📱 Context Menu Commands",
            description=(
                "Right-click (or long-press on mobile) Pokétwo messages to access quick actions.\n\n"
                "__📖 How to Use__\n"
                "- Right-click any Pokétwo message\n"
                "- Select **Apps** from the menu\n"
                "- Choose one of the commands below"
            ),
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name="__✨ Add Shiny__",
            value=(
                "- Quickly track shinies from Pokétwo shiny list\n"
                "- Works with `--sh` embed messages\n"
                "- Automatically filters out event Pokemon\n"
                "- Shows summary of tracked shinies"
            ),
            inline=False
        )

        embed.add_field(
            name="__🗑️ Remove Shiny__",
            value=(
                "- Remove shinies from tracking\n"
                "- Works with any message containing Pokemon IDs\n"
                "- Extracts IDs and removes from your collection\n"
                "- Shows count of removed shinies"
            ),
            inline=False
        )

        embed.add_field(
            name="__🎉 Event Shiny Add__",
            value=(
                "- Track event Pokemon specifically\n"
                "- Works with `--sh` messages containing event forms\n"
                "- Separate tracking from regular shinies\n"
                "- View with `m!eventdex`"
            ),
            inline=False
        )

        embed.add_field(
            name="__🗑️ Event Shiny Remove__",
            value=(
                "- Remove event Pokemon from tracking\n"
                "- Similar to Remove Shiny but for events\n"
                "- Extracts IDs from message\n"
                "- Updates event dex"
            ),
            inline=False
        )

        embed.add_field(
            name="__⚠️ Requirements__",
            value=(
                "- Must be used on Pokétwo bot messages\n"
                "- Message must contain embed or Pokemon IDs\n"
                "- Works in any channel where bot has access\n"
                "- Ephemeral responses (only you see them)"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Context commands work even in archived threads!")

        return embed

    def get_listtools_embed(self):
        """List Tools commands help"""
        embed = discord.Embed(
            title="📋 __List Tools Commands__",
            description="Compare and manage Pokemon lists with powerful filtering",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"__🔍 Compare Command__",
            value=(
                f"`{HELP_PREFIX}compare <message_id_1> <message_id_2>`\n"
                f"- Compare Pokemon between two messages\n"
                f"- Shows Pokemon unique to each message\n"
                f"- Shows Pokemon common to both messages\n"
                f"- Displays statistics and counts\n"
                f"- Creates .txt file if output is large"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__✅ Check Command__",
            value=(
                f"`{HELP_PREFIX}check <pokemon names>`\n"
                f"- Check if specific Pokemon exist in a message\n"
                f"- Reply to any message containing Pokemon\n"
                f"- Provide comma-separated Pokemon names\n"
                f"- Shows which are found and which are missing\n"
                f"**Example:** Reply to message + `{HELP_PREFIX}check pikachu, charizard, mew`"
            ),
            inline=False
        )

        embed.add_field(
            name=f"__🗑️ Remove Command__",
            value=(
                f"`{HELP_PREFIX}removemons <pokemon names>`\n"
                f"Aliases: `{HELP_PREFIX}exclude`\n"
                f"- Remove specific Pokemon from a list\n"
                f"- Reply to message with Pokemon list\n"
                f"- Creates new filtered list without specified Pokemon\n"
                f"- Outputs as .txt file if list is large\n"
                f"**Example:** Reply to list + `{HELP_PREFIX}removemons mew, mewtwo`"
            ),
            inline=False
        )

        embed.add_field(
            name="__📄 Supported Formats__",
            value=(
                "All commands support:\n"
                "> - Message text content\n"
                "> - Discord embeds\n"
                "> - .txt file attachments\n"
                "> - Case-insensitive matching\n"
                "> - Automatic duplicate removal"
            ),
            inline=False
        )

        embed.add_field(
            name="__💡 Use Cases__",
            value=(
                "> **Compare:** Find missing Pokemon between two collections\n"
                "> **Check:** Verify if you have specific Pokemon\n"
                "> **Remove:** Filter out unwanted Pokemon from lists"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Perfect for trading, collecting, and inventory management!")

        return embed


async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
