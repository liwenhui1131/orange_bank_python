import base64

from Crypto.Cipher import DES3


class EncryptDate:
    def __init__(self, key):
        self.key = key  # 初始化密钥
        self.length = DES3.block_size  # 初始化数据块大小
        self.aes = DES3.new(self.key, DES3.MODE_ECB)  # 初始化AES,ECB模式的实例
        # 截断函数，去除填充的字符
        self.unpad = lambda date: date[0:-(date[-1])]

    def pad(self, text):
        """
        #填充函数，使被加密数据的字节码长度是block_size的整数倍
        """
        add = self.length - (len(text) % self.length)
        entext = text + (chr(add) * add)
        return entext

    def encrypt(self, encr_data):  # 加密函数
        encrypt_data = self.aes.encrypt(self.pad(encr_data).encode("utf8"))
        return base64.b64encode(encrypt_data)

    def decrypt(self, decr_data):  # 解密函数
        res = base64.b64decode(decr_data)
        msg = self.aes.decrypt(res)
        return self.unpad(msg)


if __name__ == '__main__':
    eg1 = EncryptDate("1234567890qwertyuiopzdlw")
    encrypt_data1 = eg1.encrypt('11111111111')
    print(111, encrypt_data1)
    str1 = eg1.decrypt(encrypt_data1)
    print(str1.decode())
