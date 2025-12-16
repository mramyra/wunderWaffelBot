import asyncio
import requests
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ContentType
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ♡♡♡ Настройки, сенпай! Меняй здесь ♡♡♡
INTERVAL_MINUTES = 30  # Периодичка в минутах~
TOKEN = "8071968546:AAHflXlR1nkVfIGHdlQSPe3rj4Q---1BQ4g"  # Вставь токен от @BotFather!

# ♡♡♡ Запрещённые теги! Ботику никогда их не покажет ♡♡♡
FORBIDDEN_TAGS = ["futanari", "loli", "lolicon", "yaoi", "gay", "femboy", "trap", "transgender", "male", "furry", "shota"]

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

active_chats = set()  # Чаты с включенной периодичкой

# Доступные команды по тегам с описаниями ♡
ALL_TAGS = {
    "waifu": "Классическая вайфу~ ♡",
    "neko": "Милые неко-девочки с ушками! nya~",
    "maid": "Горничные, такие послушные... ууу~ ♡",
    "marin-kitagawa": "Марин Китагава, супер-кавай! ♡",
    "mori-calliope": "Мори Каллиопа, загадочная~",
    "raiden-shogun": "Райден Сёгун, мощная и красивая! ⚡♡",
    "oppai": "Пышные бусики... щёчки горят! ♡",
    "selfies": "Селфи от вайфу~ 📸",
    "uniform": "В униформе, как в школе аниме! ♡",
    "ass": "Попки... н-ня, стесняюсь! ♡",
    "hass": "Очень соблазнительные попки... ууу~ 🔥",
    "hoppai": "Огромные бусики... я краснею! ♡🔥",
    "ecchi": "Эччи-артики, горяченькие~",
    "paizuri": "П-паизури... стесняюсь до ушек! ♡🔥",
}

NSFW_TAGS = ["oppai", "ass", "hass", "hoppai", "ecchi", "paizuri"]

# Функция для добавления запретов в URL ♡
def build_excluded_param():
    if FORBIDDEN_TAGS:
        return "&excluded_tags=" + "+".join(FORBIDDEN_TAGS)
    return ""

async def send_random_mixed(chat_id, amount=3, caption_base=""):
    try:
        is_nsfw = random.choice([True, False])
        url = f"https://api.waifu.im/search/?limit={amount}"
        if is_nsfw:
            url += "&is_nsfw=true"
        url += build_excluded_param()
        
        response = requests.get(url)
        data = response.json()
        if 'images' in data and data['images']:
            for image in data['images']:
                url_img = image['url']
                caption = f"{caption_base}Случайная вкусняшка~ ♡"
                if is_nsfw:
                    caption += " (Горяченькая NSFW 🔥)"
                else:
                    caption += " (Миленькая SFW 🌸)"
                await bot.send_photo(chat_id, url_img, caption=caption)
        else:
            await bot.send_message(chat_id, "Ууу~ Ничего не нашлось с учётом запретов... Прости, ня~ ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка с API... ♡")
        print(e)

async def send_waifu_by_tag(chat_id, tag, amount=3, caption_base=""):
    try:
        is_nsfw = tag in NSFW_TAGS
        url = f"https://api.waifu.im/search/?included_tags={tag}&limit={amount}"
        if is_nsfw:
            url += "&is_nsfw=true"
        url += build_excluded_param()
        
        response = requests.get(url)
        data = response.json()
        if 'images' in data and data['images']:
            for image in data['images']:
                url_img = image['url']
                caption = f"{caption_base}{ALL_TAGS.get(tag, tag.capitalize())} вкусняшка~ ♡"
                if is_nsfw:
                    caption += " (NSFW 🔥)"
                await bot.send_photo(chat_id, url_img, caption=caption)
        else:
            await bot.send_message(chat_id, f"Ууу~ Нет артов с тегом {tag}... Прости ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка... ♡")
        print(e)

# Триггер на фото ♡
@dp.message(lambda message: message.content_type == ContentType.PHOTO)
async def on_photo(message: types.Message):
    await message.reply("Ууу~ Фото? Держи три случайные вкусняшки~ ♡♡♡ (может быть горяченько 🔥)")
    await send_random_mixed(message.chat.id, amount=3, caption_base="Ответ на твоё фото: ")

# /help ♡
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = "<b>Кавайные команды ботика~ ♡</b>\n\n"
    help_text += "<b>Команды по тегам (шлёт 3 артика):</b>\n"
    for tag, desc in ALL_TAGS.items():
        emoji = "🔥" if tag in NSFW_TAGS else "🌸"
        help_text += f"/{tag} — {desc} {emoji}\n"
    
    help_text += "\n<b>Другие команды:</b>\n"
    help_text += "/nsfw — 3 случайные горяченькие ♡🔥\n"
    help_text += f"/start_spam — авто-арты каждые {INTERVAL_MINUTES} мин\n"
    help_text += "/stop_spam — выключить авто\n"
    help_text += "/help — это меню~ ♡\n\n"
    help_text += "Кидай фото — получишь 3 случайные (SFW/NSFW)! ♡"
    
    await message.answer(help_text, parse_mode="HTML")

# /nsfw ♡
@dp.message(Command("nsfw"))
async def cmd_nsfw(message: types.Message):
    await send_random_mixed(message.chat.id, amount=3, caption_base="Горяченькая случайная: ")

# Динамические команды по тегам ♡ (исправлено для aiogram 3.x!)
for tag in ALL_TAGS:
    async def tag_handler(message: types.Message):
        await send_waifu_by_tag(message.chat.id, tag, amount=3, caption_base="")
    
    dp.message.register(tag_handler, Command(commands=[tag]))

# Периодичка ♡
@dp.message(Command("start_spam"))
async def cmd_start_spam(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        active_chats.add(chat_id)
        await message.answer(f"Няя~! Периодичка включена! Вкусняшки каждые {INTERVAL_MINUTES} минут ♡")
        if not scheduler.running:
            scheduler.start()

@dp.message(Command("stop_spam"))
async def cmd_stop_spam(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        active_chats.discard(chat_id)
        await message.answer("Ууу~ Периодичка выключена... Но триггер и команды работают ♡")

async def scheduled_job():
    for chat_id in list(active_chats):
        await send_random_mixed(chat_id, amount=1, caption_base=f"Авто-вкусняшка каждые {INTERVAL_MINUTES} мин~ ")

async def main():
    scheduler.add_job(scheduled_job, 'interval', minutes=INTERVAL_MINUTES, id='waifu_spam')
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())