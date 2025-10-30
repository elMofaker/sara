from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL = "01007246142"
PASSWORD = "kes$hav12N"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        page = context.new_page()

        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

        # تعامل مع نافذة الموافقة لو ظهرت
        try:
            consent = page.query_selector("button[data-cookiebanner='accept_button']")
            if consent:
                consent.click()
        except Exception:
            pass

        # املأ الحقول
        page.fill("input[name='email']", EMAIL)
        page.fill("input[name='pass']", PASSWORD)

        # اضغط تسجيل الدخول (بدون expect_navigation)
        page.click("button[name='login']")

        # انتظر العناصر اللي تدل إن الدخول نجح
        try:
            page.wait_for_selector(
                "div[role='feed'], input[aria-label='Search Facebook'], a[title='Profile']",
                timeout=60000
            )
            print("✅ تم تسجيل الدخول")
        except PWTimeout:
            print("✖ لم يتم العثور على مؤشرات نجاح تسجيل الدخول خلال 60s")
            page.screenshot(path="debug_login.png")
            print("Saved screenshot debug_login.png")

        # خلي المتصفح مفتوح لحد ما تضغط Enter
        input("\n⏸ اضغط Enter لحفظ الكوكيز والخروج...")

        # حفظ الكوكيز
        context.storage_state(path="account.json")
        print("💾 تم حفظ cookies في account.json")

        browser.close()

if __name__ == "__main__":
    run()

