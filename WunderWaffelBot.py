import asyncio
import random
import json
import os
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import UpdateType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv


# ♡♡♡ Настройки, сенпай! ♡♡♡
INTERVAL_MINUTES = 50

load_dotenv()

TOKEN = os.getenv("TOKEN")
RULE34_API_KEY = os.getenv("RULE34_API_KEY")
RULE34_USER_ID = os.getenv("RULE34_USER_ID")

if not TOKEN:
    raise ValueError("Не найден TOKEN в переменных окружения (.env)!")

LISTENED_CHATS_FILE = "listened_chats.txt"
SPAM_CHATS_FILE = "spam_chats.txt"
CHAT_BLACKLISTS_FILE = "blacklists.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- Работа с хранилищем чатов и блеклистов ---

def load_chats(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("chats", []))
        except Exception as e:
            print(f"[DEBUG] Ошибка чтения {filename}: {e}")
    return set()

def save_chats(chats, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"chats": list(chats)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DEBUG] Ошибка записи {filename}: {e}")

def load_blacklists():
    if os.path.exists(CHAT_BLACKLISTS_FILE):
        try:
            with open(CHAT_BLACKLISTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DEBUG] Ошибка чтения {CHAT_BLACKLISTS_FILE}: {e}")
    return {}

def save_blacklists(data):
    try:
        with open(CHAT_BLACKLISTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DEBUG] Ошибка записи {CHAT_BLACKLISTS_FILE}: {e}")

listened_chats = load_chats(LISTENED_CHATS_FILE)
spam_chats = load_chats(SPAM_CHATS_FILE)
chat_blacklists = load_blacklists()

# Базовый блеклист от нейронок и брака
GLOBAL_BLACKLIST = "-ai_generated -stable_diffusion -midjourney -bad_anatomy -3d"

NSFW_TAGS = {
    "hentai": ("Хентай-артик, очень горяченький~ ууу ♡🔥", "paizuri hentai"),
    "anal": ("Анальное приключение... щёчки горят от стыда! 🔥", "anal"),
    "bj": ("О-орал... я краснею до кончиков ушек! ♡🔥", "oral"),
    "cum": ("Кам-артик... ууу, сенпай, это слишком смущает~ 🔥", "cum_in_ass cum_on_face"),
    "ero": ("Эро, полное соблазна... ууу~ 🔥", "ecchi"),
    "feet": ("Нюхаем ножки... бака, сенпай, извращенец! 🐾🔥", "im_feet barefoot"),
    "femdom": ("Фемдом, властная девочка... трепещи, сенпай! 👑🔥", "femdom pegging"),
    "les": ("Лесбийский мотивчик, нежно и горячо~ ♡🔥", "lesbian threesome"),
    "neko": ("Горячая неко-вайфу, мяу~ ♡🔥", "catgirl nsfw"),
    "solo": ("Соло-артик, только она и её тайные фантазии... ♡🔥", "solo masturbation"),
    "wallpaper": ("Горячий артик на рабочий стол... вау! 🔥", "highres absurd_res")
}

# --- НОВОЕ, РАСШИРЕННОЕ МЕНЮ КАТЕГОРИЙ И ИГР ---
TAG_CATEGORIES = {
    "chars": {
        "title": "🎮 Вселенные & Аниме",
        "tags": {
            "Genshin Impact": "genshin_impact",
            "Honkai Star Rail": "honkai:_star_rail",
            "Blue Archive": "blue_archive",
            "Wuthering Waves": "wuthering_waves",
            "Arknights": "arknights",
            "Azur Lane": "azur_lane",
            "Evangelion": "neon_genesis_evangelion",
            "Fate / Grand Order": "fate/grand_order"
        }
    },
    "mlbb": {
        "title": "⚔️ Mobile Legends: Bang Bang",
        "tags": {
            "Fanny": "fanny_(mobile_legends)",
            "Kagura": "kagura_(mobile_legends)",
            "Guinevere": "guinevere_(mobile_legends)",
            "Lesley": "lesley_(mobile_legends)",
            "Layla": "layla_(mobile_legends)",
            "Alice": "alice_(mobile_legends)",
            "Miya": "miya_(mobile_legends)",
            "Selena": "selena_(mobile_legends)"
        }
    },
    "outfits": {
        "title": "👗 Костюмы & Атрибуты",
        "tags": {
            "🐱 Неко-ушки": "catgirl",
            "🧹 Горничная": "maid",
            "👙 Купальник": "swimsuit",
            "🐰 Зайчик": "bunny_girl",
            "🏫 Школьная форма": "school_uniform",
            "🧦 Чулочки": "thighhighs",
            "🥼 Медсестра": "nurse"
        }
    },
    "actions": {
        "title": "🔥 Действия & Позы",
        "tags": {
            "Пайдзури (Грудь)": "paizuri",
            "Минет": "oral",
            "Анальчик": "anal",
            "Фемдом": "femdom",
            "Соло / Мастурбация": "solo masturbation",
            "Сзади (Doggy)": "doggystyle",
            "Поцелуйчики": "kissing"
        }
    }
}

