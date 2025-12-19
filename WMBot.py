import requests
import random
import vk_api
from vk_api import VkUpload
import telegram
import time
import os

# ==========================
# Настройки
# ==========================
DANBOORU_TAGS = ["Arknights+rating:s","Zenless_Zone_Zero+rating:s","Genshin_Impact+rating:s",
                 "goddess_of_victory:_nikke+rating:s","wuthering_waves+rating:s",
                 "honkai:_star_rail+rating:s","hololive+rating:s","azur_lane+rating:s",
                 "umamusume+rating:s","touhou+rating:s","fate+rating:s""pokemon+rating:s",
                 "original+rating:s","vocaloid+rating:s","sports_bra+rating:s","girls'_frontline+rating:s",
                 "idolmaster+rating:s","bleach+rating:s","honkai_(series)+rating:s","chainsaw_man+rating:s",
                 "sono_bisque_doll_wa_koi_wo_suru+rating:s","bocchi_the_rock!+rating:s"]

# VK
VK_TOKEN = os.environ['VK_TOKEN']
VK_GROUP_ID = 234714085  

# Telegram
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL_ID = -1003291448082

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# ==========================
# Функции
# ==========================

def get_random_post(tags):
    try:
        r = requests.get(f"https://kagamihara.donmai.us/posts.json?tags={random.choice(tags)}&limit=150")
        r.raise_for_status()
        posts = r.json()
        if not posts:
            return None
        return random.choice(posts)
    except Exception as e:
        print("Error getting post:", e)
        return None

def format_caption(post):
    artist = post.get("tag_string_artist", "unknown").replace(" ", ", ")
    copyright_ = post.get("tag_string_copyright", "original").replace(" ", ", ")
    character = post.get("tag_string_character", "").replace(" ", ", ")

    source = post.get("source")
    post_url = f"https://danbooru.donmai.us/posts/{post.get('id')}"

    caption = f"Author: {artist}\nCopyright: {copyright_}\n"
    if character:
        caption += f"Character: {character}\n"
    caption += f"\nDanbooru: {post_url}"
    if source:
        caption += f"\nSource: {source}"
    return caption

def download_image(url, filename="image.jpg", retries=3):
    for i in range(retries):
        try:
            img_data = requests.get(url, timeout=10).content
            with open(filename, "wb") as f:
                f.write(img_data)
            return filename
        except requests.exceptions.RequestException as e:
            print(f"Download attempt {i+1} failed:", e)
            time.sleep(2)
    return None

def send_to_vk(image_path, caption=None):
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        upload = VkUpload(vk_session)
        photo = upload.photo_wall(photos=image_path)[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        vk = vk_session.get_api()
        vk.wall.post(owner_id=-VK_GROUP_ID, attachments=attachment, message=caption or "")
        print("Posted to VK:", image_path)
    except Exception as e:
        print("VK post error:", e)

def send_to_telegram(img_url, caption):
    try:
        # Логируем попытку отправки
        print(f"[Telegram] Пытаюсь отправить: {img_url}")
        
        # Отправка фото
        message = bot.send_photo(
            chat_id=CHANNEL_ID, 
            photo=img_url, 
            caption=caption[:1024], # Обрезка до лимита Telegram
            timeout=30  # Увеличиваем таймаут
        )
        
        # Если дошли сюда, отправка успешна
        print(f"[Telegram] Успешно отправлено! ID сообщения: {message.message_id}")
        return True
        
    except telegram.error.TelegramError as e:
        # Ловим специфичные ошибки Telegram API
        print(f"[Telegram] Критическая ошибка: {e}")
        return False
    except Exception as e:
        # Любые другие ошибки
        print(f"[Telegram] Неизвестная ошибка: {e}")
        return False

# ==========================
# Основной код
# ==========================

post = get_random_post(DANBOORU_TAGS)
if post:
    caption = format_caption(post)
    img_url = post.get("file_url")
    if img_url:
        # Сначала Telegram (можно напрямую через URL)
        send_to_telegram(img_url, caption)
        
        # Для VK нужно скачать
        image_path = download_image(img_url)
        if image_path:
            send_to_vk(image_path, caption)
            os.remove(image_path)
