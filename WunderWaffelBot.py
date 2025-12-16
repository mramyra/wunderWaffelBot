import asyncio
import requests
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ContentType
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ♡♡♡ Настройки, сенпай! ♡♡♡
INTERVAL_MINUTES = 1
TOKEN = "8071968546:AAHflXlR1nkVfIGHdlQSPe3rj4Q---1BQ4g"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

active_chats = set()

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

async def send_random_mixed(chat_id, amount=3, caption_base="", force_nsfw=False):
    try:
        is_nsfw = force_nsfw or random.choice([True, False])
        params_str = f"limit={amount}"
        if is_nsfw:
            params_str += "&is_nsfw=true"
        
        response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=10)
        response.raise_for_status()
        
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
            return
        await bot.send_message(chat_id, "Ууу~ Сегодня API пустенький... Прости, ня~ ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка с API... ♡")
        print(e)

async def send_waifu_by_tag(chat_id, tag, amount=3, caption_base=""):
    try:
        params_str = f"included_tags={tag}&limit={amount}&is_nsfw=true"
        
        response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'images' in data and data['images']:
            for image in data['images']:
                url_img = image['url']
                caption = f"{caption_base}{NSFW_TAGS.get(tag, tag.capitalize())} вкусняшка~ (NSFW 🔥)"
                await bot.send_photo(chat_id, url_img, caption=caption)
            return
        await bot.send_message(chat_id, f"Ууу~ Нет горяченьких артов с тегом {tag} сегодня... ♡")
    except Exception as e:
        await bot.send_message(chat_id, "Ууу~ Ошибочка... ♡")
        print(e)

# Триггер на фото в группах и личке ♡
@dp.message(F.photo)
async def on_photo(message: types.Message):
    await message.reply("Ууу~ Фото? Держи три случайные вкусняшки~ ♡♡♡ (может быть горяченько 🔥)")
    await send_random_mixed(message.chat.id, amount=3, caption_base="Ответ на твоё фото: ")

# /help ♡
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = "<b>Кавайные команды ботика~ ♡</b>\n\n"
    help_text += "<b>NSFW команды по тегам (шлёт 3 горяченьких артика 🔥):</b>\n"
    for tag, desc in NSFW_TAGS.items():
        help_text += f"/{tag} — {desc}\n"
    
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
    await send_random_mixed(message.chat.id, amount=3, caption_base="Горяченькая случайная: ", force_nsfw=True)

# Динамические команды только для NSFW тегов ♡
for tag in NSFW_TAGS:
    @dp.message(Command(tag))
    async def dynamic_tag_cmd(message: types.Message):
        await send_waifu_by_tag(message.chat.id, tag, amount=3, caption_base="")

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
        await message.answer("Ууу~ Периодичка выключена... Но всё остальное работает ♡")

async def scheduled_job():
    for chat_id in list(active_chats):
        try:
            # 50/50 шанс на NSFW или SFW ♡
            if random.choice([True, False]):
                # Горяченький NSFW с случайным тегом
                tag = random.choice(list(NSFW_TAGS.keys()))
                params_str = f"included_tags={tag}&limit=1&is_nsfw=true"
                caption_add = f" (Горяченькая {tag} NSFW 🔥)"
            else:
                # Миленький SFW с тегом waifu
                params_str = "included_tags=waifu&limit=1"
                caption_add = " (Миленькая waifu SFW 🌸)"
            
            response = requests.get(f"https://api.waifu.im/search?{params_str}", timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if 'images' in data and data['images']:
                url_img = data['images'][0]['url']
                caption = f"Авто-вкусняшка каждые {INTERVAL_MINUTES} мин~ ♡{caption_add}"
                await bot.send_photo(chat_id, url_img, caption=caption)
            else:
                await bot.send_message(chat_id, "Ууу~ Сегодня мало вкусняшек по этому тегу... Прости, ня~ ♡")
        except requests.exceptions.HTTPError as http_err:
            await bot.send_message(chat_id, "Ууу~ API немножко капризничает... ♡")
            print(f"HTTP error: {http_err}")
        except Exception as e:
            await bot.send_message(chat_id, "Ууу~ Ошибочка в спаме... ♡")
            print(e)

async def main():
    scheduler.add_job(scheduled_job, 'interval', minutes=INTERVAL_MINUTES, id='waifu_spam')
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())