async def add_to_listened(chat_id):
    if chat_id not in listened_chats:
        listened_chats.add(chat_id)
        save_chats(listened_chats, LISTENED_CHATS_FILE)

def get_chat_blacklist(chat_id):
    str_id = str(chat_id)
    tags = chat_blacklists.get(str_id, [])
    if not tags:
        return ""
    return " " + " ".join([f"-{t}" for t in tags])

# --- Умное форматирование поисковых запросов ---
def format_user_tags(raw_text):
    if not raw_text:
        return ""
    raw_text = raw_text.replace(",", " ")
    parts = raw_text.split()
    formatted = [p.strip().lower() for p in parts if p.strip()]
    return " ".join(formatted)

# --- Работа с API Rule34 ---

async def fetch_single_from_rule34(tags_str, chat_id=None):
    def _request():
        try:
            random_page = random.randint(0, 20)
            custom_ban = get_chat_blacklist(chat_id) if chat_id else ""
            full_tags = f"{tags_str} {GLOBAL_BLACKLIST}{custom_ban}"
            
            url = (
                f"https://api.rule34.xxx/index.php"
                f"?page=dapi&s=post&q=index&json=1"
                f"&tags={full_tags}"
                f"&pid={random_page}&limit=50"
            )
            if RULE34_API_KEY and RULE34_USER_ID:
                url += f"&api_key={RULE34_API_KEY.strip()}&user_id={RULE34_USER_ID.strip()}"

            print(f"[DEBUG] URL запроса: {url}")

            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=6)
            
            print(f"[DEBUG] Статус ответа Rule34: {response.status_code}")

            if response.status_code == 200:
                posts = response.json()
                if isinstance(posts, list) and len(posts) > 0:
                    valid_posts = [p['file_url'] for p in posts if 'file_url' in p and not p['file_url'].endswith(('.webm', '.mp4'))]
                    if valid_posts:
                        chosen = random.choice(valid_posts)
                        print(f"[DEBUG] Успешно найдено изображение: {chosen[:60]}...")
                        return chosen
                else:
                    print(f"[DEBUG] Rule34 вернул пустой ответ для tags: {tags_str}")
            else:
                print(f"[DEBUG] Ошибка Rule34 API: код ответа {response.status_code}")
        except Exception as e:
            print(f"[DEBUG] Ошибка запроса к Rule34: {e}")
        return None

    return await asyncio.to_thread(_request)

async def fetch_image_safely(tag_key, is_nsfw=True, chat_id=None):
    if tag_key in NSFW_TAGS:
        _, r34_tags = NSFW_TAGS[tag_key]
        url = await fetch_single_from_rule34(r34_tags, chat_id=chat_id)
        if url: return url

    formatted_tags = format_user_tags(tag_key)
    url = await fetch_single_from_rule34(formatted_tags, chat_id=chat_id)
    if url: return url

    # Страховка на рандомный NSFW арт, если точный запрос пустой
    if is_nsfw:
        print(f"[DEBUG] По запросу '{tag_key}' ничего не нашлось, включаем страховку на рандом!")
        return await fetch_single_from_rule34("rating:explicit", chat_id=chat_id)
        
    return None

