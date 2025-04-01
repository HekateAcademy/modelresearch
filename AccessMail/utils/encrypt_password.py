import bcrypt

class PasswordHasher:
    """
    Hash mật khẩu bằng thuật toán bcrypt.
    """
    def __init__(self, password: str):
        """
        Khởi tạo đối tượng với mật khẩu cần băm.
        password: mật khẩu đầu vào
        """
        self.password = password
    
    def hash_password(self) -> str:
        """
        Tạo mật khẩu đã băm sử dụng thuật toán bcrypt.
        return: mật khẩu đã được hash
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(self.password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')