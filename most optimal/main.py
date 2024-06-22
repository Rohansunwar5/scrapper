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
from typing import List, Set, Dict, Any, Union

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
browser_lock = asyncio.Lock()
# path = "/usr/bin/google-chrome"  # or the appropriate path for your environment
path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

invalid_channels = set([
    "snatch_team", "spmias", "lbbotnews", "MEzZKwya_dg4ODM1", "x_legacy", 
    "S0D", "ck_nt", "ZLcOzVBENZg2ZWRl", "sipvoip", "thehydramarket", 
    "durov", "mrrobothackingstuff", "zerodaylaz", "worlddoctorsalliance",
    "AAAAAE1eCVFTLGzOhkU","AAAAAEyTZ0JoovFxE","deepdatamarket",
    "thevirusss","loljsjsjsjssh","6miLWkw70RxjYmE0","ykoIXVJBirI0NzU0",
    "m4nifest0","GvfPnZMWZEMyMDFl","XLi5D7RLLTBmMjM1","cybertrickszone"
])

async def get_browser() -> Any:
    global browser_instance
    async with browser_lock:
        if browser_instance is None:
            browser_instance = await launch(
                executablePath=path,
                options={"args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-extensions", "--disable-infobars", "--disable-notifications"]}
            )
    return browser_instance

async def scrape_page(browser: Any, search_query: str, page_num: int) -> List[str]:
    page = await browser.newPage()
    s_url = f"https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.q={search_query}&gsc.sort=date&gsc.page={page_num}"
    await page.goto(s_url, {"waitUntil": "networkidle2"})
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

async def scrape_links(search_query: str, num_pages: int = 2) -> List[str]:
    browser = await get_browser()
    tasks = [scrape_page(browser, search_query, page_num) for page_num in range(1, num_pages + 1)]
    all_links = await asyncio.gather(*tasks)
    scraped_links = [link for sublist in all_links for link in sublist]
    return scraped_links

def extract_channel_names(pattern: re.Pattern, all_links: List[str]) -> Set[str]:
    return {match.group(1) for url in all_links if (match := pattern.search(url))}

async def retrieve_channel_names(search_query: str) -> List[str]:
    try:
        modified_query = f'"{search_query}" AND ("malware" OR "c2") AND ("hack" OR "trojan" OR "leak" OR "stealer") -telegraph -news'
        all_links = await scrape_links(modified_query)
        
        tgstat_pattern = re.compile(r"@([^/]+)")
        telegram_pattern = re.compile(r"https?://(t\.me|telegram\.me)/s/([^/?]+)(?:\?[^/]+)?$")
        telemetr_pattern = re.compile(r"telemetr.io/\w+/channels/\d+-(\w+)")
        
        tgstat_channel_names = extract_channel_names(tgstat_pattern, all_links)
        telegram_channel_names = extract_channel_names(telegram_pattern, all_links)
        telemetr_channel_names = extract_channel_names(telemetr_pattern, all_links)
        
        channel_names = tgstat_channel_names | telegram_channel_names | telemetr_channel_names
        valid_channel_names = [channel for channel in channel_names if channel not in invalid_channels]
        
        return valid_channel_names
    except Exception as e:
        print(f"Error retrieving channel names: {e}")
        return []

async def fetch_messages_from_channel(client: TelegramClient, channel_name: str, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
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
                messages_info.append({
                    "channel_name": channel_name,
                    "message_id": message.id,
                    "text": message.text,
                    "date": message.date.isoformat(),
                })
    except (ChannelInvalidError, ChannelPrivateError) as e:
        invalid_channels.add(channel_name)
    except Exception as e:
        print(f"An error occurred with channel '{channel_name}': {e}")
        invalid_channels.add(channel_name)
    return messages_info

async def retrieve_telegram_messages(search_query: str, limit: int = 5) -> Union[Dict[str, Any], Dict[str, str]]:
    try:
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        channel_names = await retrieve_channel_names(search_query)
        async with TelegramClient("saum", api_id, api_hash) as client:
            tasks = [fetch_messages_from_channel(client, channel, search_query, limit) for channel in channel_names]
            messages_info = await asyncio.gather(*tasks)
        messages_info = [item for sublist in messages_info if isinstance(sublist, list) for item in sublist]
        return {"messages_info": messages_info}
    except Exception as e:
        print(f"Error occurred during message retrieval: {e}")
        return {"error": "Internal Server Error"}

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
