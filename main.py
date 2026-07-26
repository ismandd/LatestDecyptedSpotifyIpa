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

DEFAULT_URL = "https://apps.apple.com/dk/app/spotify-music-and-podcasts/id324684580"
app_url = os.environ.get('APP_URL', DEFAULT_URL).strip()
if not app_url:
    app_url = DEFAULT_URL

is_default = (app_url == DEFAULT_URL)

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
    if not is_default:
        return "0.0.0"
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
    await client.send_message(bot_username, app_url)

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
                    file_name = "App.ipa"

                if not file_name.lower().endswith(".ipa"):
                    continue

                version_match = re.search(r'v?(\d+(?:\.\d+)+)', file_name)
                actual_version = version_match.group(1) if version_match else "1.0.0"

                if is_default and parse_version(actual_version) <= parse_version(latest_version):
                    print(f"[{bot_username}] Skipped: version {actual_version} is not higher than latest release {latest_version}")
                    return None

                file_name = clean_filename(file_name)

                print(f"[{bot_username}] Downloading: {file_name}")
                await client.download_media(msg, file=file_name)
                print(f"[{bot_username}] Download complete.")
                return (file_name, actual_version)

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
    if is_default:
        print(f"Latest GitHub release version: {latest_version}")

    tasks = []
    for bot in bots:
        tasks.append(asyncio.create_task(wait_for_file(client, bot, latest_version)))

    results = await asyncio.gather(*tasks)
    successful_downloads = [result for result in results if result is not None]

    print("")
    print("========== SUMMARY ==========")
    print(f"Downloaded {len(successful_downloads)} IPA files.")

    max_version = latest_version
    for file_name, actual_version in successful_downloads:
        print(f" - {file_name} (Version: {actual_version})")
        if parse_version(actual_version) > parse_version(max_version):
            max_version = actual_version

    with open(os.environ.get("GITHUB_OUTPUT", "output.txt"), "a") as f:
        f.write(f"downloaded_count={len(successful_downloads)}\n")
        f.write(f"actual_version={max_version}\n")
        f.write(f"is_default={'true' if is_default else 'false'}\n")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
