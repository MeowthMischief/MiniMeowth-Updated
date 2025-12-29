import discord
from discord.ext import commands
import re
import csv
import config

class Utils(commands.Cog):
    """Utility functions for Pokemon parsing, breeding compatibility, and Shiny Dex"""

    # ===== CLASS-LEVEL CACHE (SHARED ACROSS ALL INSTANCES) =====
    # This data is loaded ONCE and shared by all bot instances
    _data_loaded = False
    _shared_data = {}

    def __init__(self, bot):
        self.bot = bot

        # Use shared class-level data instead of instance data
        if not Utils._data_loaded:
            print("📦 Loading Utils data for the first time...")
            Utils._shared_data = self._initialize_data_structures()
            self._load_all_data()
            Utils._data_loaded = True
            print(f"✅ Utils data loaded and cached")
        else:
            print("✅ Utils using cached data (no reload needed)")

        # Create instance references to shared data (for backward compatibility)
        self.egg_groups = Utils._shared_data['egg_groups']
        self.male_only_dex = Utils._shared_data['male_only_dex']
        self.female_only_dex = Utils._shared_data['female_only_dex']
        self.base_species_cache = Utils._shared_data['base_species_cache']
        self.dex_numbers = Utils._shared_data['dex_numbers']
        self.dex_forms = Utils._shared_data['dex_forms']
        self.dex_data = Utils._shared_data['dex_data']
        self.dex_by_number = Utils._shared_data['dex_by_number']
        self.pokemon_info = Utils._shared_data['pokemon_info']
        self.event_data = Utils._shared_data['event_data']
        self.event_pokemon_list = Utils._shared_data['event_pokemon_list']

        # Precompile regex patterns (instance-specific is fine)
        self.id_pattern = re.compile(r'`(\s*\d+\s*)`')
        self.name_pattern = re.compile(r'> ([^<]+)<:(?:male|female|unknown):')
        self.iv_pattern = re.compile(r'•\s*([\d.]+)%')

    def _initialize_data_structures(self):
        """Initialize all data structures (called once)"""
        return {
            'egg_groups': {},
            'male_only_dex': set(),
            'female_only_dex': set(),
            'base_species_cache': {},
            'dex_numbers': {},
            'dex_forms': {},
            'dex_data': {},
            'dex_by_number': {},
            'pokemon_info': {},
            'event_data': {},
            'event_pokemon_list': []
        }

    def _load_all_data(self):
        """Load all CSV data into shared cache"""
        self.load_dex_numbers()
        self.load_egg_groups()
        self.load_gender_only_species()
        self.load_pokemon_data()
        self.load_event_pokemon()

    def load_dex_numbers(self):
        """Load both dex_number.csv (breeding) and dex_number_updated.csv (shiny dex)"""
        dex_numbers = Utils._shared_data['dex_numbers']
        dex_forms = Utils._shared_data['dex_forms']
        dex_data = Utils._shared_data['dex_data']
        dex_by_number = Utils._shared_data['dex_by_number']

        # Load breeding bot dex numbers from dex_number.csv
        try:
            with open('data/dex_number.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        dex_num = int(row['Number']) if row['Number'] else 0
                        name = row['Name'].strip()
                        form = row['Form'].strip() if row['Form'] else ""

                        # Store full name with form if it exists
                        full_name = f"{form} {name}".strip() if form else name

                        # Map full name to dex number (for breeding bot)
                        dex_numbers[full_name] = dex_num

                        # Also map base name to dex number (for lookups)
                        if not form:
                            dex_numbers[name] = dex_num

                        # Store in forms dict for reverse lookup (for breeding bot)
                        dex_forms[(dex_num, form)] = full_name

                    except (ValueError, KeyError) as e:
                        continue

            print(f"✅ Loaded {len(dex_numbers)} breeding dex number entries from data/dex_number.csv")
        except Exception as e:
            print(f"❌ Error loading data/dex_number.csv: {e}")

        # Load shiny dex numbers from dex_number_updated.csv
        try:
            with open('data/dex_number_updated.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        dex_num = int(row['Number']) if row['Number'] else 0
                        name = row['Name'].strip()
                        has_gender_diff = row.get('HasGenderDifference', '').strip().lower() == 'yes'

                        # Store in dex_data (for shiny dex)
                        dex_data[name] = {
                            'dex_number': dex_num,
                            'has_gender_diff': has_gender_diff
                        }

                        # Store in dex_by_number (for shiny dex)
                        if dex_num not in dex_by_number:
                            dex_by_number[dex_num] = []
                        dex_by_number[dex_num].append((name, has_gender_diff))

                    except (ValueError, KeyError) as e:
                        continue

            print(f"✅ Loaded {len(dex_data)} shiny dex number entries from data/dex_number_updated.csv")
        except Exception as e:
            print(f"❌ Error loading data/dex_number_updated.csv: {e}")

    def load_egg_groups(self):
        """Load egg groups for breeding bot"""
        egg_groups = Utils._shared_data['egg_groups']
        try:
            with open('data/egg_groups.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['Name'].strip()
                    groups = row['Egg Groups'].strip()
                    if groups:
                        egg_groups[name] = [g.strip() for g in groups.split(',')]
            print(f"✅ Loaded {len(egg_groups)} egg group entries")
        except Exception as e:
            print(f"❌ Error loading data/egg_groups.csv: {e}")

    def load_gender_only_species(self):
        """Load male-only and female-only species by dex number"""
        male_only_dex = Utils._shared_data['male_only_dex']
        female_only_dex = Utils._shared_data['female_only_dex']

        # Load male-only species
        try:
            with open('data/male.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'dex' in row:
                        try:
                            dex_num = int(row['dex'])
                            male_only_dex.add(dex_num)
                        except ValueError:
                            continue
            print(f"✅ Loaded {len(male_only_dex)} male-only dex numbers")
        except Exception as e:
            print(f"❌ Error loading data/male.csv: {e}")

        # Load female-only species
        try:
            with open('data/female.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'dex' in row:
                        try:
                            dex_num = int(row['dex'])
                            female_only_dex.add(dex_num)
                        except ValueError:
                            continue
            print(f"✅ Loaded {len(female_only_dex)} female-only dex numbers")
        except Exception as e:
            print(f"❌ Error loading data/female.csv: {e}")

    def load_pokemon_data(self):
        """Load pokemon_data.csv for region/type filtering (shiny dex)"""
        pokemon_info = Utils._shared_data['pokemon_info']
        try:
            with open('data/pokemon_data.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['name'].strip()
                    region = row['region'].strip() if row['region'] else ""
                    type1 = row['type1'].strip() if row['type1'] else ""
                    type2 = row['type2'].strip() if row['type2'] else ""

                    pokemon_info[name] = {
                        'region': region,
                        'type1': type1,
                        'type2': type2
                    }

            print(f"✅ Loaded {len(pokemon_info)} pokemon data entries")
        except Exception as e:
            print(f"❌ Error loading data/pokemon_data.csv: {e}")

    def load_event_pokemon(self):
        """Load event_pokemon.csv (shiny dex)"""
        event_data = Utils._shared_data['event_data']
        event_pokemon_list = Utils._shared_data['event_pokemon_list']

        try:
            with open('data/event_pokemon.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        name = row['Name'].strip()
                        has_gender_diff = row['HasGenderDifference'].strip().lower() == 'yes'

                        # Store in event_data
                        event_data[name] = {
                            'has_gender_diff': has_gender_diff
                        }

                        # Store in list
                        event_pokemon_list.append((name, has_gender_diff))

                    except (ValueError, KeyError) as e:
                        continue

            print(f"✅ Loaded {len(event_data)} event pokemon entries")
        except Exception as e:
            print(f"❌ Error loading data/event_pokemon.csv: {e}")

    # ===== SHARED METHODS =====

    def get_dex_number(self, pokemon_name: str):
        """Get dex number for a pokemon name"""
        # Try exact match first (for breeding bot compatibility)
        if pokemon_name in self.dex_numbers:
            return self.dex_numbers[pokemon_name]

        # Try dex_data (for shiny dex)
        if pokemon_name in self.dex_data:
            return self.dex_data[pokemon_name]['dex_number']

        # Try base species
        base = self.get_base_species(pokemon_name)
        if base in self.dex_numbers:
            return self.dex_numbers[base]
        if base in self.dex_data:
            return self.dex_data[base]['dex_number']

        # Return 0 for unknown (breeding bot) or None (shiny dex)
        return 0

    # ===== BREEDING BOT METHODS =====

    def get_egg_groups(self, species_name: str):
        """Get egg groups for a species (with caching)"""
        # Use cached base species lookup
        base_name = self.get_base_species(species_name)
        return self.egg_groups.get(base_name, ['Undiscovered'])

    def get_base_species(self, name: str):
        """Remove regional/form prefixes to get base species (cached)"""
        # Check cache first
        if name in self.base_species_cache:
            return self.base_species_cache[name]

        original_name = name
        prefixes = [
            'Alolan ', 'Galarian ', 'Hisuian ', 'Paldean ',
            'Gigantamax ', 'Mega ', 'Primal ',
            'Aqua Breed ', 'Combat Breed ', 'Blaze Breed '
        ]

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name.replace(prefix, '', 1)
                break  # Only remove first matching prefix

        result = name.strip()

        # Cache the result
        self.base_species_cache[original_name] = result
        return result

    def is_regional(self, name: str):
        """Check if Pokemon is a regional form"""
        return name.startswith((
            'Alolan ', 'Galarian ', 'Hisuian ', 'Paldean ',
            'Aqua Breed ', 'Combat Breed ', 'Blaze Breed '
        ))

    def is_gigantamax(self, name: str):
        """Check if Pokemon is Gigantamax"""
        return 'Gigantamax' in name

    def is_male_only(self, species: str):
        """Check if species is male-only by dex number"""
        dex_num = self.get_dex_number(species)
        return dex_num in self.male_only_dex

    def is_female_only(self, species: str):
        """Check if species is female-only by dex number"""
        dex_num = self.get_dex_number(species)
        return dex_num in self.female_only_dex

    def can_breed(self, species1: str, species2: str, gender1: str, gender2: str):
        """Check if two Pokemon can breed together"""
        groups1 = self.get_egg_groups(species1)
        groups2 = self.get_egg_groups(species2)

        # Can't breed with Undiscovered
        if 'Undiscovered' in groups1 or 'Undiscovered' in groups2:
            return False

        # Ditto can breed with anything except Undiscovered
        if 'Ditto' in groups1 or 'Ditto' in groups2:
            return True

        # Need opposite genders
        if not ((gender1 == 'male' and gender2 == 'female') or 
                (gender1 == 'female' and gender2 == 'male')):
            return False

        # Check for shared egg group
        return any(group in groups2 for group in groups1)

    def categorize_id(self, pokemon_id: int, overrides: dict = None):
        """
        Categorize Pokemon ID as old, new, or unknown
        overrides: dict of {pokemon_id: 'old'/'new'} from database
        """
        # Check override first
        if overrides and pokemon_id in overrides:
            return overrides[pokemon_id]

        # Use default logic
        if pokemon_id <= config.OLD_ID_MAX:
            return 'old'
        elif pokemon_id >= config.NEW_ID_MIN:
            return 'new'
        else:
            return 'unknown'

    def can_pair_ids(self, id1: int, id2: int, overrides: dict = None):
        """
        Check if two IDs can be paired (one old, one new)
        overrides: dict of {pokemon_id: 'old'/'new'} from database
        """
        cat1 = self.categorize_id(id1, overrides)
        cat2 = self.categorize_id(id2, overrides)

        if cat1 == 'unknown' or cat2 == 'unknown':
            return False

        return (cat1 == 'old' and cat2 == 'new') or (cat1 == 'new' and cat2 == 'old')

    def get_compatibility(self, pokemon1: dict, pokemon2: dict, selective_mode: bool, overrides: dict = None):
        """Calculate expected compatibility (High/Medium/Low) with ID overrides"""
        # Use pre-computed fields
        is_ditto1 = pokemon1.get('is_ditto', False)
        is_ditto2 = pokemon2.get('is_ditto', False)

        # Ditto pairs: Medium or Low (never High)
        if is_ditto1 or is_ditto2:
            if selective_mode and self.can_pair_ids(pokemon1['pokemon_id'], pokemon2['pokemon_id'], overrides):
                return "Medium"
            else:
                return "Low/Medium"

        # Same dex number
        dex1 = pokemon1.get('dex_number', 0)
        dex2 = pokemon2.get('dex_number', 0)

        if dex1 == dex2 and dex1 > 0:
            # Same dex number - check old/new
            if selective_mode and self.can_pair_ids(pokemon1['pokemon_id'], pokemon2['pokemon_id'], overrides):
                return "High"
            else:
                return "Medium"
        else:
            # Different dex number (same egg group)
            if selective_mode and self.can_pair_ids(pokemon1['pokemon_id'], pokemon2['pokemon_id'], overrides):
                return "Medium"
            else:
                return "Low/Medium"

    def parse_embed_content(self, embed_description: str):
        """Parse Poketwo embed description to extract Pokemon data (optimized with pre-computed fields)"""
        if not embed_description:
            return []

        pokemon_data = []
        lines = embed_description.strip().split('\n')

        for line in lines:
            # Quick pre-check to skip irrelevant lines
            if '`' not in line or '•' not in line:
                continue

            try:
                # Extract ID using precompiled regex
                id_match = self.id_pattern.search(line)
                if not id_match:
                    continue
                pokemon_id = int(id_match.group(1).strip())

                # Extract name using precompiled regex
                name_match = self.name_pattern.search(line)
                if not name_match:
                    continue
                pokemon_name = name_match.group(1).strip()

                # Skip shinies (early exit)
                if '✨' in pokemon_name:
                    continue

                # Remove Gigantamax emoji if present
                pokemon_name = pokemon_name.replace('✨ ', '').strip()

                # Extract gender (optimized with elif)
                if '<:male:' in line:
                    gender = 'male'
                elif '<:female:' in line:
                    gender = 'female'
                elif '<:unknown:' in line:
                    gender = 'unknown'
                else:
                    continue

                # Extract IV percentage using precompiled regex
                iv_match = self.iv_pattern.search(line)
                iv_percent = float(iv_match.group(1)) if iv_match else 0.0

                # Get dex number
                dex_number = self.get_dex_number(pokemon_name)

                # Pre-compute all derived fields
                egg_groups = self.get_egg_groups(pokemon_name)
                base_species = self.get_base_species(pokemon_name)
                is_gmax = self.is_gigantamax(pokemon_name)
                is_regional = self.is_regional(pokemon_name)
                is_ditto = 'Ditto' in egg_groups

                pokemon_data.append({
                    'pokemon_id': pokemon_id,
                    'name': pokemon_name,
                    'gender': gender,
                    'iv_percent': iv_percent,
                    'dex_number': dex_number,
                    # Pre-computed fields for breeding logic
                    'egg_groups': egg_groups,
                    'base_species': base_species,
                    'is_gmax': is_gmax,
                    'is_regional': is_regional,
                    'is_ditto': is_ditto
                })

            except (ValueError, AttributeError):
                # Skip problematic lines silently
                continue

        return pokemon_data

    async def fetch_embed_by_id(self, ctx, message_id: int):
        """Fetch a message and return its first embed"""
        try:
            message = await ctx.channel.fetch_message(message_id)
            return message.embeds[0] if message.embeds else None
        except (discord.NotFound, discord.Forbidden, ValueError):
            return None

    # ===== SHINY DEX METHODS =====

    def has_gender_difference(self, pokemon_name: str) -> bool:
        """Check if a specific Pokemon name has gender differences"""
        if pokemon_name in self.dex_data:
            return self.dex_data[pokemon_name]['has_gender_diff']
        return False

    def is_event_pokemon(self, pokemon_name: str) -> bool:
        """Check if a Pokemon is an event Pokemon"""
        return pokemon_name in self.event_data

    def has_gender_difference_event(self, pokemon_name: str) -> bool:
        """Check if an event Pokemon has gender differences"""
        if pokemon_name in self.event_data:
            return self.event_data[pokemon_name]['has_gender_diff']
        return False

    def get_pokemon_info(self, pokemon_name: str):
        """Get region and type info for a Pokemon"""
        return self.pokemon_info.get(pokemon_name)

    def get_basic_dex_entries(self):
        """Get list of (dex_number, pokemon_name) for basic dex - one per dex number (the first/top one)"""
        entries = []
        for dex_num in sorted(self.dex_by_number.keys()):
            # Get the first Pokemon for this dex number
            if self.dex_by_number[dex_num]:
                first_pokemon = self.dex_by_number[dex_num][0][0]  # (name, has_gender_diff)[0] = name
                entries.append((dex_num, first_pokemon))
        return entries

    def get_full_dex_entries(self):
        """Get list of (dex_number, pokemon_name, has_gender_diff) for full dex - all forms"""
        entries = []
        for dex_num in sorted(self.dex_by_number.keys()):
            for name, has_gender_diff in self.dex_by_number[dex_num]:
                entries.append((dex_num, name, has_gender_diff))
        return entries

    def get_event_entries(self):
        """Get list of (pokemon_name, has_gender_diff) for event Pokemon"""
        return self.event_pokemon_list.copy()

    def get_total_unique_dex(self) -> int:
        """Get total number of unique dex numbers"""
        return len(self.dex_by_number)

    def get_total_forms_count(self) -> int:
        """Get total count of all forms including gender variants"""
        count = 0
        for dex_num in self.dex_by_number:
            for name, has_gender_diff in self.dex_by_number[dex_num]:
                if has_gender_diff:
                    count += 2  # Male and female
                else:
                    count += 1
        return count

    def get_total_event_count(self) -> int:
        """Get total count of event Pokemon including gender variants"""
        count = 0
        for name, has_gender_diff in self.event_pokemon_list:
            if has_gender_diff:
                count += 2  # Male and female
            else:
                count += 1
        return count

    def is_rare_pokemon(self, pokemon_name: str) -> bool:
        """Check if a Pokemon is rare"""
        return pokemon_name in config.RARE

    def count_rare_shinies(self, shinies_list: list) -> int:
        """Count rare shinies"""
        return sum(1 for s in shinies_list if self.is_rare_pokemon(s['name']))

    def count_regional_shinies(self, shinies_list: list) -> int:
        """Count regional form shinies"""
        return sum(1 for s in shinies_list if self.is_regional(s['name']))

    def count_mint_shinies(self, shinies_list: list) -> int:
        """Count level 1 shinies"""
        return sum(1 for s in shinies_list if s.get('level', 0) == 1)


async def setup(bot):
    await bot.add_cog(Utils(bot))
