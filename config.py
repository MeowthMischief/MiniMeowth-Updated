import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
PREFIX = ["m!", "M!", "n!", "N!"] 
EMBED_COLOR = 0x9c8e8b  # RGB: 156, 142, 139

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://your_connection_string")
DATABASE_NAME = "poketwo_daycare"

# Collections
COLLECTION_POKEMON = "pokemon"
COLLECTION_COOLDOWNS = "cooldowns"
COLLECTION_SETTINGS = "settings"

# Category Constants
NORMAL_CATEGORY = "normal"
TRIPMAX_CATEGORY = "tripmax"
TRIPZERO_CATEGORY = "tripzero"


# Cooldown Duration
COOLDOWN_DAYS = 5
COOLDOWN_HOURS = 0.5

# ID Categories (for old/new system)
OLD_ID_MAX = 271800
NEW_ID_MIN = 271900

# Pairing Constants
MAX_BREED_PAIRS = 2  # Maximum pairs per breed command

# Inventory Categories
NORMAL_CATEGORY = "normal"
TRIPMAX_CATEGORY = "tripmax"
TRIPZERO_CATEGORY = "tripzero"

# Gender display 
GENDER_MALE = "<:male_sign:1449750028536250420>"
GENDER_FEMALE = "<:female_sign:1449750041035145407>"
GENDER_UNKNOWN = "<:grey_question:1449750016481562787>"

# Tick/Cross display
TICK = "<:white_check_mark:1449749985057964094>"
CROSS = "<:cross_mark:1449750002388959377>"



# Poketwo id
POKETWO_BOT_ID = 716390085896962058
# Add this to config.py

# Pokemon with visible gender differences that should be tracked separately in full dex
GENDER_DIFFERENCE_POKEMON = {
    "Hisuian Sneasel","Basculegion","Butterfree","Kricketune","Hippopotas","Oinkologne","Vileplume","Sudowoodo","Wobbuffet","Girafarig","Heracross","Piloswine","Octillery","Combusken","Beautifly","Relicanth","Staraptor","Kricketot","Pachirisu","Hippowdon","Toxicroak","Abomasnow","Rhyperior","Tangrowth","Mamoswine","Jellicent","Venusaur","Raticate","Alakazam","Magikarp","Gyarados","Meganium","Politoed","Quagsire","Ursaring","Houndoom","Blaziken","Ludicolo","Meditite","Medicham","Camerupt","Cacturne","Staravia","Roserade","Floatzel","Garchomp","Croagunk","Lumineon","Unfezant","Frillish","Meowstic","Indeedee","Rattata","Pikachu","Kadabra","Rhyhorn","Goldeen","Seaking","Scyther","Murkrow","Steelix","Sneasel","Donphan","Torchic","Nuzleaf","Shiftry","Roselia","Milotic","Bibarel","Ambipom","Finneon","Weavile","Raichu","Golbat","Dodrio","Rhydon","Ledyba","Ledian","Wooper","Gligar","Scizor","Dustox","Gulpin","Swalot","Starly","Bidoof","Luxray","Combee","Buizel","Gabite","Snover","Pyroar","Zubat","Gloom","Doduo","Hypno","Eevee","Aipom","Numel","Shinx","Luxio","Gible","Xatu"
}

