import asyncio
from quart import Quart, request, jsonify
from time import time
import os
from telethon.errors import ChannelInvalidError, ChannelPrivateError
from quart_cors import cors
from telethon.sync import TelegramClient
from datetime import datetime
from dotenv import load_dotenv

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

custom_channel_names = {
    "breachchat",
    "Cdma66",
    "Blackmarketgermany",
    # "nolivesmatterNLM",
    # "No Lives Matter®",
    # "DivisionNLM",
    "mmcadapter141221",
    "vendettaoperations",
    "leakdataprivate",
    "AnonymousEgypt",
    "Data_Security_Breach",
    "secretforums",
    "noname05716eng",
    "OceanLeak",
    "SiegedSecurity",
    "ransomservice",
    # "DAISY CLOUD [NEW]",
    # "Goblin's Database",
    "8BASE Chat",
    "Akatsuki",
    # "LEAKS AGGREGATOR | УТЕЧКИ АГРЕГАТОР | БАЗЫ ДАННЫХ | СЛИВ |",
    "leakbase_official",
    "AnonymousCyberWarriors",
    "SilentForceMTB",
    "eaglecyberwashere",
    "BLOODYSECC",
    "fckindia",
    "GrabSmtpNow",
    "revolusigbanon17",
    "IRoX_Team",
    "hackingtoolsprvi8",
    "AccountSquadChat",
    "Team_r70YEMEN",
    "GhostSecc",
    "goblins_gang",
    "HacktivistIndonesia",
    "HacktivistPakistan",
    "ganosecteam",
    "MysteriousTeam0",
    "Team_insane_Pakistan",
}

async def fetch_messages_from_channel(client, channel_name, keyword):
    messages_info = []

    try:
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
        print(f"An error occurred with channel '{channel_name}': {e}")

    return messages_info

async def retrieve_telegram_messages(search_query):
    try:
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")

        messages_info = []
        async with TelegramClient("saum", api_id, api_hash) as client:
            tasks = [
                fetch_messages_from_channel(client, channel, search_query)
                for channel in custom_channel_names
            ]
            messages_info = await asyncio.gather(*tasks)

        messages_info = [item for sublist in messages_info for item in sublist]

        return {
            "messages_info": messages_info,
        }
    except Exception as e:
        print("Error occurred during message retrieval:", e)
        return {"error": "Internal Server Error telegram"}

@app.route("/")
async def home():
    print("working")
    return jsonify("HELLO FROM GENERIC Search")

@app.route("/api/retrieve-telegram-messages-group2", methods=["POST"])
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