async def send_single_art(chat_id, tag_key="hentai", caption_base="", force_nsfw=False):
    try:
        url_img = await fetch_image_safely(tag_key, is_nsfw=True, chat_id=chat_id)
        if not url_img:
            await bot.send_message(chat_id, "Ууу~ Совсем ничего не нашлось... Прости, ня~ ♡")
            return

        desc_text = NSFW_TAGS.get(tag_key, (f"Поиск: {tag_key}", ""))[0]
        caption = f"{caption_base}{desc_text} (Rule34 🔥)"
        
        more_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔄 Еще арт по этому запросу!", callback_data=f"more_{tag_key[:30]}")
        ]])

        await bot.send_photo(chat_id, url_img, caption=caption, reply_markup=more_keyboard)
    except Exception as e:
        print(f"[DEBUG] Ошибка в send_single_art: {e}")

# --- Клавиатуры Меню и Категорий ---

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Вселенные", callback_data="cat_chars"),
            InlineKeyboardButton(text="⚔️ MLBB Героини", callback_data="cat_mlbb")
        ],
        [
            InlineKeyboardButton(text="👗 Костюмы", callback_data="cat_outfits"),
            InlineKeyboardButton(text="🔥 Действия", callback_data="cat_actions")
        ],
        [
            InlineKeyboardButton(text="🎲 Рандом NSFW", callback_data="cmd_nsfw"),
            InlineKeyboardButton(text="❓ Справка", callback_data="cmd_help")
        ]
    ])

