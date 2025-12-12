# Custom filters for shiny dex
# Each filter is a list of Pokemon names (exact match with base species names or forms)

FILTERS = {
    "eevee": {
        "name":
        "Eeveelutions",
        "aliases":
        ["ibui", "eievui", "eeveelutions", "evoli", "イーブイ", "Ībui", "Évoli"],
        "pokemon": [
            "Eevee", "Partner Eevee", "Vaporeon", "Jolteon", "Flareon",
            "Espeon", "Umbreon", "Leafeon", "Glaceon", "Sylveon"
        ]
    },
    "genderdifference": {
        "name":
        "Gender Difference Pokémons",
        "aliases": ["gd", "gender"],
        "pokemon": [
            "Hisuian Sneasel","Basculegion","Butterfree","Kricketune","Hippopotas","Oinkologne","Vileplume","Sudowoodo","Wobbuffet","Girafarig","Heracross","Piloswine","Octillery","Combusken","Beautifly","Relicanth","Staraptor","Kricketot","Pachirisu","Hippowdon","Toxicroak","Abomasnow","Rhyperior","Tangrowth","Mamoswine","Jellicent","Venusaur","Raticate","Alakazam","Magikarp","Gyarados","Meganium","Politoed","Quagsire","Ursaring","Houndoom","Blaziken","Ludicolo","Meditite","Medicham","Camerupt","Cacturne","Staravia","Roserade","Floatzel","Garchomp","Croagunk","Lumineon","Unfezant","Frillish","Meowstic","Indeedee","Rattata","Pikachu","Kadabra","Rhyhorn","Goldeen","Seaking","Scyther","Murkrow","Steelix","Sneasel","Donphan","Torchic","Nuzleaf","Shiftry","Roselia","Milotic","Bibarel","Ambipom","Finneon","Weavile","Raichu","Golbat","Dodrio","Rhydon","Ledyba","Ledian","Wooper","Gligar","Scizor","Dustox","Gulpin","Swalot","Starly","Bidoof","Luxray","Combee","Buizel","Gabite","Snover","Pyroar","Zubat","Gloom","Doduo","Hypno","Eevee","Aipom","Numel","Shinx","Luxio","Gible","Xatu"
        ]
    },
    "newmegas": {
        "name":
        "Gender New Mega Pokémons",
        "aliases": ["newmega", "new-megas", "mega2", "mega-2"],
        "pokemon": [
            "Stretchy Tatsugiri","Original Magearna","Droopy Tatsugiri","Crabominable","Victreebel","Feraligatr","Eelektross","Chandelure","Chesnaught","Barbaracle","Scovillain","Baxcalibur","Dragonite","Staraptor","Excadrill","Scolipede","Golisopod","Tatsugiri","Clefable","Meganium","Skarmory","Chimecho","Garchomp","Froslass","Greninja","Meowstic","Dragalge","Hawlucha","Magearna","Glimmora","Starmie","Lucario","Heatran","Darkrai","Scrafty","Delphox","Floette","Malamar","Zygarde","Zeraora","Falinks","Raichu","Emboar","Golurk","Pyroar","Drampa","Absol" 
    },
    "starters": {
        "name":
        "Starter Pokémon",
        "aliases": ["starter"],
        "pokemon": [
            # Gen 1
            "Bulbasaur",
            "Ivysaur",
            "Venusaur",
            "Charmander",
            "Charmeleon",
            "Charizard",
            "Squirtle",
            "Wartortle",
            "Blastoise",
            # Gen 2
            "Chikorita",
            "Bayleef",
            "Meganium",
            "Cyndaquil",
            "Quilava",
            "Typhlosion",
            "Totodile",
            "Croconaw",
            "Feraligatr",
            # Gen 3
            "Treecko",
            "Grovyle",
            "Sceptile",
            "Torchic",
            "Combusken",
            "Blaziken",
            "Mudkip",
            "Marshtomp",
            "Swampert",
            # Gen 4
            "Turtwig",
            "Grotle",
            "Torterra",
            "Chimchar",
            "Monferno",
            "Infernape",
            "Piplup",
            "Prinplup",
            "Empoleon",
            # Gen 5
            "Snivy",
            "Servine",
            "Serperior",
            "Tepig",
            "Pignite",
            "Emboar",
            "Oshawott",
            "Dewott",
            "Samurott",
            # Gen 6
            "Chespin",
            "Quilladin",
            "Chesnaught",
            "Fennekin",
            "Braixen",
            "Delphox",
            "Froakie",
            "Frogadier",
            "Greninja",
            # Gen 7
            "Rowlet",
            "Dartrix",
            "Decidueye",
            "Litten",
            "Torracat",
            "Incineroar",
            "Popplio",
            "Brionne",
            "Primarina",
            # Gen 8
            "Grookey",
            "Thwackey",
            "Rillaboom",
            "Scorbunny",
            "Raboot",
            "Cinderace",
            "Sobble",
            "Drizzile",
            "Inteleon",
            # Gen 9
            "Sprigatito",
            "Floragato",
            "Meowscarada",
            "Fuecoco",
            "Crocalor",
            "Skeledirge",
            "Quaxly",
            "Quaxwell",
            "Quaquaval"
        ]
    },
    "legendaries": {
        "name":
        "Legendary Pokémon",
        "aliases": ["legendary", "legend", "legends"],
        "pokemon": [
            "Articuno", "Zapdos", "Moltres", "Mewtwo", "Raikou", "Entei",
            "Suicune", "Lugia", "Ho-Oh", "Regirock", "Regice", "Registeel",
            "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza", "Uxie",
            "Mesprit", "Azelf", "Dialga", "Palkia", "Heatran", "Regigigas",
            "Giratina", "Cresselia", "Cobalion", "Terrakion", "Virizion",
            "Tornadus", "Thundurus", "Reshiram", "Zekrom", "Landorus",
            "Kyurem", "Xerneas", "Yveltal", "Zygarde", "Type: Null",
            "Silvally", "Tapu Koko", "Tapu Lele", "Tapu Bulu", "Tapu Fini",
            "Cosmog", "Cosmoem", "Solgaleo", "Lunala", "Necrozma", "Zacian",
            "Zamazenta", "Eternatus", "Kubfu", "Urshifu", "Regieleki",
            "Regidrago", "Glastrier", "Spectrier", "Calyrex", "Enamorus",
            "Wo-Chien", "Chien-Pao", "Ting-Lu", "Chi-Yu", "Koraidon",
            "Miraidon", "Okidogi", "Munkidori", "Fezandipiti", "Ogerpon",
            "Terapagos"
        ]
    },
    "legendarieswithforms": {
        "name":
        "Legendary Pokémons With Forms And Variants",
        "aliases":
        ["legendarywithforms", "legendwithforms", "legendswithforms"],
        "pokemon": [
            "Gigantamax Single Strike Urshifu",
            "Gigantamax Rapid Strike Urshifu", "Sprinting Build Koraidon",
            "Hearthflame Mask Ogerpon", "Cornerstone Mask Ogerpon",
            "Wellspring Mask Ogerpon", "Gliding Build Koraidon",
            "Rapid Strike Urshifu", "Shadow Rider Calyrex",
            "Dawn Wings Necrozma", "Eternamax Eternatus",
            "Drive Mode Miraidon", "Glide Mode Miraidon", "Dusk Mane Necrozma",
            "Terastal Terapagos", "Galarian Articuno", "Therian Thundurus",
            "Electric Silvally", "Fighting Silvally", "Crowned Zamazenta",
            "Ice Rider Calyrex", "Galarian Moltres", "Therian Tornadus",
            "Therian Landorus", "Complete Zygarde", "Psychic Silvally",
            "Therian Enamorus", "Galarian Zapdos", "Origin Giratina",
            "Neutral Xerneas", "Dragon Silvally", "Flying Silvally",
            "Ground Silvally", "Poison Silvally", "Primal Groudon",
            "Ghost Silvally", "Grass Silvally", "Steel Silvally",
            "Water Silvally", "Fairy Silvally", "Ultra Necrozma",
            "Crowned Zacian", "Mega Mewtwo X", "Mega Mewtwo Y",
            "Primal Kyogre", "Mega Rayquaza", "Origin Dialga", "Origin Palkia",
            "Dark Silvally", "Fire Silvally", "Rock Silvally", "Black Kyurem",
            "White Kyurem", "Zygarde Cell", "Zygarde Core", "Bug Silvally",
            "Ice Silvally", "Mega Latias", "Mega Latios", "10% Zygarde",
            "Fezandipiti", "Type: Null", "Registeel", "Regigigas", "Cresselia",
            "Terrakion", "Thundurus", "Tapu Koko", "Tapu Lele", "Tapu Bulu",
            "Tapu Fini", "Zamazenta", "Eternatus", "Regieleki", "Regidrago",
            "Glastrier", "Spectrier", "Chien-Pao", "Munkidori", "Terapagos",
            "Articuno", "Regirock", "Rayquaza", "Giratina", "Cobalion",
            "Virizion", "Tornadus", "Reshiram", "Landorus", "Silvally",
            "Solgaleo", "Necrozma", "Enamorus", "Wo-Chien", "Koraidon",
            "Miraidon", "Moltres", "Suicune", "Groudon", "Mesprit", "Heatran",
            "Xerneas", "Yveltal", "Zygarde", "Cosmoem", "Urshifu", "Calyrex",
            "Ting-Lu", "Okidogi", "Ogerpon", "Zapdos", "Mewtwo", "Raikou",
            "Regice", "Latias", "Latios", "Kyogre", "Dialga", "Palkia",
            "Zekrom", "Kyurem", "Cosmog", "Lunala", "Zacian", "Chi-Yu",
            "Entei", "Lugia", "Ho-Oh", "Azelf", "Kubfu", "Uxie"
        ]
    },
    "mythical": {
        "name":
        "Mythical Pokémon",
        "aliases": ["mythicals", "myth"],
        "pokemon": [
            "Mew", "Celebi", "Jirachi", "Deoxys", "Phione", "Manaphy",
            "Darkrai", "Shaymin", "Arceus", "Victini", "Keldeo", "Meloetta",
            "Genesect", "Diancie", "Hoopa", "Volcanion", "Magearna",
            "Marshadow", "Zeraora", "Meltan", "Melmetal", "Zarude", "Pecharunt"
        ]
    },
    "mythicalwithforms": {
        "name":
        "Mythical Pokémon With All Forms And Variants",
        "aliases": ["mythicalswithforms", "mythwithforms"],
        "pokemon": [
            "High-speed Flight Configuration Genesect", "Gigantamax Melmetal",
            "Pirouette Meloetta", "Original Magearna", "Zenith Marshadow",
            "Electric Arceus", "Fighting Arceus", "Resolute Keldeo",
            "Defense Deoxys", "Psychic Arceus", "Attack Deoxys",
            "Dragon Arceus", "Flying Arceus", "Ground Arceus", "Poison Arceus",
            "Hoopa Unbound", "Speed Deoxys", "Ghost Arceus", "Grass Arceus",
            "Steel Arceus", "Water Arceus", "Fairy Arceus", "Mega Diancie",
            "Sky Shaymin", "Dark Arceus", "Fire Arceus", "Rock Arceus",
            "Dada Zarude", "Bug Arceus", "Ice Arceus", "Volcanion",
            "Marshadow", "Pecharunt", "Meloetta", "Genesect", "Magearna",
            "Melmetal", "Jirachi", "Manaphy", "Darkrai", "Shaymin", "Victini",
            "Diancie", "Zeraora", "Celebi", "Deoxys", "Phione", "Arceus",
            "Keldeo", "Meltan", "Zarude", "Hoopa", "Mew"
        ]
    },
    "ub": {
        "name":
        "Ultra Beasts",
        "aliases": ["ultrabeasts", "ultrabeast"],
        "pokemon": [
            "Blacephalon", "Celesteela", "Pheromosa", "Xurkitree", "Naganadel",
            "Stakataka", "Nihilego", "Buzzwole", "Guzzlord", "Kartana",
            "Poipole"
        ]
    },
    "mega": {
        "name":
        "Mega Pokémon",
        "aliases": ["megas", "megaevolution", "megaevolutions"],
        "pokemon": [
            "Mega Charizard X", "Mega Charizard Y", "Mega Kangaskhan",
            "Mega Aerodactyl", "Mega Blastoise", "Mega Heracross",
            "Mega Tyranitar", "Mega Gardevoir", "Mega Venusaur",
            "Mega Alakazam", "Mega Gyarados", "Mega Mewtwo X", "Mega Mewtwo Y",
            "Mega Ampharos", "Mega Houndoom", "Mega Blaziken", "Mega Gengar",
            "Mega Pinsir", "Mega Scizor", "Mega Mawile", "Mega Manectric",
            "Mega Abomasnow", "Mega Sceptile", "Mega Swampert",
            "Mega Medicham", "Mega Sharpedo", "Mega Garchomp", "Mega Pidgeot",
            "Mega Slowbro", "Mega Steelix", "Mega Sableye", "Mega Altaria",
            "Mega Banette", "Mega Lucario", "Mega Gallade", "Mega Aggron",
            "Mega Latias", "Mega Latios", "Mega Audino", "Mega Absol",
            "Mega Salamence", "Mega Metagross", "Primal Groudon",
            "Mega Beedrill", "Mega Camerupt", "Primal Kyogre", "Mega Rayquaza",
            "Mega Lopunny", "Mega Diancie", "Mega Glalie"
        ]
    },
    "pseudo": {
        "name":
        "Pseudo-Legendary Pokémon",
        "aliases": ["pseudos", "pseudolegendary", "pseudolegendaries"],
        "pokemon": [
            "Baxcalibur", "Dragonite", "Tyranitar", "Salamence", "Metagross",
            "Hydreigon", "Dragapult", "Garchomp", "Kommo-o", "Goodra"
        ]
    },
    "startersonly": {
        "name":
        "First Stage Starter Pokémon",
        "aliases":
        ["firststagestarters", "starters-only", "firststageofstartersonly"],
        "pokemon": [
            "Charmander", "Sprigatito", "Bulbasaur", "Chikorita", "Cyndaquil",
            "Scorbunny", "Squirtle", "Totodile", "Chimchar", "Oshawott",
            "Fennekin", "Treecko", "Torchic", "Turtwig", "Chespin", "Froakie",
            "Popplio", "Grookey", "Fuecoco", "Mudkip", "Piplup", "Rowlet",
            "Litten", "Sobble", "Quaxly", "Snivy", "Tepig"
        ]
    },
    "regionals": {
        "name":
        "Regional Pokémon",
        "aliases": ["regional", "reg", "regionalpokemons"],
        "pokemon": [
            "Galarian Zen Darmanitan", "Galarian Farfetch'd",
            "Combat Breed Tauros", "Galarian Darmanitan", "Blaze Breed Tauros",
            "Hisuian Typhlosion", "Galarian Zigzagoon", "Hisuian Growlithe",
            "Galarian Rapidash", "Galarian Slowpoke", "Hisuian Electrode",
            "Galarian Mr. Mime", "Aqua Breed Tauros", "Galarian Articuno",
            "Galarian Slowking", "Hisuian Lilligant", "Galarian Darumaka",
            "Galarian Stunfisk", "Hisuian Decidueye", "Alolan Sandshrew",
            "Alolan Sandslash", "Alolan Ninetales", "Hisuian Arcanine",
            "Galarian Slowbro", "Alolan Exeggutor", "Galarian Weezing",
            "Galarian Moltres", "Hisuian Qwilfish", "Galarian Corsola",
            "Galarian Linoone", "Hisuian Samurott", "Hisuian Braviary",
            "Alolan Raticate", "Galarian Meowth", "Alolan Graveler",
            "Galarian Ponyta", "Hisuian Voltorb", "Galarian Zapdos",
            "Hisuian Sneasel", "Galarian Yamask", "Hisuian Zoroark",
            "Hisuian Sliggoo", "Hisuian Avalugg", "Alolan Rattata",
            "Alolan Diglett", "Alolan Dugtrio", "Alolan Persian",
            "Alolan Geodude", "Alolan Marowak", "Paldean Wooper",
            "Hisuian Goodra", "Alolan Raichu", "Alolan Vulpix",
            "Alolan Meowth", "Alolan Grimer", "Hisuian Zorua", "Alolan Golem",
            "Alolan Muk"
        ]
    },
    "paradox": {
        "name":
        "Paradox Pokémon",
        "aliases": ["para", "par", "parad"],
        "pokemon": [
            "Great Tusk", "Scream Tail", "Brute Bonnet", "Flutter Mane",
            "Slither Wing", "Sandy Shocks", "Iron Treads", "Iron Bundle",
            "Iron Hands", "Iron Jugulis", "Iron Moth", "Iron Thorns",
            "Roaring Moon", "Iron Valiant", "Koraidon", "Miraidon",
            "Walking Wake", "Iron Leaves", "Gouging Fire", "Raging Bolt",
            "Iron Boulder", "Iron Crown"
        ]
    },
    "alcremie": {
        "name":
        "Alcremie Pokémon",
        "aliases": ["charmilly", "pokusan", "mahoippu"],
        "pokemon": [
            "Vanilla Cream Clover Sweet Alcremie",
            "Vanilla Cream Flower Sweet Alcremie",
            "Vanilla Cream Ribbon Sweet Alcremie",
            "Vanilla Cream Berry Sweet Alcremie",
            "Vanilla Cream Love Sweet Alcremie",
            "Vanilla Cream Star Sweet Alcremie", "Gigantamax Alcremie",
            "Alcremie"
        ]
    },
    "unown": {
        "name":
        "Unown Pokémon",
        "aliases": ["zarbi", "annon", "unknown", "icognito"],
        "pokemon": [
            "Unown Exclamation", "Unown Question", "Unown A", "Unown B",
            "Unown C", "Unown D", "Unown E", "Unown G", "Unown H", "Unown I",
            "Unown J", "Unown K", "Unown L", "Unown M", "Unown N", "Unown O",
            "Unown P", "Unown Q", "Unown R", "Unown S", "Unown T", "Unown U",
            "Unown V", "Unown W", "Unown X", "Unown Y", "Unown Z", "Unown"
        ]
    },
    "vivillon": {
        "name":
        "Vivillon Pokémon",
        "aliases": ["bibiyon", "viviyon", "prismillon"],
        "pokemon": [
            "Continental Vivillon", "Archipelago Vivillon",
            "High Plain Vivillon", "Sandstorm Vivillon", "Poké Ball Vivillon",
            "Icy Snow Vivillon", "Elegant Vivillon", "Monsoon Vivillon",
            "Savanna Vivillon", "Tundra Vivillon", "Garden Vivillon",
            "Modern Vivillon", "Marine Vivillon", "Jungle Vivillon",
            "Polar Vivillon", "River Vivillon", "Ocean Vivillon",
            "Fancy Vivillon", "Sun Vivillon", "Vivillon"
        ]
    },
    "furfrou": {
        "name":
        "Furfrou Pokémon",
        "aliases": ["coiffwaff", "torimian", "trimmien", "couafarel"],
        "pokemon": [
            "Debutante Trim Furfrou", "La Reine Trim Furfrou",
            "Diamond Trim Furfrou", "Pharaoh Trim Furfrou",
            "Matron Trim Furfrou", "Kabuki Trim Furfrou", "Heart Trim Furfrou",
            "Dandy Trim Furfrou", "Star Trim Furfrou", "Furfrou"
        ]
    },
    "rotom": {
        "name":
        "Rotom Pokémon",
        "aliases": ["motisma", "rotomu"],
        "pokemon": [
            "Rotom Pokédex", "Frost Rotom", "Rotom Phone", "Rotom Drone",
            "Heat Rotom", "Wash Rotom", "Fan Rotom", "Mow Rotom", "Rotom"
        ]
    },
    "minior": {
        "name":
        "Minior Pokémon",
        "aliases": ["meteno"],
        "pokemon": [
            "Orange Meteor Minior", "Yellow Meteor Minior",
            "Indigo Meteor Minior", "Violet Meteor Minior",
            "Green Meteor Minior", "Blue Meteor Minior", "Orange Core Minior",
            "Yellow Core Minior", "Indigo Core Minior", "Violet Core Minior",
            "Red Meteor Minior", "Green Core Minior", "Blue Core Minior",
            "Red Core Minior", "Minior"
        ]
    },
    "arceus": {
        "name":
        "Arceus Pokémon",
        "aliases": ["aruseusu"],
        "pokemon": [
            "Electric Arceus", "Fighting Arceus", "Psychic Arceus",
            "Dragon Arceus", "Flying Arceus", "Ground Arceus", "Poison Arceus",
            "Ghost Arceus", "Grass Arceus", "Steel Arceus", "Water Arceus",
            "Fairy Arceus", "Dark Arceus", "Fire Arceus", "Rock Arceus",
            "Bug Arceus", "Ice Arceus", "Arceus"
        ]
    },
    "silvally": {
        "name":
        "Silvally Pokémon",
        "aliases":
        ["shiruvadi", "silvady", "amigento", "silvallie", "silvallié"],
        "pokemon": [
            "Electric Silvally", "Fighting Silvally", "Psychic Silvally",
            "Dragon Silvally", "Flying Silvally", "Ground Silvally",
            "Poison Silvally", "Ghost Silvally", "Grass Silvally",
            "Steel Silvally", "Water Silvally", "Fairy Silvally",
            "Dark Silvally", "Fire Silvally", "Rock Silvally", "Bug Silvally",
            "Ice Silvally", "Silvally"
        ]
    },
    "oricorio": {
        "name":
        "Oricorio Pokémon",
        "aliases": ["odoridori", "choreogel", "plumeline"],
        "pokemon":
        ["Pom-pom Oricorio", "Sensu Oricorio", "Pa'u Oricorio", "Oricorio"]
    },
    "evoflabebe": {
        "name":
        "Flabébé Pokémon With Evo",
        "aliases": ["flabébé", "furabebe", "flabebe"],
        "pokemon": [
            "Yellow Flower Flabébé", "Orange Flower Flabébé",
            "Yellow Flower Floette", "Orange Flower Floette",
            "Yellow Flower Florges", "Orange Flower Florges",
            "White Flower Flabébé", "White Flower Floette",
            "White Flower Florges", "Blue Flower Flabébé",
            "Blue Flower Floette", "Blue Flower Florges", "Flabébé", "Floette",
            "Florges"
        ]
    },
    "tatsugiri": {
        "name": "Tatsugiri Pokémon",
        "aliases": ["syaritatsu", "nigiragi", "nigirigon"],
        "pokemon": ["Stretchy Tatsugiri", "Droopy Tatsugiri", "Tatsugiri"]
    },
    "squawkabilly": {
        "name":
        "Squawkabilly Pokémon",
        "aliases": ["ikirinko", "tapatoes", "krawalloro"],
        "pokemon": [
            "Yellow Plumage Squawkabilly", "White Plumage Squawkabilly",
            "Blue Plumage Squawkabilly", "Squawkabilly"
        ]
    },
    "1/225": {
        "name":
        "Spawnrate 1/225 Pokémon",
        "aliases": ["1in225", "225"],
        "pokemon": [
            "Caterpie", "Weedle", "Pidgey", "Nidoran♀️", "Nidoran♂️", "Zubat",
            "Oddish", "Poliwag", "Abra", "Machop", "Bellsprout", "Geodude",
            "Magnemite", "Gastly", "Rhyhorn", "Horsea", "Porygon", "Togepi",
            "Mareep", "Hoppip", "Teddiursa", "Swinub", "Wurmple", "Lotad",
            "Seedot", "Ralts", "Slakoth", "Whismur", "Aron", "Trapinch",
            "Duskull", "Spheal", "Starly", "Shinx", "Lillipup", "Pidove",
            "Roggenrola", "Timburr", "Tympole", "Sewaddle", "Venipede",
            "Sandile", "Gothita", "Solosis", "Vanillite", "Klink", "Tynamo",
            "Litwick", "Axew", "Fletchling", "Scatterbug", "Honedge",
            "Pikipek", "Grubbin", "Bounsweet", "Rookidee", "Blipbug",
            "Rolycoly", "Hatenna", "Impidimp", "Dreepy", "Lechonk",
            "Tarountula", "Nymble", "Pawmi", "Tandemaus", "Fidough", "Smoliv",
            "Nacli", "Charcadet", "Tadbulb", "Wattrel", "Maschiff", "Shroodle",
            "Bramblin", "Toedscool", "Klawf", "Capsakid", "Rellor", "Flittle",
            "Tinkatink", "Wiglett", "Bombirdier", "Finizen", "Varoom",
            "Orthworm", "Glimmet", "Greavard", "Flamigo", "Cetoddle", "Veluza",
            "Dondozo", "Frigibax", "Gimmighoul"
        ]
    },
    "1/337": {
        "name":
        "Spawnrate 1/337 Pokémon",
        "aliases": ["1in337", "337"],
        "pokemon": [
            "Rattata", "Dratini", "Larvitar", "Bagon", "Beldum", "Gible",
            "Deino", "Goomy", "Jangmo-o", "Roaming Gimmighoul"
        ]
    },
    "1/674": {
        "name":
        "Spawnrate 1/674 Pokémon",
        "aliases": ["1in674", "674"],
        "pokemon": [
            "Bulbasaur", "Charmander", "Squirtle", "Chikorita", "Cyndaquil",
            "Totodile", "Treecko", "Torchic", "Mudkip", "Turtwig", "Chimchar",
            "Piplup", "Snivy", "Tepig", "Oshawott", "Chespin", "Fennekin",
            "Froakie", "Rowlet", "Litten", "Popplio", "Grookey", "Scorbunny",
            "Sobble", "Sprigatito", "Fuecoco", "Quaxly", "Cyclizar",
            "Tatsugiri", "Droopy Tatsugiri", "Stretchy Tatsugiri",
            "Battle Cyclizar", "Ride Cyclizar"
        ]
    },
    "1/899": {
        "name":
        "Spawnrate 1/899 Pokémon",
        "aliases": ["1in899", "899"],
        "pokemon": [
            "Metapod", "Kakuna", "Pidgeotto", "Spearow", "Ekans", "Pikachu",
            "Sandshrew", "Nidorina", "Nidorino", "Clefairy", "Vulpix",
            "Jigglypuff", "Golbat", "Gloom", "Paras", "Venonat", "Diglett",
            "Meowth", "Psyduck", "Mankey", "Growlithe", "Poliwhirl", "Kadabra",
            "Machoke", "Weepinbell", "Tentacool", "Graveler", "Ponyta",
            "Slowpoke", "Magneton", "Doduo", "Seel", "Grimer", "Shellder",
            "Haunter", "Onix", "Drowzee", "Krabby", "Voltorb", "Exeggcute",
            "Cubone", "Lickitung", "Koffing", "Rhydon", "Chansey", "Tangela",
            "Seadra", "Goldeen", "Staryu", "Scyther", "Electabuzz", "Magmar",
            "Magikarp", "Eevee", "Omanyte", "Kabuto", "Bayleef", "Quilava",
            "Croconaw", "Sentret", "Hoothoot", "Ledyba", "Spinarak",
            "Chinchou", "Togetic", "Natu", "Flaaffy", "Marill", "Skiploom",
            "Aipom", "Sunkern", "Yanma", "Wooper", "Murkrow", "Misdreavus",
            "Pineco", "Gligar", "Snubbull", "Sneasel", "Ursaring", "Slugma",
            "Piloswine", "Remoraid", "Houndour", "Phanpy", "Porygon2",
            "Stantler", "Tyrogue", "Grovyle", "Combusken", "Marshtomp",
            "Poochyena", "Zigzagoon", "Silcoon", "Cascoon", "Lombre",
            "Nuzleaf", "Taillow", "Wingull", "Kirlia", "Surskit", "Shroomish",
            "Vigoroth", "Nincada", "Loudred", "Makuhita", "Nosepass", "Skitty",
            "Lairon", "Meditite", "Electrike", "Roselia", "Gulpin", "Carvanha",
            "Wailmer", "Numel", "Spoink", "Vibrava", "Cacnea", "Swablu",
            "Barboach", "Corphish", "Baltoy", "Lileep", "Anorith", "Feebas",
            "Shuppet", "Dusclops", "Snorunt", "Sealeo", "Clamperl", "Grotle",
            "Monferno", "Prinplup", "Staravia", "Bidoof", "Kricketot", "Luxio",
            "Cranidos", "Shieldon", "Combee", "Buizel", "Cherubi", "Shellos",
            "Drifloon", "Buneary", "Glameow", "Stunky", "Bronzor", "Riolu",
            "Hippopotas", "Skorupi", "Croagunk", "Finneon", "Snover",
            "Servine", "Pignite", "Dewott", "Patrat", "Herdier", "Purrloin",
            "Pansage", "Pansear", "Panpour", "Munna", "Tranquill", "Blitzle",
            "Boldore", "Woobat", "Drilbur", "Gurdurr", "Palpitoad", "Swadloon",
            "Whirlipede", "Cottonee", "Petilil", "Krokorok", "Darumaka",
            "Dwebble", "Scraggy", "Yamask", "Tirtouga", "Archen", "Trubbish",
            "Zorua", "Minccino", "Gothorita", "Duosion", "Ducklett",
            "Vanillish", "Deerling", "Karrablast", "Foongus", "Frillish",
            "Joltik", "Ferroseed", "Klang", "Eelektrik", "Elgyem", "Lampent",
            "Fraxure", "Cubchoo", "Shelmet", "Mienfoo", "Golett", "Pawniard",
            "Rufflet", "Vullaby", "Larvesta", "Quilladin", "Braixen",
            "Frogadier", "Bunnelby", "Fletchinder", "Spewpa", "Litleo",
            "Skiddo", "Pancham", "Espurr", "Doublade", "Spritzee", "Swirlix",
            "Inkay", "Binacle", "Skrelp", "Clauncher", "Helioptile", "Tyrunt",
            "Amaura", "Phantump", "Pumpkaboo", "Bergmite", "Noibat", "Dartrix",
            "Torracat", "Brionne", "Trumbeak", "Yungoos", "Charjabug",
            "Crabrawler", "Cutiefly", "Rockruff", "Mareanie", "Mudbray",
            "Dewpider", "Fomantis", "Morelull", "Salandit", "Stufful",
            "Steenee", "Wimpod", "Sandygast", "Thwackey", "Raboot", "Drizzile",
            "Skwovet", "Corvisquire", "Dottler", "Nickit", "Gossifleur",
            "Wooloo", "Chewtle", "Yamper", "Carkol", "Applin", "Silicobra",
            "Arrokuda", "Toxel", "Sizzlipede", "Clobbopus", "Sinistea",
            "Hattrem", "Morgrem", "Milcery", "Snom", "Cufant", "Drakloak",
            "Oinkologne", "Spidops", "Lokix", "Pawmo", "Maushold", "Dachsbun",
            "Dolliv", "Squawkabilly", "Naclstack", "Armarouge", "Ceruledge",
            "Bellibolt", "Kilowattrel", "Mabosstiff", "Grafaiai",
            "Brambleghast", "Toedscruel", "Scovillain", "Rabsca", "Espathra",
            "Tinkatuff", "Wugtrio", "Palafin", "Revavroom", "Glimmora",
            "Houndstone", "Cetitan", "Clodsire", "Farigiraf", "Dudunsparce",
            "Arctibax", "Gholdengo", "Blue Plumage Squawkabilly",
            "Yellow Plumage Squawkabilly", "White Plumage Squawkabilly",
            "East Sea Shellos", "Summer Deerling", "Autumn Deerling",
            "Winter Deerling"
        ]
    },
    "1/1121": {
        "name":
        "Spawnrate 1/1121 Pokémon",
        "aliases": ["1in1121", "1121"],
        "pokemon": [
            "Flabébé", "Yellow Flower Flabébé", "Orange Flower Flabébé",
            "Blue Flower Flabébé", "White Flower Flabébé"
        ]
    },
    "1/1199": {
        "name": "Spawnrate 1/1199 Pokémon",
        "aliases": ["1in1199", "1199"],
        "pokemon": ["Lycanroc", "Midnight Lycanroc", "Dusk Lycanroc"]
    },
    "1/1349": {
        "name":
        "Spawnrate 1/1349 Pokémon",
        "aliases": ["1in1349", "1349"],
        "pokemon": [
            "Ivysaur", "Charmeleon", "Wartortle", "Raticate", "Dragonair",
            "Pupitar", "Shelgon", "Metang", "Gabite", "Zweilous", "Sliggoo",
            "Hakamo-o", "Floragato", "Crocalor", "Quaxwell"
        ]
    },
    "1/2697": {
        "name": "Spawnrate 1/2697 Pokémon",
        "aliases": ["1in2697", "2697"],
        "pokemon": ["Burmy", "Sandy Burmy", "Trash Burmy"]
    },
    "1/3596": {
        "name":
        "Spawnrate 1/3596 Pokémon",
        "aliases": ["1in3596", "3596"],
        "pokemon": [
            "Venusaur", "Charizard", "Blastoise", "Butterfree", "Beedrill",
            "Pidgeot", "Fearow", "Arbok", "Raichu", "Sandslash", "Nidoqueen",
            "Nidoking", "Clefable", "Ninetales", "Wigglytuff", "Vileplume",
            "Parasect", "Venomoth", "Dugtrio", "Persian", "Golduck",
            "Primeape", "Arcanine", "Poliwrath", "Alakazam", "Machamp",
            "Victreebel", "Tentacruel", "Golem", "Rapidash", "Slowbro",
            "Farfetch'd", "Dodrio", "Dewgong", "Muk", "Cloyster", "Gengar",
            "Hypno", "Kingler", "Electrode", "Exeggutor", "Marowak",
            "Hitmonlee", "Hitmonchan", "Weezing", "Kangaskhan", "Seaking",
            "Starmie", "Mr. Mime", "Jynx", "Pinsir", "Tauros", "Gyarados",
            "Lapras", "Ditto", "Vaporeon", "Jolteon", "Flareon", "Omastar",
            "Kabutops", "Aerodactyl", "Snorlax", "Meganium", "Typhlosion",
            "Feraligatr", "Furret", "Noctowl", "Ledian", "Ariados", "Crobat",
            "Lanturn", "Cleffa", "Igglybuff", "Xatu", "Ampharos", "Bellossom",
            "Azumarill", "Sudowoodo", "Politoed", "Jumpluff", "Sunflora",
            "Quagsire", "Espeon", "Umbreon", "Slowking", "Wobbuffet",
            "Girafarig", "Forretress", "Dunsparce", "Steelix", "Granbull",
            "Qwilfish", "Scizor", "Shuckle", "Heracross", "Magcargo",
            "Corsola", "Octillery", "Delibird", "Mantine", "Skarmory",
            "Houndoom", "Kingdra", "Donphan", "Smeargle", "Hitmontop",
            "Smoochum", "Elekid", "Magby", "Miltank", "Blissey", "Sceptile",
            "Blaziken", "Swampert", "Mightyena", "Linoone", "Beautifly",
            "Dustox", "Ludicolo", "Shiftry", "Swellow", "Pelipper",
            "Gardevoir", "Masquerain", "Breloom", "Slaking", "Ninjask",
            "Shedinja", "Exploud", "Hariyama", "Azurill", "Delcatty",
            "Sableye", "Mawile", "Aggron", "Medicham", "Manectric", "Plusle",
            "Minun", "Volbeat", "Illumise", "Swalot", "Sharpedo", "Wailord",
            "Camerupt", "Torkoal", "Grumpig", "Spinda", "Flygon", "Cacturne",
            "Altaria", "Zangoose", "Seviper", "Lunatone", "Solrock",
            "Whiscash", "Crawdaunt", "Claydol", "Cradily", "Armaldo",
            "Milotic", "Castform", "Kecleon", "Banette", "Tropius", "Chimecho",
            "Absol", "Wynaut", "Glalie", "Walrein", "Huntail", "Gorebyss",
            "Relicanth", "Luvdisc", "Torterra", "Infernape", "Empoleon",
            "Staraptor", "Bibarel", "Kricketune", "Luxray", "Budew",
            "Roserade", "Rampardos", "Bastiodon", "Wormadam", "Mothim",
            "Vespiquen", "Pachirisu", "Floatzel", "Cherrim", "Gastrodon",
            "Ambipom", "Drifblim", "Lopunny", "Mismagius", "Honchkrow",
            "Purugly", "Chingling", "Skuntank", "Bronzong", "Bonsly",
            "Mime Jr.", "Happiny", "Chatot", "Spiritomb", "Munchlax",
            "Lucario", "Hippowdon", "Drapion", "Toxicroak", "Carnivine",
            "Lumineon", "Mantyke", "Abomasnow", "Weavile", "Magnezone",
            "Lickilicky", "Rhyperior", "Tangrowth", "Electivire", "Magmortar",
            "Togekiss", "Yanmega", "Leafeon", "Glaceon", "Gliscor",
            "Mamoswine", "Porygon-Z", "Gallade", "Probopass", "Dusknoir",
            "Froslass", "Serperior", "Emboar", "Samurott", "Watchog",
            "Stoutland", "Liepard", "Simisage", "Simisear", "Simipour",
            "Musharna", "Unfezant", "Zebstrika", "Gigalith", "Swoobat",
            "Excadrill", "Audino", "Conkeldurr", "Seismitoad", "Throh", "Sawk",
            "Leavanny", "Scolipede", "Whimsicott", "Lilligant", "Basculin",
            "Krookodile", "Darmanitan", "Maractus", "Crustle", "Scrafty",
            "Sigilyph", "Cofagrigus", "Carracosta", "Archeops", "Garbodor",
            "Zoroark", "Cinccino", "Gothitelle", "Reuniclus", "Swanna",
            "Vanilluxe", "Sawsbuck", "Emolga", "Escavalier", "Amoonguss",
            "Jellicent", "Alomomola", "Galvantula", "Ferrothorn", "Klinklang",
            "Eelektross", "Beheeyem", "Chandelure", "Haxorus", "Beartic",
            "Cryogonal", "Accelgor", "Stunfisk", "Mienshao", "Druddigon",
            "Golurk", "Bisharp", "Bouffalant", "Braviary", "Mandibuzz",
            "Heatmor", "Durant", "Volcarona", "Chesnaught", "Delphox",
            "Greninja", "Diggersby", "Talonflame", "Pyroar", "Gogoat",
            "Pangoro", "Furfrou", "Meowstic", "Aegislash", "Aromatisse",
            "Slurpuff", "Malamar", "Barbaracle", "Dragalge", "Clawitzer",
            "Heliolisk", "Tyrantrum", "Aurorus", "Sylveon", "Hawlucha",
            "Dedenne", "Carbink", "Klefki", "Trevenant", "Gourgeist",
            "Avalugg", "Noivern", "Decidueye", "Incineroar", "Primarina",
            "Toucannon", "Gumshoos", "Vikavolt", "Crabominable", "Oricorio",
            "Ribombee", "Wishiwashi", "Toxapex", "Mudsdale", "Araquanid",
            "Lurantis", "Shiinotic", "Salazzle", "Bewear", "Tsareena",
            "Comfey", "Oranguru", "Passimian", "Golisopod", "Palossand",
            "Pyukumuku", "Minior", "Komala", "Turtonator", "Togedemaru",
            "Mimikyu", "Bruxish", "Drampa", "Dhelmise", "Rillaboom",
            "Cinderace", "Inteleon", "Greedent", "Corviknight", "Orbeetle",
            "Thievul", "Eldegoss", "Dubwool", "Drednaw", "Boltund",
            "Coalossal", "Flapple", "Appletun", "Sandaconda", "Cramorant",
            "Barraskewda", "Amped Toxtricity", "Centiskorch", "Grapploct",
            "Polteageist", "Hatterene", "Grimmsnarl", "Falinks", "Pincurchin",
            "Frosmoth", "Stonjourner", "Eiscue", "Indeedee", "Morpeko",
            "Copperajah", "Dracozolt", "Arctozolt", "Dracovish", "Arctovish",
            "Duraludon", "Dragapult", "Wyrdeer", "Kleavor", "Ursaluna",
            "Meowscarada", "Skeledirge", "Quaquaval", "Pawmot", "Arboliva",
            "Garganacl", "Tinkaton", "Annihilape", "Kingambit", "Baxcalibur",
            "Dipplin", "Poltchageist", "Sandy Wormadam", "Trash Wormadam",
            "Sunny Castform", "Rainy Castform", "Snowy Castform",
            "Blue-Striped Basculin", "Pom-pom Oricorio", "Pa'u Oricorio",
            "Sensu Oricorio", "Low Key Toxtricity", "White-Striped Basculin",
            "Three-Segment Dudunsparce", "Hero Palafin",
            "Family of Three Maushold", "Sunshine Cherrim",
            "East Sea Gastrodon", "Summer Sawsbuck", "Autumn Sawsbuck",
            "Winter Sawsbuck"
        ]
    },
    "1/4483": {
        "name":
        "Spawnrate 1/4483 Pokémon",
        "aliases": ["1in4483", "4483"],
        "pokemon": [
            "Floette", "Yellow Flower Floette", "Orange Flower Floette",
            "Blue Flower Floette", "White Flower Floette"
        ]
    },
    "1/5394": {
        "name":
        "Spawnrate 1/5394 Pokémon",
        "aliases": ["1in5394", "5394"],
        "pokemon": [
            "Dragonite", "Tyranitar", "Salamence", "Metagross", "Garchomp",
            "Hydreigon", "Goodra", "Kommo-o", "School Wishiwashi"
        ]
    },
    "1/7192": {
        "name": "Spawnrate 1/7192 Pokémon",
        "aliases": ["1in7192", "7192"],
        "pokemon": ["Pichu", "Spiky-eared Pichu"]
    },
    "1/14384": {
        "name":
        "Spawnrate 1/14384 Pokémon",
        "aliases": ["1in14384", "14384"],
        "pokemon": [
            "Basculegion", "Sneasler", "Sinistcha", "Okidogi", "Munkidori",
            "Fezandipiti", "Archaludon", "Hydrapple", "Zen Darmanitan",
            "Pirouette Meloetta", "Blade Aegislash", "Alolan Rattata",
            "Alolan Raichu", "Alolan Sandshrew", "Alolan Vulpix",
            "Alolan Diglett", "Alolan Meowth", "Alolan Geodude",
            "Alolan Grimer", "Galarian Meowth", "Galarian Ponyta",
            "Galarian Slowpoke", "Galarian Farfetch'd", "Galarian Corsola",
            "Galarian Linoone", "Galarian Darmanitan",
            "Galarian Zen Darmanitan", "Galarian Yamask", "Noice Face Eiscue",
            "Hisuian Growlithe", "Hisuian Voltorb", "Hisuian Sneasel",
            "Hisuian Zorua", "Hisuian Sliggoo", "Hangry Morpeko",
            "Paldean Wooper"
        ]
    },
    "1/17261": {
        "name":
        "Spawnrate 1/17261 Pokémon",
        "aliases": ["1in17261", "17261"],
        "pokemon": [
            "Florges", "Yellow Flower Florges", "Orange Flower Florges",
            "Blue Flower Florges", "White Flower Florges", "Polar Vivillon",
            "Elegant Vivillon", "Marine Vivillon", "Archipelago Vivillon",
            "Monsoon Vivillon"
        ]
    },
    "1/21576": {
        "name":
        "Spawnrate 1/21576 Pokémon",
        "aliases": ["1in21576", "21576"],
        "pokemon": [
            "Rotom", "Heat Rotom", "Wash Rotom", "Frost Rotom", "Fan Rotom",
            "Mow Rotom"
        ]
    },
    "1/24658": {
        "name":
        "Spawnrate 1/24658 Pokémon",
        "aliases": ["1in24658", "24658"],
        "pokemon": [
            "Alcremie", "Vanilla Cream Berry Sweet Alcremie",
            "Vanilla Cream Love Sweet Alcremie",
            "Vanilla Cream Star Sweet Alcremie",
            "Vanilla Cream Clover Sweet Alcremie",
            "Vanilla Cream Flower Sweet Alcremie",
            "Vanilla Cream Ribbon Sweet Alcremie"
        ]
    },
    "1/28768": {
        "name":
        "Spawnrate 1/28768 Pokémon",
        "aliases": ["1in28768", "28768"],
        "pokemon": [
            "Mew", "Celebi", "Jirachi", "Deoxys", "Phione", "Manaphy",
            "Darkrai", "Shaymin", "Victini", "Keldeo", "Meloetta", "Diancie",
            "Hoopa", "Volcanion", "Magearna", "Marshadow", "Zeraora", "Meltan",
            "Melmetal", "Obstagoon", "Perrserker", "Cursola", "Sirfetch'd",
            "Runerigus", "Zarude", "Overqwil", "Pecharunt", "Attack Deoxys",
            "Defense Deoxys", "Speed Deoxys", "Alolan Raticate",
            "Alolan Sandslash", "Alolan Ninetales", "Alolan Dugtrio",
            "Alolan Persian", "Alolan Graveler", "Alolan Muk",
            "Alolan Exeggutor", "Alolan Marowak", "Galarian Rapidash",
            "Galarian Slowbro", "Galarian Weezing", "Galarian Mr. Mime",
            "Galarian Zigzagoon", "Galarian Darumaka", "Galarian Stunfisk",
            "Hisuian Arcanine", "Hisuian Electrode", "Hisuian Typhlosion",
            "Hisuian Qwilfish", "Hisuian Samurott", "Hisuian Lilligant",
            "Hisuian Zoroark", "Hisuian Braviary", "Hisuian Goodra",
            "Hisuian Avalugg", "Hisuian Decidueye", "Combat Breed Tauros",
            "Blaze Breed Tauros", "Aqua Breed Tauros"
        ]
    },
    "1/31383": {
        "name":
        "Spawnrate 1/31383 Pokémon",
        "aliases": ["1in31383", "31383"],
        "pokemon": [
            "Ruby Cream Strawberry Sweet Alcremie",
            "Matcha Cream Strawberry Sweet Alcremie",
            "Mint Cream Strawberry Sweet Alcremie",
            "Lemon Cream Strawberry Sweet Alcremie",
            "Salted Cream Strawberry Sweet Alcremie",
            "Ruby Swirl Strawberry Sweet Alcremie",
            "Caramel Swirl Strawberry Sweet Alcremie",
            "Rainbow Swirl Strawberry Sweet Alcremie",
            "Ruby Cream Berry Sweet Alcremie",
            "Matcha Cream Berry Sweet Alcremie",
            "Mint Cream Berry Sweet Alcremie",
            "Lemon Cream Berry Sweet Alcremie",
            "Salted Cream Berry Sweet Alcremie",
            "Ruby Swirl Berry Sweet Alcremie",
            "Caramel Swirl Berry Sweet Alcremie",
            "Rainbow Swirl Berry Sweet Alcremie",
            "Ruby Cream Love Sweet Alcremie",
            "Matcha Cream Love Sweet Alcremie",
            "Mint Cream Love Sweet Alcremie",
            "Lemon Cream Love Sweet Alcremie",
            "Salted Cream Love Sweet Alcremie",
            "Ruby Swirl Love Sweet Alcremie",
            "Caramel Swirl Love Sweet Alcremie",
            "Rainbow Swirl Love Sweet Alcremie",
            "Ruby Cream Star Sweet Alcremie",
            "Matcha Cream Star Sweet Alcremie",
            "Mint Cream Star Sweet Alcremie",
            "Lemon Cream Star Sweet Alcremie",
            "Salted Cream Star Sweet Alcremie",
            "Ruby Swirl Star Sweet Alcremie",
            "Caramel Swirl Star Sweet Alcremie",
            "Rainbow Swirl Star Sweet Alcremie",
            "Ruby Cream Clover Sweet Alcremie",
            "Matcha Cream Clover Sweet Alcremie",
            "Mint Cream Clover Sweet Alcremie",
            "Lemon Cream Clover Sweet Alcremie",
            "Salted Cream Clover Sweet Alcremie",
            "Ruby Swirl Clover Sweet Alcremie",
            "Caramel Swirl Clover Sweet Alcremie",
            "Rainbow Swirl Clover Sweet Alcremie",
            "Ruby Cream Flower Sweet Alcremie",
            "Matcha Cream Flower Sweet Alcremie",
            "Mint Cream Flower Sweet Alcremie",
            "Lemon Cream Flower Sweet Alcremie",
            "Salted Cream Flower Sweet Alcremie",
            "Ruby Swirl Flower Sweet Alcremie",
            "Caramel Swirl Flower Sweet Alcremie",
            "Rainbow Swirl Flower Sweet Alcremie",
            "Ruby Cream Ribbon Sweet Alcremie",
            "Matcha Cream Ribbon Sweet Alcremie",
            "Mint Cream Ribbon Sweet Alcremie",
            "Lemon Cream Ribbon Sweet Alcremie",
            "Salted Cream Ribbon Sweet Alcremie",
            "Ruby Swirl Ribbon Sweet Alcremie",
            "Caramel Swirl Ribbon Sweet Alcremie",
            "Rainbow Swirl Ribbon Sweet Alcremie"
        ]
    },
    "1/34522": {
        "name":
        "Spawnrate 1/34522 Pokémon",
        "aliases": ["1in34522", "34522"],
        "pokemon": [
            "Gulping Cramorant", "Gorging Cramorant", "Dada Zarude",
            "Heart Trim Furfrou", "Star Trim Furfrou", "Diamond Trim Furfrou",
            "Debutante Trim Furfrou", "Matron Trim Furfrou",
            "Dandy Trim Furfrou", "La Reine Trim Furfrou",
            "Kabuki Trim Furfrou", "Pharaoh Trim Furfrou", "Zygarde Cell",
            "Zygarde Core", "Zenith Marshadow"
        ]
    },
    "1/43152": {
        "name":
        "Spawnrate 1/43152 Pokémon",
        "aliases": ["1in43152", "43152"],
        "pokemon": [
            "Vivillon", "Great Tusk", "Scream Tail", "Brute Bonnet",
            "Flutter Mane", "Slither Wing", "Sandy Shocks", "Iron Treads",
            "Iron Bundle", "Iron Hands", "Iron Jugulis", "Iron Moth",
            "Iron Thorns", "Roaring Moon", "Iron Valiant", "Walking Wake",
            "Iron Leaves", "Gouging Fire", "Raging Bolt", "Iron Boulder",
            "Iron Crown", "Icy Snow Vivillon", "Tundra Vivillon",
            "Continental Vivillon", "Garden Vivillon", "Modern Vivillon",
            "High Plain Vivillon", "Sandstorm Vivillon", "River Vivillon",
            "Savanna Vivillon", "Sun Vivillon", "Ocean Vivillon",
            "Jungle Vivillon", "Rotom Pokédex", "Rotom Phone", "Rotom Drone"
        ]
    },
    "1/57536": {
        "name":
        "Spawnrate 1/57536 Pokémon",
        "aliases": ["1in57536", "57536"],
        "pokemon": [
            "Articuno", "Zapdos", "Moltres", "Mewtwo", "Raikou", "Entei",
            "Suicune", "Lugia", "Ho-Oh", "Regirock", "Regice", "Registeel",
            "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza", "Uxie",
            "Mesprit", "Azelf", "Dialga", "Palkia", "Heatran", "Regigigas",
            "Giratina", "Cresselia", "Cobalion", "Terrakion", "Virizion",
            "Tornadus", "Thundurus", "Reshiram", "Zekrom", "Landorus",
            "Kyurem", "Genesect", "Yveltal", "Zygarde", "Type: Null",
            "Tapu Koko", "Tapu Lele", "Tapu Bulu", "Tapu Fini", "Cosmog",
            "Cosmoem", "Solgaleo", "Lunala", "Necrozma", "Mr. Rime", "Zacian",
            "Zamazenta", "Eternatus", "Kubfu", "Urshifu", "Regieleki",
            "Regidrago", "Glastrier", "Spectrier", "Calyrex", "Enamorus",
            "Wo-Chien", "Chien-Pao", "Ting-Lu", "Chi-Yu", "Ogerpon",
            "Terapagos", "Alolan Golem", "10% Zygarde", "Complete Zygarde",
            "Galarian Slowking", "Rapid Strike Urshifu", "Bloodmoon Ursaluna",
            "Wellspring Mask Ogerpon", "Hearthflame Mask Ogerpon",
            "Cornerstone Mask Ogerpon", "Terastal Terapagos",
            "High-speed Flight Configuration Genesect"
        ]
    },
    "1/69043": {
        "name": "Spawnrate 1/69043 Pokémon",
        "aliases": ["1in69043", "69043"],
        "pokemon": ["Partner Pikachu", "Partner Eevee"]
    },
    "1/86304": {
        "name":
        "Spawnrate 1/86304 Pokémon",
        "aliases": ["1in86304", "86304"],
        "pokemon": [
            "Unown", "Unown A", "Unown B", "Unown C", "Unown D", "Unown E",
            "Unown G", "Unown H", "Unown I", "Unown J", "Unown K", "Unown L",
            "Unown M", "Unown N", "Unown O", "Unown P", "Unown Q", "Unown R",
            "Unown S", "Unown T", "Unown U", "Unown V", "Unown W", "Unown X",
            "Unown Y", "Unown Z", "Unown Exclamation", "Unown Question"
        ]
    },
    "1/115072": {
        "name":
        "Spawnrate 1/115072 Pokémon",
        "aliases": ["1in115072", "115072"],
        "pokemon": [
            "Xerneas", "Nihilego", "Buzzwole", "Pheromosa", "Xurkitree",
            "Celesteela", "Kartana", "Guzzlord", "Poipole", "Naganadel",
            "Stakataka", "Blacephalon", "Fancy Vivillon", "Poké Ball Vivillon",
            "Neutral Xerneas"
        ]
    },
    "1/172608": {
        "name":
        "Spawnrate 1/172608 Pokémon",
        "aliases": ["1in172608", "172608"],
        "pokemon": [
            "Koraidon", "Miraidon", "Galarian Articuno", "Galarian Zapdos",
            "Galarian Moltres", "Sprinting Build Koraidon",
            "Gliding Build Koraidon", "Drive Mode Miraidon",
            "Glide Mode Miraidon"
        ]
    },
    "1/345217": {
        "name":
        "Spawnrate 1/345217 Pokémon",
        "aliases": ["1in345217", "345217"],
        "pokemon": [
            "MissingNo.", "Arceus", "Silvally", "Bug Arceus", "Dark Arceus",
            "Dragon Arceus", "Electric Arceus", "Fighting Arceus",
            "Fire Arceus", "Flying Arceus", "Ghost Arceus", "Grass Arceus",
            "Ground Arceus", "Ice Arceus", "Poison Arceus", "Psychic Arceus",
            "Rock Arceus", "Steel Arceus", "Water Arceus", "Fairy Arceus",
            "Bug Silvally", "Dark Silvally", "Dragon Silvally",
            "Electric Silvally", "Fighting Silvally", "Fire Silvally",
            "Flying Silvally", "Ghost Silvally", "Grass Silvally",
            "Ground Silvally", "Ice Silvally", "Poison Silvally",
            "Psychic Silvally", "Rock Silvally", "Steel Silvally",
            "Water Silvally", "Fairy Silvally"
        ]
    }
}

# Build alias mapping
ALIAS_MAP = {}
for key, data in FILTERS.items():
    # Main key is accessible
    ALIAS_MAP[key] = key
    # Add all aliases
    if "aliases" in data:
        for alias in data["aliases"]:
            ALIAS_MAP[alias.lower()] = key


def get_filter(filter_name):
    """Get filter by name or alias (case-insensitive)"""
    filter_key = ALIAS_MAP.get(filter_name.lower())
    if filter_key:
        return FILTERS.get(filter_key)
    return None


def get_all_filter_names():
    """Get list of all available filter names (main keys only)"""
    return list(FILTERS.keys())
