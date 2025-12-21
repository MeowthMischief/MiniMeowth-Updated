import discord
from discord.ext import commands
from discord import app_commands
import config
from database import db

class MoreInfoView(discord.ui.View):
    """Button view for showing detailed settings info"""
    def __init__(self):
        super().__init__(timeout=300)  # 5 minute timeout

    @discord.ui.button(label="More Info", style=discord.ButtonStyle.primary, emoji="ℹ️")
    async def more_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📚 Detailed Settings Guide",
            color=config.EMBED_COLOR
        )

        # Pairing Modes
        embed.add_field(
            name="# Pairing Modes",
            value=(
                "**Selective (Old/New)**\n"
                "> Pairs old IDs (≤271800) with new IDs (≥271900)\n"
                "> - Same species + old/new = High compatibility\n"
                "> - Different species + old/new = Medium compatibility\n\n"
                "**Not Selective**\n"
                "> Pairs any compatible Pokemon regardless of ID\n"
                "> - Compatibility may vary based on species match"
            ),
            inline=False
        )

        # Target Options
        embed.add_field(
            name="# Target Options",
            value=(
                "**Special Modes:**\n"
                "- `all` - Breed any compatible Pokemon\n"
                "- `tripmax` - Breed from TripMax inventory (high IV)\n"
                "- `tripzero` - Breed from TripZero inventory (low IV)\n"
                "- `mychoice` - Use your custom male/female settings\n"
                "- `gigantamax` or `gmax` - Gigantamax Pokemon only\n"
                "- `regionals` or `reg` - Regional forms only\n\n"
                "**Specific Pokemon:**\n"
                "- Single: `pikachu`, `eevee`, `ditto`\n"
                "- Multiple: `pikachu, eevee, meowth`\n"
                "- Forms: `alolan meowth`, `gigantamax eevee`"
            ),
            inline=False
        )

        # Info Display Modes
        embed.add_field(
            name="# Info Display Modes",
            value=(
                "- `detailed` - Full embed with IVs, names, compatibility, reasons\n"
                "- `simple` - Basic embed with names and compatibility only\n"
                "- `compact` - Non-embed, just command + compatibility\n"
                "- `off` - Command only, no extra info"
            ),
            inline=False
        )

        # Quick Commands
        embed.add_field(
            name="# Quick Commands",
            value=(
                "```\n"
                f"{config.PREFIX}settings mode selective\n"
                f"{config.PREFIX}settings target pikachu, eevee\n"
                f"{config.PREFIX}settings setmale pikachu\n"
                f"{config.PREFIX}settings setfemale ditto\n"
                f"{config.PREFIX}settings info compact\n"
                f"{config.PREFIX}reset-settings\n"
                "```"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Settings(commands.Cog):
    """User settings management for breeding preferences"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='settings')
    @app_commands.describe(
        setting_type="Setting to change: mode, target, setmale, setfemale, or info",
        value="New value for the setting"
    )
    async def settings_command(self, ctx, setting_type: str = None, *, value: str = None):
        """
        Manage breeding settings
        Usage: settings [type] [value]
        """
        user_id = ctx.author.id

        if not setting_type:
            await self.show_settings(ctx)
            return

        setting_type = setting_type.lower()

        if setting_type == 'mode':
            await self.set_mode(ctx, value)
        elif setting_type == 'target':
            await self.set_target(ctx, value)
        elif setting_type == 'setmale':
            await self.set_mychoice_male(ctx, value)
        elif setting_type == 'setfemale':
            await self.set_mychoice_female(ctx, value)
        elif setting_type == 'info':
            await self.set_info_display(ctx, value)
        else:
            await ctx.send("❌ Invalid setting type. Use `mode`, `target`, `setmale`, `setfemale`, or `info`", reference=ctx.message, mention_author=False)

    async def show_settings(self, ctx):
        """Display current user settings - CLEAN REDESIGN"""
        user_id = ctx.author.id
        settings = await db.get_settings(user_id)

        embed = discord.Embed(
            title="⚙️ Your Breeding Settings",
            color=config.EMBED_COLOR
        )

        # ===== CURRENT MODE =====
        mode = settings.get('mode', 'notselective')
        mode_display = "Selective (Old/New)" if mode == 'selective' else "Not Selective"
        
        embed.add_field(
            name="# Current Mode",
            value=f"> {mode_display}",
            inline=False
        )

        # ===== CURRENT TARGET =====
        targets = settings.get('target', ['all'])
        
        if 'all' in targets:
            target_display = "> All Pokemon"
        elif 'tripmax' in targets:
            target_display = "> TripMax (High IV pairs)"
        elif 'tripzero' in targets:
            target_display = "> TripZero (Low IV pairs)"
        elif 'mychoice' in targets:
            mychoice_male = settings.get('mychoice_male', 'Not set')
            mychoice_female = settings.get('mychoice_female', 'Not set')
            target_display = f"> MyChoice\n> - {config.GENDER_MALE} Male: `{mychoice_male}`\n> - {config.GENDER_FEMALE} Female: `{mychoice_female}`"
        elif 'gigantamax' in targets or 'gmax' in targets:
            target_display = "> Gigantamax Pokemon"
        elif 'regionals' in targets or 'regional' in targets or 'reg' in targets:
            target_display = "> Regional forms"
        else:
            if len(targets) <= 3:
                target_list = ", ".join(f"`{t}`" for t in targets)
                target_display = f"> {target_list}"
            else:
                first_three = ", ".join(f"`{t}`" for t in targets[:3])
                remaining = len(targets) - 3
                target_display = f"> {first_three}\n> + {remaining} more"

        embed.add_field(
            name="# Current Target",
            value=target_display,
            inline=False
        )

        # ===== MYCHOICE SPECIES (if not active) =====
        if 'mychoice' not in targets:
            mychoice_male = settings.get('mychoice_male')
            mychoice_female = settings.get('mychoice_female')

            if mychoice_male or mychoice_female:
                mychoice_parts = []
                if mychoice_male:
                    mychoice_parts.append(f"> - {config.GENDER_MALE} Male: `{mychoice_male}`")
                if mychoice_female:
                    mychoice_parts.append(f"> - {config.GENDER_FEMALE} Female: `{mychoice_female}`")

                embed.add_field(
                    name="# MyChoice Species",
                    value="\n".join(mychoice_parts) + f"\n> *(Set target to `mychoice` to use)*",
                    inline=False
                )

        # ===== INFO DISPLAY =====
        show_info = settings.get('show_info', 'detailed')
        info_display = {
            "detailed": "> Detailed (Full embed)",
            "simple": "> Simple (Non-embed)",
            "compact": "> Compact (Basic embed)",
            "off": "> Off (Command only)"
        }

        embed.add_field(
            name="# Info Display",
            value=info_display.get(show_info, "> Unknown"),
            inline=False
        )

        embed.set_footer(text=f"Use {config.PREFIX}settings <type> <value> to change • Click 'More Info' for details")

        # Add button for detailed info
        view = MoreInfoView()
        await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=False)

    async def set_mychoice_male(self, ctx, value: str):
        """Set male species for mychoice target"""
        if not value:
            await ctx.send("❌ Please specify a species name or `none` to clear", reference=ctx.message, mention_author=False)
            return

        if value.lower() == 'none':
            user_id = ctx.author.id
            await db.update_settings(user_id, {'mychoice_male': None})
            await ctx.send("✅ MyChoice male cleared", reference=ctx.message, mention_author=False)
            return

        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        species_name = value.title()
        egg_groups = utils.get_egg_groups(species_name)

        if 'Undiscovered' in egg_groups and 'Ditto' not in egg_groups:
            await ctx.send(f"❌ **{species_name}** cannot breed (Undiscovered egg group)", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        settings = await db.get_settings(user_id)
        await db.update_settings(user_id, {'mychoice_male': species_name})

        mychoice_female = settings.get('mychoice_female')
        if mychoice_female:
            await self._validate_mychoice_pair(ctx, species_name, mychoice_female, utils)
        else:
            await ctx.send(f"✅ MyChoice male set to: `{species_name}`", reference=ctx.message, mention_author=False)

    async def set_mychoice_female(self, ctx, value: str):
        """Set female species for mychoice target"""
        if not value:
            await ctx.send("❌ Please specify a species name or `none` to clear", reference=ctx.message, mention_author=False)
            return

        if value.lower() == 'none':
            user_id = ctx.author.id
            await db.update_settings(user_id, {'mychoice_female': None})
            await ctx.send("✅ MyChoice female cleared", reference=ctx.message, mention_author=False)
            return

        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded", reference=ctx.message, mention_author=False)
            return

        species_name = value.title()
        egg_groups = utils.get_egg_groups(species_name)

        if 'Undiscovered' in egg_groups and 'Ditto' not in egg_groups:
            await ctx.send(f"❌ **{species_name}** cannot breed (Undiscovered egg group)", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        settings = await db.get_settings(user_id)
        await db.update_settings(user_id, {'mychoice_female': species_name})

        mychoice_male = settings.get('mychoice_male')
        if mychoice_male:
            await self._validate_mychoice_pair(ctx, mychoice_male, species_name, utils)
        else:
            await ctx.send(f"✅ MyChoice female set to: `{species_name}`", reference=ctx.message, mention_author=False)

    async def _validate_mychoice_pair(self, ctx, male_species: str, female_species: str, utils):
        """Validate mychoice male/female compatibility"""
        male_groups = utils.get_egg_groups(male_species)
        female_groups = utils.get_egg_groups(female_species)

        if 'Ditto' in male_groups and 'Ditto' in female_groups:
            await ctx.send("❌ Cannot set both male and female to Ditto!", reference=ctx.message, mention_author=False)
            return

        is_ditto_male = 'Ditto' in male_groups
        is_ditto_female = 'Ditto' in female_groups

        if not is_ditto_male and not is_ditto_female:
            shared_groups = set(male_groups) & set(female_groups)
            if not shared_groups:
                await ctx.send(
                    f"⚠️ **Warning**: {male_species} and {female_species} don't share any egg groups!\n"
                    f"- {male_species}: {', '.join(male_groups)}\n"
                    f"- {female_species}: {', '.join(female_groups)}\n"
                    f"> They cannot breed together!",
                    reference=ctx.message,
                    mention_author=False
                )
                return

        is_gmax_male = utils.is_gigantamax(male_species)
        is_gmax_female = utils.is_gigantamax(female_species)
        is_regional_male = utils.is_regional(male_species)
        is_regional_female = utils.is_regional(female_species)

        warnings = []
        if is_gmax_male and is_gmax_female:
            warnings.append("⚠️ Both are Gigantamax - consider saving one for another pair")
        if is_regional_male and is_regional_female:
            warnings.append("⚠️ Both are Regional forms - consider saving one for another pair")

        embed = discord.Embed(
            title="✅ MyChoice Pair Configured",
            color=config.EMBED_COLOR
        )

        male_info = f"> `{male_species}`\n> - Egg Groups: {', '.join(male_groups)}"
        female_info = f"> `{female_species}`\n> - Egg Groups: {', '.join(female_groups)}"

        embed.add_field(
            name=f"# {config.GENDER_MALE} Male",
            value=male_info,
            inline=True
        )

        embed.add_field(
            name=f"# {config.GENDER_FEMALE} Female",
            value=female_info,
            inline=True
        )

        if warnings:
            embed.add_field(
                name="# Warnings",
                value="\n".join(f"> {w}" for w in warnings),
                inline=False
            )
        else:
            embed.add_field(
                name="# Status",
                value="> ✅ Pair is compatible for breeding!",
                inline=False
            )

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def set_info_display(self, ctx, value: str):
        """Set breed info display mode"""
        if not value:
            await ctx.send("❌ Please specify: `simple`, `detailed`, `compact`, or `off`", reference=ctx.message, mention_author=False)
            return

        value = value.lower()

        if value not in ['simple', 'detailed', 'compact', 'off']:
            await ctx.send("❌ Invalid option. Use: `simple`, `detailed`, `compact`, or `off`", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        await db.update_settings(user_id, {'show_info': value})

        embed = discord.Embed(
            title="✅ Info Display Updated",
            color=config.EMBED_COLOR
        )

        descriptions = {
            'detailed': (
                "# Detailed Mode (Embed)\n"
                "> Shows complete pair information:\n"
                "> - Pokemon names and IDs\n"
                "> - IV percentages\n"
                "> - Expected compatibility\n"
                "> - Pairing reasons (Gmax, regional, high IV, etc.)"
            ),
            'compact': (
                "# Compact Mode (Embed)\n"
                "> Shows basic pair information:\n"
                "> - Pokemon names and IDs\n"
                "> - Expected compatibility only\n"
                "> - No IV details or pairing reasons"
            ),
            'simple': (
                "# Simple Mode (Non-embed)\n"
                "> Shows command with compatibility only:\n"
                "> - Breeding command in code block\n"
                "> - Expected compatibility per pair\n"
                "> - No embed formatting"
            ),
            'off': (
                "# Off Mode\n"
                "> Shows only the breeding command:\n"
                "> - Just the `@Pokétwo dc add` command\n"
                "> - No additional information"
            )
        }

        embed.description = descriptions[value]
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def set_mode(self, ctx, value: str):
        """Set pairing mode"""
        if not value:
            await ctx.send("❌ Please specify mode: `selective` or `notselective`", reference=ctx.message, mention_author=False)
            return

        value = value.lower()

        if value not in ['selective', 'notselective']:
            await ctx.send("❌ Invalid mode. Use `selective` or `notselective`", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        await db.update_settings(user_id, {'mode': value})

        embed = discord.Embed(
            title="✅ Mode Updated",
            color=config.EMBED_COLOR
        )

        if value == 'selective':
            description = (
                "# Selective Mode (Old/New) Enabled\n\n"
                "> Will pair old IDs (≤271800) with new IDs (≥271900)\n\n"
                "**Compatibility:**\n"
                "- Same species + old/new = High\n"
                "- Different species + old/new = Medium\n"
                "- Ditto + old/new = Medium"
            )
        else:
            description = (
                "# Not Selective Mode Enabled\n\n"
                "> Will pair any compatible Pokemon regardless of ID\n\n"
                "**Compatibility:**\n"
                "- Same species = Medium\n"
                "- Different species = Low/Medium\n"
                "- Ditto = Low/Medium"
            )

        embed.description = description
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def set_target(self, ctx, value: str):
        """Set breeding target"""
        if not value:
            await ctx.send("❌ Please specify target(s)", reference=ctx.message, mention_author=False)
            return

        value = value.lower()

        if 'all' in value:
            targets = ['all']
        else:
            targets = [t.strip() for t in value.split(',') if t.strip()]
            if not targets:
                await ctx.send("❌ No valid targets provided", reference=ctx.message, mention_author=False)
                return

        utils = self.bot.get_cog('Utils')
        if utils:
            special_keywords = ['all', 'gigantamax', 'gmax', 'regionals', 'regional', 'reg', 'tripmax', 'tripzero', 'mychoice']
            invalid_targets = []

            for target in targets:
                if target in special_keywords:
                    continue

                egg_groups = utils.get_egg_groups(target.title())
                if egg_groups == ['Undiscovered'] and target.lower() != 'ditto':
                    invalid_targets.append(target)

            if invalid_targets:
                await ctx.send(
                    f"⚠️ **Warning**: Some targets not found:\n"
                    f"{', '.join(f'`{t}`' for t in invalid_targets)}\n\n"
                    f"> These may not match any Pokemon.",
                    reference=ctx.message,
                    mention_author=False
                )

        user_id = ctx.author.id
        await db.update_settings(user_id, {'target': targets})

        embed = discord.Embed(
            title="✅ Target Updated",
            color=config.EMBED_COLOR
        )

        if 'all' in targets:
            embed.description = (
                "# Target: All Pokemon\n\n"
                "> Will breed any compatible Pokemon in your inventory"
            )
        else:
            if len(targets) <= 5:
                target_list = "\n".join(f"- `{t}`" for t in targets)
            else:
                first_five = "\n".join(f"- `{t}`" for t in targets[:5])
                remaining = len(targets) - 5
                target_list = f"{first_five}\n- ... and {remaining} more"

            embed.description = (
                f"# Breeding Targets Set\n\n{target_list}\n\n"
                f"> Will only breed Pokemon matching these targets"
            )

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    @commands.hybrid_command(name='reset-settings', aliases=['resetsettings'])
    async def reset_settings(self, ctx):
        """Reset all settings to defaults"""
        user_id = ctx.author.id

        await db.update_settings(user_id, {
            'mode': 'notselective',
            'target': ['all'],
            'mychoice_male': None,
            'mychoice_female': None,
            'show_info': 'detailed'
        })

        embed = discord.Embed(
            title="✅ Settings Reset",
            description="All settings have been reset to defaults",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name="# Current Settings",
            value=(
                "> - Mode: `notselective`\n"
                "> - Target: `all`\n"
                "> - MyChoice: cleared\n"
                "> - Info Display: `detailed`"
            ),
            inline=False
        )

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

async def setup(bot):
    await bot.add_cog(Settings(bot))
