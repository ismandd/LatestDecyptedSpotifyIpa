import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

api_id = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
session_str = os.environ['TELEGRAM_SESSION']

bot_username = "FastDecryptBot"
spotify_url = "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"

async def main():
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.start()
    
    print(f"Sending link to {bot_username}...")
    await client.send_message(bot_username, spotify_url)

    print("Actively checking for response...")
    
    # Loop for 15 minutes max
    for _ in range(180): 
        # Get the last 2 messages in the chat
        messages = await client.get_messages(bot_username, limit=2)
        
        for msg in messages:
            if msg.document:
                original_name = msg.file.name or "decrypted.ipa"
                print(f"Found file! Downloading: {original_name}")
                await client.download_media(msg, file=original_name)
                print("Download complete.")
                return # Exits the script immediately

        # Wait 5 seconds before checking again
        await asyncio.sleep(5) 
        
    print("Timed out waiting for bot.")

if __name__ == "__main__":
    asyncio.run(main())
