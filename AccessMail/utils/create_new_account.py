from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import pymongo
from datetime import datetime

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]
temporary_emails = db["temporary_emails"]

class CreateNewAccount:
    """
    tạo tài khoản mới với email tạm thời
    """
    def __init__(self, email: str, ciphertext_mail: str, password_hash: str, public_key, private_key):
        """
        Khởi tạo đối tượng với thông tin cần thiết để tạo tài khoản.
        
        email: Địa chỉ email.
        ciphertext_mail: Email được mã hóa.
        password_hash: Mật khẩu đã được băm.
        public_key: Khóa công khai RSA.
        private_key: Khóa riêng RSA.
        """
        self.email = email
        self.ciphertext_mail = ciphertext_mail
        self.password_hash = password_hash
        
        self.public_key = self.strip_pem(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

        self.private_key = self.strip_pem(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    def strip_pem(self, pem_bytes: bytes) -> str:
        """
        Loại bỏ phần header và footer của PEM để lưu trữ dễ dàng hơn.
        
        pem_bytes: Dữ liệu PEM dưới dạng byte.
        return: Chuỗi PEM đã loại bỏ phần header và footer.
        """
        pem_str = pem_bytes.decode('utf-8')
        return "".join(pem_str.splitlines()[1:-1])

    def create_temporary_email(self):
        """
        Tạo một email tạm thời và lưu vào cơ sở dữ liệu.
        """
        email_data = {
            "email": self.email,
            "ciphertext_mail": self.ciphertext_mail,
            "password": self.password_hash,
            "public_key": self.public_key,
            "private_key": self.private_key,
            "createdAt": datetime.utcnow() 
        }
        
        temporary_emails.insert_one(email_data)
        
        print("Đã tạo email tạm thời")
