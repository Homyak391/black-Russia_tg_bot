import os
import asyncio
import aiohttp
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# ТВОИ ДАННЫЕ (уже вставлены!)
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
                    
                    changes = []
                    
                    for server in data:
                        online = int(server.get('online', 0))
                        status = 'online' if online > 0 else 'offline'
                        name = server.get('name') or server.get('firstname') or 'Сервер'
                        server_key = f"{server['ip']}:{server['port']}"
                        
                        if server_key in last_status:
                            old_status = last_status[server_key]
                            if old_status != status:
                                changes.append({
                                    'name': name,
                                    'old': old_status,
                                    'new': status,
                                    'online': online,
                                    'maxonline': server.get('maxonline', 1300),
                                    'ip': server['ip'],
                                    'port': server['port']
                                })
                        
                        last_status[server_key] = status
                    
                    if changes and notifications_enabled:
                        await send_notifications(changes)
                        
    except Exception as e:
        print(f"Ошибка проверки: {e}")

async def send_notifications(changes):
    bot = Bot(token=TOKEN)
    
    for change in changes:
        if change['new'] == 'online':
            status_emoji = "🟢"
            status_text = "ОТКРЫЛСЯ"
        else:
            status_emoji = "🔴"
            status_text = "ЗАКРЫЛСЯ"
        
        message = f"""{status_emoji} <b>{status_text}</b> {status_emoji}

<b>📡 Сервер:</b> {change['name']}
<b>📍 Адрес:</b> {change['ip']}:{change['port']}
<b>📊 Статус:</b> {change['new'].upper()} ({change['online']}/{change['maxonline']})
<b>🕐 Время:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}

Был {change['old']} → стал {change['new']}"""
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка отправки: {e}")

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🟢 Включить уведомления", callback_data="on")],
        [InlineKeyboardButton("🔴 Выключить уведомления", callback_data="off")],
        [InlineKeyboardButton("📊 Статус всех серверов", callback_data="status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 <b>Black Russia Monitor Bot</b>\n\n"
        "Я слежу за 91 сервером и присылаю уведомления, когда они открываются или закрываются.\n\n"
        "📋 <b>Команды:</b>\n"
        "/start - показать меню\n"
        "/status - текущий статус всех серверов\n"
        "/on - включить уведомления\n"
        "/off - выключить уведомления\n"
        "/stats - статистика работы бота",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def status_command(update, context):
    await update.message.reply_text("🔄 Получаю данные с серверов...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not isinstance(data, list):
                        data = list(data.values())
                    
                    online = [s for s in data if int(s.get('online', 0)) > 0]
                    offline = [s for s in data if int(s.get('online', 0)) == 0]
                    total_players = sum(int(s.get('online', 0)) for s in data)
                    
                    message = f"""📊 <b>СТАТУС СЕРВЕРОВ</b>

🟢 <b>Онлайн:</b> {len(online)} серверов
🔴 <b>Офлайн:</b> {len(offline)} серверов
👥 <b>Всего игроков:</b> {total_players}

<b>🟢 Онлайн серверы (первые 10):</b>
"""
                    for s in online[:10]:
                        message += f"  • {s.get('name')}: {s.get('online')}/{s.get('maxonline')}\n"
                    
                    if len(online) > 10:
                        message += f"\n  ... и ещё {len(online)-10} серверов"
                    
                    await update.message.reply_text(message, parse_mode='HTML')
                    
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def turn_on(update, context):
    global notifications_enabled
    notifications_enabled = True
    await update.message.reply_text("🟢 Уведомления <b>включены</b>", parse_mode='HTML')

async def turn_off(update, context):
    global notifications_enabled
    notifications_enabled = False
    await update.message.reply_text("🔴 Уведомления <b>выключены</b>", parse_mode='HTML')

async def stats_command(update, context):
    total = len(last_status)
    online = sum(1 for s in last_status.values() if s == 'online')
    offline = total - online
    
    message = f"""📈 <b>СТАТИСТИКА БОТА</b>

📡 <b>Отслеживается серверов:</b> {total}
🟢 <b>Онлайн:</b> {online}
🔴 <b>Офлайн:</b> {offline}
🔔 <b>Уведомления:</b> {'Включены' if notifications_enabled else 'Выключены'}

🕐 <b>Бот работает с момента запуска</b>"""
    
    await update.message.reply_text(message, parse_mode='HTML')

async def button_handler(update, context):
    global notifications_enabled
    query = update.callback_query
    await query.answer()
    
    if query.data == "on":
        notifications_enabled = True
        await query.edit_message_text("🟢 Уведомления <b>включены</b>", parse_mode='HTML')
    elif query.data == "off":
        notifications_enabled = False
        await query.edit_message_text("🔴 Уведомления <b>выключены</b>", parse_mode='HTML')
    elif query.data == "status":
        await status_command(update, context)

async def background_check():
    while True:
        await check_servers()
        await asyncio.sleep(30)

async def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("on", turn_on))
    application.add_handler(CommandHandler("off", turn_off))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    asyncio.create_task(background_check())
    
    print("🤖 Бот запущен и следит за серверами...")
    print(f"📡 API: {API_URL}")
    print(f"📨 Уведомления будут приходить в чат: {CHAT_ID}")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())