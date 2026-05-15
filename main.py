import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Get credentials from GitHub Secrets
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

    print("Waiting for Eevee to decrypt... (This may take a few minutes)")

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        # We only care if the bot sends a file (document)
        if event.message.document:
            print("Decryption finished! Downloading file...")
            # Download the file to the current folder
            path = await client.download_media(event.message, file="spotify_decrypted.ipa")
            print(f"Saved to: {path}")
            await client.disconnect()
        elif "Queue" in event.raw_text:
            print(f"Status: {event.raw_text.splitlines()[0]}")

    # The script will stay alive until the file is downloaded and client.disconnect() is called
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
