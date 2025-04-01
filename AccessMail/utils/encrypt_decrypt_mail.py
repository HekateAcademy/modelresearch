from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
import pymongo
from cryptography.hazmat.primitives import serialization
import hashlib

class RSAKeyGenerator:
    def __init__(self):
        self.keys = {}
    
    def generate_keys(self, email: str):
        if email in self.keys:
            return self.keys[email]["private"], self.keys[email]["public"]

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        self.keys[email] = {"private": private_key, "public": public_key}
        return private_key, public_key


    def encrypt(self, email: str, plaintext: str):
        private_key, public_key = self.generate_keys(email)
        ciphertext = public_key.encrypt(
            plaintext.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        #email_hash = self.hash_email(email)  # Lấy hash của email
        return ciphertext.hex(), public_key, private_key

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["data"]
temporary_emails = db["temporary_emails"]
class RSAEncryption:
    """
    giải mã dữ liệu RSA
    """
    def __init__(self):
        pass
    
    def load_keys_from_db(self, email: str):
        """
        Truy xuất khóa riêng tư và công khai từ MongoDB.
        email: Địa chỉ email để tìm khóa RSA
        return: Tuple (private_key, public_key)
        """
        email_data = temporary_emails.find_one({"email": email}, {"private_key": 1, "public_key": 1})
        
        if not email_data:
            raise ValueError("Không tìm thấy khóa cho email này.")
        
        private_key = serialization.load_pem_private_key(
            email_data["private_key"].encode(), password=None
        )
        public_key = serialization.load_pem_public_key(
            email_data["public_key"].encode()
        )
        return private_key, public_key
    
    def decrypt(self, email: str, ciphertext_hex: str) -> str:
        """
        Giải mã dữ liệu sử dụng khóa riêng tư từ MongoDB.
        email: Địa chỉ email để lấy khóa RSA
        ciphertext_hex: Chuỗi hex đã mã hóa cần giải mã
        return: Chuỗi dữ liệu đã giải mã
        """
        private_key, _ = self.load_keys_from_db(email)
        ciphertext = bytes.fromhex(ciphertext_hex)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode()
 