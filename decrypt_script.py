import os
import asyncio
from telethon import TelegramClient, events

api_id = os.environ['API_ID']
api_hash = os.environ['API_HASH']
session_str = os.environ['SESSION_STRING']
bot_username = "eeveedecrypterbot"
app_link = "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"

async def main():
    # We use a session string to avoid logging in with a phone code every time
    async with TelegramClient(StringSession(session_str), api_id, api_hash) as client:
        # 1. Send the link to the bot
        await client.send_message(bot_username, app_link)
        
        # 2. Wait for the bot to reply with a document
        @client.on(events.NewMessage(from_users=bot_username))
        async def handler(event):
            if event.message.document:
                print("Downloading decrypted IPA...")
                await client.download_media(event.message, file="spotify_decrypted.ipa")
                print("Done!")
                await client.disconnect()
        
        await client.run_until_disconnected()

asyncio.run(main())
