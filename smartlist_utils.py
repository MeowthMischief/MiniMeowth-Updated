"""Utility functions for smartlist generation"""
import config


def categorize_pokemon(pokemon_names: list):
    """Categorize Pokemon into different groups

    Returns: (regular, rare, gigantamax, mega, transformable, hard_to_obtain)
    """
    regular = []
    rare = []
    gigantamax = []
    mega = []
    transformable = []
    hard_to_obtain = []

    # Get sets from config
    rare_set = set(config.RARE_POKEMONS) if hasattr(config, 'RARE_POKEMONS') else set()
    transformable_set = set(config.TRANSFORMABLE_POKEMONS) if hasattr(config, 'TRANSFORMABLE_POKEMONS') else set()
    hard_to_obtain_set = set(config.HARD_TO_OBTAIN_POKEMONS) if hasattr(config, 'HARD_TO_OBTAIN_POKEMONS') else set()

    for name in pokemon_names:
        name_lower = name.lower()

        # Check Gigantamax first
        if 'gigantamax' in name_lower:
            gigantamax.append(name)
        # Check if it's a Mega Pokemon (but not Meganium)
        elif name_lower.startswith('mega ') or (name_lower.startswith('mega') and name_lower != 'meganium'):
            mega.append(name)
        # Check if it's transformable
        elif name in transformable_set:
            transformable.append(name)
        # Check if it's hard to obtain
        elif name in hard_to_obtain_set:
            hard_to_obtain.append(name)
        # Check if it's rare
        elif name in rare_set:
            rare.append(name)
        else:
            regular.append(name)

    return regular, rare, gigantamax, mega, transformable, hard_to_obtain


def build_smartlist_sections(pokemon_data: list, utils):
    """Build smartlist sections from pokemon data

    Args:
        pokemon_data: list of tuples (name, gender_key, count)
        utils: Utils cog instance

    Returns:
        list of sections (strings) and total_count, gender_diff_count
    """
    # Separate by gender difference status
    no_gender_diff = []
    male_gender_diff = []
    female_gender_diff = []

    for name, gender_key, count in pokemon_data:
        has_gender_diff = utils.has_gender_difference(name)

        if has_gender_diff:
            if gender_key == 'male':
                male_gender_diff.append(name)
            elif gender_key == 'female':
                female_gender_diff.append(name)
        else:
            no_gender_diff.append(name)

    # Categorize each group
    regular, rare, gigantamax, mega, transformable, hard_to_obtain = categorize_pokemon(no_gender_diff)
    male_regular, male_rare, male_gmax, male_mega, male_transform, male_hard = categorize_pokemon(male_gender_diff)
    female_regular, female_rare, female_gmax, female_mega, female_transform, female_hard = categorize_pokemon(female_gender_diff)

    # Build the formatted output
    sections = []

    # Calculate total count based on actual entries in the list
    total_count = len(no_gender_diff) + len(male_gender_diff) + len(female_gender_diff)

    # Count unique species with gender differences that appear in this list
    gender_diff_species = set()
    for name, gender_key, count in pokemon_data:
        if utils.has_gender_difference(name):
            gender_diff_species.add(name)
    gender_diff_count = len(gender_diff_species)

    # Helper function to format pokemon names to lowercase
    def format_names(names):
        return " ".join([f"--n {name.lower()}" for name in names])

    # Header
    sections.append(f"**total pokemon: {total_count}** ({gender_diff_count} species with gender differences)\n")

    # Regular Pokemon (no gender difference)
    if regular:
        sections.append(format_names(regular))

    # Transformable Pokemon (no gender difference)
    if transformable:
        sections.append(format_names(transformable))

    # Hard to Obtain Pokemon (no gender difference)
    if hard_to_obtain:
        sections.append(format_names(hard_to_obtain))

    # Mega Pokemon (no gender difference)
    if mega:
        sections.append(format_names(mega))

    # Male Gender Difference Pokemon (regular only)
    if male_regular:
        sections.append(format_names(male_regular) + " --g male")

    # Female Gender Difference Pokemon (regular only)
    if female_regular:
        sections.append(format_names(female_regular) + " --g female")

    # Rare Pokemon (no gender difference)
    if rare:
        sections.append(format_names(rare))

    # Gigantamax Pokemon (no gender difference)
    if gigantamax:
        sections.append(format_names(gigantamax))

    return sections, total_count, gender_diff_count