def get_category_keyboard(cat_key):
    category = TAG_CATEGORIES.get(cat_key)
    if not category:
        return get_main_menu_keyboard()

    buttons = []
    row = []
    for label, tag_val in category["tags"].items():
        row.append(InlineKeyboardButton(text=label, callback_data=f"search_{tag_val}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Обработчики Команд ---

def command_handler(func):
    async def wrapper(message: types.Message):
        if message.chat.type in ['group', 'supergroup']:
            await add_to_listened(message.chat.id)
        return await func(message)
    return wrapper

@dp.message(Command("start"))
@dp.message(Command("menu"))
@command_handler
async def cmd_menu(message: types.Message):
    await message.answer("Добро пожаловать в обновленное меню! Выбери вселенную или категорию, сенпай~ ♡", reply_markup=get_main_menu_keyboard())

@dp.message(Command("search"))
@command_handler
async def cmd_search(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Напиши теги после команды через пробел, сенпай!\n"
            "Пример: <code>/search blue_archive swimsuit</code>\n"
            "Или используй /menu для выбора кнопками! ♡",
            parse_mode="HTML"
        )
        return

    raw_query = args[1].strip()
    formatted = format_user_tags(raw_query)

    await message.answer(f"Ищу по запросу: <b>{formatted}</b>... ♡", parse_mode="HTML")
    await send_single_art(message.chat.id, tag_key=raw_query, caption_base="Нашлось: ")

@dp.message(Command("add_ban"))
@command_handler
async def cmd_add_ban(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи тег для бана, сенпай! Пример: /add_ban loli")
        return
    
    ban_tag = args[1].strip().lower().replace("-", "")
    str_chat_id = str(message.chat.id)
    
    if str_chat_id not in chat_blacklists:
        chat_blacklists[str_chat_id] = []
        
    if ban_tag not in chat_blacklists[str_chat_id]:
        chat_blacklists[str_chat_id].append(ban_tag)
        save_blacklists(chat_blacklists)
        await message.answer(f"Тег -{ban_tag} успешно добавлен в блеклист этого чата! ♡")
    else:
        await message.answer("Этот тег уже есть в вашем блеклисте~")

@dp.message(Command("my_ban"))
@command_handler
async def cmd_my_ban(message: types.Message):
    str_chat_id = str(message.chat.id)
    tags = chat_blacklists.get(str_chat_id, [])
    if not tags:
        await message.answer("В этом чате пока нет кастомных забаненных тегов~ ♡")
    else:
        tags_str = ", ".join([f"-{t}" for t in tags])
        await message.answer(f"Забаненные теги в этом чате:\n{tags_str}\n\nОчистить: /clear_ban")

@dp.message(Command("clear_ban"))
@command_handler
async def cmd_clear_ban(message: types.Message):
    str_chat_id = str(message.chat.id)
    if str_chat_id in chat_blacklists:
        chat_blacklists[str_chat_id] = []
        save_blacklists(chat_blacklists)
    await message.answer("Блеклист этого чата успешно очищен! ♡")

@dp.message(Command("help"))
@command_handler
async def cmd_help(message: types.Message):
    help_text = (
        "Кавайный ботик с расширенными играми! ♡\n\n"
        "🎮 Навигация:\n"
        "• /menu — выбор игр, вселенных и поз на кнопках\n"
        "• /search <теги> — комбинированный поиск\n\n"
        "🚫 Персональный Блеклист чата:\n"
        "• /add_ban <тег> — забанить тег в этом чате\n"
        "• /my_ban — посмотреть черный список\n"
        "• /clear_ban — очистить черный список"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())

@dp.message(Command("nsfw"))
@command_handler
async def cmd_nsfw(message: types.Message):
    await send_single_art(message.chat.id, tag_key="random_nsfw", caption_base="Случайная: ", force_nsfw=True)

# --- Обработчик Инлайн-Кнопок ---

@dp.callback_query()
async def process_callback(callback: types.CallbackQuery):
    action = callback.data
    chat_id = callback.message.chat.id
    await callback.answer()

    if action == "menu_main":
        await callback.message.edit_text("Выбери категорию ниже, сенпай~ ♡", reply_markup=get_main_menu_keyboard())
    elif action.startswith("cat_"):
        cat_key = action.replace("cat_", "")
        category = TAG_CATEGORIES.get(cat_key)
        if category:
            await callback.message.edit_text(f"Раздел: <b>{category['title']}</b>\nВыбери тег:", parse_mode="HTML", reply_markup=get_category_keyboard(cat_key))
    elif action.startswith("search_"):
        tag = action.replace("search_", "")
        await callback.message.answer(f"Ищу по тегу: {tag}... ♡")
        await send_single_art(chat_id, tag_key=tag, caption_base="Нашлось: ")
    elif action.startswith("more_"):
        tag = action.replace("more_", "")
        await send_single_art(chat_id, tag_key=tag, caption_base="Еще арт: ")
    elif action == "cmd_nsfw":
        await send_single_art(chat_id, tag_key="random_nsfw", caption_base="Случайная: ", force_nsfw=True)
    elif action == "cmd_help":
        await cmd_help(callback.message)

for tag_name in NSFW_TAGS:
    def make_handler(t):
        @dp.message(Command(t))
        @command_handler
        async def dynamic_tag_cmd(message: types.Message):
            await send_single_art(message.chat.id, tag_key=t)
        return dynamic_tag_cmd
    make_handler(tag_name)

@dp.message(Command("start_spam"))
@command_handler
async def cmd_start_spam(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        spam_chats.add(chat_id)
        save_chats(spam_chats, SPAM_CHATS_FILE)
        await message.answer(f"Няя~! Авто-рассылка включена каждые {INTERVAL_MINUTES} минут ♡")
        if not scheduler.running:
            scheduler.start()

@dp.message(Command("stop_spam"))
@command_handler
async def cmd_stop_spam(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        spam_chats.discard(chat_id)
        save_chats(spam_chats, SPAM_CHATS_FILE)
        await message.answer("Ууу~ Авто-рассылка выключена ♡")

async def scheduled_job():
    for chat_id in list(spam_chats):
        try:
            tag = random.choice(list(NSFW_TAGS.keys()))
            url_img = await fetch_image_safely(tag, is_nsfw=True, chat_id=chat_id)
            if url_img:
                await bot.send_photo(chat_id, url_img, caption=f"Авто-вкусняшка~ ♡ (Rule34 🔥)")
        except Exception as e:
            print(f"[DEBUG] Ошибка спама в {chat_id}: {e}")

async def main():
    print("[DEBUG] Бот запускается...")
    scheduler.add_job(scheduled_job, 'interval', minutes=INTERVAL_MINUTES, id='waifu_spam')
    scheduler.start()
    await dp.start_polling(bot, skip_updates=True, allowed_updates=[UpdateType.MESSAGE, UpdateType.CALLBACK_QUERY])

if __name__ == '__main__':
    print('Пошла родимая <3')
    asyncio.run(main())