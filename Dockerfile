FROM python:3.10-slim

# تثبيت بعض المتطلبات الأساسية
RUN apt-get update && apt-get install -y wget gnupg curl libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 \
    libxrandr2 libxdamage1 libxext6 libxfixes3 libx11-xcb1 libnss3 libxss1 libasound2 libxtst6 libgbm1 \
    libgtk-3-0 libxshmfence-dev libxinerama1 libglu1-mesa xvfb fonts-liberation libappindicator3-1 libu2f-udev \
    && apt-get clean

# نسخ الملفات
WORKDIR /app
COPY . /app

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# تثبيت متصفحات Playwright
RUN python -m playwright install --with-deps

CMD ["nohup", "python3", "main_bot.py", ">", "output.log", "2>&1", "&"]
