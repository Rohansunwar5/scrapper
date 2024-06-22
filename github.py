import asyncio
from quart import Quart, request, jsonify
from quart_cors import cors
from pyppeteer import launch
from dotenv import load_dotenv
import os
import logging
from time import time

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Allow requests from any origin

load_dotenv()

browser_instance = None
browser_lock = asyncio.Lock()
path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Update this path if needed

async def get_browser():
    global browser_instance
    async with browser_lock:
        if browser_instance is None:
            logging.info("Launching browser...")
            browser_instance = await launch(
                executablePath=path,
                options={"args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-extensions", "--disable-infobars", "--disable-notifications"]}
            )
            logging.info("Browser launched.")
    return browser_instance

async def scrape_search_results(browser, search_query):
    logging.info(f"Scraping search results for query: {search_query}")
    page = await browser.newPage()
    await page.goto("https://cse.google.com/cse?cx=1b053c8ec746d6611", {"waitUntil": "networkidle2"})

    logging.info("Inserting search query and performing search")
    # Insert search query
    await page.type('input.gsc-input', search_query)
    await page.click('button.gsc-search-button-v2')
    await page.waitForSelector('div.gsc-webResult', {"timeout": 5000})

    # Extract search results
    logging.info("Extracting search results")
    results = await page.evaluate('''() => {
        const results = [];
        const items = document.querySelectorAll('div.gsc-webResult div.gs-bidi-start-align.gs-snippet[dir="ltr"]');
        items.forEach(item => {
            results.push(item.innerText);
        });
        return results;
    }''')

    await page.close()
    logging.info(f"Scraped {len(results)} results")
    return results

@app.route("/")
async def home():
    logging.info("Endpoint '/' called")
    response = jsonify("Hello from GitHub Search Scraper")
    return response

@app.route("/api/retrieve-github-links", methods=["POST"])
async def api_retrieve_github_links():
    logging.info("Endpoint '/api/retrieve-github-links' called")
    start_time = time()
    try:
        form = await request.form
        search_query = form["search_query"]
        logging.info(f"Received search query: {search_query}")

        browser = await get_browser()
        results = await scrape_search_results(browser, search_query)

        end_time = time()
        logging.info(f"Time taken to process request: {end_time - start_time} seconds")
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error in '/api/retrieve-github-links': {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    logging.info("Starting the application...")
    app.run()
