import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

api_id = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
session_str = os.environ['TELEGRAM_SESSION']

bot_username = "eeveedecrypterbot"
spotify_url = "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"

async def main():
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.start()
    
    print(f"Sending link to {bot_username}...")
    await client.send_message(bot_username, spotify_url)

    print("Waiting for Eevee to decrypt...")

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        if event.message.document:
            # Grab the original filename sent by the bot (e.g. Spotify_v9.1.48-AppAssassin.ipa)
            original_name = event.message.file.name or "decrypted.ipa"
            print(f"Decryption finished! Original name: {original_name}")
            
            # Download using the exact name preserved
            path = await client.download_media(event.message, file=original_name)
            print(f"Saved directly to: {path}")
            await client.disconnect()
        elif "Queue" in event.raw_text:
            print(f"Status: {event.raw_text.splitlines()[0]}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
