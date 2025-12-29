from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import re
import config

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        # Collections
        self.pokemon = None
        self.user_data = None  # NEW: Consolidated user data (settings + cooldowns + id_overrides)
        self.shinies = None
        self.event_shinies = None

    @staticmethod
    def clean_pokemon_name(name: str) -> str:
        """Remove Discord emojis and Unicode emojis from Pokemon names"""
        if not name:
            return name

        name = name.replace('<:_:1242455099213877248>', '')
        name = re.sub(r'<a?:[^:]*:\d+>', '', name)
        name = name.replace('✨', '')
        name = re.sub(r'[\u2600-\u263F\u2641\u2643-\u27BF\U0001F300-\U0001F9FF]', '', name)
        name = ' '.join(name.split())
        return name.strip()

    async def connect(self):
        """Connect to MongoDB with optimized indexes"""
        self.client = AsyncIOMotorClient(config.MONGODB_URI)
        self.db = self.client[config.DATABASE_NAME]

        # Collections
        self.pokemon = self.db['pokemon']
        self.user_data = self.db['user_data']
        self.shinies = self.db['shinies']
        self.event_shinies = self.db['event_shinies']

        # ===== CREATE OPTIMIZED INDEXES =====

        # Pokemon collection - compound indexes for common queries
        await self._create_index_safe(
            self.pokemon,
            [("user_id", 1), ("categories", 1), ("gender", 1)],
            name="user_category_gender"
        )

        await self._create_index_safe(
            self.pokemon,
            [("user_id", 1), ("categories", 1), ("iv_percent", -1)],
            name="user_category_iv"
        )

        await self._create_index_safe(
            self.pokemon,
            [("user_id", 1), ("pokemon_id", 1)],
            unique=True,
            name="user_pokemon_unique"
        )

        # Additional indexes for filtering
        await self._create_index_safe(
            self.pokemon,
            "user_id",
            name="user_id_idx"
        )

        await self._create_index_safe(
            self.pokemon,
            "categories",
            name="categories_idx"
        )

        await self._create_index_safe(
            self.pokemon,
            "dex_number",
            name="dex_number_idx"
        )

        # Partial indexes for special types
        await self._create_index_safe(
            self.pokemon,
            [("user_id", 1), ("is_gmax", 1)],
            partialFilterExpression={"is_gmax": True},
            name="user_gmax_partial"
        )

        await self._create_index_safe(
            self.pokemon,
            [("user_id", 1), ("is_regional", 1)],
            partialFilterExpression={"is_regional": True},
            name="user_regional_partial"
        )

        # User data collection
        await self._create_index_safe(
            self.user_data,
            "user_id",
            unique=True,
            name="user_data_user_id"
        )

        # Shiny dex indexes
        await self._create_index_safe(
            self.shinies,
            [("user_id", 1), ("pokemon_id", 1)],
            unique=True,
            name="shiny_user_pokemon"
        )
        await self._create_index_safe(
            self.shinies,
            "user_id",
            name="shiny_user_id"
        )
        await self._create_index_safe(
            self.shinies,
            "dex_number",
            name="shiny_dex_number"
        )
        await self._create_index_safe(
            self.shinies,
            [("user_id", 1), ("name", 1)],
            name="shiny_user_name"
        )
        await self._create_index_safe(
            self.shinies,
            [("user_id", 1), ("dex_number", 1)],
            name="shiny_user_dex"
        )

        # Event shinies indexes
        await self._create_index_safe(
            self.event_shinies,
            [("user_id", 1), ("pokemon_id", 1)],
            unique=True,
            name="event_shiny_user_pokemon"
        )
        await self._create_index_safe(
            self.event_shinies,
            "user_id",
            name="event_shiny_user_id"
        )
        await self._create_index_safe(
            self.event_shinies,
            [("user_id", 1), ("name", 1)],
            name="event_shiny_user_name"
        )

        print("✅ Connected to MongoDB with optimized indexes")

    async def _create_index_safe(self, collection, keys, **kwargs):
        """Helper method to create indexes with error handling"""
        try:
            await collection.create_index(keys, **kwargs)
            index_name = kwargs.get('name', 'unnamed')
            print(f"✅ Index ready: {index_name}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"⚠️  Index creation warning: {e}")

    # ========================================
    # POKEMON OPERATIONS (BREEDING BOT)
    # ========================================

    async def get_pokemon_for_breeding(self, user_id: int, category: str, gender: str = None, 
                                       is_gmax: bool = None, is_regional: bool = None,
                                       cooldown_ids: set = None):
        """
        OPTIMIZED: Get Pokemon for breeding with all filters in single query
        Returns only necessary fields, excludes cooldowns at query level
        """
        query = {
            "user_id": user_id,
            "categories": category
        }

        if gender:
            query["gender"] = gender

        if is_gmax is not None:
            query["is_gmax"] = is_gmax

        if is_regional is not None:
            query["is_regional"] = is_regional

        # Exclude cooldowns in the query itself (faster than filtering in code)
        if cooldown_ids:
            query["pokemon_id"] = {"$nin": list(cooldown_ids)}

        # Project only needed fields (reduces network transfer)
        projection = {
            "pokemon_id": 1,
            "name": 1,
            "gender": 1,
            "iv_percent": 1,
            "dex_number": 1,
            "egg_groups": 1,
            "base_species": 1,
            "is_gmax": 1,
            "is_regional": 1,
            "is_ditto": 1
        }

        # Sort by IV descending (use index)
        cursor = self.pokemon.find(query, projection).sort("iv_percent", -1)
        return await cursor.to_list(length=None)

    async def get_pokemon_by_ids_bulk(self, user_id: int, pokemon_ids: list):
        """
        OPTIMIZED: Fetch multiple Pokemon in a single query
        Returns dict for O(1) lookups: {pokemon_id: pokemon_data}
        """
        if not pokemon_ids:
            return {}

        cursor = self.pokemon.find({
            "user_id": user_id,
            "pokemon_id": {"$in": pokemon_ids}
        })

        results = await cursor.to_list(length=None)
        return {p['pokemon_id']: p for p in results}

    async def add_pokemon(self, user_id: int, pokemon_data: dict, category: str = "normal"):
        """Add a single Pokemon to inventory with category"""
        try:
            # Ensure required fields
            pokemon_data.setdefault('dex_number', 0)
            pokemon_data.setdefault('egg_groups', [])
            pokemon_data.setdefault('is_ditto', False)
            pokemon_data.setdefault('is_gmax', False)
            pokemon_data.setdefault('is_regional', False)
            pokemon_data.setdefault('base_species', '')

            # Check if exists
            existing = await self.pokemon.find_one({
                "user_id": user_id,
                "pokemon_id": pokemon_data['pokemon_id']
            })

            if existing:
                # Add category if not present
                if category not in existing.get('categories', []):
                    await self.pokemon.update_one(
                        {"user_id": user_id, "pokemon_id": pokemon_data['pokemon_id']},
                        {"$addToSet": {"categories": category}}
                    )
                return False
            else:
                # New Pokemon
                pokemon_data['user_id'] = user_id
                pokemon_data['categories'] = [category]
                await self.pokemon.insert_one(pokemon_data)
                return True
        except Exception as e:
            print(f"Error adding Pokemon: {e}")
            return False

    async def add_pokemon_bulk(self, user_id: int, pokemon_list: list, category: str = "normal"):
        """
        OPTIMIZED: Add multiple Pokemon using true bulk operations
        Uses bulk_write for maximum performance
        """
        if not pokemon_list:
            return 0

        from pymongo import UpdateOne, InsertOne

        pokemon_ids = [p['pokemon_id'] for p in pokemon_list]

        # Single query to find all existing Pokemon
        existing_ids = set()
        async for doc in self.pokemon.find(
            {"user_id": user_id, "pokemon_id": {"$in": pokemon_ids}},
            {"pokemon_id": 1}  # Only fetch pokemon_id field
        ):
            existing_ids.add(doc['pokemon_id'])

        # Build bulk operations
        operations = []
        new_count = 0

        for pokemon in pokemon_list:
            pid = pokemon['pokemon_id']

            # Ensure required fields
            pokemon.setdefault('dex_number', 0)
            pokemon.setdefault('egg_groups', [])
            pokemon.setdefault('is_ditto', False)
            pokemon.setdefault('is_gmax', False)
            pokemon.setdefault('is_regional', False)
            pokemon.setdefault('base_species', '')

            if pid not in existing_ids:
                # New Pokemon - insert
                pokemon['user_id'] = user_id
                pokemon['categories'] = [category]
                operations.append(InsertOne(pokemon))
                new_count += 1
            else:
                # Existing - add category
                operations.append(UpdateOne(
                    {"user_id": user_id, "pokemon_id": pid},
                    {"$addToSet": {"categories": category}}
                ))

        if operations:
            try:
                await self.pokemon.bulk_write(operations, ordered=False)
            except Exception as e:
                if "duplicate key" in str(e).lower():
                    # Some succeeded, count them
                    pass
                else:
                    print(f"Bulk operation error: {e}")

        return new_count

    async def remove_pokemon(self, user_id: int, pokemon_ids: list, category: str = None):
        """Remove Pokemon by IDs. If category specified, only remove from that category"""
        if category:
            from pymongo import UpdateMany, DeleteMany

            # Remove category from Pokemon
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
        """Get Pokemon with optional filters and category"""
        query = {"user_id": user_id}

        if category:
            query["categories"] = category

        if filters:
            query.update(filters)

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

    # ========================================
    # USER DATA (SETTINGS + COOLDOWNS + ID_OVERRIDES)
    # ========================================

    async def get_user_data(self, user_id: int):
        """
        OPTIMIZED: Get all user data in a SINGLE query
        Includes: settings, cooldowns, id_overrides
        """
        doc = await self.user_data.find_one({"user_id": user_id})

        if not doc:
            # Return defaults
            return {
                "user_id": user_id,
                "settings": {
                    "mode": "notselective",
                    "target": ["all"],
                    "mychoice_male": None,
                    "mychoice_female": None,
                    "show_info": "detailed"
                },
                "cooldowns": {},
                "id_overrides": {}
            }

        # Ensure all fields exist
        doc.setdefault("settings", {
            "mode": "notselective",
            "target": ["all"],
            "mychoice_male": None,
            "mychoice_female": None,
            "show_info": "detailed"
        })
        doc.setdefault("cooldowns", {})
        doc.setdefault("id_overrides", {})

        return doc

    async def get_settings(self, user_id: int):
        """Get user settings from consolidated document"""
        user_data = await self.get_user_data(user_id)
        return user_data["settings"]

    async def update_settings(self, user_id: int, updates: dict):
        """Update user settings"""
        update_dict = {f"settings.{k}": v for k, v in updates.items()}

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$set": update_dict},
            upsert=True
        )

    # ========================================
    # COOLDOWN OPERATIONS
    # ========================================

    async def get_active_cooldowns(self, user_id: int):
        """
        OPTIMIZED: Get only active cooldowns with automatic cleanup
        Returns set of pokemon_ids for O(1) lookups
        """
        doc = await self.user_data.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )

        if not doc or not doc.get("cooldowns"):
            return set()

        now = datetime.utcnow()
        cooldowns = doc.get("cooldowns", {})

        active = set()
        expired = []

        for pid_str, expiry in cooldowns.items():
            if expiry > now:
                active.add(int(pid_str))
            else:
                expired.append(pid_str)

        # Cleanup expired in background (don't wait)
        if expired:
            unset_dict = {f"cooldowns.{pid}": "" for pid in expired}
            await self.user_data.update_one(
                {"user_id": user_id},
                {"$unset": unset_dict}
            )

        return active

    async def get_cooldowns(self, user_id: int):
        """
        Get cooldowns with expiry times (for cooldown list command)
        Returns dict: {pokemon_id: expiry_datetime}
        """
        doc = await self.user_data.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )

        if not doc:
            return {}

        cooldowns = doc.get("cooldowns", {})
        now = datetime.utcnow()

        active_cooldowns = {}
        expired = []

        for pid_str, expiry in cooldowns.items():
            if expiry > now:
                active_cooldowns[int(pid_str)] = expiry
            else:
                expired.append(pid_str)

        # Cleanup expired
        if expired:
            unset_dict = {f"cooldowns.{pid}": "" for pid in expired}
            await self.user_data.update_one(
                {"user_id": user_id},
                {"$unset": unset_dict}
            )

        return active_cooldowns

    async def add_cooldown(self, user_id: int, pokemon_ids: list):
        """Add Pokemon IDs to cooldown (backward compatibility wrapper)"""
        await self.add_cooldowns_bulk(user_id, pokemon_ids)

    async def add_cooldowns_bulk(self, user_id: int, pokemon_ids: list):
        """OPTIMIZED: Add multiple cooldowns in single operation"""
        if not pokemon_ids:
            return

        expiry = datetime.utcnow() + timedelta(
            days=config.COOLDOWN_DAYS,
            hours=config.COOLDOWN_HOURS
        )

        update_dict = {f"cooldowns.{pid}": expiry for pid in pokemon_ids}

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$set": update_dict},
            upsert=True
        )

    async def remove_cooldown(self, user_id: int, pokemon_ids: list):
        """Remove Pokemon IDs from cooldown"""
        if not pokemon_ids:
            return

        unset_dict = {f"cooldowns.{pid}": "" for pid in pokemon_ids}

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$unset": unset_dict}
        )

    async def clear_all_cooldowns(self, user_id: int):
        """Clear all cooldowns and return count"""
        doc = await self.user_data.find_one(
            {"user_id": user_id},
            {"cooldowns": 1}
        )

        if not doc:
            return 0

        count = len(doc.get("cooldowns", {}))

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$set": {"cooldowns": {}}}
        )

        return count

    async def is_on_cooldown(self, user_id: int, pokemon_id: int):
        """Check if a Pokemon is on cooldown"""
        doc = await self.user_data.find_one(
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

    # ========================================
    # ID OVERRIDE OPERATIONS
    # ========================================

    async def get_id_overrides(self, user_id: int):
        """
        Get all ID overrides for a user
        Returns: dict of {pokemon_id: 'old'/'new'}
        """
        user_data = await self.get_user_data(user_id)
        overrides = user_data.get("id_overrides", {})
        # Convert string keys to int
        return {int(k): v for k, v in overrides.items()}

    async def get_id_override(self, user_id: int, pokemon_id: int):
        """
        Get override for a specific ID
        Returns: 'old', 'new', or None if no override
        """
        doc = await self.user_data.find_one(
            {"user_id": user_id},
            {"id_overrides": 1}
        )
        if not doc:
            return None

        overrides = doc.get("id_overrides", {})
        return overrides.get(str(pokemon_id))

    async def set_id_override(self, user_id: int, pokemon_id: int, category: str):
        """
        Set an ID override for selective mode
        category: 'old' or 'new'
        """
        if category not in ['old', 'new']:
            return False

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$set": {f"id_overrides.{pokemon_id}": category}},
            upsert=True
        )
        return True

    async def remove_id_override(self, user_id: int, pokemon_id: int):
        """Remove an ID override"""
        await self.user_data.update_one(
            {"user_id": user_id},
            {"$unset": {f"id_overrides.{pokemon_id}": ""}}
        )

    async def clear_all_id_overrides(self, user_id: int):
        """Clear all ID overrides for a user"""
        doc = await self.user_data.find_one(
            {"user_id": user_id},
            {"id_overrides": 1}
        )
        if not doc:
            return 0

        count = len(doc.get("id_overrides", {}))

        await self.user_data.update_one(
            {"user_id": user_id},
            {"$set": {"id_overrides": {}}}
        )
        return count

    # ========================================
    # SHINY DEX OPERATIONS
    # ========================================

    async def add_shiny(self, user_id: int, shiny_data: dict):
        """Add or update a single shiny"""
        try:
            # Clean the name before storing
            if 'name' in shiny_data:
                shiny_data['name'] = self.clean_pokemon_name(shiny_data['name'])

            # Check if exists
            existing = await self.shinies.find_one({
                "user_id": user_id,
                "pokemon_id": shiny_data['pokemon_id']
            })

            if existing:
                # Update existing
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
                return False
            else:
                # Insert new
                shiny_data['user_id'] = user_id
                await self.shinies.insert_one(shiny_data)
                return True

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

        shiny_ids = [s['pokemon_id'] for s in shinies_list]

        # Find existing shinies
        existing_docs = await self.shinies.find(
            {"user_id": user_id, "pokemon_id": {"$in": shiny_ids}},
            {"pokemon_id": 1}
        ).to_list(length=None)

        existing_ids = {doc['pokemon_id'] for doc in existing_docs}

        new_shinies = []
        update_operations = []

        for shiny in shinies_list:
            pid = shiny['pokemon_id']

            if pid not in existing_ids:
                # New shiny
                shiny['user_id'] = user_id
                new_shinies.append(shiny)
            else:
                # Existing - update
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

    # ========================================
    # EVENT SHINY OPERATIONS
    # ========================================

    async def add_event_shiny(self, user_id: int, shiny_data: dict):
        """Add or update a single event shiny"""
        try:
            # Clean the name before storing
            if 'name' in shiny_data:
                shiny_data['name'] = self.clean_pokemon_name(shiny_data['name'])

            # Check if exists
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
                return False
            else:
                # Insert new
                shiny_data['user_id'] = user_id
                await self.event_shinies.insert_one(shiny_data)
                return True

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

    async def get_shiny_by_id(self, user_id: int, pokemon_id: int):
        """Get a specific shiny by pokemon_id"""
        return await self.shinies.find_one({
            "user_id": user_id,
            "pokemon_id": pokemon_id
        })

    async def set_pokemon_nickname(self, user_id: int, pokemon_id: int, nickname: str):
        """Set nickname for a pokemon"""
        await self.shinies.update_one(
            {"user_id": user_id, "pokemon_id": pokemon_id},
            {"$set": {"nickname": nickname}}
        )

    async def get_user_customization(self, user_id: int):
        """Get user customization settings"""
        user_data = await self.get_user_data(user_id)
        settings = user_data.get('settings', {})
        return {
            'background': settings.get('background', 'default.png'),
            'user_title': settings.get('user_title', 'Shiny Hunter')
        }

    async def set_user_customization(self, user_id: int, background: str = None, user_title: str = None):
        """Set user customization settings"""
        updates = {}
        if background:
            updates['background'] = background
        if user_title:
            updates['user_title'] = user_title

        if updates:
            await self.update_settings(user_id, updates)


    # Global database instance
db = Database()
