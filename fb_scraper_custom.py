import random
import time
import uuid
from playwright.sync_api import sync_playwright
from utils import remove_duplicate_lines, normalize_text, load_processed, save_processed, save_to_excel
from config import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keywords_handler import load_keywords
from telegram.helpers import escape_markdown
from state import pending_comments, pending_messages
import threading
from handlers import *

def extract_post_text(post):
    """
    يستخرج نص المنشور فقط، ويضغط على زر "عرض المزيد" أو "See more" إذا وجدهما تماماً.
    """
    try:
        # البحث عن أزرار التوسيع المطابقة تماماً
        expand_btns = post.locator(
            'div[role="button"]:has-text("See more"),'
            'div[role="button"]:has-text("عرض المزيد")'
        )
        for j in range(expand_btns.count()):
            try:
                btn = expand_btns.nth(j)
                btn_text = btn.inner_text(timeout=2000).strip()
                
                # الضغط فقط إذا كان النص مطابقاً تماماً
                if btn_text in ["See more", "عرض المزيد"]:
                    print(f"🔘 Attempting to click button #{j}: '{btn_text}'")
                    btn.click()
                    time.sleep(0.5) # انتظر قليلاً ليظهر النص
            except Exception as e:
                continue # أكمل حتى لو فشل الضغط
        time.sleep(1) # انتظر ثانية بعد محاولات الضغط
    except Exception:
        pass # لا توقف الكود إذا فشلت عملية "عرض المزيد"

 
    try:
        # !! تنبيه: قد تحتاج لتحديث هذا الـ Selector إذا غير فيسبوك تصميمه
        msg_loc = post.locator('div[data-ad-preview="message"], div[data-testid="post_message"]')
        if msg_loc.count() > 0:
            text = msg_loc.first.inner_text(timeout=3000).strip()
            return text
    except Exception as e:
        print(f"⚠️ خطأ في جلب نص المنشور الرسمي: {e}")

    return "" # إرجاع نص فارغ إذا فشل كل شيء

# --- دالة استخراج البروفايل (كما هي) ---
def extract_poster_profile(post):
    """
    (نسخة مُحدثة 3.0) مع منطق فلترة صحيح.
    """
    try:
        # 1. التحقق من الناشر المجهول
        anonymous_poster = post.locator('span:has-text("مشارك مجهول الهوية")').first
        if anonymous_poster.count() > 0 and anonymous_poster.is_visible(timeout=1000):
            print("👤 (تخطي) الناشر مجهول الهوية.")
            return None 
    except Exception:
        pass 

    try:
        # 2. البحث عن الرابط بتسلسل
        
        # (أ) محاولة إيجاد /user/
        author_link = post.locator('a[href*="/user/"]').first
        if author_link.count() == 0:
            # (ب) محاولة إيجاد profile.php
            author_link = post.locator('a[href*="facebook.com/profile.php"]').first
        if author_link.count() == 0:
            # (ج) محاولة إيجاد /people/
            author_link = post.locator('a[href*="facebook.com/people/"]').first
        if author_link.count() == 0:
             # (د) محاولة إيجاد الرابط داخل <strong>
             author_link = post.locator('strong > a[href*="facebook.com/"][role="link"]').first
        if author_link.count() == 0:
             # (هـ) محاولة إيجاد الرابط داخل <span>
             author_link = post.locator('span > a[href*="facebook.com/"][role="link"]').first
        if author_link.count() == 0:
             # (و) محاولة أخيرة
             author_link = post.locator('div[role="presentation"] a[role="link"]').first

        if author_link.count() == 0:
            print("⚠️ لم يتم العثور على رابط ناشر (فشلت كل المحددات).")
            return None 

        href = author_link.get_attribute("href", timeout=2000) or ""

        # 3. (!!! هذا هو التعديل الأهم !!!)
        # فلترة الروابط غير المرغوبة (مثل رابط الجروب أو البوست نفسه)
        
        # أولاً، تحقق إذا كان الرابط هو رابط مستخدم صالح
        is_user_link = "/user/" in href or "profile.php" in href
        
        # ثانياً، تحقق إذا كان الرابط يحتوي على كلمات غير مرغوبة
        is_unwanted_link = "/groups/" in href or "/posts/" in href or "/permalink/" in href or "/photos/" in href

        # (المنطق الجديد): احذف الرابط فقط إذا كان "غير مرغوب" (يحتوي على /groups/)
        # و "ليس رابط مستخدم" (لا يحتوي على /user/)
        if is_unwanted_link and not is_user_link:
            print(f"🔗 (تخطي) الرابط الذي تم العثور عليه هو رابط للجروب أو البوست: {href}")
            return None
        
        # (إذا وصل الكود إلى هنا، فالرابط سليم)

        # 4. تنظيف الرابط
        if "/user/" in href:
            # (تعديل بسيط هنا) استخراج الرابط حتى لو كان بداخله /groups/
            user_id = href.split('/user/')[1].split('/')[0]
            profile_url = f"https://www.facebook.com/user/{user_id}"
        else:
            profile_url = href.split('?', 1)[0]
            if not profile_url.startswith('http'):
                profile_url = f"https://www.facebook.com{profile_url}"
        
        print(f"✅ تم العثور على رابط الناشر: {profile_url}")
        return profile_url

    except Exception as e:
        print(f"⚠️ خطأ استخراج رابط الناشر: {e}")
        return None

