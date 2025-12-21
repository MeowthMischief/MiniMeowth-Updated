import discord
from discord.ext import commands
from discord import app_commands
import config
from database import db

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
        Usage:
          settings - View current settings
          settings mode [selective/notselective] - Set pairing mode
          settings target [targets...] - Set breeding targets
          settings setmale [species] - Set male species for mychoice
          settings setfemale [species] - Set female species for mychoice
          settings info [simple/detailed/off] - Set info display mode

        Examples:
          settings mode selective
          settings target gigantamax pikachu, eevee
          settings target regionals
          settings target all
          settings setmale pikachu
          settings setfemale ditto
          settings info simple
        """
        user_id = ctx.author.id

        if not setting_type:
            # Display current settings
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
        """Display current user settings - REDESIGNED"""
        user_id = ctx.author.id
        settings = await db.get_settings(user_id)

        embed = discord.Embed(
            title="⚙️ Breeding Settings",
            description="Your current breeding configuration",
            color=config.EMBED_COLOR
        )

        # ===== PAIRING MODE =====
        mode = settings.get('mode', 'notselective')
        mode_icon = "🎯" if mode == 'selective' else "🔀"

        if mode == 'selective':
            mode_value = "**Selective (Old/New)**\nPairs old IDs (≤271800) with new IDs (≥271900) for higher compatibility"
        else:
            mode_value = "**Not Selective**\nPairs any compatible Pokemon regardless of ID"

        embed.add_field(
            name=f"{mode_icon} Current Mode",
            value=mode_value,
            inline=False
        )

        # ===== BREEDING TARGET =====
        targets = settings.get('target', ['all'])

        # Determine target type and description
        if 'all' in targets:
            target_icon = "🌐"
            target_title = "Current Target: All Pokemon"
            target_desc = "Breeds any compatible Pokemon in your inventory"

        elif 'tripmax' in targets:
            target_icon = "📈"
            target_title = "Current Target: TripMax"
            target_desc = "Breeds from TripMax inventory (high IV pairs)"

        elif 'tripzero' in targets:
            target_icon = "📉"
            target_title = "Current Target: TripZero"
            target_desc = "Breeds from TripZero inventory (low IV pairs)"

        elif 'mychoice' in targets:
            target_icon = "💑"
            target_title = "Current Target: MyChoice"
            mychoice_male = settings.get('mychoice_male', 'Not set')
            mychoice_female = settings.get('mychoice_female', 'Not set')
            target_desc = f"{config.GENDER_MALE} Male: `{mychoice_male}`\n{config.GENDER_FEMALE} Female: `{mychoice_female}`"

        elif 'gigantamax' in targets or 'gmax' in targets:
            target_icon = "⭐"
            target_title = "Current Target: Gigantamax"
            target_desc = "Breeds Pokemon where at least one parent is Gigantamax"

        elif 'regionals' in targets or 'reg' in targets:
            target_icon = "🗺️"
            target_title = "Current Target: Regionals"
            target_desc = "Breeds Pokemon where at least one parent is a regional form"

        else:
            target_icon = "🎯"
            target_title = f"Current Target: {len(targets)} Specific Pokemon"
            if len(targets) <= 5:
                target_desc = "Breeding: " + ", ".join(f"`{t}`" for t in targets)
            else:
                first_five = ", ".join(f"`{t}`" for t in targets[:5])
                remaining = len(targets) - 5
                target_desc = f"Breeding: {first_five}\n+ {remaining} more species"

        embed.add_field(
            name=f"{target_icon} {target_title}",
            value=target_desc,
            inline=False
        )

        # ===== MYCHOICE DETAILS (if not already shown) =====
        if 'mychoice' not in targets:
            mychoice_male = settings.get('mychoice_male')
            mychoice_female = settings.get('mychoice_female')

            if mychoice_male or mychoice_female:
                mychoice_parts = []
                if mychoice_male:
                    mychoice_parts.append(f"{config.GENDER_MALE} Male: `{mychoice_male}`")
                if mychoice_female:
                    mychoice_parts.append(f"{config.GENDER_FEMALE} Female: `{mychoice_female}`")

                embed.add_field(
                    name="💑 MyChoice Configuration",
                    value="\n".join(mychoice_parts) + f"\n*(Use `{config.PREFIX}settings target mychoice` to activate)*",
                    inline=False
                )

        # ===== INFO DISPLAY MODE =====
        show_info = settings.get('show_info', 'detailed')
        info_icons = {"detailed": "📋", "simple": "📄", "compact": "📦", "off": "🚫"}
        info_descs = {
            "detailed": "Shows full pair info (IVs, compatibility, reasons) - Embed",
            "simple": "Shows basic info (names, compatibility only) - Embed",
            "compact": "Shows command + compatibility only - Non-embed",
            "off": "Shows only the breeding command"
        }

        embed.add_field(
            name=f"{info_icons.get(show_info, '📋')} Info Display: {show_info.title()}",
            value=info_descs.get(show_info, "Unknown"),
            inline=False
        )

        # ===== AVAILABLE TARGETS GUIDE =====
        embed.add_field(
            name="📚 Available Targets",
            value=(
                "**Special Modes:**\n"
                "• `all` - Breed any compatible Pokemon\n"
                "• `tripmax` - Breed from TripMax inventory\n"
                "• `tripzero` - Breed from TripZero inventory\n"
                "• `mychoice` - Use your male/female settings\n"
                "• `gigantamax` or `gmax` - Gigantamax Pokemon\n"
                "• `regionals` - Regional forms\n\n"
                "**Specific Pokemon:**\n"
                "• Species name: `pikachu`, `eevee`, `meowth`\n"
                "• Multiple: `pikachu, eevee, meowth`\n"
                "• Forms: `alolan meowth`, `gigantamax eevee`"
            ),
            inline=False
        )

        # ===== QUICK COMMANDS =====
        embed.add_field(
            name="⚡ Quick Commands",
            value=(
                "```\n"
                f"{config.PREFIX}settings mode selective\n"
                f"{config.PREFIX}settings mode notselective\n"
                f"{config.PREFIX}settings target all\n"
                f"{config.PREFIX}settings target pikachu, eevee\n"
                f"{config.PREFIX}settings setmale pikachu\n"
                f"{config.PREFIX}settings setfemale ditto\n"
                f"{config.PREFIX}settings info simple\n"
                f"{config.PREFIX}reset-settings\n"
                "```"
            ),
            inline=False
        )

        embed.set_footer(text=f"Use {config.PREFIX}settings <type> <value> to change settings")

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

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

        # Validate species
        species_name = value.title()
        egg_groups = utils.get_egg_groups(species_name)

        # Check if species exists and can breed
        if 'Undiscovered' in egg_groups and 'Ditto' not in egg_groups:
            await ctx.send(f"❌ **{species_name}** cannot breed (Undiscovered egg group)", reference=ctx.message, mention_author=False)
            return

        # Save setting
        user_id = ctx.author.id
        settings = await db.get_settings(user_id)
        await db.update_settings(user_id, {'mychoice_male': species_name})

        # Check compatibility with female if already set
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

        # Validate species
        species_name = value.title()
        egg_groups = utils.get_egg_groups(species_name)

        # Check if species exists and can breed
        if 'Undiscovered' in egg_groups and 'Ditto' not in egg_groups:
            await ctx.send(f"❌ **{species_name}** cannot breed (Undiscovered egg group)", reference=ctx.message, mention_author=False)
            return

        # Save setting
        user_id = ctx.author.id
        settings = await db.get_settings(user_id)
        await db.update_settings(user_id, {'mychoice_female': species_name})

        # Check compatibility with male if already set
        mychoice_male = settings.get('mychoice_male')
        if mychoice_male:
            await self._validate_mychoice_pair(ctx, mychoice_male, species_name, utils)
        else:
            await ctx.send(f"✅ MyChoice female set to: `{species_name}`", reference=ctx.message, mention_author=False)

    async def _validate_mychoice_pair(self, ctx, male_species: str, female_species: str, utils):
        """Validate mychoice male/female compatibility"""
        male_groups = utils.get_egg_groups(male_species)
        female_groups = utils.get_egg_groups(female_species)

        # Check if both are Ditto
        if 'Ditto' in male_groups and 'Ditto' in female_groups:
            await ctx.send("❌ Cannot set both male and female to Ditto!", reference=ctx.message, mention_author=False)
            return

        # Check if they share egg groups or one is Ditto
        is_ditto_male = 'Ditto' in male_groups
        is_ditto_female = 'Ditto' in female_groups

        if not is_ditto_male and not is_ditto_female:
            # Check for shared egg group
            shared_groups = set(male_groups) & set(female_groups)
            if not shared_groups:
                await ctx.send(
                    f"⚠️ **Warning**: {male_species} and {female_species} don't share any egg groups!\n"
                    f"• {male_species}: {', '.join(male_groups)}\n"
                    f"• {female_species}: {', '.join(female_groups)}\n"
                    f"They cannot breed together!",
                    reference=ctx.message,
                    mention_author=False
                )
                return

        # Check if both are Gigantamax or both are Regional
        is_gmax_male = utils.is_gigantamax(male_species)
        is_gmax_female = utils.is_gigantamax(female_species)
        is_regional_male = utils.is_regional(male_species)
        is_regional_female = utils.is_regional(female_species)

        warnings = []
        if is_gmax_male and is_gmax_female:
            warnings.append("⚠️ Both are Gigantamax - you may want to save one for another pair")
        if is_regional_male and is_regional_female:
            warnings.append("⚠️ Both are Regional forms - you may want to save one for another pair")

        embed = discord.Embed(
            title="✅ MyChoice Pair Configured",
            color=config.EMBED_COLOR
        )

        embed.add_field(
            name=f"{config.GENDER_MALE} Male",
            value=f"`{male_species}`\nEgg Groups: {', '.join(male_groups)}",
            inline=True
        )

        embed.add_field(
            name=f"{config.GENDER_FEMALE} Female",
            value=f"`{female_species}`\nEgg Groups: {', '.join(female_groups)}",
            inline=True
        )

        if warnings:
            embed.add_field(
                name="⚠️ Warnings",
                value="\n".join(warnings),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Status",
                value="Pair is compatible for breeding!",
                inline=False
            )

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def set_info_display(self, ctx, value: str):
        """Set breed info display mode"""
        if not value:
            await ctx.send("❌ Please specify: `simple`, `detailed`, or `off`", reference=ctx.message, mention_author=False)
            return

        value = value.lower()

        if value not in ['simple', 'detailed', 'off']:
            await ctx.send("❌ Invalid option. Use: `simple`, `detailed`, or `off`", reference=ctx.message, mention_author=False)
            return

        user_id = ctx.author.id
        await db.update_settings(user_id, {'show_info': value})

        embed = discord.Embed(
            title="✅ Info Display Updated",
            color=config.EMBED_COLOR
        )

        descriptions = {
            'detailed': (
                "**Detailed Mode**\n\n"
                "Shows complete pair information:\n"
                "• Pokemon names and IDs\n"
                "• IV percentages\n"
                "• Expected compatibility\n"
                "• Pairing reasons (Gmax, regional, high IV, etc.)"
            ),
            'simple': (
                "**Simple Mode**\n\n"
                "Shows basic pair information:\n"
                "• Pokemon names and IDs\n"
                "• Expected compatibility only\n"
                "• No IV details or pairing reasons"
            ),
            'off': (
                "**Off Mode**\n\n"
                "Shows only the breeding command:\n"
                "• Just the `@Pokétwo dc add` command\n"
                "• No additional information"
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
                "**Selective Mode (Old/New) Enabled**\n\n"
                "✨ Will pair old IDs (≤271800) with new IDs (≥271900)\n"
                "✨ Maximizes compatibility:\n"
                "  • Same species + old/new = **High** compatibility\n"
                "  • Different species + old/new = **Medium** compatibility\n"
                "  • Ditto + old/new = **Medium** compatibility"
            )
        else:
            description = (
                "**Not Selective Mode Enabled**\n\n"
                "🔀 Will pair any compatible Pokemon regardless of ID\n"
                "🔀 Compatibility may vary:\n"
                "  • Same species = **Medium** compatibility\n"
                "  • Different species = **Low/Medium** compatibility\n"
                "  • Ditto = **Low/Medium** compatibility"
            )

        embed.description = description
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    async def set_target(self, ctx, value: str):
        """Set breeding target"""
        if not value:
            await ctx.send("❌ Please specify target(s)", reference=ctx.message, mention_author=False)
            return

        value = value.lower()

        # Parse targets (comma-separated)
        if 'all' in value:
            targets = ['all']
        else:
            # Split by comma and clean
            targets = [t.strip() for t in value.split(',') if t.strip()]

            if not targets:
                await ctx.send("❌ No valid targets provided", reference=ctx.message, mention_author=False)
                return

        # Validate species exist in egg_groups.csv (except special keywords)
        utils = self.bot.get_cog('Utils')
        if utils:
            special_keywords = ['all', 'gigantamax', 'gmax', 'regionals', 'reg', 'tripmax', 'tripzero', 'mychoice']
            invalid_targets = []

            for target in targets:
                if target in special_keywords:
                    continue

                # Check if species exists
                egg_groups = utils.get_egg_groups(target.title())
                if egg_groups == ['Undiscovered'] and target.lower() != 'ditto':
                    invalid_targets.append(target)

            if invalid_targets:
                await ctx.send(
                    f"⚠️ **Warning**: Some targets not found in egg groups data:\n"
                    f"{', '.join(f'`{t}`' for t in invalid_targets)}\n\n"
                    f"These may not match any Pokemon. Continue anyway?",
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
                "**Target: All Pokemon**\n\n"
                "Will breed any compatible Pokemon in your inventory"
            )
        else:
            if len(targets) <= 10:
                target_list = "\n".join(f"• `{t}`" for t in targets)
            else:
                first_ten = "\n".join(f"• `{t}`" for t in targets[:10])
                remaining = len(targets) - 10
                target_list = f"{first_ten}\n• ... and {remaining} more"

            embed.description = (
                f"**Breeding Targets Set:**\n{target_list}\n\n"
                f"Will only breed Pokemon matching these criteria:\n"
                f"• Species names (e.g., `pikachu`, `eevee`)\n"
                f"• Forms (e.g., `gigantamax`, `regionals`)\n"
                f"• Combinations (e.g., `gigantamax pikachu`)"
            )

        embed.add_field(
            name="💡 Special Keywords",
            value="• `gigantamax` or `gmax` - All Gigantamax Pokemon\n"
                  "• `regionals` - All regional forms (Alolan, Galarian, etc.)\n"
                  "• `tripmax` - Breed from TripMax inventory\n"
                  "• `tripzero` - Breed from TripZero inventory\n"
                  "• `mychoice` - Breed using your male/female settings\n"
                  "• `all` - Reset to breed everything",
            inline=False
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

        await ctx.send(
            "✅ Settings reset to defaults:\n"
            "• Mode: `notselective`\n"
            "• Target: `all`\n"
            "• MyChoice: cleared\n"
            "• Info Display: `detailed`",
            reference=ctx.message,
            mention_author=False
        )

async def setup(bot):
    await bot.add_cog(Settings(bot))
