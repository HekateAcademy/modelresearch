import time
import pymongo
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone
from utils import (
    encrypt_decrypt_mail,
    create_new_account,
    encrypt_password,
    email_password_checker,
    write_log_messages,
)

# Kết nối đến MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]

def main():
    """Hàm chính để xử lý logic kiểm tra và tạo tài khoản email."""
    email = input("Nhập email: ")
    
    # Mã hóa email bằng RSA
    rsa_generator = encrypt_decrypt_mail.RSAKeyGenerator()
    rsa_generator.generate_keys(email)
    encrypted_email, public_key, private_key = rsa_generator.encrypt(email, email)
    
    # Kiểm tra email đã tồn tại chưa
    checker = email_password_checker.EmailChecker(email)
    WLM = write_log_messages.WriteLogMessages()
    
    if not checker.check_exists():  # Nếu email chưa tồn tại
        logged_emails = list(db.email_logs.find({"email": email}, {"_id": 0, "email": 1}))
        
        # Nếu email đã bị xóa trước đó
        if logged_emails:
            print("Email đã hết hạn và bị xóa trước đó.")
            WLM.print_email_logs(email)
        
        print("Tạo tài khoản mới")
        user_password = input("Nhập password mới: ")
        
        # Mã hóa mật khẩu
        password_hasher = encrypt_password.PasswordHasher(user_password)
        hashed_password = password_hasher.hash_password()
        
        # Tạo tài khoản mới
        temp_account = create_new_account.CreateNewAccount(
            email, encrypted_email, hashed_password, public_key, private_key
        )
        temp_account.create_temporary_email()  # Lưu tài khoản mới vào database
        print("Account đã tạo")
        
        # Ghi log hành động tạo tài khoản
        WLM.log_email_action(email, "create")
    else:
        print("Account đã được tạo")
        
        # Yêu cầu nhập mật khẩu để đăng nhập
        user_password = input("Nhập password: ")
        checker = email_password_checker.PasswordChecker(user_password)
        
        while not checker.check_exists():
            print("Sai password.")
            user_password = input("Nhập lại password: ")
            checker = email_password_checker.PasswordChecker(user_password)
        
        print("Đăng nhập thành công")
        WLM.log_email_action(email, "login")
        WLM.print_email_logs(email)

if __name__ == "__main__":
    main()