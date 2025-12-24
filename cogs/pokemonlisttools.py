import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import os
import io
from datetime import datetime
from typing import List
from config import EMBED_COLOR, POKETWO_BOT_ID

# Global variables to track active commands
pokemon_lists = {}
monitored_messages = {}


class PokemonListTools(commands.Cog):
    """Pokemon list management and comparison tools"""

    def __init__(self, bot):
        self.bot = bot
        # Load Pokemon names from file
        self.pokemon_names = self._load_pokemon_names()

    # ==================== Pokemon Name Loading ====================

    def _load_pokemon_names(self):
        """Load Pokemon names from pokemonnames.txt"""
        try:
            pokemon_file = 'data/pokemonnames.txt'
            if not os.path.exists(pokemon_file):
                print(f"Warning: {pokemon_file} not found. Pokemon extraction will not work.")
                return []

            with open(pokemon_file, 'r', encoding='utf-8') as f:
                names = [line.strip() for line in f if line.strip()]

            print(f"Loaded {len(names)} Pokemon names")
            return names
        except Exception as e:
            print(f"Error loading Pokemon names: {e}")
            return []

    def _normalize_pokemon_name(self, name):
        """
        Normalize Pokemon names for matching.
        Handles special cases like Nidoran♂/♀ by keeping gender variants distinct.
        """
        if 'nidoran' in name.lower():
            if '♂' in name:
                return 'nidoran♂'
            elif '♀' in name:
                return 'nidoran♀'
        return name.lower()

    def _get_original_pokemon_name(self, normalized_name, original_names):
        """Get the original Pokemon name from the normalized version."""
        if normalized_name == 'nidoran':
            for name in original_names:
                if 'nidoran' in name.lower() and ('♂' in name or '♀' in name):
                    return name

        for name in original_names:
            if self._normalize_pokemon_name(name) == normalized_name:
                return name
        return normalized_name

    def _remove_markdown(self, text):
        """Remove all markdown formatting from text"""
        cleaned = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
        cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned)
        cleaned = re.sub(r'__(.+?)__', r'\1', cleaned)
        cleaned = re.sub(r'_(.+?)_', r'\1', cleaned)
        cleaned = re.sub(r'~~(.+?)~~', r'\1', cleaned)
        cleaned = re.sub(r'`(.+?)`', r'\1', cleaned)
        cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\|\|(.+?)\|\|', r'\1', cleaned)
        return cleaned

    def _create_pokemon_pattern(self, pokemon_name):
        """Create a regex pattern for matching Pokemon names."""
        escaped = re.escape(pokemon_name)
        
        if pokemon_name.endswith('.'):
            escaped = escaped[:-2] + r'\.?'
        
        pattern = r'\b' + escaped + r'(?=\W|$)'
        return pattern

    def _extract_pokemon_from_text(self, text):
        """Extract Pokemon names from any text using the comprehensive method"""
        if not self.pokemon_names:
            return []

        cleaned = self._remove_markdown(text)
        pokemon_found = []
        found_set = set()

        sorted_pokemon = sorted(self.pokemon_names, key=len, reverse=True)
        matched_ranges = []

        for pokemon in sorted_pokemon:
            normalized_pokemon = self._normalize_pokemon_name(pokemon)
            pattern = self._create_pokemon_pattern(pokemon)

            for match in re.finditer(pattern, cleaned, re.IGNORECASE):
                start, end = match.span()

                overlap = False
                for prev_start, prev_end in matched_ranges:
                    if not (end <= prev_start or start >= prev_end):
                        overlap = True
                        break

                if not overlap:
                    if normalized_pokemon not in found_set:
                        original_name = self._get_original_pokemon_name(normalized_pokemon, self.pokemon_names)
                        pokemon_found.append(original_name)
                        found_set.add(normalized_pokemon)
                    matched_ranges.append((start, end))

        return pokemon_found

    def _extract_all_text_from_message(self, message: discord.Message) -> str:
        """Extract all text content from a message including embeds"""
        all_text_parts = []

        if message.content:
            all_text_parts.append(message.content)

        for embed in message.embeds:
            if embed.title:
                all_text_parts.append(embed.title)
            if embed.description:
                all_text_parts.append(embed.description)
            for field in embed.fields:
                if field.name:
                    all_text_parts.append(field.name)
                if field.value:
                    all_text_parts.append(field.value)
            if embed.footer and embed.footer.text:
                all_text_parts.append(embed.footer.text)
            if embed.author and embed.author.name:
                all_text_parts.append(embed.author.name)

        return " ".join(all_text_parts)

    async def _extract_text_from_file(self, attachment: discord.Attachment) -> str:
        """Extract text from a .txt file attachment"""
        if not attachment.filename.endswith('.txt'):
            return ""
        
        try:
            content = await attachment.read()
            return content.decode('utf-8')
        except Exception as e:
            print(f"Error reading file {attachment.filename}: {e}")
            return ""

    # ==================== Event Listeners ====================

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Handle message edits to update Pokemon lists"""
        message_id = after.id
        
        # Handle createlist monitoring
        if message_id in monitored_messages:
            await self._handle_createlist_update(after)

    # ==================== CreateList Command ====================

    @commands.command(name='createlist')
    async def createlist(self, ctx):
        """Create or update a Pokemon list from any message containing Pokemon names"""
        if not ctx.message.reference:
            return await self._send_error(ctx, "Please reply to a message containing Pokemon names!")

        if not self.pokemon_names:
            return await self._send_error(ctx, "Pokemon names database not loaded! Please contact the bot admin.")

        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            
            # Extract all text from the message
            all_text = self._extract_all_text_from_message(replied_message)
            
            # Also check for .txt file attachments
            if replied_message.attachments:
                for attachment in replied_message.attachments:
                    if attachment.filename.endswith('.txt'):
                        file_text = await self._extract_text_from_file(attachment)
                        all_text += " " + file_text
            
            if not all_text.strip():
                return await self._send_error(ctx, "No text content found in the message!")

            # Extract Pokemon names using comprehensive method
            pokemon_names = self._extract_pokemon_from_text(all_text)
            
            if not pokemon_names:
                return await self._send_error(ctx, "No Pokemon names found in the message!")

            # Create or update list
            list_key = f"{ctx.channel.id}_{ctx.author.id}"
            
            if list_key in pokemon_lists:
                await self._update_pokemon_list(ctx, list_key, pokemon_names)
            else:
                await self._create_pokemon_list(ctx, list_key, pokemon_names)

            # Monitor for updates
            monitored_messages[replied_message.id] = {
                'list_key': list_key,
                'user_id': ctx.author.id,
                'channel_id': ctx.channel.id
            }

            # Auto cleanup after 15 seconds
            asyncio.create_task(self._cleanup_list_after_timeout(list_key))

        except Exception as e:
            await self._send_error(ctx, f"An error occurred: {str(e)}")

    # ==================== Remove Command ====================

    @commands.command(name='remove', aliases=['exclude'])
    async def remove(self, ctx, *, pokemon_names: str):
        """
        Remove specific Pokemon from a list and create a new list
        Usage: Reply to a message/file and use ?remove pikachu, charizard, mewtwo
        
        Creates a new list excluding the specified Pokemon.
        Supports message content, embeds, and .txt file attachments.
        """
        if not ctx.message.reference:
            return await self._send_error(ctx, "Please reply to a message containing Pokemon to remove from!")

        if not self.pokemon_names:
            return await self._send_error(ctx, "Pokemon names database not loaded! Please contact the bot admin.")

        try:
            # Fetch the replied message
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Extract Pokemon from the replied message
            found_pokemon = await self._extract_pokemon_from_message(replied_message)

            if not found_pokemon:
                return await self._send_error(ctx, "No Pokemon found in the replied message!")

            # Parse the Pokemon names to remove (comma-separated)
            pokemon_to_remove = [name.strip() for name in pokemon_names.split(',') if name.strip()]

            if not pokemon_to_remove:
                return await self._send_error(ctx, "Please provide Pokemon names to remove, separated by commas!\nExample: `?remove pikachu, charizard, mewtwo`")

            # Normalize Pokemon to remove for comparison
            remove_normalized = set(self._normalize_pokemon_name(p) for p in pokemon_to_remove)

            # Filter out Pokemon that should be removed
            remaining_pokemon = []
            removed_pokemon = []

            for pokemon in found_pokemon:
                normalized = self._normalize_pokemon_name(pokemon)
                if normalized in remove_normalized:
                    removed_pokemon.append(pokemon)
                else:
                    remaining_pokemon.append(pokemon)

            # Remove duplicates while preserving order
            remaining_pokemon = list(dict.fromkeys(remaining_pokemon))
            removed_pokemon = list(dict.fromkeys(removed_pokemon))

            if not remaining_pokemon:
                return await self._send_error(ctx, "No Pokemon would remain after removal! The list would be empty.")

            # Build and send result
            await self._send_remove_result(ctx, remaining_pokemon, removed_pokemon, len(found_pokemon))

        except discord.NotFound:
            await self._send_error(ctx, "Replied message not found!")
        except Exception as e:
            await self._send_error(ctx, f"An error occurred: {str(e)}")

    async def _send_remove_result(self, ctx, remaining: List[str], removed: List[str], original_count: int):
        """Send remove command result with new list"""
        # Create summary embed
        embed = discord.Embed(
            title="🗑️ Pokemon Removed",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📊 Summary",
            value=f"Original: {original_count} Pokemon\nRemoved: {len(removed)} Pokemon\nRemaining: {len(remaining)} Pokemon",
            inline=False
        )

        if removed:
            removed_text = ", ".join(removed)
            embed.add_field(
                name=f"❌ Removed ({len(removed)})",
                value=removed_text if len(removed_text) <= 1024 else removed_text[:1021] + "...",
                inline=False
            )

        # Build the new list
        new_list_text = ", ".join(remaining)

        # If the new list is short, send as message
        if len(new_list_text) <= 1800:
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            await ctx.send(f"**New List ({len(remaining)} Pokemon):**\n{new_list_text}", reference=ctx.message, mention_author=False)
        else:
            # Create a text file for the new list
            file = io.BytesIO(new_list_text.encode('utf-8'))
            discord_file = discord.File(file, filename='filtered_pokemon_list.txt')
            
            await ctx.send(
                embed=embed,
                file=discord_file,
                reference=ctx.message,
                mention_author=False
            )

    # ==================== Check Command ====================

    @commands.command(name='check')
    async def check(self, ctx, *, pokemon_names: str):
        """
        Check if specific Pokemon are in a message
        Usage: Reply to a message and use ?check pikachu, charizard, mewtwo
        
        Shows which Pokemon from your list are found and which are missing.
        Supports message content, embeds, and .txt file attachments.
        """
        if not ctx.message.reference:
            return await self._send_error(ctx, "Please reply to a message to check Pokemon in it!")

        if not self.pokemon_names:
            return await self._send_error(ctx, "Pokemon names database not loaded! Please contact the bot admin.")

        try:
            # Fetch the replied message
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Extract Pokemon from the replied message
            found_pokemon = await self._extract_pokemon_from_message(replied_message)

            if not found_pokemon:
                return await self._send_error(ctx, "No Pokemon found in the replied message!")

            # Parse the Pokemon names to check (comma-separated)
            pokemon_to_check = [name.strip() for name in pokemon_names.split(',') if name.strip()]

            if not pokemon_to_check:
                return await self._send_error(ctx, "Please provide Pokemon names separated by commas!\nExample: `?check pikachu, charizard, mewtwo`")

            # Normalize found Pokemon for comparison
            found_normalized = set(self._normalize_pokemon_name(p) for p in found_pokemon)

            # Check which Pokemon are present and which are missing
            present = []
            missing = []

            for pokemon in pokemon_to_check:
                normalized = self._normalize_pokemon_name(pokemon)
                if normalized in found_normalized:
                    present.append(pokemon)
                else:
                    missing.append(pokemon)

            # Build and send result
            await self._send_check_result(ctx, present, missing, len(found_pokemon))

        except discord.NotFound:
            await self._send_error(ctx, "Replied message not found!")
        except Exception as e:
            await self._send_error(ctx, f"An error occurred: {str(e)}")

    async def _send_check_result(self, ctx, present: List[str], missing: List[str], total_in_message: int):
        """Send check command result"""
        embed = discord.Embed(
            title="🔍 Pokemon Check Results",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📊 Summary",
            value=f"Total Pokemon in message: {total_in_message}\nChecked: {len(present) + len(missing)} Pokemon",
            inline=False
        )

        if present:
            present_text = ", ".join(present)
            embed.add_field(
                name=f"✅ Found ({len(present)})",
                value=present_text if len(present_text) <= 1024 else present_text[:1021] + "...",
                inline=False
            )
        else:
            embed.add_field(
                name=f"✅ Found ({len(present)})",
                value="None",
                inline=False
            )

        if missing:
            missing_text = ", ".join(missing)
            embed.add_field(
                name=f"❌ Missing ({len(missing)})",
                value=missing_text if len(missing_text) <= 1024 else missing_text[:1021] + "...",
                inline=False
            )
        else:
            embed.add_field(
                name=f"❌ Missing ({len(missing)})",
                value="None",
                inline=False
            )

        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    # ==================== Compare Command ====================

    @commands.command(name='compare')
    async def compare(self, ctx, message_id_1: int, message_id_2: int):
        """
        Compare Pokemon between two messages
        Usage: ?compare <message_id_1> <message_id_2>
        
        Shows Pokemon unique to each message and common Pokemon.
        Supports message content, embeds, and .txt file attachments.
        """
        if not self.pokemon_names:
            return await self._send_error(ctx, "Pokemon names database not loaded! Please contact the bot admin.")

        try:
            # Fetch both messages
            message_1 = await ctx.channel.fetch_message(message_id_1)
            message_2 = await ctx.channel.fetch_message(message_id_2)

            # Extract Pokemon from both messages
            pokemon_1 = await self._extract_pokemon_from_message(message_1)
            pokemon_2 = await self._extract_pokemon_from_message(message_2)

            if not pokemon_1 and not pokemon_2:
                return await self._send_error(ctx, "No Pokemon found in either message!")

            # Convert to sets for comparison (normalized names for comparison)
            set_1 = set(self._normalize_pokemon_name(p) for p in pokemon_1)
            set_2 = set(self._normalize_pokemon_name(p) for p in pokemon_2)

            # Find unique and common Pokemon
            only_in_1_normalized = set_1 - set_2
            only_in_2_normalized = set_2 - set_1
            common_normalized = set_1 & set_2

            # Convert back to original names
            only_in_1 = [p for p in pokemon_1 if self._normalize_pokemon_name(p) in only_in_1_normalized]
            only_in_2 = [p for p in pokemon_2 if self._normalize_pokemon_name(p) in only_in_2_normalized]
            common = [p for p in pokemon_1 if self._normalize_pokemon_name(p) in common_normalized]

            # Remove duplicates while preserving order
            only_in_1 = list(dict.fromkeys(only_in_1))
            only_in_2 = list(dict.fromkeys(only_in_2))
            common = list(dict.fromkeys(common))

            # Build result text
            result_text = self._build_compare_result(
                len(pokemon_1), len(pokemon_2),
                only_in_1, only_in_2, common
            )

            # Send result (as message or file)
            await self._send_compare_result(ctx, result_text, 
                                           len(pokemon_1), len(pokemon_2),
                                           len(only_in_1), len(only_in_2), len(common))

        except discord.NotFound:
            await self._send_error(ctx, "One or both message IDs not found in this channel!")
        except Exception as e:
            await self._send_error(ctx, f"An error occurred: {str(e)}")

    async def _extract_pokemon_from_message(self, message: discord.Message) -> List[str]:
        """Extract Pokemon from a message (content, embeds, and files)"""
        all_text = self._extract_all_text_from_message(message)
        
        # Also check for .txt file attachments
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith('.txt'):
                    file_text = await self._extract_text_from_file(attachment)
                    all_text += " " + file_text
        
        return self._extract_pokemon_from_text(all_text)

    def _build_compare_result(self, total_1: int, total_2: int,
                              only_1: List[str], only_2: List[str], 
                              common: List[str]) -> str:
        """Build the comparison result text"""
        sections = []
        
        # Statistics
        sections.append("**📊 Statistics:**")
        sections.append(f"Message 1: {total_1} Pokemon")
        sections.append(f"Message 2: {total_2} Pokemon")
        sections.append(f"Only in Message 1: {len(only_1)} Pokemon")
        sections.append(f"Only in Message 2: {len(only_2)} Pokemon")
        sections.append(f"Common in Both: {len(common)} Pokemon")
        sections.append("")

        # Only in Message 1
        if only_1:
            sections.append("**🔵 Only in Message 1:**")
            sections.append(", ".join(only_1))
            sections.append("")
        else:
            sections.append("**🔵 Only in Message 1:** None")
            sections.append("")

        # Only in Message 2
        if only_2:
            sections.append("**🔴 Only in Message 2:**")
            sections.append(", ".join(only_2))
            sections.append("")
        else:
            sections.append("**🔴 Only in Message 2:** None")
            sections.append("")

        # Common Pokemon
        if common:
            sections.append("**🟢 Common in Both:**")
            sections.append(", ".join(common))
        else:
            sections.append("**🟢 Common in Both:** None")

        return "\n".join(sections)

    async def _send_compare_result(self, ctx, result_text: str, 
                                   total_1: int, total_2: int,
                                   only_1_count: int, only_2_count: int, 
                                   common_count: int):
        """Send comparison result as message or file"""
        # Create summary embed
        embed = discord.Embed(
            title="📊 Pokemon Comparison",
            color=EMBED_COLOR
        )
        embed.add_field(name="Message 1", value=f"{total_1} Pokemon", inline=True)
        embed.add_field(name="Message 2", value=f"{total_2} Pokemon", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="🔵 Only in Message 1", value=f"{only_1_count} Pokemon", inline=True)
        embed.add_field(name="🔴 Only in Message 2", value=f"{only_2_count} Pokemon", inline=True)
        embed.add_field(name="🟢 Common", value=f"{common_count} Pokemon", inline=True)

        # If result fits in message, send directly
        if len(result_text) <= 1900:
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            await ctx.send(result_text, reference=ctx.message, mention_author=False)
        else:
            # Create a text file
            file = discord.File(
                io.BytesIO(result_text.encode('utf-8')),
                filename='pokemon_comparison.txt'
            )
            await ctx.send(
                embed=embed,
                file=file,
                reference=ctx.message,
                mention_author=False
            )

    # ==================== Helper Methods for CreateList ====================

    async def _handle_createlist_update(self, message: discord.Message):
        """Handle updates to monitored createlist messages"""
        list_data = monitored_messages.get(message.id)
        if not list_data:
            return
        
        list_key = list_data['list_key']
        if list_key not in pokemon_lists:
            del monitored_messages[message.id]
            return

        # Extract all text from the updated message
        all_text = self._extract_all_text_from_message(message)
        
        # Also check for .txt file attachments
        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith('.txt'):
                    file_text = await self._extract_text_from_file(attachment)
                    all_text += " " + file_text
        
        if not all_text.strip():
            return

        # Extract Pokemon names using comprehensive method
        new_pokemon_names = self._extract_pokemon_from_text(all_text)
        
        if not new_pokemon_names:
            return

        existing_data = pokemon_lists[list_key]
        added_count = sum(1 for name in new_pokemon_names if name not in existing_data['pokemon'])

        if added_count == 0:
            return

        # Add new pokemon
        existing_data['pokemon'].extend(name for name in new_pokemon_names if name not in existing_data['pokemon'])
        await self._update_list_message(existing_data)
        existing_data['timestamp'] = datetime.now()

    def _split_pokemon_list(self, pokemon_list: List[str]) -> List[str]:
        """Split long pokemon lists into chunks"""
        chunks = []
        current_chunk = []
        current_length = 0

        for pokemon in pokemon_list:
            test_length = current_length + len(pokemon) + 2
            if test_length > 1900 and current_chunk:
                chunks.append(", ".join(current_chunk))
                current_chunk = [pokemon]
                current_length = len(pokemon)
            else:
                current_chunk.append(pokemon)
                current_length = test_length

        if current_chunk:
            chunks.append(", ".join(current_chunk))
        return chunks

    async def _update_list_message(self, list_data: dict):
        """Update the list message with new pokemon"""
        pokemon_list_str = ", ".join(list_data['pokemon'])
        channel = self.bot.get_channel(list_data['channel_id'])
        
        if not channel:
            return

        try:
            if len(pokemon_list_str) > 1900:
                chunks = self._split_pokemon_list(list_data['pokemon'])
                
                # Edit the first message
                await list_data['message'].edit(content=f"**Pokemon List ({len(list_data['pokemon'])} total):**\n{chunks[0]}")
                
                # Get existing continuation messages
                continuation_msgs = list_data.get('continuation_messages', [])
                
                # Update or create continuation messages
                for i, chunk in enumerate(chunks[1:], 2):
                    chunk_index = i - 2  # Index in continuation_messages list
                    
                    if chunk_index < len(continuation_msgs):
                        # Edit existing continuation message
                        try:
                            await continuation_msgs[chunk_index].edit(content=f"**Pokemon List (continued - part {i}):**\n{chunk}")
                        except discord.NotFound:
                            # Message was deleted, create new one
                            new_msg = await channel.send(f"**Pokemon List (continued - part {i}):**\n{chunk}")
                            continuation_msgs[chunk_index] = new_msg
                    else:
                        # Create new continuation message
                        new_msg = await channel.send(f"**Pokemon List (continued - part {i}):**\n{chunk}")
                        continuation_msgs.append(new_msg)
                
                # Delete extra continuation messages if list got shorter
                if len(chunks) - 1 < len(continuation_msgs):
                    for msg in continuation_msgs[len(chunks) - 1:]:
                        try:
                            await msg.delete()
                        except:
                            pass
                    list_data['continuation_messages'] = continuation_msgs[:len(chunks) - 1]
                else:
                    list_data['continuation_messages'] = continuation_msgs
                    
            else:
                # List fits in one message, update main message and delete continuations
                await list_data['message'].edit(content=f"**Pokemon List ({len(list_data['pokemon'])} total):**\n{pokemon_list_str}")
                
                # Delete all continuation messages if they exist
                for msg in list_data.get('continuation_messages', []):
                    try:
                        await msg.delete()
                    except:
                        pass
                list_data['continuation_messages'] = []
        
        except discord.NotFound:
            # Main message was deleted, recreate everything
            if len(pokemon_list_str) > 1900:
                chunks = self._split_pokemon_list(list_data['pokemon'])
                new_message = await channel.send(f"**Pokemon List ({len(list_data['pokemon'])} total):**\n{chunks[0]}")
                list_data['message'] = new_message
                
                continuation_msgs = []
                for i, chunk in enumerate(chunks[1:], 2):
                    new_msg = await channel.send(f"**Pokemon List (continued - part {i}):**\n{chunk}")
                    continuation_msgs.append(new_msg)
                list_data['continuation_messages'] = continuation_msgs
            else:
                new_message = await channel.send(f"**Pokemon List ({len(list_data['pokemon'])} total):**\n{pokemon_list_str}")
                list_data['message'] = new_message
                list_data['continuation_messages'] = []

    async def _create_pokemon_list(self, ctx, list_key: str, pokemon_names: List[str]):
        """Create a new Pokemon list"""
        pokemon_list_str = ", ".join(pokemon_names)
        
        # Create initial message
        list_message = await ctx.channel.send(f"**Pokemon List ({len(pokemon_names)} total):**\n{pokemon_list_str}")

        pokemon_lists[list_key] = {
            'pokemon': pokemon_names.copy(),
            'message': list_message,
            'continuation_messages': [],  # Track continuation messages
            'user_id': ctx.author.id,
            'channel_id': ctx.channel.id,
            'timestamp': datetime.now()
        }

    async def _update_pokemon_list(self, ctx, list_key: str, new_pokemon: List[str]):
        """Update an existing Pokemon list"""
        existing_data = pokemon_lists[list_key]
        added_count = sum(1 for name in new_pokemon if name not in existing_data['pokemon'])

        if added_count > 0:
            existing_data['pokemon'].extend(name for name in new_pokemon if name not in existing_data['pokemon'])
            await self._update_list_message(existing_data)
            
            embed = discord.Embed(
                description=f"✅ Added {added_count} new Pokemon to the list!",
                color=EMBED_COLOR
            )
            await ctx.channel.send(embed=embed)

        existing_data['timestamp'] = datetime.now()

    async def _cleanup_list_after_timeout(self, list_key: str):
        """Clean up list after 15 seconds of inactivity"""
        await asyncio.sleep(15)
        if list_key in pokemon_lists:
            time_diff = (datetime.now() - pokemon_lists[list_key]['timestamp']).total_seconds()
            if time_diff >= 15:
                del pokemon_lists[list_key]
                for msg_id, data in list(monitored_messages.items()):
                    if data['list_key'] == list_key:
                        del monitored_messages[msg_id]

    async def _send_error(self, ctx, message: str):
        """Send error embed"""
        embed = discord.Embed(description=f"❌ {message}", color=EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)

    async def _send_success(self, ctx, message: str):
        """Send success embed"""
        embed = discord.Embed(description=f"✅ {message}", color=EMBED_COLOR)
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(PokemonListTools(bot))
