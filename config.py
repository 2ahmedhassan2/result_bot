import os

TOKEN = os.getenv("BOT_TOKEN", "8649992184:AAES8IEZiLph55200eClirtuSyM5TOiSWWE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1679372391"))
DATABASE_NAME = "database.db"
CACHE_TIMEOUT = 600  # مدة الكاش بالثواني (10 دقائق)
RATE_LIMIT_COUNT = 50  # الحد الأقصى للطلبات في الدقيقة لمنع السبام
RATE_LIMIT_PERIOD = 60  # المدة الزمنية لحساب السبام بالثواني
