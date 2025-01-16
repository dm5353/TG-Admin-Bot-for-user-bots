from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden, YouBlockedUser
from functools import reduce
import logging
import json
import asyncio
import configparser
from AI_Web import talk

# https://my.telegram.org/auth
# -1002386346005

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot_log.log',  # Имя файла для логов
    filemode='a'  # 'a' для добавления логов в конец файла, 'w' для перезаписи
)

with open('accounts.json', 'r') as file:
    config_data = json.load(file)

config = configparser.ConfigParser()
config.read('config.ini')

channel_chat = None
bot = None

reactions = {
    "like": "👍",
    "love": "❤️",
    "fire": "🔥",
    "celebrate": "🎉",
    "happy": "😁",
    "surprised": "😱",
    "excited": "🤩",
    "sad": "😢",
    "dislike": "👎",
    "poop": "💩",
    "sick": "🤮"
}

async def add(index):
    global bot, channel_chat
    if bot is None:
        bot = Client(name=config_data[index]['login'],
                     api_id=config_data[index]['api_id'],
                     api_hash=config_data[index]['api_hash'],
                     phone_number=config_data[index]['phone_number'])
        await bot.start()
    else:
        await bot.start()

    config_data[index]['active'] = "True"
    with open('accounts.json', 'w') as file:
        json.dump(config_data, file, indent=4)

    logging.info(f"Bot started for account index: {index}")

    channel_chats = [config.get('channels', str(i)) for i in range(len(config.options('channels')))]
    channel_filters = [filters.chat(int(channel_chat)) for channel_chat in channel_chats]
    combined_filter = (filters.text | filters.forwarded | filters.reply) & reduce(lambda a, b: a | b, channel_filters)

    @bot.on_message(combined_filter)
    async def comment_and_reaction_on_post(client: Client, message: Message):
        logging.info(f"Received message in channel {message.chat.id}")
        await asyncio.sleep(10)
        try:
            channel_chat = message.chat.id
            chat = await client.get_chat(chat_id=channel_chat)
            if chat.available_reactions:
                try:    
                    text, url = await talk(f"{clean_text(message.text)} Выбери одно из слов и ответь им c маленькой буквы без знаков препинания: 'like', 'love', 'fire', 'celebrate', 'happy', 'surprised', 'excited', 'sad', 'dislike','poop', 'sick'", "https://huggingface.co/chat/conversation/6783e5032ccc87fbdeda6204")
                    emoji = reactions.get(text)
                    await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)
                    logging.info(f"Reaction '{emoji}' sent to message {message.id} in channel {channel_chat}")
                except ChatWriteForbidden:
                    logging.warning("Bot does not have permission to react in this channel.")
                except Exception as e:
                    logging.error(f"Error sending reaction: {e}, Channel ID: {channel_chat}")
            await asyncio.sleep(10)
            if chat.linked_chat:
                try:
                    text, url = await talk(clean_text(message.text), config_data[index]['chat_url'])
                    config_data[index]['chat_url'] = url
                    with open('accounts.json', 'w') as file:
                        json.dump(config_data, file, indent=4)
                    linked_chat_id = chat.linked_chat.id
                    if message.forward_from_chat:
                        async for msg in client.search_messages(linked_chat_id, limit=10, query=clean_text(message.text)):
                            reply_id = msg.id
                            break
                        await client.send_message(chat_id=linked_chat_id, text=text, reply_to_message_id=reply_id)
                        logging.info(f"Comment '{text}' sent to linked chat {linked_chat_id}")
                    elif message.sender_chat:
                        discussion_message = await client.get_discussion_message(chat.id, message.id)
                        await client.send_message(chat_id=linked_chat_id, text=text, reply_to_message_id=discussion_message.id)
                        logging.info(f"Comment '{text}' sent to discussion message {discussion_message.id}")
                except ChatWriteForbidden:
                    logging.warning("Bot does not have permission to comment in this channel.")
                except Exception as e:
                    logging.error(f"Error sending comment: {e}, Channel ID: {channel_chat}")
        except Exception as e:
            logging.error(f"Unhandled error: {e}")
        await asyncio.sleep(10)

    @bot.on_message(filters.reply & filters.text)
    async def handle_reply(client: Client, message: Message):
        logging.info(f"Handling reply from {message.from_user.id} in chat {message.chat.id}")
        if message.from_user and message.from_user.id != client.me.id:
            try:
                text, url = await talk(message.text, config_data[index]['chat_url'])
                config_data[index]['chat_url'] = url
                with open('accounts.json', 'w') as file:
                    json.dump(config_data, file, indent=4)
                await client.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)
                logging.info(f"Reply '{text}' sent to message {message.id}")
            except YouBlockedUser:
                logging.warning("User has blocked the bot, unable to reply.")
            except Exception as e:
                logging.error(f"Error handling reply: {e}")
        await asyncio.sleep(5)

    @bot.on_message(filters.text)
    async def talking(client: Client, message: Message):
        logging.info(f"Received text message in chat {message.chat.id}")
        if message.from_user and message.from_user.id != client.me.id:
            try:
                text, url = await talk(message.text, config_data[index]['chat_url'])
                config_data[index]['chat_url'] = url
                with open('accounts.json', 'w') as file:
                    json.dump(config_data, file, indent=4)
                await client.send_message(chat_id=message.chat.id, text=text)
                logging.info(f"Message '{text}' sent in response to chat {message.chat.id}")
            except Exception as e:
                logging.error(f"Error responding to message: {e}")
        await asyncio.sleep(5)

async def remove(index):
    global bot
    if bot is not None:
        await bot.stop()
        config_data[index]['active'] = "False"
        config_data[index]['chat_url'] = "none"
        with open('accounts.json', 'w') as file:
            json.dump(config_data, file, indent=4)
        bot = None
        logging.info(f"Bot stopped for account index: {index}")

def clean_text(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF).replace('\n', ' ').replace('\r', '').strip()