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
GENDER_MALE = "<:male_sign:1445995042333397033>"
GENDER_FEMALE = "<:female_sign:1445995032749277285>"
GENDER_UNKNOWN = "<:grey_question:1445995074847510609>"

# Poketwo id
POKETWO_BOT_ID = 716390085896962058

# Add this to config.py

# Pokemon with visible gender differences that should be tracked separately in full dex
GENDER_DIFFERENCE_POKEMON = {
    "Hisuian Sneasel","Basculegion","Butterfree","Kricketune","Hippopotas","Oinkologne","Vileplume","Sudowoodo","Wobbuffet","Girafarig","Heracross","Piloswine","Octillery","Combusken","Beautifly","Relicanth","Staraptor","Kricketot","Pachirisu","Hippowdon","Toxicroak","Abomasnow","Rhyperior","Tangrowth","Mamoswine","Jellicent","Venusaur","Raticate","Alakazam","Magikarp","Gyarados","Meganium","Politoed","Quagsire","Ursaring","Houndoom","Blaziken","Ludicolo","Meditite","Medicham","Camerupt","Cacturne","Staravia","Roserade","Floatzel","Garchomp","Croagunk","Lumineon","Unfezant","Frillish","Meowstic","Indeedee","Rattata","Pikachu","Kadabra","Rhyhorn","Goldeen","Seaking","Scyther","Murkrow","Steelix","Sneasel","Donphan","Torchic","Nuzleaf","Shiftry","Roselia","Milotic","Bibarel","Ambipom","Finneon","Weavile","Raichu","Golbat","Dodrio","Rhydon","Ledyba","Ledian","Wooper","Gligar","Scizor","Dustox","Gulpin","Swalot","Starly","Bidoof","Luxray","Combee","Buizel","Gabite","Snover","Pyroar","Zubat","Gloom","Doduo","Hypno","Eevee","Aipom","Numel","Shinx","Luxio","Gible","Xatu"
}
