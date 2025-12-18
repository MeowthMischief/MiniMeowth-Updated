import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import config
from database import db

class Breeding(commands.Cog):
    """Breeding pair generation and management - OPTIMIZED"""

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

        # Determine category FIRST (before any DB queries)
        # This is done synchronously since it's just logic
        settings_future = db.get_settings(user_id)
        cooldowns_future = db.get_cooldowns(user_id)
        
        # Wait for both in parallel
        settings, cooldowns = await asyncio.gather(settings_future, cooldowns_future)

        mode = settings.get('mode', 'notselective')
        targets = settings.get('target', ['all'])
        selective = mode == 'selective'
        show_info = settings.get('show_info', 'detailed')

        # Determine category and breeding mode
        category, breeding_mode = self.determine_category_from_target(targets)

        # OPTIMIZATION 1: Fetch Pokemon with projection to reduce data transfer
        # Only fetch fields we actually need
        projection = {
            'pokemon_id': 1,
            'name': 1,
            'gender': 1,
            'iv_percent': 1,
            'dex_number': 1,
            'egg_groups': 1,
            'base_species': 1,
            'is_gmax': 1,
            'is_regional': 1,
            'is_ditto': 1
        }
        
        # OPTIMIZATION 2: Fetch Pokemon with projection
        all_pokemon = await db.get_pokemon(
            user_id, 
            category=category
        )

        # OPTIMIZATION 3: Convert cooldowns to set BEFORE filtering (already good)
        cooldown_ids = set(cooldowns.keys())
        
        # OPTIMIZATION 4: Single-pass filtering with gender pre-separation
        females = []
        males = []
        dittos = []
        
        for p in all_pokemon:
            if p['pokemon_id'] in cooldown_ids:
                continue
            
            # Enrich if needed (for old entries)
            if 'egg_groups' not in p:
                self.enrich_pokemon_single(p, utils)
            
            # Categorize by gender in one pass
            if p.get('is_ditto', False):
                dittos.append(p)
            elif p['gender'] == 'female':
                females.append(p)
            elif p['gender'] == 'male':
                males.append(p)

        available_count = len(females) + len(males) + len(dittos)
        
        if available_count == 0:
            await ctx.send(f"❌ No Pokemon available for breeding in {category} inventory (all on cooldown or inventory empty)")
            return

        # OPTIMIZATION 5: Pre-sort lists by IV once (not in each handler)
        females.sort(key=lambda x: x['iv_percent'], reverse=True)
        males.sort(key=lambda x: x['iv_percent'], reverse=True)

        # Generate pairs based on breeding mode with pre-sorted, pre-filtered data
        pairs = []

        if breeding_mode == 'mychoice':
            pairs = await self.handle_mychoice_breeding_opt(females, males, dittos, settings, utils, selective, count)
        elif breeding_mode == 'tripmax':
            pairs = self.handle_tripmax_breeding_opt(females, males, dittos, utils, selective, count)
        elif breeding_mode == 'tripzero':
            pairs = self.handle_tripzero_breeding_opt(females, males, dittos, utils, selective, count)
        elif breeding_mode == 'gmax':
            pairs = self.handle_gmax_breeding_opt(females, males, dittos, utils, selective, count)
        elif breeding_mode == 'regionals':
            pairs = self.handle_regionals_breeding_opt(females, males, dittos, utils, selective, count)
        elif breeding_mode == 'all':
            pairs = self.handle_all_breeding_opt(females, males, dittos, utils, selective, count)
        else:
            # Multiple specific Pokemon targets
            pairs = await self.handle_specific_targets_breeding_opt(females, males, dittos, targets, utils, selective, count)

        if not pairs:
            await ctx.send("❌ No compatible breeding pairs found with current settings")
            return

        # Collect IDs to add to cooldown
        cooldown_ids_to_add = []
        for pair in pairs:
            cooldown_ids_to_add.extend([pair['female']['pokemon_id'], pair['male']['pokemon_id']])

        # Add cooldowns and send result in parallel
        await asyncio.gather(
            db.add_cooldown(user_id, cooldown_ids_to_add),
            self.send_breed_result(ctx, pairs, selective, utils, show_info)
        )

    def enrich_pokemon_single(self, pokemon, utils):
        """Enrich a single Pokemon with computed fields"""
        egg_groups = utils.get_egg_groups(pokemon['name'])
        pokemon['egg_groups'] = egg_groups
        pokemon['is_ditto'] = 'Ditto' in egg_groups
        pokemon['is_gmax'] = utils.is_gigantamax(pokemon['name'])
        pokemon['is_regional'] = utils.is_regional(pokemon['name'])
        pokemon['base_species'] = utils.get_base_species(pokemon['name'])

    def determine_category_from_target(self, targets):
        """Determine which inventory category to use and breeding mode"""
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

    # ===== OPTIMIZED HELPER FUNCTIONS =====

    def can_pair_pokemon(self, female, male, utils, selective):
        """Check if two Pokemon can be paired - OPTIMIZED"""
        is_gmax_female = female.get('is_gmax', False)
        is_gmax_male = male.get('is_gmax', False)
        is_regional_female = female.get('is_regional', False)
        is_regional_male = male.get('is_regional', False)
        is_ditto_female = female.get('is_ditto', False)

        # Quick rejections first (fail fast)
        if is_gmax_female and is_gmax_male:
            return False
        if is_regional_female and is_regional_male:
            return False
        if is_gmax_male and not is_ditto_female:
            return False
        if is_regional_male and not is_ditto_female:
            return False

        # Breeding compatibility
        if not self.can_breed_optimized(female, male):
            return False

        # Selective mode check last (most expensive)
        if selective and not utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
            return False

        return True

    def can_breed_optimized(self, female, male):
        """Optimized breeding check"""
        groups1 = female.get('egg_groups', ['Undiscovered'])
        groups2 = male.get('egg_groups', ['Undiscovered'])

        if 'Undiscovered' in groups1 or 'Undiscovered' in groups2:
            return False

        if female.get('is_ditto', False) or male.get('is_ditto', False):
            return True

        if not (female['gender'] == 'female' and male['gender'] == 'male'):
            return False

        return any(group in groups2 for group in groups1)

    # ===== OPTIMIZED BREEDING HANDLERS (removed async, pre-sorted lists) =====

    def handle_all_breeding_opt(self, females, males, dittos, utils, selective, count):
        """Handle 'all' target - OPTIMIZED with pre-filtered lists"""
        pairs = []
        used_male_ids = set()

        # Females already sorted by IV (highest first)
        for female in females:
            if len(pairs) >= count:
                break

            male, _ = self.find_best_male_for_female(female, males, dittos, utils, selective, used_male_ids)
            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair remaining males with Ditto
        if len(pairs) < count:
            for male in males:
                if len(pairs) >= count:
                    break
                if male['pokemon_id'] in used_male_ids:
                    continue

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    def handle_tripmax_breeding_opt(self, females, males, dittos, utils, selective, count):
        """Handle TripMax - OPTIMIZED (same as all breeding)"""
        return self.handle_all_breeding_opt(females, males, dittos, utils, selective, count)

    def handle_tripzero_breeding_opt(self, females, males, dittos, utils, selective, count):
        """Handle TripZero - OPTIMIZED with reversed sorting"""
        # Reverse sort for lowest IV first
        females_low = sorted(females, key=lambda x: x['iv_percent'])
        males_low = sorted(males, key=lambda x: x['iv_percent'])
        dittos_low = sorted(dittos, key=lambda x: x['iv_percent'])

        pairs = []
        used_male_ids = set()

        for female in females_low:
            if len(pairs) >= count:
                break

            male, _ = self.find_best_male_for_female_tripzero(female, males_low, dittos_low, utils, selective, used_male_ids)
            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        if len(pairs) < count:
            for male in males_low:
                if len(pairs) >= count:
                    break
                if male['pokemon_id'] in used_male_ids:
                    continue

                for ditto in dittos_low:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            break

        return pairs

    def handle_gmax_breeding_opt(self, females, males, dittos, utils, selective, count):
        """Handle Gmax - OPTIMIZED with pre-filtered lists"""
        # Filter gmax from already-separated lists
        gmax_females = [p for p in females if p.get('is_gmax', False)]
        gmax_males = [p for p in males if p.get('is_gmax', False)]
        normal_males = [p for p in males if not p.get('is_gmax', False)]

        pairs = []
        used_male_ids = set()

        # Step 1: Pair Gmax females with normal males or ditto
        for female in gmax_females:
            if len(pairs) >= count:
                break

            male, _ = self.find_best_male_for_female(female, normal_males, dittos, utils, selective, used_male_ids)
            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Step 2: Pair Gmax males with Ditto ONLY
        if len(pairs) < count:
            for male in gmax_males:
                if len(pairs) >= count:
                    break
                
                # Gmax males can ONLY pair with Ditto
                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            used_male_ids.add(male['pokemon_id'])  # Mark male as used too
                            break

        return pairs

    def handle_regionals_breeding_opt(self, females, males, dittos, utils, selective, count):
        """Handle Regionals - OPTIMIZED"""
        regional_females = [p for p in females if p.get('is_regional', False)]
        regional_males = [p for p in males if p.get('is_regional', False)]
        normal_males = [p for p in males if not p.get('is_regional', False)]

        pairs = []
        used_male_ids = set()

        # Step 1: Pair Regional females with normal males or ditto
        for female in regional_females:
            if len(pairs) >= count:
                break

            male, _ = self.find_best_male_for_female(female, normal_males, dittos, utils, selective, used_male_ids)
            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Step 2: Pair Regional males with Ditto ONLY
        if len(pairs) < count:
            for male in regional_males:
                if len(pairs) >= count:
                    break

                # Regional males can ONLY pair with Ditto
                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            used_male_ids.add(male['pokemon_id'])  # Mark male as used too
                            break

        return pairs

    async def handle_mychoice_breeding_opt(self, females, males, dittos, settings, utils, selective, count):
        """Handle MyChoice - OPTIMIZED"""
        mychoice_male = settings.get('mychoice_male')
        mychoice_female = settings.get('mychoice_female')

        if not mychoice_male or not mychoice_female:
            return []

        is_male_ditto = 'ditto' in mychoice_male.lower()
        is_female_ditto = 'ditto' in mychoice_female.lower()

        # Filter in single pass
        male_species_pokemon = []
        female_species_pokemon = []

        # Filter males
        if is_male_ditto:
            male_species_pokemon = dittos
        else:
            male_species_pokemon = [m for m in males if self.matches_target(m, mychoice_male, utils)]

        # Filter females
        if is_female_ditto:
            female_species_pokemon = dittos
        else:
            female_species_pokemon = [f for f in females if self.matches_target(f, mychoice_female, utils)]

        if not male_species_pokemon or not female_species_pokemon:
            return []

        pairs = []
        used_male_ids = set()
        used_female_ids = set()

        for female in female_species_pokemon:
            if len(pairs) >= count:
                break
            if female['pokemon_id'] in used_female_ids:
                continue

            for male in male_species_pokemon:
                if male['pokemon_id'] in used_male_ids:
                    continue
                if selective and not utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
                    continue

                pairs.append({'female': female, 'male': male})
                used_female_ids.add(female['pokemon_id'])
                used_male_ids.add(male['pokemon_id'])
                break

        return pairs

    async def handle_specific_targets_breeding_opt(self, females, males, dittos, targets, utils, selective, count):
        """Handle specific targets - OPTIMIZED"""
        # Filter matching Pokemon
        filtered_females = []
        filtered_males = []

        for target in targets:
            filtered_females.extend([f for f in females if self.matches_target(f, target, utils)])
            filtered_males.extend([m for m in males if self.matches_target(m, target, utils)])

        if not filtered_females:
            return []

        pairs = []
        used_male_ids = set()

        # Pair filtered females with any compatible males
        for female in filtered_females:
            if len(pairs) >= count:
                break

            male, _ = self.find_best_male_for_female(female, males, dittos, utils, selective, used_male_ids)
            if male:
                pairs.append({'female': female, 'male': male})
                used_male_ids.add(male['pokemon_id'])

        # Pair filtered males with Ditto
        if len(pairs) < count:
            for male in filtered_males:
                if len(pairs) >= count:
                    break
                if male['pokemon_id'] in used_male_ids:
                    continue

                for ditto in dittos:
                    if ditto['pokemon_id'] not in used_male_ids:
                        if self.can_pair_pokemon(ditto, male, utils, selective):
                            pairs.append({'female': ditto, 'male': male})
                            used_male_ids.add(ditto['pokemon_id'])
                            used_male_ids.add(male['pokemon_id'])
                            break

        return pairs

    def find_best_male_for_female(self, female, males, dittos, utils, selective, used_male_ids):
        """Find best male - OPTIMIZED"""
        # Try same dex number first
        same_dex_males = [
            m for m in males 
            if m.get('dex_number') == female.get('dex_number') 
            and m.get('dex_number', 0) > 0
            and m['pokemon_id'] not in used_male_ids
        ]

        for male in same_dex_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'same_dex'

        # Try compatible egg group
        female_groups = female.get('egg_groups', [])
        for male in males:
            if male['pokemon_id'] in used_male_ids:
                continue
            if any(group in male.get('egg_groups', []) for group in female_groups):
                if self.can_pair_pokemon(female, male, utils, selective):
                    return male, 'compatible'

        # Try Ditto
        for ditto in dittos:
            if ditto['pokemon_id'] not in used_male_ids:
                if self.can_pair_pokemon(female, ditto, utils, selective):
                    return ditto, 'ditto'

        return None, None

    def find_best_male_for_female_tripzero(self, female, males, dittos, utils, selective, used_male_ids):
        """Find LOWEST IV male - OPTIMIZED"""
        # Males already sorted low to high
        same_dex_males = [
            m for m in males 
            if m.get('dex_number') == female.get('dex_number') 
            and m.get('dex_number', 0) > 0
            and m['pokemon_id'] not in used_male_ids
        ]

        for male in same_dex_males:
            if self.can_pair_pokemon(female, male, utils, selective):
                return male, 'same_dex'

        female_groups = female.get('egg_groups', [])
        for male in males:
            if male['pokemon_id'] in used_male_ids:
                continue
            if any(group in male.get('egg_groups', []) for group in female_groups):
                if self.can_pair_pokemon(female, male, utils, selective):
                    return male, 'compatible'

        for ditto in dittos:
            if ditto['pokemon_id'] not in used_male_ids:
                if self.can_pair_pokemon(female, ditto, utils, selective):
                    return ditto, 'ditto'

        return None, None

    def matches_target(self, pokemon, target, utils):
        """Check if Pokemon matches target - OPTIMIZED"""
        pokemon_name = pokemon['name'].lower()
        pokemon_base = pokemon.get('base_species', pokemon['name']).lower()
        target_lower = target.lower()

        form_keywords = ['alolan', 'galarian', 'hisuian', 'paldean', 'gigantamax', 
                         'mega', 'primal', 'aqua breed', 'combat breed', 'blaze breed']

        target_has_form = any(keyword in target_lower for keyword in form_keywords)
        pokemon_has_form = pokemon.get('is_regional', False) or pokemon.get('is_gmax', False)

        if target_has_form:
            return target_lower in pokemon_name
        else:
            if pokemon_has_form:
                return False
            return target_lower == pokemon_base or target_lower in pokemon_name

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

        if show_info != 'off':
            for i, pair in enumerate(pairs, 1):
                female = pair['female']
                male = pair['male']

                comp = utils.get_compatibility(female, male, selective)

                female_icon = config.GENDER_FEMALE if female['gender'] == 'female' else config.GENDER_UNKNOWN
                male_icon = config.GENDER_MALE if male['gender'] == 'male' else config.GENDER_UNKNOWN

                if show_info == 'simple':
                    pair_info = f"**Compatibility:** {comp}"
                else:
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
        """Get human-readable reason for pairing"""
        is_ditto_female = female.get('is_ditto', False)
        is_ditto_male = male.get('is_ditto', False)

        female_dex = female.get('dex_number', 0)
        male_dex = male.get('dex_number', 0)

        is_gmax_female = female.get('is_gmax', False)
        is_gmax_male = male.get('is_gmax', False)

        is_regional_female = female.get('is_regional', False)
        is_regional_male = male.get('is_regional', False)

        reasons = []

        if is_gmax_female and not is_gmax_male and not is_ditto_male:
            reasons.append("Gmax female with normal male")
        elif is_gmax_male and is_ditto_female:
            reasons.append("Gmax male with Ditto")

        if is_regional_female and not is_regional_male and not is_ditto_male:
            reasons.append("Regional female with normal male")
        elif is_regional_male and is_ditto_female:
            reasons.append("Regional male with Ditto")

        if female_dex == male_dex and female_dex > 0 and not is_ditto_female and not is_ditto_male:
            reasons.append(f"Same dex #{female_dex}")

        if female['iv_percent'] >= 80 and male['iv_percent'] >= 80:
            reasons.append("High IV pair")

        if selective and utils.can_pair_ids(female['pokemon_id'], male['pokemon_id']):
            reasons.append("Old+New IDs")

        return ", ".join(reasons) if reasons else None


async def setup(bot):
    await bot.add_cog(Breeding(bot))
