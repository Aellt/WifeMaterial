import requests
import random
import vk_api
from vk_api import VkUpload
import telegram
import asyncio
import time
import os

# ==========================
# Настройки (оставляем как были)
# ==========================
DANBOORU_TAGS = ["Arknights+rating:q","Zenless_Zone_Zero+rating:q","Genshin_Impact+rating:q",
                 "goddess_of_victory:_nikke+rating:q","wuthering_waves+rating:q",
                 "honkai:_star_rail+rating:q","hololive+rating:q","azur_lane+rating:q",
                 "umamusume+rating:q","touhou+rating:q","fate+rating:q","pokemon+rating:q",
                 "original+rating:q","vocaloid+rating:q","sports_bra+rating:q","girls'_frontline+rating:q",
                 "idolmaster+rating:q","bleach+rating:q","honkai_(series)+rating:q","chainsaw_man+rating:q",
                 "sono_bisque_doll_wa_koi_wo_suru+rating:q","bocchi_the_rock!+rating:q"]

VK_TOKEN = os.environ['VK_TOKEN']
VK_GROUP_ID = 234714085  
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID'] # Лучше брать из env

# ==========================
# Функции
# ==========================

def get_random_post(tags):
    try:
        # Используем kagamihara (прокси Danbooru)
        r = requests.get(f"https://kagamihara.donmai.us/posts.json?tags={random.choice(tags)}&limit=150", timeout=10)
        r.raise_for_status()
        posts = r.json()
        return random.choice(posts) if posts else None
    except Exception as e:
        print("Error getting post:", e)
        return None

def format_caption(post):
    artist = post.get("tag_string_artist", "unknown").replace(" ", ", ")
    copyright_ = post.get("tag_string_copyright", "original").replace(" ", ", ")
    character = post.get("tag_string_character", "").replace(" ", ", ")
    post_url = f"https://danbooru.donmai.us/posts/{post.get('id')}"
    
    caption = f"Author: {artist}\nCopyright: {copyright_}\n"
    if character: caption += f"Character: {character}\n"
    caption += f"\nDanbooru: {post_url}"
    return caption

def send_to_vk(image_path, caption=None):
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        upload = VkUpload(vk_session)
        photo = upload.photo_wall(photos=image_path)[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        vk = vk_session.get_api()
        vk.wall.post(owner_id=-VK_GROUP_ID, attachments=attachment, message=caption or "")
        print("Successfully posted to VK")
    except Exception as e:
        print("VK post error:", e)

async def send_to_telegram(img_url, caption):
    try:
        # В новых версиях библиотеки бот создается и используется асинхронно
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        async with bot:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=img_url, caption=caption[:1024])
            print("Successfully sent to Telegram")
    except Exception as e:
        print("Telegram send error:", e)

async def main():
    post = get_random_post(DANBOORU_TAGS)
    if not post:
        print("No post found")
        return

    img_url = post.get("file_url")
    if not img_url:
        print("No image URL in post")
        return

    caption = format_caption(post)
    
    # Отправка в Telegram (асинхронно)
    await send_to_telegram(img_url, caption)
    
    # Отправка в VK
    img_data = requests.get(img_url).content
    with open("temp.jpg", "wb") as f:
        f.write(img_data)
    
    send_to_vk("temp.jpg", caption)
    if os.path.exists("temp.jpg"):
        os.remove("temp.jpg")

if __name__ == "__main__":
    asyncio.run(main())
