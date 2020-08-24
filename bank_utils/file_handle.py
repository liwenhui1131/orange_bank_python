import base64
import os
import zipfile

from Crypto.Cipher import DES3, DES, AES

from config.dev import SUPPLIER_DIR


class FileHandle:
    @staticmethod
    def uncompress(zip_file):
        if not os.path.exists(zip_file):
            return -1, '待解压文件不存在', None
        try:
            zip_files = zipfile.ZipFile(zip_file, 'r')
            for file in zip_files.namelist():
                zip_files.extract(file, os.path.dirname(zip_file))
            zip_files.close()
        except zipfile.BadZipFile:
            return -1, '解压失败', None
        return 0, 'success', None

    @staticmethod
    def compress(src_file, zip_file):
        if not os.path.exists(src_file):
            return -1, '文件不存在', None

        try:
            f = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
            f.write(src_file, os.path.split(src_file)[-1])
            f.close()
        except zipfile.BadZipFile:
            return -1, '压缩失败', None
        return 0, 'success', None

    @staticmethod
    def pad(text):
        add = 8 - (len(text) % 8)
        return text + (chr(add) * add).encode()

    def encryp_text(self, plain_text, key, iv=b"12345678"):
        encrypt = DES3.new(key, DES3.MODE_CBC, iv)
        return encrypt.encrypt(self.pad(plain_text))

    @staticmethod
    def decrypt_text(cipher_text, key, iv=b"12345678"):
        cipher = DES3.new(key, DES3.MODE_CBC, iv)
        msg = cipher.decrypt(cipher_text)
        return msg[0:-msg[len(msg) - 1]]

    def zip(self, fsrc, key):
        src_file = fsrc
        zip_file = f'{fsrc}.zip'
        enc_file = f'{fsrc}.enc'
        key = base64.b64decode(key)
        self.compress(src_file, zip_file)
        with open(zip_file, 'rb') as file_obj:
            plain_text = file_obj.read()
        encrypt_text = self.encryp_text(plain_text, key)

        with open(enc_file, 'wb') as file_obj:
            file_obj.write(encrypt_text)

        return 0, 'success', None

    def unzip(self, fsrc, key):
        zip_file = f'{fsrc}.zip'
        src_file = f'{fsrc}.enc'
        key = base64.b64decode(key)
        if not os.path.exists(src_file):
            return -1, '文件不存在', None

        with open(src_file, 'rb') as file_obj:
            plain_text = file_obj.read()

        decrypt_text = self.decrypt_text(plain_text, key)
        # 使用b'PK\x03\x04\x14\x00\x08\x08\x08\x00]'替换解密后的b'`{34$088\x08\x00]'
        decrypt_text = b'PK\x03\x04\x14\x00\x08\x08' + decrypt_text[8:]

        if not decrypt_text:
            return -1, '解密失败，请检查密钥'

        os.remove(src_file)
        with open(zip_file, 'wb') as file_obj:
            file_obj.write(decrypt_text)

        return self.uncompress(zip_file)


file_handle = FileHandle()

if __name__ == '__main__':
    fsrc1 = 'TX2020073138621.txt'
    key1 = '3TnzbKz2qbLeYaA9ShYFAyv+YYtkdHgZ'
    print(file_handle.unzip(os.path.join(SUPPLIER_DIR, fsrc1), key1))
