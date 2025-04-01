import time
import pymongo
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from utils import (
    write_log_messages,
)

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]

def delete_expired_emails():
    """
    Xóa các email hết hạn khỏi db.
    - Lọc ra các email có thời gian tạo nhỏ hơn thời gian hiện tại trừ đi 10 giây.
    - Ghi log và xóa các email đó khỏi db.
    """
    try:
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=48)
        expired_emails = list(
            db.temporary_emails.find({"createdAt": {"$lt": expired_time}}, {"_id": 1, "email": 1})
        )

        if not expired_emails:
            print("Không có email nào hết hạn để xóa.")
            return

        print("Danh sách email bị xóa:")
        WLM = write_log_messages.WriteLogMessages()
        for email in expired_emails:
            print(email["email"])
            WLM.log_deleted_emails(email["email"])

        deleted_count = db.temporary_emails.delete_many({"createdAt": {"$lt": expired_time}}).deleted_count
        print(f"Đã xóa {deleted_count} email hết hạn.")
    
    except Exception as e:
        print(f"Lỗi khi xóa email hết hạn: {e}")

# Khởi tạo scheduler để chạy hàm xóa email định kỳ
scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_emails, "interval", seconds=3600)
scheduler.start()

print("Hệ thống kiểm tra và xóa email hết hạn đang chạy...")

# Giữ chương trình chạy liên tục để kiểm tra email hết hạn
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    print("\nDừng hệ thống kiểm tra email.")
    scheduler.shutdown()
