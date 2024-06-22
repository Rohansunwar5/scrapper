import asyncio
from quart import Quart, request, jsonify
from time import time
import os
from telethon.errors import ChannelInvalidError, ChannelPrivateError, UserAlreadyParticipantError
from quart_cors import cors
from telethon.sync import TelegramClient
from datetime import datetime
from dotenv import load_dotenv
from pyppeteer import launch
from telethon.tl.functions.channels import InviteToChannelRequest

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
path = r"C:\Program Files (x86)\chrome-win\chrome.exe"

# List of channels to scrape messages from
custom_channel_names = {
    "+fcxhFl9JSRE3YTdi", "+9P5FQ85afTc4NGNl", "+V_oM-vx0YnSN7nzH", "+nCFeH8PT-XUxZjEy",
    "+OZheKtZ368YxMDBl", "+ipEzVrjM43NkODc0", "+4atVullEWwsxYTA0", "+GxHjaDP0bOphZjNh",
    "+9ETFYLy5Tc1lNzBh", "+uuz8-qLUNeU2ZmI0", "TheUnderground 4?", "LEAKS AGGREGATOR | УТЕЧКИ АГРЕГАТОР | БАЗЫ ДАННЫХ | СЛИВ |"
}

async def get_browser():
    global browser_instance
    if browser_instance is None:
        browser_instance = await launch(
            executablePath=path,
            options={"args": ["--no-sandbox"]}
        )
    return browser_instance

async def scrape_links(search_query, num_pages=2):
    start_time = time()
    browser = await get_browser()

    async def scrape_page(page_num):
        page = await browser.newPage()
        s_url = f"https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.q={search_query}&gsc.sort=date&gsc.page={page_num}"
        print(s_url)
        await page.goto(s_url, {"waitUntil": "networkidle0"})
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

    tasks = [scrape_page(page_num) for page_num in range(1, num_pages + 1)]
    all_links = await asyncio.gather(*tasks)

    # Flatten the list of lists into a single list
    scraped_links = [link for sublist in all_links for link in sublist]

    print(f"Time taken: {time() - start_time} seconds")
    print("this are", scraped_links[1:-2])
    return scraped_links[1:-2]

async def retrieve_channel_names(search_query):
    try:
        # Create the first modified search query
        modified_query1 = f'"{search_query}" AND "database" "leak" -telegraph'

        # Create the second modified search query
        modified_query2 = f'"{search_query}" AND ("database leak" OR "data breach") AND ("hack" OR "database" OR "leak") -telegraph -news'

        print(modified_query1, "\n", modified_query2)

        # Use asyncio.gather to run both queries concurrently
        results1 = await asyncio.gather(
            scrape_links(modified_query1), scrape_links(modified_query2)
        )
        
        # Merge the results from both queries into a single list
        all_links = [link for sublist in results1 for link in sublist]

        channel_names = custom_channel_names

        return list(channel_names)
    except Exception as e:
        print(e)
        return []

async def fetch_messages_from_channel(client, channel_name, keyword):
    messages_info = []

    try:
        # Get the entity for the channel
        if channel_name.startswith("+"):
            invite_link = f"https://t.me/{channel_name[1:]}"
            channel_entity = await client.get_entity(invite_link)
        else:
            channel_entity = await client.get_entity(channel_name)

        # Fetch messages from the channel
        async for message in client.iter_messages(
            channel_entity,
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
    print("working")
    return jsonify("HELLO FROM GENERIC Search")

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
