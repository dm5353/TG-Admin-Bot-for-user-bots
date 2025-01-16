from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import configparser
from Add_Account import add, remove
from AI_Web import login, quit

config = configparser.ConfigParser()
config.read('config.ini')

TELEGRAM_TOKEN = config['telegram']['bot_token']
CHAT_ID = config['telegram']['chat_id']
ADMIN = False

bot = Bot(token=TELEGRAM_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):            # Функция для обработки команды /start
    global CHAT_ID, ADMIN
    if CHAT_ID == "none":
        CHAT_ID = update.message.chat_id
        config.set('telegram', 'chat_id', str(CHAT_ID))
        with open('config.ini', 'w') as configfile:
            config.write(configfile) 
    if str(CHAT_ID) == str(update.message.chat_id):
        ADMIN = True
        message = await bot.send_message(chat_id=CHAT_ID, text="Запуск...")
        await bot.edit_message_text(chat_id=CHAT_ID, message_id=message.message_id, text="Подключение ИИ...")
        await login()
        await bot.edit_message_text(chat_id=CHAT_ID, message_id=message.message_id, text="ИИ подключен")
        await bot.edit_message_text(chat_id=CHAT_ID, message_id=message.message_id, text="Подключение ботов...")
        await add(0)
        await bot.edit_message_text(chat_id=CHAT_ID, message_id=message.message_id, text="Боты подключены")
        await bot.edit_message_text(chat_id=CHAT_ID, message_id=message.message_id, text="Админ-бот работает")
    else:
        await bot.send_message(chat_id=update.message.chat_id, text="Админ-бот не работает: вы не администратор")
        ADMIN = False
async def admin_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):# Функция для обработки команды /add_channel
    if ADMIN:
        if context.args:
            try:
                channel_name = ' '.join(context.args)
                config.set('channels', str(len(config.options('channels'))), channel_name)
                with open('config.ini', 'w') as configfile:
                    config.write(configfile) 
                await bot.send_message(chat_id=CHAT_ID, text=f"Канал {channel_name} добавлен")
            except ValueError:
                await bot.send_message(chat_id=CHAT_ID, text="Ошибка")
        else:
            await bot.send_message(chat_id=CHAT_ID, text="Пожалуйста, укажите название после команды /add_channel")
async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):        # Функция для обработки команды /add
    if ADMIN:
        if context.args:
            try:
                index = int(context.args[0])
                await add(index)
                await bot.send_message(chat_id=CHAT_ID, text=f"Подбот с индексом {index} включен")
            except ValueError:
                await bot.send_message(chat_id=CHAT_ID, text="Индекс должен быть числом")
        else:
            await bot.send_message(chat_id=CHAT_ID, text="Пожалуйста, укажите индекс после команды /add")
async def admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):     # Функция для обработки команды /remove
        if ADMIN:
            try:
                index = int(context.args[0])
                await remove(index)
                await bot.send_message(chat_id=CHAT_ID, text=f"Подбот с индексом {index} выключен")
            except ValueError:
                await bot.send_message(chat_id=CHAT_ID, text="Индекс должен быть числом")
        else:
            await bot.send_message(chat_id=CHAT_ID, text="Пожалуйста, укажите индекс после команды /remove")
async def admin_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):      # Функция для обработки команды /reset
    if ADMIN:
        await bot.send_message(chat_id=CHAT_ID, text="Перезапуск...")
        await remove(0)
        await quit()
        await bot.send_message(chat_id=CHAT_ID, text="Нажмите /start")
async def admin_ai_work(update: Update, context: ContextTypes.DEFAULT_TYPE):    # Функция для обработки команды /ai_work
    if ADMIN:
        await login()
        await bot.send_message(chat_id=CHAT_ID, text="AI вкл")

if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ai_work', admin_ai_work))
    application.add_handler(CommandHandler('add', admin_add))
    application.add_handler(CommandHandler('add_channel', admin_add_channel))
    application.add_handler(CommandHandler('reset', admin_reset))
    application.add_handler(CommandHandler('remove', admin_remove))

    asyncio.run(application.run_polling())