import pymongo
import bcrypt

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]
temporary_emails = db["temporary_emails"]

class EmailChecker:
    """
    Kiểm tra xem email có tồn tại trong db hay không.
    """
    def __init__(self, email: str):
        self.email = email

    def check_exists(self) -> bool:
        """
        Kiểm tra sự tồn tại của email.
        return: True nếu email tồn tại, False nếu không.
        """
        all_hashes = list(temporary_emails.find({}, {"email": 1, "_id": 0}))
        return any(self.email == entry["email"] for entry in all_hashes)


class PasswordChecker:
    """
    Kiểm tra xem mật khẩu có khớp với bất kỳ mật khẩu nào trong db hay không.
    """
    def __init__(self, password: str):
        self.password = password

    def check_exists(self) -> bool:
        """
        Kiểm tra xem mật khẩu đã nhập có khớp với bất kỳ mật khẩu nào đã lưu không.
        return: True nếu mật khẩu hợp lệ, False nếu không.
        """
        all_hashes = list(temporary_emails.find({}, {"password": 1, "_id": 0}))
        
        for entry in all_hashes:
            if bcrypt.checkpw(self.password.encode("utf-8"), entry["password"].encode("utf-8")):
                return True
        return False
