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
from telethon.tl.functions.channels import InviteToChannelRequest

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
path = r"C:\Program Files (x86)\chrome-win\chrome.exe" 

custom_channel_names = {
    "BreachedMarketplace/10733",
    "vxunderground",
    "pwn3rzs_chat",
    "+4atVullEWwsxYTA0",
    "SkiddieSec",
    '+9ETFYLy5Tc1lNzBh',
    "DataRecordsShop",
    "DataBreachPremium",
    "CryptoHackers_Market",
    "Trade_With_trust",
    "sixtysixchat",
    "+kqmKctQZnTFiZGM0",
    "ANONYMOUS_CHAT_VIP",
    "seekshell_com",
    "hydramarketrebuild",
    "SMokerFiles",
    "zer0daylab",
    "Deathmatics",
    "illsvcleaksupload",
    "shieldteam1",
    "+fcxhFl9JSRE3YTdi",
    "+OZheKtZ368YxMDBl",
    "+V_oM-vx0YnSN7nzH",
    "bradmax_cloud",
    "expertsa11m",
    "Sl1ddifree",
    "cookiecloudfree",
    "DarkSideCloud",
    "Redscritp",
    "enigmaLogS",
    "ManticoreCloud",
    "cvv190_cloud",
    "BreachedDiscussion1",
    "SiegedSecurity",
    "ransomservice",
    "+uuz8-qLUNeU2ZmI0",
    "+9P5FQ85afTc4NGNl",
    "+GxHjaDP0bOphZjNh",
    "+ipEzVrjM43NkODc0",
    "+nCFeH8PT-XUxZjEy",
    "leakbase_official",
    "shadowleakss",
    "AnonymousCyberWarriors",
    "SilentForceMTB",
    "eaglecyberwashere",
    "BLOODYSECC",
    "fckindia",
    "GrabSmtpNow",
    "revolusigbanon17",
    "IRoX_Team",
    "hackingtoolsprvi8",
    "GHOSTPalestine",
    "AccountSquadChat",
    "Team_r70YEMEN",
    "GhostSecc",
    "leaksploit",
    "goblins_gang",
    "DarkStormTeams",
    "HacktivistIndonesia",
    "HacktivistPakistan",
    "ganosecteam",
    "MysteriousTeam0",
    "Team_insane_Pakistan",
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

# async def extract_tgstat_channel_names(all_links):
#     # Simulate extraction of tgstat channel names
#     tgstat_channel_names = {
#         match.group(1)
#         for url in all_links
#         if "tgstat.com" in url and (match := re.search(r"@([^/]+)", url))
#     }
#     print("TGSTAT Channel Names Fetched:", tgstat_channel_names)
#     return tgstat_channel_names

# async def extract_telegram_channel_names(all_links):
#     # Simulate extraction of Telegram channel names
#     pattern = re.compile(r"https?://(t\.me|telegram\.me)/s/([^/?]+)(?:\?[^/]+)?$")
#     telegram_channel_names = {
#         match.group(2) for url in all_links if (match := pattern.search(url))
#     }
#     print("Telegram Channel Names Fetched:", telegram_channel_names)
#     return telegram_channel_names

# async def extract_telemetr_channel_names(all_links):
    # Simulate extraction of Telegram channel names
    # telemetr_channel_names = {
    #     match.group(1)
    #     for url in all_links
    #     if "telemetr.io" in url
    #     and (match := re.search(r"telemetr.io/\w+/channels/\d+-(\w+)", url))
    # }
    # print("TELEMETR CHANNEL NAMES:", telemetr_channel_names)
    # return telemetr_channel_names

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

        # Extract channel names concurrently
        # tgstat_channel_names = await extract_tgstat_channel_names(all_links)
        # telegram_channel_names = await extract_telegram_channel_names(all_links)
        # telemetr_channel_names = await extract_telemetr_channel_names(all_links)

        # Combine the sets of channel names
        channel_names = custom_channel_names

        # Add custom channel names
        # channel_names |= custom_channel_names

        return list(channel_names)
    except Exception as e:
        print(e)
        return []

async def fetch_messages_from_channel(client, channel_name, keyword):
    messages_info = []

    try:
        # Use the full invite link if the channel name starts with a '+'
        if channel_name.startswith("+"):
            invite_link = f"https://t.me/joinchat/{channel_name[1:]}"
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

        # Sort the result based on the custom channel names priority and date
        # sorted_result = sorted(
        #     result["messages_info"],
        #     key=lambda x: (x["channel_name"] not in custom_channel_names, x["date"]),
        #     reverse=False,
        # )

        # Update the messages_info with the sorted result
        # result["messages_info"] = sorted_result

        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500
