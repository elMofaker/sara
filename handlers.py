# handlers.py (الملف الكامل والصحيح)

from playwright.sync_api import sync_playwright
import time
from telebot import types
import random
# استيراد من ملفات المشروع
from config import ACCOUNTS , TELEGRAM_CHAT_ID
from state import active_replies, pending_comments, pending_messages
# (تعديل) هنستورد دوال الكلمات المفتاحية من هنا
from keywords_handler import load_keywords, save_keywords
def get_account_content(account_key):
    """
    هذه الدالة تنشئ محتوى تعليق ورسالة مختلف لكل حساب.
    (account_key) هو مثلاً "account_Youssef"
    """
    # استخراج الاسم من المفتاح (مثل "Youssef")
    name = account_key.replace("account_", "").title()
    
    # --- 1. إنشاء نص الرسالة الخاصة ---
    # (استخدمت القالب الذي أرسلته)
    message_text = f"""💙 السلام عليكم،
    🤍 أنا {name} الفضالي مطور برمجيات 👨‍💻

    💙 تقدر تطّلع على أعمالنا من هنا:
    🔗 elmofaker.com

    🤍 منتظر تواصلك معانا من خلال:-

    💬 واتساب :
    wa.me/+201021170207

    📧 ايميل :
    info@elmofaker.com

    💙 بانتظار حضرتك،"""
    
    
    
    # --- 2. إنشاء نص التعليق (بشكل عشوائي) ---
    # (يمكنك إضافة أي عدد من التعليقات هنا ليختار منها)
    possible_comments = [
        f"بالتوفيق يا غالي! (معك {name} الفضالي)",
      
        "مهتم بالتفاصيل.",
        f"شركة المفكر بتقدم أفضل الحلول البرمجية.   {name} ",
        f"مطور برمجيات  {name}  جاهز لخدمتك، تواصل معنا."
       
    ]
    # اختر تعليق عشوائي واحد
    comment_text = random.choice(possible_comments)
    
    return comment_text, message_text


