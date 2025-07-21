import telebot
import requests
import os
import uuid
import zipfile
import shutil
import xml.etree.ElementTree as ET

TOKEN = "8097520541:AAEe_HlOl0sS6aFTMM9shiCRTA0CMCVSVMM"
bot = telebot.TeleBot(TOKEN)

BASE_DIR = "work"
os.makedirs(BASE_DIR, exist_ok=True)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "👋 أهلاً بك في بوت *كروري فالفيردي*\n\n"
        "📥 أرسل رابط مباشر لملف APK وسأقوم بتحميله وتعديله.",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip().endswith(".apk"))
def handle_apk_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "📥 جاري تحميل ملف APK...")

    try:
        file_id = str(uuid.uuid4())
        work_dir = os.path.join(BASE_DIR, file_id)
        os.makedirs(work_dir, exist_ok=True)

        apk_path = os.path.join(work_dir, "original.apk")
        modified_apk_path = os.path.join(work_dir, "modified.apk")
        extract_dir = os.path.join(work_dir, "extracted")

        # تحميل الملف
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(apk_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # فك الضغط
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # تعديل AndroidManifest.xml
        manifest_path = os.path.join(extract_dir, "AndroidManifest.xml")
        if os.path.exists(manifest_path):
            try:
                tree = ET.parse(manifest_path)
                root = tree.getroot()
                if 'package' in root.attrib:
                    old_package = root.attrib['package']
                    root.attrib['package'] = old_package + ".edited"
                    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ لم أتمكن من تعديل AndroidManifest.xml:\n{e}")

        # تعديل app_name في strings.xml
        strings_path = os.path.join(extract_dir, "res", "values", "strings.xml")
        if os.path.exists(strings_path):
            try:
                tree = ET.parse(strings_path)
                root = tree.getroot()
                for string in root.findall("string"):
                    if string.attrib.get("name") == "app_name":
                        string.text = "كروري فالفيردي 🔥"
                        break
                tree.write(strings_path, encoding="utf-8", xml_declaration=True)
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ لم أتمكن من تعديل strings.xml:\n{e}")

        # إعادة ضغط APK
        with zipfile.ZipFile(modified_apk_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for foldername, subfolders, filenames in os.walk(extract_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zipf.write(file_path, arcname)

        # إرسال APK المعدل
        if os.path.getsize(modified_apk_path) < 49 * 1024 * 1024:
            with open(modified_apk_path, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ APK المعدل جاهز!")
        else:
            bot.send_message(message.chat.id, "❌ الملف المعدل حجمه كبير جدًا ولا يمكن إرساله عبر Telegram.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ:\n{e}")

print("🤖 بوت كروري فالفيردي - يعمل الآن...")
bot.polling()
