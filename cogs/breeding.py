import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import config
from database import db

class Breeding(commands.Cog):
    """Breeding pair generation and management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='breed')
    @app_commands.describe(count="Number of pairs to generate (max 2)")
    async def breed_command(self, ctx, count: int = 1):
        """
        Generate optimal breeding pairs
        Usage: ?breed [count] or /breed [count]
        Max 2 pairs at a time
        """
        if count < 1 or count > config.MAX_BREED_PAIRS:
            await ctx.send(f"❌ Count must be between 1 and {config.MAX_BREED_PAIRS}")
            return

        utils = self.bot.get_cog('Utils')
        if not utils:
            await ctx.send("❌ Utils cog not loaded")
            return

        user_id = ctx.author.id

        # OPTIMIZATION: Fetch all data in parallel
        settings, cooldowns = await asyncio.gather(
            db.get_settings(user_id),
            db.get_cooldowns(user_id)
        )

        mode = settings.get('mode', 'notselective')
        targets = settings.get('target', ['all'])
        selective = mode == 'selective'
        show_info = settings.get('show_info', 'detailed')

        # Determine which category/inventory to use based on target
        category, breeding_mode = self.determine_category_from_target(targets)

        # Fetch Pokemon after determining category
        all_pokemon = await db.get_pokemon(user_id, category=category)

        # OPTIMIZATION: Convert cooldowns to set for O(1) lookups
        cooldown_ids = set(cooldowns.keys())
        available = [p for p in all_pokemon if p['pokemon_id'] not in cooldown_ids]

        if not available:
            await ctx.send(f"❌ No Pokemon available for breeding in {category} inventory (all on cooldown or inventory empty)")
            return

        # OPTIMIZATION: Enrich Pokemon data if needed (for old entries without pre-computed fields)
        available = self.enrich_pokemon_data(available, utils)

        # Generate pairs based on breeding mode
        pairs = []

        if breeding_mode == 'mychoice':
            pairs = await self.handle_mychoice_breeding(available, settings, utils, selective, count)
        elif breeding_mode == 'tripmax':
            pairs = await self.handle_tripmax_breeding(available, utils, selective, count)
        elif breeding_mode == 'tripzero':
            pairs = await self.handle_tripzero_breeding(available, utils, selective, count)
        elif breeding_mode == 'gmax':
            pairs = await self.handle_gmax_breeding(available, targets, utils, selective, count)
        elif breeding_mode == 'regionals':
            pairs = await self.handle_regionals_breeding(available, targets, utils, selective, count)
        elif breeding_mode == 'all':
            pairs = await self.handle_all_breeding(available, utils, selective, count)
        else:
            # Multiple specific Pokemon targets
            pairs = await self.handle_specific_targets_breeding(available, targets, utils, selective, count)

        if not pairs:
            await ctx.send("❌ No compatible breeding pairs found with current settings")
            return

        # Collect IDs to add to cooldown
        cooldown_ids_to_add = []
        for pair in pairs:
            cooldown_ids_to_add.extend([pair['female']['pokemon_id'], pair['male']['pokemon_id']])

        # OPTIMIZATION: Add cooldowns and send result in parallel
        await asyncio.gather(
            db.add_cooldown(user_id, cooldown_ids_to_add),
            self.send_breed_result(ctx, pairs, selective, utils, show_info)
        )

    def enrich_pokemon_data(self, pokemon_list, utils):
        """Add computed fields to Pokemon data if they don't exist (for backward compatibility)"""
        for pokemon in pokemon_list:
            # Only compute if fields don't exist
            if 'egg_groups' not in pokemon:
                egg_groups = utils.get_egg_groups(pokemon['name'])
                pokemon['egg_groups'] = egg_groups
                pokemon['is_ditto'] = 'Ditto' in egg_groups
                pokemon['is_gmax'] = utils.is_gigantamax(pokemon['name'])
                pokemon['is_regional'] = utils.is_regional(pokemon['name'])
                pokemon['base_species'] = utils.get_base_species(pokemon['name'])
        return pokemon_list

    def determine_category_from_target(self, targets):
        """
        Determine which inventory category to use and breeding mode
        Returns: (category, breeding_mode)
        """
        if 'tripmax' in targets:
            return (config.TRIPMAX_CATEGORY, 'tripmax')
        elif 'tripzero' in targets:
            return (config.TRIPZERO_CATEGORY, 'tripzero')
        elif 'mychoice' in targets:
            return (config.NORMAL_CATEGORY, 'mychoice')
        elif 'gigantamax' in targets or 'gmax' in targets:
            return (config.NORMAL_CATEGORY, 'gmax')
        elif 'regionals' in targets:
            return (config.NORMAL_CATEGORY, 'regionals')
        elif 'all' in targets:
            return (config.NORMAL_CATEGORY, 'all')
        else:
            return (config.NORMAL_CATEGORY, 'specific')

    # ===== HELPER FUNCTIONS =====

    def can_pair_pokemon(self, female, male, utils, selective):
        """Check if two Pokemon can be paired following all rules - OPTIMIZED"""
        # Use pre-computed fields instead of calling utils functions
        is_gmax_female = female.get('is_gmax', False)
        is_gmax_male = male.get('is_gmax', False)
        is_regional_female = female.get('is_regional', False)
        is_regional_male = male.get('is_regional', False)
        is_ditto_female = female.get('is_ditto', False)

        # Rule: Never pair two Gigantamax
        if is_gmax_female and is_gmax_male:
            return False

        # Rule: Never pair two Regional
        if is_regional_female and is_regional_male:
            return False

        # Rule: Gmax male can ONLY pair with Ditto
        if is_gmax_male and not is_ditto_female:
            return False

        # Rule: Regional male can ONLY pair with Ditto
        if is_regional_male and not is_ditto_female:
            return False

        # Check breeding compatibility using pre-computed egg groups
        if not self.can_breed_optimized(female, male):
            return False

        # If selective mode, check ID compatibility
        if selective and not utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
            return False

        return True

    def can_breed_optimized(self, female, male):
        """Optimized breeding check using pre-computed egg groups"""
        groups1 = female.get('egg_groups', ['Undiscovered'])
        groups2 = male.get('egg_groups', ['Undiscovered'])

        # Can't breed with Undiscovered
        if 'Undiscovered' in groups1 or 'Undiscovered' in groups2:
            return False

        # Ditto can breed with anything except Undiscovered
        if female.get('is_ditto', False) or male.get('is_ditto', False):
            return True

        # Need opposite genders
        if not ((female['gender'] == 'female' and male['gender'] == 'male')):
            return False

        # Check for shared egg group
        return any(group in groups2 for group in groups1)

    def find_best_male_for_female(self, female, males, dittos, utils, selective, used_male_ids):
        """
        Find best male match for a female following rule 1:
        1. Same dex number
        2. Compatible egg group
        3. Ditto
        """
        # Step 1: Try same dex number males
        same_dex_males = [
            m for m in males 
            if m.get('dex_number') == female.get('dex_number') 
            and m.get('dex_number', 0) > 0
            and m['pokemon_id'] not in used_male_ids
        ]

        for male in same_dex_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'same_dex'

        # Step 2: Try compatible egg group males
        female_groups = female.get('egg_groups', [])
        compatible_males = [
            m for m in males
            if m['pokemon_id'] not in used_male_ids
            and any(group in m.get('egg_groups', []) for group in female_groups)
        ]

        for male in compatible_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'compatible'

        # Step 3: Try Ditto
        for ditto in dittos:
            if ditto['pokemon_id'] not in used_male_ids:
                if self.can_pair_pokemon(female, ditto, utils, selective):
                    return ditto, 'ditto'

        return None, None

    # ===== BREEDING MODE HANDLERS =====

    async def handle_all_breeding(self, available, utils, selective, count):
        """Handle 'all' target - pair any compatible Pokemon"""
        females = [p for p in available if p['gender'] == 'female']
        males = [p for p in available if p['gender'] == 'male']
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort females by IV (highest first)
        females.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()

        # Pair females
        for female in females:
            if len(pairs) >= count:
                break

            male, match_type = self.find_best_male_for_female(female, males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # If still need more pairs, pair remaining males with Ditto
        if len(pairs) < count:
            remaining_males = [m for m in males if m['pokemon_id'] not in used_male_ids]
            remaining_males.sort(key=lambda x: x['iv_percent'], reverse=True)

            for male in remaining_males:
                if len(pairs) >= count:
                    break

                # Find ditto
                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    async def handle_gmax_breeding(self, available, targets, utils, selective, count):
        """Handle Gmax target - one Pokemon in pair MUST have Gigantamax"""
        gmax_females = [p for p in available if p['gender'] == 'female' and p.get('is_gmax', False)]
        gmax_males = [p for p in available if p['gender'] == 'male' and p.get('is_gmax', False)]
        normal_males = [p for p in available if p['gender'] == 'male' and not p.get('is_gmax', False)]
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort by IV
        gmax_females.sort(key=lambda x: x['iv_percent'], reverse=True)
        gmax_males.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()

        # Pair Gmax females (with normal males or ditto, NOT gmax males)
        for female in gmax_females:
            if len(pairs) >= count:
                break

            male, match_type = self.find_best_male_for_female(female, normal_males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair Gmax males with Ditto ONLY
        if len(pairs) < count:
            for male in gmax_males:
                if len(pairs) >= count:
                    break

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    async def handle_regionals_breeding(self, available, targets, utils, selective, count):
        """Handle Regionals target - one Pokemon in pair MUST be regional"""
        regional_females = [p for p in available if p['gender'] == 'female' and p.get('is_regional', False)]
        regional_males = [p for p in available if p['gender'] == 'male' and p.get('is_regional', False)]
        normal_males = [p for p in available if p['gender'] == 'male' and not p.get('is_regional', False)]
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort by IV
        regional_females.sort(key=lambda x: x['iv_percent'], reverse=True)
        regional_males.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()

        # Pair Regional females (with normal males or ditto, NOT regional males)
        for female in regional_females:
            if len(pairs) >= count:
                break

            male, match_type = self.find_best_male_for_female(female, normal_males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair Regional males with Ditto ONLY
        if len(pairs) < count:
            for male in regional_males:
                if len(pairs) >= count:
                    break

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    async def handle_tripmax_breeding(self, available, utils, selective, count):
        """Handle TripMax - pair high IV with high IV"""
        females = [p for p in available if p['gender'] == 'female']
        males = [p for p in available if p['gender'] == 'male']
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort by IV (highest first)
        females.sort(key=lambda x: x['iv_percent'], reverse=True)
        males.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()

        # Pair females in order of high IV
        for female in females:
            if len(pairs) >= count:
                break

            male, match_type = self.find_best_male_for_female(female, males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair remaining males with Ditto
        if len(pairs) < count:
            remaining_males = [m for m in males if m['pokemon_id'] not in used_male_ids]
            remaining_males.sort(key=lambda x: x['iv_percent'], reverse=True)

            for male in remaining_males:
                if len(pairs) >= count:
                    break

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    async def handle_tripzero_breeding(self, available, utils, selective, count):
        """Handle TripZero - pair low IV with low IV"""
        females = [p for p in available if p['gender'] == 'female']
        males = [p for p in available if p['gender'] == 'male']
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort by IV (lowest first)
        females.sort(key=lambda x: x['iv_percent'])
        males.sort(key=lambda x: x['iv_percent'])

        pairs = []
        used_male_ids = set()

        # Pair females in order of low IV
        for female in females:
            if len(pairs) >= count:
                break

            # For TripZero, find lowest IV compatible male
            male, match_type = self.find_best_male_for_female_tripzero(female, males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair remaining males with Ditto
        if len(pairs) < count:
            remaining_males = [m for m in males if m['pokemon_id'] not in used_male_ids]
            remaining_males.sort(key=lambda x: x['iv_percent'])

            for male in remaining_males:
                if len(pairs) >= count:
                    break

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    def find_best_male_for_female_tripzero(self, female, males, dittos, utils, selective, used_male_ids):
        """Find LOWEST IV male for TripZero"""
        # Step 1: Try same dex number males (lowest IV)
        same_dex_males = [
            m for m in males 
            if m.get('dex_number') == female.get('dex_number') 
            and m.get('dex_number', 0) > 0
            and m['pokemon_id'] not in used_male_ids
        ]
        same_dex_males.sort(key=lambda x: x['iv_percent'])

        for male in same_dex_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'same_dex'

        # Step 2: Try compatible egg group males (lowest IV)
        female_groups = female.get('egg_groups', [])
        compatible_males = [
            m for m in males
            if m['pokemon_id'] not in used_male_ids
            and any(group in m.get('egg_groups', []) for group in female_groups)
        ]
        compatible_males.sort(key=lambda x: x['iv_percent'])

        for male in compatible_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'compatible'

        # Step 3: Try Ditto (lowest IV)
        dittos_sorted = sorted(dittos, key=lambda x: x['iv_percent'])
        for ditto in dittos_sorted:
            if ditto['pokemon_id'] not in used_male_ids:
                if self.can_pair_pokemon(female, ditto, utils, selective):
                    return ditto, 'ditto'

        return None, None

    async def handle_mychoice_breeding(self, available, settings, utils, selective, count):
        """Handle MyChoice - user-specified male and female species - OPTIMIZED"""
        mychoice_male = settings.get('mychoice_male')
        mychoice_female = settings.get('mychoice_female')

        if not mychoice_male or not mychoice_female:
            return []

        # Filter available pokemon using the matches_target helper
        male_species_pokemon = []
        female_species_pokemon = []

        is_male_ditto = 'ditto' in mychoice_male.lower()
        is_female_ditto = 'ditto' in mychoice_female.lower()

        for pokemon in available:
            # Handle Ditto specially
            if is_male_ditto and pokemon.get('is_ditto', False):
                male_species_pokemon.append(pokemon)
            elif not is_male_ditto and pokemon['gender'] == 'male' and self.matches_target(pokemon, mychoice_male, utils):
                male_species_pokemon.append(pokemon)

            if is_female_ditto and pokemon.get('is_ditto', False):
                female_species_pokemon.append(pokemon)
            elif not is_female_ditto and pokemon['gender'] == 'female' and self.matches_target(pokemon, mychoice_female, utils):
                female_species_pokemon.append(pokemon)

        if not male_species_pokemon or not female_species_pokemon:
            return []

        # Sort by IV (highest first)
        male_species_pokemon.sort(key=lambda x: x['iv_percent'], reverse=True)
        female_species_pokemon.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()
        used_female_ids = set()

        for female in female_species_pokemon:
            if len(pairs) >= count:
                break

            if female['pokemon_id'] in used_female_ids:
                continue

            # Find best male (highest IV)
            best_male = None
            for male in male_species_pokemon:
                if male['pokemon_id'] in used_male_ids:
                    continue

                if selective and not utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
                    continue

                best_male = male
                break

            if best_male:
                pairs.append({'female': female, 'male': best_male})
                used_female_ids.add(female['pokemon_id'])
                used_male_ids.add(best_male['pokemon_id'])

        return pairs

    async def handle_specific_targets_breeding(self, available, targets, utils, selective, count):
        """Handle multiple specific Pokemon targets - OPTIMIZED"""
        # Filter Pokemon matching targets
        filtered = []

        for pokemon in available:
            for target in targets:
                if self.matches_target(pokemon, target, utils):
                    filtered.append(pokemon)
                    break

        if not filtered:
            return []

        # Separate filtered Pokemon by gender
        filtered_females = [p for p in filtered if p['gender'] == 'female']
        filtered_males = [p for p in filtered if p['gender'] == 'male']

        # Get ALL available males and dittos for pairing
        all_males = [p for p in available if p['gender'] == 'male']
        dittos = [p for p in available if p.get('is_ditto', False)]

        # Sort by IV (highest first)
        filtered_females.sort(key=lambda x: x['iv_percent'], reverse=True)
        filtered_males.sort(key=lambda x: x['iv_percent'], reverse=True)

        pairs = []
        used_male_ids = set()

        # Step 1: Pair filtered females with any compatible males
        for female in filtered_females:
            if len(pairs) >= count:
                break

            male, match_type = self.find_best_male_for_female(female, all_males, dittos, utils, selective, used_male_ids)

            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Step 2: If still need more pairs, pair filtered males with Ditto
        if len(pairs) < count:
            for male in filtered_males:
                if len(pairs) >= count:
                    break

                if male['pokemon_id'] in used_male_ids:
                    continue

                # Find available Ditto
                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            used_male_ids.add(male['pokemon_id'])
                            break

        return pairs

    def matches_target(self, pokemon, target, utils):
        """
        Check if a Pokemon matches the target specification - OPTIMIZED
        Uses pre-computed fields instead of calling utils functions
        """
        pokemon_name = pokemon['name'].lower()
        pokemon_base = pokemon.get('base_species', pokemon['name']).lower()
        target_lower = target.lower()

        # Form keywords that indicate a specific form is requested
        form_keywords = ['alolan', 'galarian', 'hisuian', 'paldean', 'gigantamax', 
                         'mega', 'primal', 'aqua breed', 'combat breed', 'blaze breed']

        target_has_form = any(keyword in target_lower for keyword in form_keywords)
        pokemon_has_form = pokemon.get('is_regional', False) or pokemon.get('is_gmax', False)

        # Case 1: Target specifies a form - require full name match
        if target_has_form:
            return target_lower in pokemon_name

        # Case 2: Target is base species only
        else:
            # Pokemon must NOT have a special form
            if pokemon_has_form:
                return False
            # Match base species or full name
            return target_lower == pokemon_base or target_lower in pokemon_name

    # ===== RESULT DISPLAY =====

    async def send_breed_result(self, ctx, pairs, selective, utils, show_info):
        """Send breeding pair results"""
        command_parts = ["<@716390085896962058> daycare add"]

        for pair in pairs:
            command_parts.append(str(pair['female']['pokemon_id']))
            command_parts.append(str(pair['male']['pokemon_id']))

        command = " ".join(command_parts)

        embed = discord.Embed(
            title="📝 Next Breeding Command",
            color=config.EMBED_COLOR
        )

        embed.description = f"```{command}```"

        # Only add pair details if show_info is not 'off'
        if show_info != 'off':
            for i, pair in enumerate(pairs, 1):
                female = pair['female']
                male = pair['male']

                comp = utils.get_compatibility(female, male, selective)

                female_icon = config.GENDER_FEMALE if female['gender'] == 'female' else config.GENDER_UNKNOWN
                male_icon = config.GENDER_MALE if male['gender'] == 'male' else config.GENDER_UNKNOWN

                if show_info == 'simple':
                    pair_info = f"**Compatibility:** {comp}"
                else:  # detailed
                    pair_info = (
                        f"**Female:** `{female['pokemon_id']}` {female['name']} {female_icon} • {female['iv_percent']}% IV\n"
                        f"**Male:** `{male['pokemon_id']}` {male['name']} {male_icon} • {male['iv_percent']}% IV\n"
                        f"**Compatibility:** {comp}"
                    )

                    reason = self.get_pairing_reason(female, male, utils, selective)
                    if reason:
                        pair_info += f"\n**Reason:** {reason}"

                embed.add_field(
                    name=f"Pair {i}/{len(pairs)}",
                    value=pair_info,
                    inline=False
                )

        embed.set_footer(text=f"These Pokemon have been added to cooldown for {config.COOLDOWN_DAYS}d {config.COOLDOWN_HOURS}h")

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    def get_pairing_reason(self, female, male, utils, selective):
        """Get human-readable reason for pairing - OPTIMIZED"""
        is_ditto_female = female.get('is_ditto', False)
        is_ditto_male = male.get('is_ditto', False)

        female_dex = female.get('dex_number', 0)
        male_dex = male.get('dex_number', 0)

        is_gmax_female = female.get('is_gmax', False)
        is_gmax_male = male.get('is_gmax', False)

        is_regional_female = female.get('is_regional', False)
        is_regional_male = male.get('is_regional', False)

        reasons = []

        # Gigantamax pairing
        if is_gmax_female and not is_gmax_male and not is_ditto_male:
            reasons.append("Gmax female with normal male")
        elif is_gmax_male and is_ditto_female:
            reasons.append("Gmax male with Ditto")

        # Regional pairing
        if is_regional_female and not is_regional_male and not is_ditto_male:
            reasons.append("Regional female with normal male")
        elif is_regional_male and is_ditto_female:
            reasons.append("Regional male with Ditto")

        # Same dex number
        if female_dex == male_dex and female_dex > 0 and not is_ditto_female and not is_ditto_male:
            reasons.append(f"Same dex #{female_dex}")

        # High IV match
        if female['iv_percent'] >= 80 and male['iv_percent'] >= 80:
            reasons.append("High IV pair")

        # Old/New
        if selective and utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
            reasons.append("Old+New IDs")

        return ", ".join(reasons) if reasons else None


async def setup(bot):
    await bot.add_cog(Breeding(bot))
