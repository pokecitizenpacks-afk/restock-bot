import discord
import asyncio
import requests
from bs4 import BeautifulSoup

import os
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1234567150033237545490841689
CHECK_INTERVAL = 60

PRODUCTS = [
    {
        "name": "Prismatic Evolutions ETB - Pokemon Center",
        "url": "https://www.pokemoncenter.com/product/your-product-url",
        "out_of_stock_text": "Out of Stock",
    },
    {
        "name": "Prismatic Evolutions - Target",
        "url": "https://www.target.com/p/your-product-url",
        "out_of_stock_text": "Out of stock",
    },
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
stock_status = {}

async def check_stock():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        for product in PRODUCTS:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(product["url"], headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text()

                in_stock = product["out_of_stock_text"].lower() not in page_text.lower()
                last_status = stock_status.get(product["name"])

                if in_stock and last_status != "in_stock":
                    await channel.send(
                        f"🚨 **RESTOCK ALERT** 🚨\n"
                        f"**{product['name']}** is back in stock!\n"
                        f"{product['url']}"
                    )
                    stock_status[product["name"]] = "in_stock"
                elif not in_stock:
                    stock_status[product["name"]] = "out_of_stock"

            except Exception as e:
                print(f"Error checking {product['name']}: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"Bot running as {client.user}")
    client.loop.create_task(check_stock())

client.run(TOKEN)