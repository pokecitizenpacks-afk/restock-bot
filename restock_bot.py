import discord
import asyncio
import requests
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1500332375454908416
CHECK_INTERVAL = 60

ZIP_CODE = "06790"

PRODUCTS = [
    {
        "name": "Ascended Heroes ETB",
        "tcin": "95082118",
    },
]

STORES = [
    {"id": "2305", "name": "Target", "city": "Torrington"},
    {"id": "2156", "name": "Target", "city": "Waterbury"},
    {"id": "2008", "name": "Target", "city": "Winsted"},
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
stock_status = {}

def check_target_store_stock(tcin, store_id):
    url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
    params = {
        "key": "9f36aeafbe60771e321a7cc95a78140772ab3e96",
        "tcin": tcin,
        "store_id": store_id,
        "zip": ZIP_CODE,
        "state": "CT",
        "latitude": "41.8009",
        "longitude": "-73.1287",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.target.com/p/-/A-{tcin}",
        "Origin": "https://www.target.com",
    }
    proxies = {
        "http": f"http://{os.getenv('PROXY_USER')}:{os.getenv('PROXY_PASS')}@gate.decodo.com:10001",
        "https": f"http://{os.getenv('PROXY_USER')}:{os.getenv('PROXY_PASS')}@gate.decodo.com:10001",
    }
    try:
        response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=15)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        data = response.json()

        product_data = data.get("data", {}).get("product", {})
        fulfillment = product_data.get("fulfillment", {})
        store_options = fulfillment.get("store_options", [])

        for store in store_options:
            if store.get("store_id") == str(store_id):
                in_stock = store.get("order_pickup", {}).get("availability_status", "") == "IN_STOCK"
                qty = store.get("available_to_promise_quantity", 0)
                return in_stock, qty

        return False, 0
    except Exception as e:
        print(f"Error checking stock: {e}")
        return False, 0

async def check_stock():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    print(f"Monitoring {len(STORES)} stores:")
    for store in STORES:
        print(f"  - {store['name']} ({store['city']})")

    while not client.is_closed():
        for product in PRODUCTS:
            for store in STORES:
                try:
                    in_stock, qty = check_target_store_stock(
                        product["tcin"], store["id"]
                    )
                    status_key = f"{product['name']}_{store['id']}"
                    last_status = stock_status.get(status_key)

                    if in_stock and last_status != "in_stock":
                        await channel.send(
                            f"🚨 **IN-STORE RESTOCK ALERT** 🚨\n"
                            f"**{product['name']}** is in stock!\n"
                            f"📍 {store['name']} - {store['city']}\n"
                            f"📦 Quantity: {qty}\n"
                            f"https://www.target.com/p/-/A-{product['tcin']}"
                        )
                        stock_status[status_key] = "in_stock"
                    elif not in_stock:
                        stock_status[status_key] = "out_of_stock"

                except Exception as e:
                    print(f"Error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Bot running as {client.user}")
    client.loop.create_task(check_stock())

client.run(TOKEN)