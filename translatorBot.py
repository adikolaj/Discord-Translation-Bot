# ================================================================================================= #
# File: translatorBot.py
# Author/s: Eduard Kolaj, adikolaj87@gmail.com
#           (name, email)                 
# Last Modified: 01:11 14th May 2025
# Description: Attempt at discord translation bot side project.
#              Uses GoogleTranslator from deep_translator, if that doesn't work will 
#              fallback to using MyMemoryTranslator.
# ================================================================================================= #
import os
import discord
from dotenv import load_dotenv
from deep_translator import GoogleTranslator, MyMemoryTranslator


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

whitelisted_servers_str = os.getenv('WHITELISTED_SERVER_IDS')
WHITELISTED_SERVER_IDS = set()
if whitelisted_servers_str:
    try:
        WHITELISTED_SERVER_IDS = {int(s.strip()) for s in whitelisted_servers_str.split(',')}
    except (TypeError, ValueError):
        print("ERROR: WHITELISTED_SERVER_IDS in .env file must be a comma-separated list of numbers.")
        exit()
else:
    print("ERROR: WHITELISTED_SERVER_IDS not found in .env file.")
    print("Please set WHITELISTED_SERVER_IDS=YOUR_SERVER_ID_1,YOUR_SERVER_ID_2,...")
    exit()

if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in .env file.")
    print("Please ensure DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE is correctly set.")
    exit()

intents = discord.Intents.default()
intents.message_content = True # VERY IMPORTANT: MUST BE ENABLED IN DEV PORTAL
client = discord.Client(intents=intents)




# ================================================================================================= #
#   Functions:
# ================================================================================================= #
async def get_translation(text: str, target_language: str) -> str | None:
    """
    Translates the given text to the target language, trying GoogleTranslator first,
    then falling back to MyMemoryTranslator if Google fails.
    """
    if not text:
        return "The message to translate is empty."

    # Try GoogleTranslator first.
    try:
        print(f"Attempting translation with GoogleTranslator to {target_language}...")
        translator = GoogleTranslator(source='auto', target=target_language)
        translated_text = translator.translate(text)
        if translated_text:
            return translated_text
    except Exception as e:
        print(f"GoogleTranslator failed: {e}. Falling back to MyMemoryTranslator.")

    # Fallback to MyMemoryTranslator.
    try:
        print(f"Attempting translation with MyMemoryTranslator to {target_language}...")
        translator = MyMemoryTranslator(source='auto', target=target_language)
        translated_text = translator.translate(text)
        if translated_text:
            return translated_text
    except Exception as e:
        print(f"MyMemoryTranslator also failed: {e}. Unable to translate.")

    return None # If both fail.

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print(f'Bot is configured for servers: {WHITELISTED_SERVER_IDS}')
    print('------')

@client.event
async def on_message(message):

    print(f"DEBUG: Message received from {message.author} ({message.author.id}) in guild {message.guild} ({message.guild.id if message.guild else 'DM'}): {message.content}")

    if message.author == client.user:
        return

    if message.guild and message.guild.id not in WHITELISTED_SERVER_IDS:
        print(f"Ignoring message from unauthorized server: {message.guild.name} ({message.guild.id})")
        return

    # Check for Reply Command.
    if message.reference and message.reference.message_id:
        command_prefix = "/translate"
        if message.content.lower().startswith(command_prefix):
            parts = message.content.lower().split(' ', 1)
            if len(parts) < 2:
                await message.reply("Usage: `/translate <language_code>` when replying to a message.")
                return

            target_lang = parts[1].strip()

            if len(target_lang) != 2 or not target_lang.isalpha():
                 await message.reply(f"Invalid language code: `{target_lang}`. Please use a 2-letter ISO 639-1 code.")
                 return

            try:
                referenced_message = await message.channel.fetch_message(message.reference.message_id)

                if referenced_message is None:
                    await message.reply("Could not retrieve the original message you replied to. It might be too old or deleted.")
                    return

                text_to_translate = referenced_message.content

                if not text_to_translate:
                    await message.reply("The message you replied to has no text content to translate.")
                    return

                print(f"Translating '{text_to_translate}' to '{target_lang}' from {message.author.display_name} in {message.guild.name}...")
                translated_text = await get_translation(text_to_translate, target_lang)

                if translated_text:
                    await message.reply(
                        f"Translation of {referenced_message.author.mention}'s message to `{target_lang.upper()}`:\n>>> {translated_text}"
                    )
                else:
                    await message.reply(f"Sorry, I couldn't translate that message to `{target_lang}`. Both translation services failed or returned no result.")

            except discord.NotFound:
                await message.reply("The message you replied to could not be found.")
            except discord.Forbidden:
                await message.reply("I don't have permissions to read the message you replied to.")
            except Exception as e:
                print(f"An unexpected error occurred during translation processing: {e}")
                await message.reply(f"An internal error occurred: {e}. Please try again later.")


# --- Run the Bot ---
client.run(TOKEN)

# ================================================================================================= #