import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
session_str = os.environ['TELEGRAM_SESSION']

spotify_url = "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"

bots = [
    "FastDecryptBot",
    "eeveedecrypterbot"
]

MAX_WAIT_SECONDS = 900
CHECK_INTERVAL = 5

async def wait_for_file(client, bot_username):
    print(f"[{bot_username}] Sending App Store URL...")
    
    await client.send_message(bot_username, spotify_url)

    print(f"[{bot_username}] Waiting for IPA response...")

    seen_message_ids = set()

    elapsed = 0

    while elapsed < MAX_WAIT_SECONDS:
        try:
            messages = await client.get_messages(
                bot_username,
                limit=10
            )

            for msg in messages:
                if msg.id in seen_message_ids:
                    continue

                seen_message_ids.add(msg.id)

                if not msg.document:
                    continue

                file_name = msg.file.name

                if not file_name:
                    file_name = f"{bot_username}.ipa"

                if not file_name.lower().endswith(".ipa"):
                    continue

                print(
                    f"[{bot_username}] "
                    f"Downloading: {file_name}"
                )

                await client.download_media(
                    msg,
                    file=file_name
                )

                print(
                    f"[{bot_username}] "
                    f"Download complete."
                )

                return file_name

        except Exception as e:
            print(f"[{bot_username}] Error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)
        elapsed += CHECK_INTERVAL

    print(f"[{bot_username}] Timed out.")

    return None

async def main():
    client = TelegramClient(
        StringSession(session_str),
        api_id,
        api_hash
    )

    await client.start()

    print("Connected to Telegram.")

    tasks = []

    for bot in bots:
        tasks.append(
            asyncio.create_task(
                wait_for_file(client, bot)
            )
        )

    results = await asyncio.gather(*tasks)

    successful_downloads = [
        result for result in results
        if result is not None
    ]

    print("")
    print("========== SUMMARY ==========")
    print(f"Downloaded {len(successful_downloads)} IPA files.")

    for file_name in successful_downloads:
        print(f" - {file_name}")

    if not successful_downloads:
        raise RuntimeError(
            "No IPA files were downloaded."
        )

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
