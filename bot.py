import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler

TOKEN = "8686950802:AAE3-zhmuvjh2pleOgakEdu3IbJKt2uGJ5o"
CHAT_ID = "7008766363"
API_URL = "https://brmonitoring.onrender.com/api/servers"

last_status = {}
notifications_enabled = True

async def check_servers():
    global last_status, notifications_enabled
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not isinstance(data, list):
                        data = list(data.values())
                    for server in data:
                        online = int(server.get('online', 0))
                        status = 'online' if online > 0 else 'offline'
                        key = f"{server['ip']}:{server['port']}"
                        if key in last_status and last_status[key] != status and notifications_enabled:
                            bot = Bot(token=TOKEN)
                            name = server.get('name', 'Сервер')
                            msg = f"{'🟢 ОТКРЫЛСЯ' if status == 'online' else '🔴 ЗАКРЫЛСЯ'}\n\n📡 {name}\n👥 {online}/{server.get('maxonline',1300)}\n🕐 {datetime.now().strftime('%H:%M:%S')}"
                            await bot.send_message(chat_id=CHAT_ID, text=msg)
                        last_status[key] = status
    except Exception as e:
        print(f"Ошибка: {e}")

async def start(update, context):
    await update.message.reply_text("🤖 Бот работает! Уведомления включены.")

async def status(update, context):
    await update.message.reply_text("🔄 Получаю данные...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, timeout=10) as response:
                data = await response.json()
                if not isinstance(data, list):
                    data = list(data.values())
                online = [s for s in data if int(s.get('online',0)) > 0]
                await update.message.reply_text(f"🟢 Онлайн: {len(online)}/{len(data)}\n👥 Игроков: {sum(int(s.get('online',0)) for s in data)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def on(update, context):
    global notifications_enabled
    notifications_enabled = True
    await update.message.reply_text("🟢 Уведомления включены")

async def off(update, context):
    global notifications_enabled
    notifications_enabled = False
    await update.message.reply_text("🔴 Уведомления выключены")

async def background_check():
    while True:
        await check_servers()
        await asyncio.sleep(30)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("on", on))
    app.add_handler(CommandHandler("off", off))
    asyncio.create_task(background_check())
    print("🤖 Бот запущен!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
