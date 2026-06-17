import os
import re
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
session_str = os.environ['TELEGRAM_SESSION']
github_token = os.environ['GITHUB_TOKEN']
github_repo = os.environ['GITHUB_REPOSITORY']

spotify_url = "https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"

bots = [
    "FastDecryptBot",
    "eeveedecrypterbot"
]

MAX_WAIT_SECONDS = 900
CHECK_INTERVAL = 5

def clean_filename(filename):
    cleaned = re.sub(r'[-_]v?\d+(?:\.\d+)+', '', filename)
    cleaned = re.sub(r'-+', '-', cleaned)
    return cleaned

def parse_version(v_str):
    return tuple(map(int, re.findall(r'\d+', v_str)))

def get_latest_release():
    headers = {"Authorization": f"token {github_token}"}
    url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    try:
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code == 200:
            tag = res.json().get("tag_name", "v0.0.0")
            return tag.lstrip('v')
    except:
        pass
    return "0.0.0"

async def wait_for_file(client, bot_username, latest_version):
    print(f"[{bot_username}] Sending App Store URL...")
    await client.send_message(bot_username, spotify_url)
    print(f"[{bot_username}] Waiting for IPA response...")
    seen_message_ids = set()
    elapsed = 0
    while elapsed < MAX_WAIT_SECONDS:
        try:
            messages = await client.get_messages(bot_username, limit=10)
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
                version_match = re.search(r'v?(\d+(?:\.\d+)+)', file_name)
                if not version_match:
                    continue
                actual_version = version_match.group(1)
                if parse_version(actual_version) <= parse_version(latest_version):
                    print(f"[{bot_username}] Skipped: version {actual_version} is not higher than latest release {latest_version}")
                    return None
                base_name = os.path.splitext(clean_filename(file_name))[0]
                file_name = f"{base_name}-v{actual_version}-{bot_username}.ipa"
                print(f"[{bot_username}] Downloading: {file_name}")
                await client.download_media(msg, file=file_name)
                print(f"[{bot_username}] Download complete.")
                return file_name
        except Exception as e:
            print(f"[{bot_username}] Error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)
        elapsed += CHECK_INTERVAL
    print(f"[{bot_username}] Timed out.")
    return None

async def main():
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.start()
    print("Connected to Telegram.")
    latest_version = get_latest_release()
    print(f"Latest GitHub release version: {latest_version}")
    tasks = []
    for bot in bots:
        tasks.append(asyncio.create_task(wait_for_file(client, bot, latest_version)))
    results = await asyncio.gather(*tasks)
    successful_downloads = [result for result in results if result is not None]
    print("")
    print("========== SUMMARY ==========")
    print(f"Downloaded {len(successful_downloads)} IPA files.")
    for file_name in successful_downloads:
        print(f" - {file_name}")
    with open(os.environ.get("GITHUB_OUTPUT", "output.txt"), "a") as f:
        f.write(f"downloaded_count={len(successful_downloads)}\n")
        if successful_downloads:
            version_match = re.search(r'-v(\d+(?:\.\d+)+)-', successful_downloads[0])
            if version_match:
                f.write(f"actual_version={version_match.group(1)}\n")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
