# main_bot.py (الملف النهائي والمُعدل)

import threading
import telebot
import time  # <-- تأكد من وجود السطر ده

# (استيراد المتغيرات)
from config import TELEGRAM_TOKEN, ACCOUNTS
# (استيراد دالة المراقب)
from fb_scraper_custom import watch_groups
# (استيراد دالة تسجيل الأوامر)
from handlers import register_handlers

def polling_loop(bot_instance):
    print("🤖 البوت شغّال ومستني بوستات جديدة...")
    
    # --- (بداية التعديل) ---
    # هنقول للبوت صراحةً إيه التحديثات اللي إحنا عايزينها
    allowed_updates = [
        'message', 
        'edited_message', 
        'callback_query',  # <-- أهم سطر، ده بتاع ضغطات الأزرار
        'inline_query', 
    ]
    
    print(f"📡 (البوت هيبدأ Polling وهيركز على: {allowed_updates})")
    
    bot_instance.infinity_polling(
        timeout=60, 
        long_polling_timeout=60,
        allowed_updates=allowed_updates # <-- إضافة السطر ده
    )
    # --- (نهاية التعديل) ---

if __name__ == "__main__":
    print("⏳ (جاري إنشاء البوت)")
    bot_instance = telebot.TeleBot(TELEGRAM_TOKEN)

    try:
        print("🧹 (جاري مسح أي Webhook قديم...)")
        bot_instance.delete_webhook()
        time.sleep(1)
        
        # --- (تعديل جديد: تنضيف أي تحديثات معلقة) ---
        print("🧹 (جاري مسح أي تحديثات قديمة معلقة عند تليجرام...)")
        # السطر ده بيقرأ كل الرسايل القديمة ويرميها عشان نبدأ على نضافة
        bot_instance.get_updates(offset=-1, timeout=1) 
        # ---------------------------------------------

        me = bot_instance.get_me()
        print(f"✅ (تم الاتصال بنجاح كـ: {me.username})")
    except Exception as e:
        print(f"❌❌❌ فشل الاتصال بتليجرام: {e}")
        print("الرجاء التأكد من صحة التوكن (TELEGRAM_TOKEN).")
        exit()

    print("🤖 (جاري تسجيل الأوامر...)")
    register_handlers(bot_instance)
    
    print("👀 (جاري تشغيل المراقبين)")
    for account_key, storage_file in ACCOUNTS.items():
        threading.Thread(target=watch_groups, args=(bot_instance, account_key, storage_file), daemon=True).start()
    
    polling_loop(bot_instance)