import os
from dotenv import load_dotenv
import discord
import requests
import asyncio
import time
from flask import Flask
from threading import Thread

# Завантажуємо змінні з .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")  # Токен з .env

# Налаштування Flask
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"  # Текст, що повертається при запиті

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))  # Встановлюємо порт

def keep_alive():
    t = Thread(target=run)
    t.start()

# Discord бот
intents = discord.Intents.default()
client = discord.Client(intents=intents)

COINGECKO_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=stakestone&vs_currencies=usd&include_24hr_change=true'

last_username_update = 0  # час останньої зміни імені
USERNAME_UPDATE_INTERVAL = 3600  # 1 година

async def get_price():
    try:
        response = requests.get(COINGECKO_URL)
        data = response.json()
        price = data['stakestone']['usd']
        change = data['stakestone']['usd_24h_change']
        return price, change
    except Exception as e:
        print("Error fetching price:", e)
        return None, None

async def update_bot():
    await client.wait_until_ready()
    global last_username_update

    while not client.is_closed():
        price, change = await get_price()
        if price is not None and change is not None:
            # Статус (оновлюється завжди)
            change_prefix = "+" if change >= 0 else ""
            status_msg = f"24h: {change_prefix}{change:.2f}% 📈"
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_msg))
            print(f"✅ Status updated to: {status_msg}")

            # Ім’я (оновлюється не частіше ніж раз на годину)
            current_time = time.time()
            if current_time - last_username_update >= USERNAME_UPDATE_INTERVAL:
                new_name = f"$STO | ${price:.4f}"
                try:
                    await client.user.edit(username=new_name)
                    last_username_update = current_time
                    print(f"✅ Bot name updated to: {new_name}")
                except discord.HTTPException as e:
                    print(f"❌ Failed to update name: {e}")

        await asyncio.sleep(300)  # Оновлюємо кожні 5 хвилин

async def main():
    async with client:
        client.loop.create_task(update_bot())
        await client.start(TOKEN)

if __name__ == "__main__":
    keep_alive()  # Запускаємо Flask
    asyncio.run(main())

