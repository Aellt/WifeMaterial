import requests
import random
import vk_api
from vk_api import VkUpload
import telegram
import time
import os

# ==========================
# Настройкu
# ==========================
DANBOORU_TAGS = ["Arknights+rating:q","Zenless_Zone_Zero+rating:q","Genshin_Impact+rating:q",
                 "goddess_of_victory:_nikke+rating:q","wuthering_waves+rating:q",
                 "honkai:_star_rail+rating:q","hololive+rating:q","azur_lane+rating:q",
                 "umamusume+rating:q","touhou+rating:q","fate+rating:q","pokemon+rating:q",
                 "original+rating:q","vocaloid+rating:q","sports_bra+rating:q","girls'_frontline+rating:q",
                 "idolmaster+rating:q","bleach+rating:q","honkai_(series)+rating:q","chainsaw_man+rating:q",
                 "sono_bisque_doll_wa_koi_wo_suru+rating:q","bocchi_the_rock!+rating:q"]

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
        headers = {
          'User-Agent': 'MyWMBot/1.0 (GitHub Actions)'
        }
        r = requests.get(f"https://danbooru.donmai.us/posts.json?tags={random.choice(tags)}&limit=150")
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
        bot.send_photo(chat_id=CHANNEL_ID, photo=img_url, caption=caption[:1024])
        print("Sent to Telegram:", img_url)
    except Exception as e:
        print("Telegram send error:", e)

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
