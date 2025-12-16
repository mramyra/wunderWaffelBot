import asyncio
import requests
import random
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import UpdateType
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# ♡♡♡ Настройки, сенпай! ♡♡♡
INTERVAL_MINUTES = 0.1


load_dotenv()  # Загружаем секретики ♡

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))


LISTENED_CHATS_FILE = "listened_chats.txt"  # Чаты, где бот реагирует на команды и фото
SPAM_CHATS_FILE = "spam_chats.txt"          # Чаты с включённым спамом

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# Загрузка/сохранение списков
def load_chats(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                chats = set(data.get("chats", []))
                print(f"[DEBUG] Загружено из {filename}: {len(chats)} чатов")
                return chats
        except Exception as e:
            print(f"[DEBUG] Ошибка чтения {filename}: {e}")
    return set()

def save_chats(chats, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"chats": list(chats)}, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] Сохранено в {filename}: {len(chats)} чатов")
    except Exception as e:
        print(f"[DEBUG] Ошибка записи {filename}: {e}")

listened_chats = load_chats(LISTENED_CHATS_FILE)  # Для прослушки команд и фото
spam_chats = load_chats(SPAM_CHATS_FILE)         # Только для периодического спама

# Только NSFW теги для команд по тегам! 🔥
NSFW_TAGS = {
    "ass": "Попки... н-ня, стесняюсь сильно! ♡🔥",
    "hentai": "Хентай-артики, очень горяченькие~ ууу ♡🔥",
    "milf": "Милфы, опытные и соблазнительные... щёчки горят! 🔥",
    "oral": "О-орал... я краснею до кончиков ушек! ♡🔥",
    "paizuri": "П-паизури... бака, сенпай, это так шаловливо~ 🔥",
    "ecchi": "Эччи, чуть-чуть горяченькое~ ♡🔥",
    "ero": "Эро, полное соблазна... ууу~ 🔥"
}

# Функция добавления чата в listened_chats (вызывается при любой команде в группе)
async def add_to_listened(chat_id):
    if chat_id not in listened_chats:
        listened_chats.add(chat_id)
        save_chats(listened_chats, LISTENED_CHATS_FILE)
        print(f"[DEBUG] Чат {chat_id} добавлен в listened_chats (всего: {len(listened_chats)})")

async def send_random_mixed(chat_id, amount=2, caption_base="", force_nsfw=False):
    try:
        is_nsfw = force_nsfw or random.choice([True, False])
        print(f"[DEBUG] send_random_mixed | chat_id={chat_id} | amount={amount} | force_nsfw={force_nsfw} | is_nsfw={is_nsfw}")

        params_str = f"limit={amount}"
        if is_nsfw:
            params_str += "&is_nsfw=true"
        
        response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'images' in data and data['images']:
            for i, image in enumerate(data['images'], 1):
                url_img = image['url']
                caption = f"{caption_base}Случайная вкусняшка~ ♡"
                caption += " (Горяченькая NSFW 🔥)" if is_nsfw else " (Миленькая SFW 🌸)"
                await bot.send_photo(chat_id, url_img, caption=caption)
                print(f"[DEBUG] Отправлено фото {i}/{amount} | url={url_img[:60]}...")
            return
        await bot.send_message(chat_id, "Ууу~ Сегодня API пустенький... Прости, ня~ ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка с API... ♡")
        print(f"[DEBUG] Ошибка в send_random_mixed: {e}")

async def send_waifu_by_tag(chat_id, tag, amount=1, caption_base=""):
    try:
        print(f"[DEBUG] send_waifu_by_tag | chat_id={chat_id} | tag={tag}")
        params_str = f"included_tags={tag}&limit={amount}&is_nsfw=true"
        
        response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'images' in data and data['images']:
            for i, image in enumerate(data['images'], 1):
                url_img = image['url']
                caption = f"{caption_base}{NSFW_TAGS.get(tag, tag.capitalize())} вкусняшка~ (NSFW 🔥)"
                await bot.send_photo(chat_id, url_img, caption=caption)
                print(f"[DEBUG] Отправлено по тегу {tag} ({i}/{amount}) | url={url_img[:60]}...")
            return
        await bot.send_message(chat_id, f"Ууу~ Нет горяченьких артов с тегом {tag} сегодня... ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка... ♡")
        print(f"[DEBUG] Ошибка в send_waifu_by_tag: {e}")

# Триггер на фото — только в прослушиваемых чатах
@dp.message(F.photo)
async def on_photo(message: types.Message):
    if message.chat.type not in ['group', 'supergroup'] or message.chat.id in listened_chats:
        print(f"[DEBUG] Фото от user={message.from_user.id} ({message.from_user.username or 'no_username'}) | chat_id={message.chat.id}")
        await message.reply("Ууу~ Фото? Держи три случайные вкусняшки~ ♡♡♡ (может быть горяченько 🔥)")
        await send_random_mixed(message.chat.id, amount=3, caption_base="Ответ на твоё фото: ")

