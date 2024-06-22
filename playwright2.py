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
from playwright.async_api import async_playwright, Error as PlaywrightError

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
browser_lock = asyncio.Lock()
SBR_WS_CDP = 'wss://brd-customer-hl_462c03c7-zone-genr2-country-us:ilflyw02w1d6@brd.superproxy.io:9222'
MAX_CONCURRENT_SESSIONS = 40
RETRY_ATTEMPTS = 3
TIMEOUT_MS = 60000  # 60 seconds

invalid_channels = set([
    "snatch_team", "spmias", "lbbotnews", "MEzZKwya_dg4ODM1", "x_legacy",
    "S0D", "ck_nt", "ZLcOzVBENZg2ZWRl", "sipvoip", "thehydramarket",
    "durov", "mrrobothackingstuff", "zerodaylaz", "worlddoctorsalliance","AAAAAE1eCVFTLGzOhkU","AAAAAEyTZ0JoovFxE","deepdatamarket","thevirusss","loljsjsjsjssh","6miLWkw70RxjYmE0","ykoIXVJBirI0NzU0","m4nifest0","GvfPnZMWZEMyMDFl","XLi5D7RLLTBmMjM1","cybertrickszone"
])

async def get_browser():
    global browser_instance
    async with browser_lock:
        if browser_instance is None:
            print("Connecting to Scraping Browser...")
            try:
                playwright = await async_playwright().start()
                browser_instance = await playwright.chromium.connect_over_cdp(SBR_WS_CDP)
                print("Browser connected.")
            except PlaywrightError as e:
                print(f"Error connecting to browser: {e}")
    return browser_instance

async def scrape_page(browser, search_query, page_num, retries=RETRY_ATTEMPTS):
    s_url = f"https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.q={search_query}&gsc.sort=date&gsc.page={page_num}"
    for attempt in range(retries):
        try:
            page = await browser.new_page()
            await page.goto(s_url, wait_until="networkidle", timeout=120000)
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
        except PlaywrightError as e:
            print(f"Error scraping page {page_num} for query '{search_query}', attempt {attempt + 1}: {e}")
            await page.close()
            if attempt == retries - 1:
                return []

async def scrape_links(search_query, num_pages=2):
    browser = await get_browser()
    tasks = [scrape_page(browser, search_query, page_num) for page_num in range(1, num_pages + 1)]
    all_links = await asyncio.gather(*tasks)
    scraped_links = [link for sublist in all_links for link in sublist]
    return scraped_links

async def extract_channel_names(all_links, pattern):
    return {
        match.group(2) for url in all_links if (match := pattern.search(url))
    }

async def retrieve_channel_names(search_query):
    all_links = await scrape_links(search_query)
    tgstat_pattern = re.compile(r"https?://tgstat.com/([^/]+)")
    telegram_pattern = re.compile(r"https?://(t\.me|telegram\.me)/s/([^/?]+)(?:\?[^/]+)?$")
    telemetr_pattern = re.compile(r"telemetr.io/\w+/channels/\d+-(\w+)")

    tgstat_channel_names, telegram_channel_names, telemetr_channel_names = await asyncio.gather(
        extract_channel_names(all_links, tgstat_pattern),
        extract_channel_names(all_links, telegram_pattern),
        extract_channel_names(all_links, telemetr_pattern),
    )

    channel_names = tgstat_channel_names | telegram_channel_names | telemetr_channel_names
    valid_channel_names = [channel for channel in channel_names if channel not in invalid_channels]
    return valid_channel_names

async def fetch_messages_from_channel(client, channel_name, keyword, limit=5):
    messages_info = []
    try:
        async for message in client.iter_messages(
            channel_name,
            offset_date=datetime.now(),
            reverse=False,
            limit=limit,
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
    except (ChannelInvalidError, ChannelPrivateError):
        invalid_channels.add(channel_name)
    except Exception as e:
        invalid_channels.add(channel_name)
    return messages_info

async def retrieve_telegram_messages(search_query, limit=5):
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    channel_names = await retrieve_channel_names(search_query)

    async with TelegramClient("saum", api_id, api_hash) as client:
        tasks = [
            fetch_messages_from_channel(client, channel, search_query, limit)
            for channel in channel_names
        ]
        messages_info = await asyncio.gather(*tasks)
        messages_info = [item for sublist in messages_info if isinstance(sublist, list) for item in sublist]
        return {"messages_info": messages_info}

@app.route("/")
async def home():
    return jsonify("HELLO FROM GENERIC Search 4th dork")

@app.route("/api/retrieve-telegram-messages", methods=["POST"])
async def api_retrieve_telegram_messages():
    try:
        form = await request.form
        search_query = form["search_query"]
        result = await retrieve_telegram_messages(search_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run()
