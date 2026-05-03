import discord
import asyncio
import requests
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1500332375454908416
CHECK_INTERVAL = 60

PRODUCTS = [
    {
        "name": "Ascended Heroes ETB",
        "tcin": "95082118",
    },
]

# Hardcoded nearby Target stores
# Find yours at target.com/store-locator and copy the number from the URL
STORES = [
    {"id": "2305", "name": "Target", "city": "Torrington"},
    {"id": "2156", "name": "Target", "city": "Waterbury"},
    {"id": "2008", "name": "Target", "city": "Winsted"},
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
stock_status = {}

def check_target_store_stock(tcin, store_id):
    url = "https://redsky.target.com/v3/stores/inventory"
    params = {
        "key": "ff457966e64d5e877fdbad070f276d18ecec4a01",
        "tcins": tcin,
        "store_ids": store_id,
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        products = data.get("products", [])
        for product in products:
            locations = product.get("locations", [])
            for location in locations:
                if location.get("location_id") == str(store_id):
                    qty = location.get("available_to_promise_quantity", 0)
                    return int(qty) > 0, qty
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