RARE_POKEMONS = {"Registeel","Articuno","Regirock","Rayquaza","Moltres","Suicune","Groudon","Jirachi","Zapdos","Mewtwo","Raikou","Celebi","Regice","Latias","Latios","Kyogre","Entei","Lugia","Ho-Oh","Mew","Regigigas","Cresselia","Terrakion","Giratina","Cobalion","Virizion","Tornadus","Mesprit","Heatran","Manaphy","Darkrai","Shaymin","Victini","Deoxys","Dialga","Palkia","Phione","Arceus","Azelf","Uxie","Type: Null","Thundurus","Volcanion","Tapu Koko","Tapu Lele","Tapu Bulu","Tapu Fini","Reshiram","Landorus","Meloetta","Genesect","Silvally","Xerneas","Yveltal","Zygarde","Diancie","Zekrom","Kyurem","Keldeo","Hoopa","Blacephalon","Celesteela","Pheromosa","Xurkitree","Marshadow","Naganadel","Stakataka","Solgaleo","Nihilego","Buzzwole","Guzzlord","Necrozma","Magearna","Cosmoem","Kartana","Poipole","Zeraora","Cosmog","Lunala","Meltan","Zamazenta","Eternatus","Regieleki","Regidrago","Glastrier","Spectrier","Chien-Pao","Melmetal","Enamorus","Wo-Chien","Koraidon","Miraidon","Urshifu","Calyrex","Ting-Lu","Okidogi","Zacian","Zarude","Chi-Yu","Kubfu","Pirouette Meloetta","Therian Thundurus","Therian Tornadus","Therian Landorus","Origin Giratina","Resolute Keldeo","Defense Deoxys","Mega Mewtwo X","Mega Mewtwo Y","Attack Deoxys","Speed Deoxys","Black Kyurem","White Kyurem","Mega Latias","Sky Shaymin","Fezandipiti","Munkidori","Terapagos","Pecharunt","Ogerpon","Rapid Strike Urshifu","Shadow Rider Calyrex","Dawn Wings Necrozma","Dusk Mane Necrozma","Galarian Articuno","Original Magearna","Crowned Zamazenta","Ice Rider Calyrex","Galarian Moltres","Complete Zygarde","Galarian Zapdos","Primal Groudon","Ultra Necrozma","Crowned Zacian","Primal Kyogre","Mega Rayquaza","Hoopa Unbound","Mega Diancie","Mega Latios","10% Zygarde","Gigantamax Single Strike Urshifu","Gigantamax Rapid Strike Urshifu","Sprinting Build Koraidon","Hearthflame Mask Ogerpon","Cornerstone Mask Ogerpon","Wellspring Mask Ogerpon","Gliding Build Koraidon","Gigantamax Melmetal","Eternamax Eternatus","Drive Mode Miraidon","Glide Mode Miraidon","Terastal Terapagos","Therian Enamorus","Neutral Xerneas","Origin Dialga","Origin Palkia","Dragon Arceus","Dark Arceus","Dada Zarude","Bug Arceus","Electric Silvally","Fighting Silvally","Electric Arceus","Fighting Arceus","Dragon Silvally","Psychic Arceus","Flying Arceus","Ground Arceus","Poison Arceus","Dark Silvally","Fire Silvally","Ghost Arceus","Grass Arceus","Steel Arceus","Water Arceus","Fairy Arceus","Bug Silvally","Fire Arceus","Rock Arceus","Ice Arceus","High-speed Flight Configuration Genesect","Ghost King Blacephalon","Psychic Silvally","Zenith Marshadow","Flying Silvally","Ground Silvally","Poison Silvally","Ghost Silvally","Grass Silvally","Steel Silvally","Water Silvally","Fairy Silvally","Shadow Xerneas","Rock Silvally","Festive Hoopa","Shadow Mewtwo","Zygarde Cell","Zygarde Core","Ice Silvally","Shadow Lugia","Spring Blooming Diancie","Olympic Flame Moltres","Corrupted Blacephalon","Glitched Beta Arceus","Primal Glastrier","Flower Pheromosa","Fireworks Cosmog","Bouquet Shaymin","Gradient Chi-Yu","Error Darkrai","Pride Arceus","Druid Zarude","Ice Yveltal","Lights Mew","Pride Mew","Galarian Slowpoke","Alolan Sandshrew","Alolan Sandslash","Alolan Ninetales","Alolan Exeggutor","Alolan Raticate","Galarian Meowth","Alolan Graveler","Alolan Rattata","Alolan Diglett","Alolan Dugtrio","Alolan Persian","Alolan Geodude","Alolan Marowak","Alolan Raichu","Alolan Vulpix","Alolan Meowth","Alolan Grimer","Alolan Golem","Alolan Muk","Galarian Zen Darmanitan","Galarian Farfetch'd","Galarian Darmanitan","Galarian Zigzagoon","Hisuian Growlithe","Galarian Rapidash","Galarian Mr. Mime","Galarian Articuno","Galarian Slowking","Galarian Darumaka","Galarian Stunfisk","Hisuian Arcanine","Galarian Slowbro","Galarian Weezing","Galarian Moltres","Galarian Corsola","Galarian Linoone","Galarian Ponyta","Galarian Zapdos","Galarian Yamask","Halloween Alolan Ninetales","Elsa Galarian Ponyta","Combat Breed Tauros","Blaze Breed Tauros","Hisuian Typhlosion","Hisuian Electrode","Aqua Breed Tauros","Hisuian Lilligant","Hisuian Decidueye","Hisuian Qwilfish","Hisuian Samurott","Hisuian Braviary","Hisuian Voltorb","Hisuian Sneasel","Hisuian Zoroark","Hisuian Sliggoo","Hisuian Avalugg","Paldean Wooper","Hisuian Goodra","Hisuian Zorua","Celebrating Alolan Exeggutor ft. Komala","La Catrina Hisuian Lilligant","Birthday Cake Alopix","Santa H. Zorua" }
