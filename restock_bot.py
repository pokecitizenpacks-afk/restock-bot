import discord
import asyncio
import requests
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 123456789
CHECK_INTERVAL = 60

ZIP_CODE = "06790"

PRODUCTS = [
    {
        "name": "Ascended Heroes ETB",
        "tcin": "95082118",
    },
]

STORES = [
    {"id": "2006", "name": "Target", "city": "Torrington"},
    {"id": "2007", "name": "Target", "city": "Waterbury"},
    {"id": "2008", "name": "Target", "city": "Winsted"},
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
stock_status = {}

def check_target_store_stock(tcin, store_id):
    url = "https://api.brickseek.com/target/inventory"
    params = {
        "sku": tcin,
        "store_id": store_id,
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        data = response.json()
        qty = data.get("quantity", 0)
        return int(qty) > 0, qty
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