def post_comment_playwright(storage_file, post_url, comment_text):
    """
    دالة مستقلة لنشر تعليق باستخدام Playwright.
    """
    print(f"PLAYWRIGHT: Attempting to post comment...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # (اجعلها False لرؤية المتصفح)
        ctx = browser.new_context(storage_state=storage_file)
        page = ctx.new_page()
        page.goto(post_url, timeout=60000)
        page.wait_for_timeout(3000)
        for _ in range(3):
            page.evaluate("window.scrollBy(0, window.innerHeight);")
            page.wait_for_timeout(1000)
        
        comment_box_locator = page.locator(
            'div[aria-label="اكتب تعليقًا عامًا..."],'
            'div[aria-label="Write a public comment..."],'
            'div[role="textbox"][contenteditable="true"]'
        )
        if comment_box_locator.count() == 0:
            browser.close()
            raise Exception("لم أجد مربع كتابة التعليق.")
        
        comment_box = comment_box_locator.first
        comment_box.click()
        page.wait_for_timeout(1000)
        comment_box.fill(comment_text)
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
        browser.close()
    print(f"PLAYWRIGHT: Comment posted successfully.")


def send_message_playwright(storage_file, profile_url, msg_text):
    """
    دالة مستقلة لإرسال رسالة خاصة باستخدام Playwright.
    """
    print(f"PLAYWRIGHT: Attempting to send message...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # (اجعلها False لرؤية المتصفح)
        ctx = browser.new_context(storage_state=storage_file)
        page = ctx.new_page()
        
        if "/user/" in profile_url:
            username = profile_url.split('/user/')[1].split('/')[0]
        else:
            username = profile_url.rstrip('/').split('/')[-1]
            if "profile.php?id=" in username:
                 username = username.split("profile.php?id=")[1]
                 
        msg_url = f"https://www.facebook.com/messages/t/{username}"
        print(f"Navigating to Messenger: {msg_url}")
        page.goto(msg_url, timeout=60000)
        
        input_box_locator = page.locator('div[aria-label="رسالة"][contenteditable="true"]')
        input_box_locator.wait_for(timeout=20000)
        
        input_box = input_box_locator.first
        input_box.scroll_into_view_if_needed()
        input_box.click()
        page.wait_for_timeout(500)
        input_box.fill(msg_text)
        page.wait_for_timeout(500)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000) 
        browser.close()
    print(f"PLAYWRIGHT: Message sent successfully.")


def perform_automated_actions(bot, post_url, profile_url):
    """
    هذه الدالة هي (الروبوت) الذي يعمل في الخلفية (في Thread).
    يقوم بالمرور على كل الحسابات ونشر التعليقات والرسائل مع فواصل زمنية.
    """
    
    # (تأكد أن ACCOUNTS و TELEGRAM_CHAT_ID مُعرفة كـ global في ملفك)
    global ACCOUNTS, TELEGRAM_CHAT_ID
    
    # احصل على قائمة الحسابات وقم ببعثرتها (للعشوائية)
    account_keys = list(ACCOUNTS.keys())
    random.shuffle(account_keys) 
    
    print(f"AUTOMATION: Starting action thread for {post_url} with {len(account_keys)} accounts.")
    
    is_first_account = True
    
    for account_key in account_keys:
        try:
            if not is_first_account:
                # --- هذا هو الفاصل الزمني العشوائي ---
                delay_minutes = random.randint(5, 15)
                delay_seconds = delay_minutes * 60
                print(f"AUTOMATION: Waiting {delay_minutes} minutes before next account...")
                bot.send_message(TELEGRAM_CHAT_ID, f"⏳ في انتظار {delay_minutes} دقيقة قبل استخدام الحساب التالي...")
                time.sleep(delay_seconds)
            
            is_first_account = False
            
            storage_file = ACCOUNTS[account_key]
            comment_text, message_text = get_account_content(account_key)
            account_name = account_key.replace("account_", "").title()

            # --- 1. تنفيذ التعليق ---
            try:
                print(f"AUTOMATION: Posting comment from {account_name}...")
                bot.send_message(TELEGRAM_CHAT_ID, f"⏳ جاري نشر التعليق باستخدام {account_name}...")
                post_comment_playwright(storage_file, post_url, comment_text)
                print(f"AUTOMATION: Comment posted successfully from {account_name}.")
                bot.send_message(TELEGRAM_CHAT_ID, f"✅ تم نشر التعليق بنجاح باستخدام {account_name}.")
            except Exception as e:
                print(f"AUTOMATION ERROR (Comment) from {account_name}: {e}")
                bot.send_message(TELEGRAM_CHAT_ID, f"❌ فشل نشر التعليق باستخدام {account_name}:\n`{e}`")

            # (انتظار عشوائي بسيط بين التعليق والرسالة لنفس الحساب)
            time.sleep(random.randint(10, 30))

            # --- 2. تنفيذ الرسالة ---
            if profile_url:
                try:
                    print(f"AUTOMATION: Sending message from {account_name}...")
                    bot.send_message(TELEGRAM_CHAT_ID, f"⏳ جاري إرسال الرسالة باستخدام {account_name}...")
                    send_message_playwright(storage_file, profile_url, message_text)
                    print(f"AUTOMATION: Message sent successfully from {account_name}.")
                    bot.send_message(TELEGRAM_CHAT_ID, f"✅ تم إرسال الرسالة بنجاح باستخدام {account_name}.")
                except Exception as e:
                    print(f"AUTOMATION ERROR (Message) from {account_name}: {e}")
                    bot.send_message(TELEGRAM_CHAT_ID, f"❌ فشل إرسال الرسالة باستخدام {account_name}:\n`{e}`")
            else:
                print(f"AUTOMATION: Skipping message for {account_name} (no profile URL).")

        except Exception as e:
            print(f"AUTOMATION: Critical error in loop for account {account_key}: {e}")
            bot.send_message(TELEGRAM_CHAT_ID, f"‼️ خطأ فادح في الأتمتة للحساب {account_key}: {e}")
            
    print(f"AUTOMATION: Action thread finished for {post_url}.")
    bot.send_message(TELEGRAM_CHAT_ID, f"🏁 اكتملت جميع المهام الآلية للبوست:\n{post_url}")

def register_handlers(bot):
    """
    هذه هي الدالة الوحيدة التي تسجل كل أوامر البوت.
    """
    print("🤖 ... (جاري تسجيل كل أوامر البوت) ...")
    
     
    # --- Handler 3: معالجة أوامر الكلمات المفتاحية (اللي نقلناه) ---
    
    @bot.message_handler(commands=['keywords'])
    def manage_keywords(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_add = types.KeyboardButton('➕ إضافة كلمة مفتاحية')
        btn_delete = types.KeyboardButton('➖ حذف كلمة مفتاحية')
        btn_list = types.KeyboardButton('📜 عرض كل الكلمات المفتاحية')
        markup.add(btn_add, btn_delete, btn_list)
        bot.send_message(message.chat.id, "📋 اختر ماذا تريد أن تفعل بالكلمات المفتاحية:", reply_markup=markup)

    
    @bot.message_handler(func=lambda m: m.text in ['➕ إضافة كلمة مفتاحية', '➖ حذف كلمة مفتاحية', '📜 عرض كل الكلمات المفتاحية'])
    def choose_action(message):
        if message.text == '➕ إضافة كلمة مفتاحية':
            msg = bot.send_message(message.chat.id, "✍️ أرسل الكلمة المفتاحية التي تريد إضافتها:")
            bot.register_next_step_handler(msg, add_keyword)
        elif message.text == '➖ حذف كلمة مفتاحية':
            msg = bot.send_message(message.chat.id, "✍️ أرسل الكلمة المفتاحية التي تريد حذفها:")
            bot.register_next_step_handler(msg, delete_keyword)
        elif message.text == '📜 عرض كل الكلمات المفتاحية':
            keywords = load_keywords()
            if not keywords:
                bot.send_message(message.chat.id, "⚠️ لا توجد كلمات مفتاحية بعد.")
            else:
                send_keywords(message.chat.id, keywords)

    
    def add_keyword(message):
        keyword = message.text.strip()
        if not keyword or len(keyword) < 2:
            bot.send_message(message.chat.id, "⚠️ الكلمة المفتاحية قصيرة أو غير صالحة.")
            return return_to_main(message.chat.id)
        keywords = load_keywords()
        if keyword in keywords:
            bot.send_message(message.chat.id, "⚠️ هذه الكلمة موجودة بالفعل.")
            return return_to_main(message.chat.id)
        keywords.append(keyword)
        save_keywords(keywords)
        bot.send_message(message.chat.id, f"✅ تمت إضافة الكلمة: {keyword}")
        return return_to_main(message.chat.id)

    
    def delete_keyword(message):
        keyword = message.text.strip()
        keywords = load_keywords()
        if keyword not in keywords:
            bot.send_message(message.chat.id, "⚠️ هذه الكلمة غير موجودة.")
            return return_to_main(message.chat.id)
        keywords.remove(keyword)
        save_keywords(keywords)
        bot.send_message(message.chat.id, f"✅ تم حذف الكلمة: {keyword}")
        return return_to_main(message.chat.id)

    
    def send_keywords(chat_id, keywords):
        text = "📋 الكلمات المفتاحية الحالية:\n\n" + "\n".join(f"• {kw}" for kw in keywords)
        bot.send_message(chat_id, text)

    
    def return_to_main(chat_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('/keywords'))
        bot.send_message(chat_id, "🔙 اضغط /keywords للعودة للقائمة.", reply_markup=markup)
        
 