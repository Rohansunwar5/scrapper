import asyncio
from quart import Quart, request, jsonify
from time import time
import os
import re
from telethon.errors import ChannelInvalidError, ChannelPrivateError
from quart_cors import cors
from telethon.sync import TelegramClient
from datetime import datetime
from dotenv import load_dotenv
from pyppeteer import launch
import random

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
chromium_path = r"C:\Program Files (x86)\chrome-win\chrome.exe"  # Corrected the path variable name

PROXIES = [
    "http://proxy1.com:8000",
    "http://proxy2.com:8000",
    # Add more proxies
]

# Define a list of user agents to randomize
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    # Add more user agents
]

async def get_browser(proxy=None):
    global browser_instance
    if browser_instance is None:
        launch_args = {
            "executablePath": chromium_path,
            "args": ["--no-sandbox"]
        }
        if proxy:
            launch_args["args"].append(f"--proxy-server={proxy}")

        browser_instance = await launch(**launch_args)
    return browser_instance

async def scrape_page(browser, search_query, page_num, proxy=None, retries=3):
    page = await browser.newPage()
    await page.setUserAgent(random.choice(USER_AGENTS))
    s_url = f"https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.q={search_query}&gsc.sort=date&gsc.page={page_num}"
    print(s_url)

    for attempt in range(retries):
        try:
            await page.goto(s_url, {"waitUntil": "networkidle0"})
            await asyncio.sleep(random.uniform(1, 3))
            await page.evaluate('window.scrollBy(0, window.innerHeight / 2)')
            await asyncio.sleep(random.uniform(1, 3))
            await page.evaluate('window.scrollBy(0, window.innerHeight / 2)')

            scraped_links = await page.evaluate(
                """() => {
                    const anchorNodes = document.querySelectorAll('a');
                    const linksArray = Array.from(anchorNodes);
                    const nonEmptyLinks = linksArray
                        .filter(link => link.href && link.href.trim() !== '' && !link.href.startsWith('javascript:void(0)'))
                        .map(link => link.href);

                    return nonEmptyLinks;
                }"""
            )
            await page.close()
            return scraped_links
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    await page.close()
    return []

async def scrape_links(search_query, num_pages=2, proxy=None):
    start_time = time()
    browser = await get_browser(proxy)

    tasks = [scrape_page(browser, search_query, page_num, proxy) for page_num in range(1, num_pages + 1)]
    all_links = await asyncio.gather(*tasks)

    # Flatten the list of lists into a single list
    scraped_links = [link for sublist in all_links for link in sublist]

    print(f"Time taken: {time() - start_time} seconds")
    print("Scraped links:", scraped_links)
    return scraped_links

async def extract_telemetr_channel_names(all_links):
    # Simulate extraction of Telegram channel names
    telemetr_channel_names = {
        match.group(1)
        for url in all_links
        if "telemetr.io" in url
        and (match := re.search(r"telemetr.io/\w+/channels/\d+-(\w+)", url))
    }
    print("TELEMETR CHANNEL NAMES: ", telemetr_channel_names)
    return telemetr_channel_names

async def retrieve_channel_names(search_query):
    try:
        modified_query1 = f'"{search_query}" AND "database" "leak" -telegraph'
        modified_query2 = f'"{search_query}" AND ("database leak" OR "data breach") AND ("hack" OR "database" OR "leak") -telegraph -news'

        print(modified_query1, "\n", modified_query2)

        # Select a random proxy
        proxy = random.choice(PROXIES)

        results1 = await asyncio.gather(
            scrape_links(modified_query1, proxy=proxy), scrape_links(modified_query2, proxy=proxy)
        )

        all_links = [link for sublist in results1 for link in sublist]

        telemetr_channel_names = await extract_telemetr_channel_names(all_links)

        return list(telemetr_channel_names)
    except Exception as e:
        print(e)
        return []

async def fetch_messages_from_channel(client, channel_name, keyword):
    messages_info = []

    try:
        # Fetch messages from the channel
        async for message in client.iter_messages(
            channel_name,
            offset_date=datetime.now(),
            reverse=False,
            limit=5,
            search=keyword,
        ):
            if message.text:
                message_info = {
                    "channel_name": channel_name,
                    "message_id": message.id,
                    "text": message.text,
                    "date": message.date.isoformat(),
                }
                messages_info.append(message_info)

    except ChannelInvalidError:
        print(f"Channel '{channel_name}' is invalid or does not exist.")
    except ChannelPrivateError:
        print(f"Channel '{channel_name}' is private and cannot be accessed.")
    except Exception as e:
        # Handle other generic exceptions
        print(f"An error occurred with channel '{channel_name}': {e}")

    return messages_info

async def retrieve_telegram_messages(search_query):
    try:
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")

        # Fetch channel names concurrently
        channel_names = await retrieve_channel_names(search_query)

        messages_info = []
        async with TelegramClient("saum", api_id, api_hash) as client:
            tasks = [
                fetch_messages_from_channel(client, channel, search_query)
                for channel in channel_names
            ]
            messages_info = await asyncio.gather(*tasks)

        # Flatten the list of lists
        messages_info = [item for sublist in messages_info for item in sublist]

        return {
            "messages_info": messages_info,
        }
    except Exception as e:
        print("error occurred during message retrieval:", e)
        return {"error": "Internal Server Error telegram"}


@app.route("/")
async def home():
    print("working 2")
    return jsonify("HELLO FROM GENERIC Search 2")

@app.route("/api/retrieve-telegram-messages", methods=["POST"])
async def api_retrieve_telegram_messages():
    try:
        form = await request.form
        search_query = form["search_query"]

        print(
            "Telegram Messages retrieved at: ",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        result = await retrieve_telegram_messages(search_query)

        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run()
