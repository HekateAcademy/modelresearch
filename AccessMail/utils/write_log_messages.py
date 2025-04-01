import pymongo
from datetime import datetime, timedelta

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]
email_logs = db["email_logs"]  # Collection lưu trữ log email
temporary_emails = db["temporary_emails"]

class WriteLogMessages:
    """
    ghi và in log 
    """
    def __init__(self):
        pass

    def log_email_action(self, email, action):
        """
        Ghi log khi thực hiện một hành động (tạo, đăng nhập, xóa) với email.
        email: Địa chỉ email cần ghi log
        action: Hành động được thực hiện (create, login, delete)
        """
        log_entry = {
            "email": email,
            "action": action,
            "timestamp": datetime.utcnow()
        }
        email_logs.insert_one(log_entry)
        print("Đã ghi log")

    def log_deleted_emails(self, expired_email):
        """
        Ghi log khi một email bị xóa do hết hạn.
        expired_email: Địa chỉ email bị xóa
        """
        log_entry = {
            "email": expired_email,
            "action": "deleted",
            "timestamp": datetime.utcnow()
        }
        email_logs.insert_one(log_entry)
    
    def print_email_logs(self, email):
        """
        Truy vấn và in lịch sử log của một email cụ thể.
        """
        logs = list(email_logs.find({"email": email}, {"_id": 1, "email": 1, "action": 1, "timestamp": 1}))
        
        if not logs:
            print("Không tìm thấy log cho email này.")
            return
        
        print("Lịch sử log của email:")
        for log in logs:
            print(f"Email: {log['email']}")
            print(f"Action: {log['action']}")
            print(f"Timestamp: {log['timestamp']}")