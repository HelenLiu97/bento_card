from Crypto.Cipher import DES
import binascii

# 需要加密的数据
# text = "df345"


class ImgCode(object):
    def __init__(self):
        # 设置一个密钥
        key = b'bagezifu'
        # 需要去生成一个DES对象
        self.des = DES.new(key, DES.MODE_ECB)

    # DES加密过程
    def jiami(self, text):
        text = text + (8 - (len(text) % 8)) * '='
        encrypt_text = self.des.encrypt(text.encode())
        encrypt_text = binascii.b2a_hex(encrypt_text)
        return encrypt_text.decode()

    # DES解密过程
    def jiemi(self, encrypt_text):
        decrypt_text = binascii.a2b_hex(encrypt_text)
        decrypt_text = self.des.decrypt(decrypt_text)
        s = decrypt_text.decode()
        code = s.split("=")[0]
        return code
