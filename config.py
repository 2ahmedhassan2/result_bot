import os

TOKEN = os.getenv("BOT_TOKEN", "8649992184:AAES8IEZiLph55200eClirtuSyM5TOiSWWE")
raw_admin_id = os.getenv("ADMIN_ID", "1679372391")
if raw_admin_id and raw_admin_id.strip().isdigit():
    ADMIN_ID = int(raw_admin_id)
else:
    ADMIN_ID = 1679372391

DATABASE_NAME = "database.db"
CACHE_TIMEOUT = 600
RATE_LIMIT_COUNT = 50
RATE_LIMIT_PERIOD = 60
