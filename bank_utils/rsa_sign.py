import base64
import re

from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from OpenSSL import crypto


class RsaSign:
    @staticmethod
    def sign(key_value_str, pkcs12, replace_spec_char=False):
        privatekey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkcs12.get_privatekey()).decode()
        privatekey = RSA.importKey(privatekey)
        signer = PKCS1_v1_5.new(privatekey)
        signature = signer.sign(MD5.new(key_value_str.encode('utf-8')))
        signature = base64.b64encode(signature).decode()
        if replace_spec_char:
            from orange_bank_utils import replace_special_char
            signature = replace_special_char(signature)
        return signature

    @staticmethod
    def verify(data, sign, public_key_content):
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, public_key_content)
        public_key = crypto.dump_publickey(crypto.FILETYPE_PEM, cert.get_pubkey()).decode("utf-8")
        public_key = RSA.importKey(public_key)
        signer = PKCS1_v1_5.new(public_key)
        return signer.verify(MD5.new(data.encode('utf-8')), base64.b64decode(sign))

    @staticmethod
    def pfx_public_key(pkcs12):
        return crypto.dump_publickey(crypto.FILETYPE_PEM, pkcs12.get_certificate().get_pubkey())

    @staticmethod
    def load_pkcs12(pfx_content, password):
        # return crypto.load_pkcs12(pfx_content, bytes(str(password), encoding="utf8"))
        return crypto.load_pkcs12(pfx_content, str(password))

    @staticmethod
    def get_x509_info(pkcs12):
        ou_list = []
        x509_name = pkcs12.get_certificate().get_subject()

        for name, value in x509_name.get_components():
            if name.decode() == 'OU':
                value = value.decode()
                value = re.sub(r'[^0-9a-zA-Z]', '', value)
                ou_list.append(value)

        return f'CN={x509_name.commonName},OU={ou_list[1]},OU={ou_list[0]},O={x509_name.organizationName},C={x509_name.countryName}'


rsa_sign = RsaSign()
