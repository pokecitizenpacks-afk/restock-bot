import discord
import asyncio
import requests
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1500332375454908416  # Your Discord channel ID
CHECK_INTERVAL = 60  # Check every 60 seconds

ZIP_CODE = "06790"  # Your zip code

# Target product TCINs (the internal ID Target uses)
# Find these in the URL of the Target product page
# e.g. target.com/p/-/A-XXXXXXXX <- that number is the TCIN
PRODUCTS = [
    {
        "name": "Ascended Heroes ETB",
        "tcin": "95082118",  # Replace with real TCIN from the URL
    },
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
stock_status = {}

def get_nearby_stores(zip_code):
    url = f"https://redsky.target.com/v3/stores/nearby/{zip_code}"
    params = {
        "limit": 5,
        "within": 25,
        "unit": "mile",
        "key": "ff457966e64d5e877fdbad070f276d18ecec4a01",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        stores = []
        for store in data.get("locations", []):
            stores.append({
                "id": store["location_id"],
                "name": store["location_name"],
                "city": store["address"]["city"],
            })
        return stores
    except Exception as e:
        print(f"Error getting stores: {e}")
        return []

def check_target_store_stock(tcin, store_id):
    url = f"https://redsky.target.com/v3/stores/inventory"
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

    # Get nearby stores once on startup
    print(f"Finding Target stores near {ZIP_CODE}...")
    stores = get_nearby_stores(ZIP_CODE)
    if not stores:
        print("No stores found! Check your zip code.")
        return
    
    print(f"Monitoring {len(stores)} stores:")
    for store in stores:
        print(f"  - {store['name']} ({store['city']})")

    while not client.is_close