# Базовый декоратор для всех команд — добавляет чат в listened_chats
def command_handler(func):
    async def wrapper(message: types.Message):
        if message.chat.type in ['group', 'supergroup']:
            await add_to_listened(message.chat.id)
        return await func(message)
    return wrapper

@dp.message(Command("help"))
@command_handler
async def cmd_help(message: types.Message):
    print(f"[DEBUG] Команда /help | chat_id={message.chat.id}")
    help_text = "<b>Кавайные команды ботика~ ♡</b>\n\n"
    help_text += "<b>NSFW команды по тегам (шлёт 1 горяченьких артика 🔥):</b>\n"
    for tag, desc in NSFW_TAGS.items():
        help_text += f"/{tag} — {desc}\n"
    help_text += "\n<b>Другие команды:</b>\n"
    help_text += "/nsfw — 1 случайную горяченькую ♡🔥\n"
    help_text += f"/start_spam — авто-арты каждые {INTERVAL_MINUTES} мин\n"
    help_text += "/stop_spam — выключить авто\n"
    help_text += "/help — это меню~ ♡\n\n"
    help_text += "Кидай фото — получишь 3 случайные (SFW/NSFW)! ♡"
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("nsfw"))
@command_handler
async def cmd_nsfw(message: types.Message):
    print(f"[DEBUG] Команда /nsfw | chat_id={message.chat.id}")
    await send_random_mixed(message.chat.id, amount=1, caption_base="Горяченькая случайная: ", force_nsfw=True)

# Динамические команды по тегам
for tag in NSFW_TAGS:
    @dp.message(Command(tag))
    @command_handler
    async def dynamic_tag_cmd(message: types.Message, tag=tag):
        print(f"[DEBUG] Команда /{tag} | chat_id={message.chat.id}")
        await send_waifu_by_tag(message.chat.id, tag, amount=3, caption_base="")

@dp.message(Command("start_spam"))
@command_handler
async def cmd_start_spam(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("Ууу~ Эта команда только для моего единственного сенпая... Прости, ня~ ♡")
        return
    
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        spam_chats.add(chat_id)
        save_chats(spam_chats, SPAM_CHATS_FILE)
        print(f"[DEBUG] /start_spam от владельца | chat_id={chat_id} | spam_chats: {len(spam_chats)}")
        await message.answer(f"Няя~! Периодичка включена только для тебя, сенпай! Вкусняшки каждые {INTERVAL_MINUTES} минут ♡")
        if not scheduler.running:
            scheduler.start()

@dp.message(Command("stop_spam"))
@command_handler
async def cmd_stop_spam(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("Ууу~ Только мой любимый сенпай может выключить спам... ♡")
        return
    
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        was_in = chat_id in spam_chats
        spam_chats.discard(chat_id)
        save_chats(spam_chats, SPAM_CHATS_FILE)
        print(f"[DEBUG] /stop_spam от владельца | chat_id={chat_id} | было в спаме: {was_in}")
        await message.answer("Ууу~ Периодичка выключена... Только по твоему слову, сенпай ♡")

async def scheduled_job():
    print(f"[DEBUG] Запуск scheduled_job | spam_chats: {len(spam_chats)}")
    for chat_id in list(spam_chats):
        try:
            if random.choice([True, False]):
                tag = random.choice(list(NSFW_TAGS.keys()))
                params_str = f"included_tags={tag}"
                caption_add = f" (Горяченькая {tag} NSFW 🔥)"
            else:
                params_str = "included_tags=waifu"
                caption_add = " (Миленькая waifu SFW 🌸)"
           
            response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=15)
            response.raise_for_status()
           
            data = response.json()
            if 'images' in data and data['images']:
                url_img = data['images'][0]['url']
                caption = f"Авто-вкусняшка каждые {INTERVAL_MINUTES} мин~ ♡{caption_add}"
                await bot.send_photo(chat_id, url_img, caption=caption)
                print(f"[DEBUG] Спам отправлен в {chat_id} | {caption_add}")
            else:
                print(f"[DEBUG] Нет изображений для спама в {chat_id}")
        except Exception as e:
            print(f"[DEBUG] Ошибка спама в {chat_id}: {e}")

async def main():
    print("[DEBUG] Бот запускается...")
    print(f"[DEBUG] listened_chats: {len(listened_chats)} | spam_chats: {len(spam_chats)}")
    scheduler.add_job(scheduled_job, 'interval', minutes=INTERVAL_MINUTES, id='waifu_spam')
    scheduler.start()

    # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: получаем ВСЕ обновления, включая обычные сообщения в группах
    await dp.start_polling(
        bot,
        skip_updates=True,
        allowed_updates=[
            UpdateType.MESSAGE,
            UpdateType.EDITED_MESSAGE,
            UpdateType.CHANNEL_POST,
            UpdateType.EDITED_CHANNEL_POST,
            UpdateType.CALLBACK_QUERY,
        ]
    )

if __name__ == '__main__':
    print('Пошла родимая ♡')
    asyncio.run(main())