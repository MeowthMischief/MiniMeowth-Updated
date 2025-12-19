from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import re
import config

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        # Breeding bot collections
        self.pokemon = None
        self.cooldowns = None
        self.settings = None
        # Shiny dex collections
        self.shinies = None
        self.event_shinies = None

    @staticmethod
    def clean_pokemon_name(name: str) -> str:
        """Remove Discord emojis and Unicode emojis from Pokemon names"""
        if not name:
            return name

        # Remove Gigantamax emoji specifically
        name = name.replace('<:_:1242455099213877248>', '')

        # Remove custom Discord emojis: <:name:id> or <a:name:id>
        name = re.sub(r'<a?:[^:]*:\d+>', '', name)

        # Remove sparkles emoji
        name = name.replace('✨', '')

        # Remove other Unicode emojis but keep text
        name = re.sub(r'[\u2600-\u263F\u2641\u2643-\u27BF\U0001F300-\U0001F9FF]', '', name)

        # Clean up extra whitespace
        name = ' '.join(name.split())
        return name.strip()

    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(config.MONGODB_URI)
        self.db = self.client[config.DATABASE_NAME]

        # Breeding bot collections
        self.pokemon = self.db[config.COLLECTION_POKEMON]
        self.cooldowns = self.db[config.COLLECTION_COOLDOWNS]
        self.settings = self.db[config.COLLECTION_SETTINGS]

        # Shiny dex collections
        self.shinies = self.db['shinies']
        self.event_shinies = self.db['event_shinies']

        # Create indexes for breeding bot
        await self.pokemon.create_index([("user_id", 1), ("pokemon_id", 1)], unique=True)
        await self.pokemon.create_index("user_id")
        await self.pokemon.create_index("categories")
        await self.pokemon.create_index("dex_number")
        await self.pokemon.create_index([("user_id", 1), ("categories", 1)])
        await self.pokemon.create_index([("user_id", 1), ("gender", 1)])
        await self.cooldowns.create_index("user_id")
        await self.settings.create_index("user_id", unique=True)

        # Create indexes for shinies
        await self.shinies.create_index([("user_id", 1), ("pokemon_id", 1)], unique=True)
        await self.shinies.create_index("user_id")
        await self.shinies.create_index("dex_number")
        await self.shinies.create_index([("user_id", 1), ("name", 1)])
        await self.shinies.create_index([("user_id", 1), ("dex_number", 1)])

        # Create indexes for event shinies
        await self.event_shinies.create_index([("user_id", 1), ("pokemon_id", 1)], unique=True)
        await self.event_shinies.create_index("user_id")
        await self.event_shinies.create_index([("user_id", 1), ("name", 1)])

        print("✅ Connected to MongoDB (Breeding Bot + Shiny Dex)")

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("❌ Disconnected from MongoDB")

    # ===== POKEMON OPERATIONS (BREEDING BOT) =====

    async def add_pokemon(self, user_id: int, pokemon_data: dict, category: str = "normal"):
        """Add a single Pokemon to inventory with category and dex number (ignore if duplicate user_id+pokemon_id)"""
        try:
            # Ensure required fields exist
            if 'dex_number' not in pokemon_data:
                pokemon_data['dex_number'] = 0

            # Ensure pre-computed fields exist (for new additions)
            if 'egg_groups' not in pokemon_data:
                pokemon_data['egg_groups'] = []
            if 'is_ditto' not in pokemon_data:
                pokemon_data['is_ditto'] = False
            if 'is_gmax' not in pokemon_data:
                pokemon_data['is_gmax'] = False
            if 'is_regional' not in pokemon_data:
                pokemon_data['is_regional'] = False
            if 'base_species' not in pokemon_data:
                pokemon_data['base_species'] = ''

            # Check if Pokemon already exists for this user
            existing = await self.pokemon.find_one({
                "user_id": user_id,
                "pokemon_id": pokemon_data['pokemon_id']
            })

            if existing:
                # Pokemon exists - add category if not already there
                if category not in existing.get('categories', []):
                    await self.pokemon.update_one(
                        {"user_id": user_id, "pokemon_id": pokemon_data['pokemon_id']},
                        {"$addToSet": {"categories": category}}
                    )
                return False  # Not a new Pokemon
            else:
                # New Pokemon - insert with category
                pokemon_data['user_id'] = user_id
                pokemon_data['categories'] = [category]
                await self.pokemon.insert_one(pokemon_data)
                return True  # New Pokemon added
        except Exception as e:
            print(f"Error adding Pokemon: {e}")
            return False

    async def add_pokemon_bulk(self, user_id: int, pokemon_list: list, category: str = "normal"):
        """Add multiple Pokemon using true bulk operations - FAST"""
        if not pokemon_list:
            return 0

        # Extract all Pokemon IDs we're trying to add
        pokemon_ids = [p['pokemon_id'] for p in pokemon_list]

        # Single query to find all existing Pokemon for this user
        existing_docs = await self.pokemon.find(
            {"user_id": user_id, "pokemon_id": {"$in": pokemon_ids}},
            {"pokemon_id": 1, "categories": 1}  # OPTIMIZATION: Only fetch needed fields
        ).to_list(length=None)

        # Build a set of existing IDs for fast lookup
        existing_ids = {doc['pokemon_id'] for doc in existing_docs}
        existing_by_id = {doc['pokemon_id']: doc for doc in existing_docs}

        # Separate into new vs existing
        new_pokemon = []
        update_operations = []

        for pokemon in pokemon_list:
            pid = pokemon['pokemon_id']

            # Ensure required fields exist
            if 'dex_number' not in pokemon:
                pokemon['dex_number'] = 0

            # Ensure pre-computed fields exist (should already be there from parsing)
            if 'egg_groups' not in pokemon:
                pokemon['egg_groups'] = []
            if 'is_ditto' not in pokemon:
                pokemon['is_ditto'] = False
            if 'is_gmax' not in pokemon:
                pokemon['is_gmax'] = False
            if 'is_regional' not in pokemon:
                pokemon['is_regional'] = False
            if 'base_species' not in pokemon:
                pokemon['base_species'] = ''

            if pid not in existing_ids:
                # Brand new Pokemon
                pokemon['user_id'] = user_id
                pokemon['categories'] = [category]
                new_pokemon.append(pokemon)
            else:
                # Existing Pokemon - add category if not present
                existing_doc = existing_by_id[pid]
                if category not in existing_doc.get('categories', []):
                    update_operations.append({
                        'filter': {'user_id': user_id, 'pokemon_id': pid},
                        'update': {'$addToSet': {'categories': category}}
                    })

        # Execute bulk operations
        new_count = 0

        # Bulk insert new Pokemon (ignore duplicates that might occur in race conditions)
        if new_pokemon:
            try:
                result = await self.pokemon.insert_many(new_pokemon, ordered=False)
                new_count = len(result.inserted_ids)
            except Exception as e:
                # If some duplicates slipped through, count what succeeded
                if "duplicate key" in str(e).lower():
                    # Try to count how many actually inserted
                    new_count = len([p for p in new_pokemon if p['pokemon_id'] not in existing_ids])
                else:
                    print(f"Bulk insert error: {e}")

        # Bulk update existing Pokemon categories (batched for efficiency)
        if update_operations:
            # Use bulk_write for true bulk updates
            from pymongo import UpdateOne
            bulk_ops = [UpdateOne(op['filter'], op['update']) for op in update_operations]
            try:
                await self.pokemon.bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                print(f"Bulk update error: {e}")

        return new_count

    async def remove_pokemon(self, user_id: int, pokemon_ids: list, category: str = None):
        """Remove Pokemon by IDs. If category specified, only remove from that category"""
        if category:
            # Remove category from Pokemon, delete if no categories left
            result_count = 0

            # OPTIMIZATION: Use bulk operations
            from pymongo import UpdateMany, DeleteMany

            # Update all at once
            update_result = await self.pokemon.update_many(
                {"user_id": user_id, "pokemon_id": {"$in": pokemon_ids}},
                {"$pull": {"categories": category}}
            )
            result_count = update_result.modified_count

            # Delete Pokemon with no categories left
            await self.pokemon.delete_many({
                "user_id": user_id,
                "pokemon_id": {"$in": pokemon_ids},
                "categories": {"$size": 0}
            })

            return result_count
        else:
            # Remove completely
            result = await self.pokemon.delete_many({
                "user_id": user_id,
                "pokemon_id": {"$in": pokemon_ids}
            })
            return result.deleted_count

    async def clear_inventory(self, user_id: int, category: str = None):
        """Clear Pokemon for a user. If category specified, only clear that category"""
        if category:
            # Get count before clearing
            count = await self.pokemon.count_documents({
                "user_id": user_id,
                "categories": category
            })

            # Remove category from all Pokemon
            await self.pokemon.update_many(
                {"user_id": user_id},
                {"$pull": {"categories": category}}
            )

            # Delete Pokemon with no categories left
            await self.pokemon.delete_many({
                "user_id": user_id,
                "categories": {"$size": 0}
            })

            return count
        else:
            # Clear all Pokemon
            result = await self.pokemon.delete_many({"user_id": user_id})
            return result.deleted_count

    async def get_pokemon(self, user_id: int, filters: dict = None, category: str = None):
        """Get Pokemon with optional filters and category - OPTIMIZED"""
        query = {"user_id": user_id}

        if category:
            query["categories"] = category

        if filters:
            query.update(filters)

        # OPTIMIZATION: Use projection to only fetch needed fields if they exist
        # This reduces network transfer and memory usage
        cursor = self.pokemon.find(query)
        return await cursor.to_list(length=None)

    async def get_pokemon_by_id(self, user_id: int, pokemon_id: int):
        """Get single Pokemon by ID"""
        return await self.pokemon.find_one({
            "user_id": user_id,
            "pokemon_id": pokemon_id
        })

    async def count_pokemon(self, user_id: int, filters: dict = None, category: str = None):
        """Count Pokemon with optional filters and category"""
        query = {"user_id": user_id}

        if category:
            query["categories"] = category

        if filters:
            query.update(filters)

        return await self.pokemon.count_documents(query)

    # ===== COOLDOWN OPERATIONS (BREEDING BOT) =====

    async def add_cooldown(self, user_id: int, pokemon_ids: list):
        """Add Pokemon IDs to cooldown - OPTIMIZED"""
        if not pokemon_ids:
            return

        expiry = datetime.utcnow() + timedelta(
            days=config.COOLDOWN_DAYS,
            hours=config.COOLDOWN_HOURS
        )

        # Get or create user cooldown document
        doc = await self.cooldowns.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}  # OPTIMIZATION: Only fetch cooldowns field
        )

        if doc:
            # Add new IDs to existing cooldowns
            cooldown_dict = doc.get("cooldowns", {})
            for pid in pokemon_ids:
                cooldown_dict[str(pid)] = expiry

            await self.cooldowns.update_one(
                {"user_id": user_id},
                {"$set": {"cooldowns": cooldown_dict}}
            )
        else:
            # Create new cooldown document
            cooldown_dict = {str(pid): expiry for pid in pokemon_ids}
            await self.cooldowns.insert_one({
                "user_id": user_id,
                "cooldowns": cooldown_dict
            })

    async def remove_cooldown(self, user_id: int, pokemon_ids: list):
        """Remove Pokemon IDs from cooldown"""
        if not pokemon_ids:
            return

        doc = await self.cooldowns.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )
        if not doc:
            return

        cooldown_dict = doc.get("cooldowns", {})
        for pid in pokemon_ids:
            cooldown_dict.pop(str(pid), None)

        await self.cooldowns.update_one(
            {"user_id": user_id},
            {"$set": {"cooldowns": cooldown_dict}}
        )

    async def clear_all_cooldowns(self, user_id: int):
        """Clear all cooldowns and return accurate count"""
        doc = await self.cooldowns.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )
        if not doc:
            return 0

        count = len(doc.get("cooldowns", {}))

        await self.cooldowns.update_one(
            {"user_id": user_id},
            {"$set": {"cooldowns": {}}}
        )

        return count

    async def get_cooldowns(self, user_id: int):
        """Get all active cooldowns for user - OPTIMIZED"""
        doc = await self.cooldowns.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}  # OPTIMIZATION: Only fetch cooldowns field
        )
        if not doc:
            return {}

        cooldowns = doc.get("cooldowns", {})
        now = datetime.utcnow()

        # Remove expired cooldowns
        active_cooldowns = {}
        has_expired = False

        for pid, expiry in cooldowns.items():
            if expiry > now:
                active_cooldowns[int(pid)] = expiry
            else:
                has_expired = True

        # Update document only if any expired (reduces unnecessary writes)
        if has_expired and len(active_cooldowns) != len(cooldowns):
            cooldown_dict = {str(k): v for k, v in active_cooldowns.items()}
            await self.cooldowns.update_one(
                {"user_id": user_id},
                {"$set": {"cooldowns": cooldown_dict}}
            )

        return active_cooldowns

    async def is_on_cooldown(self, user_id: int, pokemon_id: int):
        """Check if a Pokemon is on cooldown - OPTIMIZED"""
        doc = await self.cooldowns.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )
        if not doc:
            return False

        cooldowns = doc.get("cooldowns", {})
        pid_str = str(pokemon_id)

        if pid_str not in cooldowns:
            return False

        # Check if expired
        expiry = cooldowns[pid_str]
        if expiry <= datetime.utcnow():
            return False

        return True

    # ===== SETTINGS OPERATIONS (BREEDING BOT) =====

    async def get_settings(self, user_id: int):
        """Get user settings - OPTIMIZED with default handling"""
        settings = await self.settings.find_one({"user_id": user_id})

        # Default settings
        defaults = {
            "user_id": user_id,
            "mode": "notselective",
            "target": ["all"],
            "mychoice_male": None,
            "mychoice_female": None,
            "show_info": "detailed"
        }

        if not settings:
            return defaults

        # Merge with defaults to ensure all fields exist
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value

        return settings

    async def update_settings(self, user_id: int, updates: dict):
        """Update user settings"""
        await self.settings.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )

    # ===== SHINY OPERATIONS (SHINY DEX) =====

    async def add_shiny(self, user_id: int, shiny_data: dict):
        """Add or update a single shiny"""
        try:
            # Clean the name before storing
            if 'name' in shiny_data:
                shiny_data['name'] = self.clean_pokemon_name(shiny_data['name'])

            # Check if this pokemon_id exists
            existing = await self.shinies.find_one({
                "user_id": user_id,
                "pokemon_id": shiny_data['pokemon_id']
            })

            if existing:
                # Update existing (handles form changes, evolutions, etc.)
                await self.shinies.update_one(
                    {
                        "user_id": user_id,
                        "pokemon_id": shiny_data['pokemon_id']
                    },
                    {
                        "$set": {
                            "name": shiny_data['name'],
                            "gender": shiny_data['gender'],
                            "level": shiny_data['level'],
                            "iv_percent": shiny_data['iv_percent'],
                            "dex_number": shiny_data['dex_number']
                        }
                    }
                )
                return False  # Not a new shiny
            else:
                # Insert new
                shiny_data['user_id'] = user_id
                await self.shinies.insert_one(shiny_data)
                return True  # New shiny added

        except Exception as e:
            print(f"Error adding/updating shiny: {e}")
            return False

    async def add_shinies_bulk(self, user_id: int, shinies_list: list):
        """Add multiple shinies using bulk operations"""
        if not shinies_list:
            return 0

        # Clean all names first
        for shiny in shinies_list:
            if 'name' in shiny:
                shiny['name'] = self.clean_pokemon_name(shiny['name'])

        # Extract all shiny IDs
        shiny_ids = [s['pokemon_id'] for s in shinies_list]

        # Find existing shinies
        existing_docs = await self.shinies.find(
            {"user_id": user_id, "pokemon_id": {"$in": shiny_ids}},
            {"pokemon_id": 1}
        ).to_list(length=None)

        existing_ids = {doc['pokemon_id'] for doc in existing_docs}

        # Separate into new vs existing
        new_shinies = []
        update_operations = []

        for shiny in shinies_list:
            pid = shiny['pokemon_id']

            if pid not in existing_ids:
                # Brand new shiny
                shiny['user_id'] = user_id
                new_shinies.append(shiny)
            else:
                # Existing - update it (handles form changes)
                update_operations.append({
                    'filter': {'user_id': user_id, 'pokemon_id': pid},
                    'update': {
                        '$set': {
                            'name': shiny['name'],
                            'gender': shiny['gender'],
                            'level': shiny['level'],
                            'iv_percent': shiny['iv_percent'],
                            'dex_number': shiny['dex_number']
                        }
                    }
                })

        new_count = 0

        # Bulk insert new shinies
        if new_shinies:
            try:
                result = await self.shinies.insert_many(new_shinies, ordered=False)
                new_count = len(result.inserted_ids)
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    new_count = len(new_shinies)
                else:
                    print(f"Bulk insert shiny error: {e}")

        # Bulk update existing shinies
        if update_operations:
            from pymongo import UpdateOne
            bulk_ops = [UpdateOne(op['filter'], op['update']) for op in update_operations]
            try:
                await self.shinies.bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                print(f"Bulk update shiny error: {e}")

        return new_count

    async def remove_shinies(self, user_id: int, pokemon_ids: list):
        """Remove shinies by IDs"""
        result = await self.shinies.delete_many({
            "user_id": user_id,
            "pokemon_id": {"$in": pokemon_ids}
        })
        return result.deleted_count

    async def clear_all_shinies(self, user_id: int):
        """Clear all shinies for a user"""
        result = await self.shinies.delete_many({"user_id": user_id})
        return result.deleted_count

    async def get_all_shinies(self, user_id: int):
        """Get all shinies for a user"""
        cursor = self.shinies.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    async def count_shinies(self, user_id: int):
        """Count total shinies for a user"""
        return await self.shinies.count_documents({"user_id": user_id})

    async def get_shinies_by_dex(self, user_id: int, dex_number: int):
        """Get all shinies with a specific dex number"""
        cursor = self.shinies.find({
            "user_id": user_id,
            "dex_number": dex_number
        })
        return await cursor.to_list(length=None)

    async def get_shinies_by_name(self, user_id: int, name: str):
        """Get all shinies with exact name match"""
        cursor = self.shinies.find({
            "user_id": user_id,
            "name": name
        })
        return await cursor.to_list(length=None)

    # ===== EVENT SHINY OPERATIONS (SHINY DEX) =====

    async def add_event_shiny(self, user_id: int, shiny_data: dict):
        """Add or update a single event shiny"""
        try:
            # Clean the name before storing
            if 'name' in shiny_data:
                shiny_data['name'] = self.clean_pokemon_name(shiny_data['name'])

            # Check if this pokemon_id exists
            existing = await self.event_shinies.find_one({
                "user_id": user_id,
                "pokemon_id": shiny_data['pokemon_id']
            })

            if existing:
                # Update existing
                await self.event_shinies.update_one(
                    {
                        "user_id": user_id,
                        "pokemon_id": shiny_data['pokemon_id']
                    },
                    {
                        "$set": {
                            "name": shiny_data['name'],
                            "gender": shiny_data['gender'],
                            "level": shiny_data['level'],
                            "iv_percent": shiny_data['iv_percent']
                        }
                    }
                )
                return False  # Not a new shiny
            else:
                # Insert new
                shiny_data['user_id'] = user_id
                await self.event_shinies.insert_one(shiny_data)
                return True  # New shiny added

        except Exception as e:
            print(f"Error adding/updating event shiny: {e}")
            return False

    async def add_event_shinies_bulk(self, user_id: int, shinies_list: list):
        """Add multiple event shinies using bulk operations"""
        if not shinies_list:
            return 0

        # Clean all names first
        for shiny in shinies_list:
            if 'name' in shiny:
                shiny['name'] = self.clean_pokemon_name(shiny['name'])

        # Extract all shiny IDs
        shiny_ids = [s['pokemon_id'] for s in shinies_list]

        # Find existing shinies
        existing_docs = await self.event_shinies.find(
            {"user_id": user_id, "pokemon_id": {"$in": shiny_ids}},
            {"pokemon_id": 1}
        ).to_list(length=None)

        existing_ids = {doc['pokemon_id'] for doc in existing_docs}

        # Separate into new vs existing
        new_shinies = []
        update_operations = []

        for shiny in shinies_list:
            pid = shiny['pokemon_id']

            if pid not in existing_ids:
                # Brand new shiny
                shiny['user_id'] = user_id
                new_shinies.append(shiny)
            else:
                # Existing - update it
                update_operations.append({
                    'filter': {'user_id': user_id, 'pokemon_id': pid},
                    'update': {
                        '$set': {
                            'name': shiny['name'],
                            'gender': shiny['gender'],
                            'level': shiny['level'],
                            'iv_percent': shiny['iv_percent']
                        }
                    }
                })

        new_count = 0

        # Bulk insert new shinies
        if new_shinies:
            try:
                result = await self.event_shinies.insert_many(new_shinies, ordered=False)
                new_count = len(result.inserted_ids)
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    new_count = len(new_shinies)
                else:
                    print(f"Bulk insert event shiny error: {e}")

        # Bulk update existing shinies
        if update_operations:
            from pymongo import UpdateOne
            bulk_ops = [UpdateOne(op['filter'], op['update']) for op in update_operations]
            try:
                await self.event_shinies.bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                print(f"Bulk update event shiny error: {e}")

        return new_count

    async def remove_event_shinies(self, user_id: int, pokemon_ids: list):
        """Remove event shinies by IDs"""
        result = await self.event_shinies.delete_many({
            "user_id": user_id,
            "pokemon_id": {"$in": pokemon_ids}
        })
        return result.deleted_count

    async def clear_all_event_shinies(self, user_id: int):
        """Clear all event shinies for a user"""
        result = await self.event_shinies.delete_many({"user_id": user_id})
        return result.deleted_count

    async def get_all_event_shinies(self, user_id: int):
        """Get all event shinies for a user"""
        cursor = self.event_shinies.find({"user_id": user_id})
        return await cursor.to_list(length=None)

    async def count_event_shinies(self, user_id: int):
        """Count total event shinies for a user"""
        return await self.event_shinies.count_documents({"user_id": user_id})

    async def get_event_shinies_by_name(self, user_id: int, name: str):
        """Get all event shinies with exact name match"""
        cursor = self.event_shinies.find({
            "user_id": user_id,
            "name": name
        })
        return await cursor.to_list(length=None)


# Global database instance
db = Database()