processed_links, processed_texts = load_processed()
# --- دالة استخراج البروفايل (كما هي من الكود الأصلي) ---
def watch_groups(bot, account_key, storage_file):
    print(f"👀 بدء المراقبة بـ {account_key}")
    
    seen_links = set()
    do_scroll = True

    while True:
        try:
            with sync_playwright() as p:
                # تشغيل المتصفح (Headless=False لرؤية ما يحدث، اجعليها True لاحقاً)
                browser = p.chromium.launch(headless=False) 
                context = browser.new_context(
                    storage_state=storage_file,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                print("🌍 الذهاب إلى صفحة Feed...")
                page.goto("https://www.facebook.com/", timeout=60000)

                # 1. التحقق من تسجيل الدخول
                if page.url.startswith("https://www.facebook.com/login") or \
                   "checkpoint" in page.url or \
                   "recover" in page.url or \
                   page.locator("input[name='email'], input[name='pass']").count() > 0:

                    print(f"🚫 تم اكتشاف حظر أو تسجيل خروج من الحساب: {account_key}!")
                    bot.send_message(
                        TELEGRAM_CHAT_ID,
                        f"🚫 تم حظر أو تسجيل خروج حساب {account_key} من فيسبوك!\nالرجاء التحقق يدوياً.",
                        parse_mode="Markdown"
                    )
                    browser.close()
                    break 

                # انتظار تحميل الـ Feed
                try:
                    page.wait_for_selector('div[role="feed"]', timeout=60000)
                except:
                    print("⚠️ لم يتم العثور على Feed، محاولة تخطي...")

                session_start_time = time.time()
                
                # ✅✅✅ التصحيح هنا: تعريف متغيرات الوقت قبل الدخول في اللوب ✅✅✅
                last_reload_time = time.time()
                current_reload_interval = random.randint(300, 600) # بين 5 و 10 دقائق
                print(f"⏱️ التوقيت العشوائي الأول للريلود: بعد {int(current_reload_interval/60)} دقيقة.")
                # --------------------------------------------------------------

                while True:
                    try:
                        page.wait_for_timeout(random.randint(5000, 10000))    
                        keywords = load_keywords()

                        # ✅ 2. التحقق من مرور الوقت لعمل Reload
                        time_passed = time.time() - last_reload_time
                        
                        if time_passed > current_reload_interval:
                            print(f"⏰ مرت {int(time_passed/60)} دقيقة. جاري تحديث الصفحة...")
                            try:
                                page.reload(timeout=60000)
                                page.wait_for_selector('div[role="feed"]', timeout=60000) 
                                print("✅ تم تحديث الصفحة بنجاح.")
                                
                                # إعادة ضبط المؤقت وتوليد وقت عشوائي جديد
                                last_reload_time = time.time()
                                current_reload_interval = random.randint(300, 600)
                                print(f"🎲 الموعد القادم للريلود بعد: {int(current_reload_interval/60)} دقيقة.")
                                
                                do_scroll = True
                                page.wait_for_timeout(5000)
                            except Exception as e:
                                print(f"⚠️ فشل الريلود: {e}")

                        # ✅ 3. السكرول لتحميل بوستات جديدة
                        if do_scroll:
                            print("📜 Scrolling...")
                            page.evaluate("window.scrollBy(0, window.innerHeight * 2);")
                            page.wait_for_timeout(random.randint(3000, 6000)) 

                        # ✅ 4. استخراج البوستات
                        feed = page.locator('div[role="feed"] div[role="article"]')
                        post_count = feed.count()
                        # print(f"🕵️ فحص {post_count} بوست...")
                        
                        for i in range(post_count):
                            post = feed.nth(i)
                            full_link = ""
                            
                            try:
                                # استخراج الرابط
                                link_el = post.locator('a[href*="/posts/"], a[href*="/permalink/"]').first
                                href = link_el.get_attribute("href", timeout=1000) or "" 
                                if not href: continue 
                                href = href.split('?', 1)[0]
                                full_link = href if href.startswith("http") else f"https://www.facebook.com{href}"
                            except:
                                continue 

                            if full_link in processed_links or full_link in seen_links:
                                continue 

                            # إضافة للروابط المرئية مؤقتاً لتجنب التكرار في نفس الجلسة
                            seen_links.add(full_link)

                            # استخراج النص
                            text = extract_post_text(post)
                            text = remove_duplicate_lines(text)
                            norm_text = normalize_text(text)

                            if not text or norm_text in processed_texts:
                                continue

                            # التحقق من الكلمات المفتاحية
                            if not any(k in norm_text for k in keywords):
                                continue

                            # ✅ 5. إرسال التنبيه
                            print(f"🚨 بوست مطابق: {full_link}")
                            
                            MAX_TEXT_LENGTH = 4000
                            safe_text = (text[:MAX_TEXT_LENGTH] + '...') if len(text) > MAX_TEXT_LENGTH else text
                            escaped_text = escape_markdown(safe_text, version=2)
                            escaped_link = escape_markdown(full_link, version=2)
                           
                            msg = f"📢 *بوست جديد*\n\n{escaped_text}\n\n[عرض على فيسبوك]({escaped_link})" 

                            bot.send_message(
                                TELEGRAM_CHAT_ID,
                                msg,
                                parse_mode="MarkdownV2",
                                disable_web_page_preview=True
                            )
                            save_to_excel(full_link, text) 

                            # الحفظ لتجنب التكرار مستقبلاً
                            processed_links.add(full_link)
                            processed_texts.add(norm_text)
                            save_processed(processed_links, processed_texts)
                        
                        # ✅ 6. التحقق من مدة الجلسة (3 ساعات)
                        if time.time() - session_start_time > (3 * 60 * 60): 
                            print("🔁 إعادة تشغيل المتصفح لتجديد الجلسة...")
                            break 

                    except Exception as inner_e:
                        print(f"⚠️ خطأ عابر: {inner_e}")
                        time.sleep(5)
                        # لا نكسر اللوب هنا، نستمر للمحاولة التالية

        except Exception as outer_e:
            print(f"❌ خطأ في المتصفح: {outer_e}")
            print("🔁 إعادة المحاولة بعد 30 ثانية...")
            time.sleep(30)
