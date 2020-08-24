import collections
import datetime
import hashlib
import json
import random

import math
import requests
import xmltodict

from config.dev import *
from bank_utils.DES3 import EncryptDate
from bank_utils.rsa_sign import rsa_sign


def dict_to_xml(data_dict):
    data_xml = []
    for key, value in data_dict.items():
        data_xml.append(f'<{key}>{value}</{key}>')

    return '<?xml version="1.0" encoding="UTF-8"?>\n<FileRoot>{}</FileRoot>\n'.format(''.join(data_xml))  # 返回XML


def replace_special_char(string):
    string = string.replace(" ", "")
    string = string.replace("  ", "")
    string = string.replace("\n", "")
    string = string.replace("\r", "")
    string = string.replace("\t", "")
    string = string.replace("+", "%2B")
    string = string.replace("=", "%3D")

    return string


def read_file_content(file_path):
    if not os.path.exists(file_path):
        return -1, '证书不存在', None
    with open(file_path, 'rb') as file:
        content = file.read()

    return content


def verify(json_data, public_key_path):
    if json_data.get('errorCode') is not None:
        return -1, json_data, None

    key_val_list = []
    for key, val in json_data.items():
        if val == '' or val is None or key == 'RsaSign':
            continue

        if isinstance(val, str):
            key_val_list.append(f'{key}={val}')
        else:
            for sub_key, sub_val in val[-1].items():
                if sub_val == '' or sub_val is None:
                    continue
                key_val_list.append(f'{key}{sub_key}={sub_val}')

    key_val_str = '&'.join(key_val_list)
    key_val_str = f'{key_val_str}&'
    public_key_content = read_file_content(public_key_path)
    verify_result = rsa_sign.verify(key_val_str, json_data.get('RsaSign'), public_key_content)
    if verify_result:
        del json_data['RsaSign']
        return 0, json_data, None
    return -1, 'verify failed!', None


class AuthHandler:
    def __init__(self, app_id, public_url, key_path, client_pwd, public_key_path):
        self.app_id = app_id
        self.public_url = public_url
        self.key_path = key_path
        self.client_pwd = client_pwd
        self.public_key_path = public_key_path

    def get_token(self):
        sign_dict = {
            'ApplicationID': self.app_id,
            'RandomNumber': ''.join([str(random.randint(0, 9)) for _ in range(6)]),
            'SDKType': 'api'
        }

        pfx_content = read_file_content(self.key_path)
        public_key_content = read_file_content(self.public_key_path)
        pkcs12 = rsa_sign.load_pkcs12(pfx_content, self.client_pwd)
        sign_dict['PK'] = self.pk(pkcs12)
        sign_dict['DN'] = self.dn(pkcs12)

        key_value_str = "ApplicationID={}&RandomNumber={}&SDKType={}&".format(sign_dict['ApplicationID'],
                                                                              sign_dict['RandomNumber'],
                                                                              sign_dict['SDKType'])
        sign_dict['RsaSign'] = rsa_sign.sign(key_value_str, pkcs12, True)
        json_data = json.dumps(sign_dict)

        res = requests.post(self.public_url, data=json_data)
        response_dict = res.json()
        print(f'获取token接口返回值：{res.content.decode()}')

        if response_dict.get('errorCode') != 'OPEN-E-000000':
            response_dict['error'] = 1
            return -1, 'fail', response_dict

        verify_content = 'appAccessToken={}&'.format(response_dict.get('appAccessToken'))
        verify_result = rsa_sign.verify(verify_content, response_dict.get('RsaSign'), public_key_content)
        if verify_result:
            return 0, 'success', {'error': 0, 'appAccessToken': response_dict.get('appAccessToken')}

        return -1, 'fail', {'error': 1, 'errorMsg': 'verify failed!'}

    @staticmethod
    def pk(pkcs12):
        public_key = rsa_sign.pfx_public_key(pkcs12).decode()
        public_key = public_key.replace("-----BEGIN PUBLIC KEY-----", '')
        public_key = public_key.replace("-----END PUBLIC KEY-----", '')
        return replace_special_char(public_key)

    @staticmethod
    def dn(pkcs12):
        return replace_special_char(rsa_sign.get_x509_info(pkcs12))


class FileDownloadHandler:
    def __init__(self, token, app_id, url):
        self.url = url
        self.app_id = app_id
        self.start_piece = 0
        self.uid = None
        self.file_name = None
        self.client_file_name = None
        self.private_auth = None
        self.passwd = None
        self.continue_flag = 'false'

        if token:
            self.token = token
        else:
            raise ValueError('Token can not be empty!')

    def download_prepar(self, uid, passwd, file_name, private_auth, client_file_name):
        self.uid = uid
        self.file_name = file_name
        self.private_auth = private_auth
        self.client_file_name = client_file_name
        self.passwd = self.analyze_passwd(passwd)

        if os.path.splitext(file_name)[1] != os.path.splitext(client_file_name)[1]:
            return -1, f'本地文件{client_file_name}和服务器保存文件{file_name}格式不一样', None

        return 0, 'success', None

    def upload_prepar(self, uid, passwd, file_name, client_file_name, continue_flag):
        self.uid = uid
        self.file_name = file_name
        self.continue_flag = continue_flag
        self.client_file_name = client_file_name
        self.passwd = self.analyze_passwd(passwd)

        if f'/{uid}/' != file_name[:len(uid) + 2]:
            return -1, f'按照规格服务端文件一级目录必须为：/{uid}/', None

        if not os.path.exists(self.client_file_name):
            return -1, f'{self.client_file_name}文件不存在'

        if os.path.splitext(file_name)[1] != os.path.splitext(client_file_name)[1]:
            return -1, f'本地文件{client_file_name}和服务器保存文件{file_name}格式不一样', None

        return 0, 'success', None

    def get_file_right(self, api_type='download'):
        xml_dict = {
            'token': self.token,
            'FileName': self.file_name,
            'startPiece': self.start_piece,
            'Passwd': self.passwd,
            'appID': self.app_id,
            'Uid': self.uid,
        }
        if api_type == 'download':
            xml_dict['FileMsgFlag'] = 102
            xml_dict['privateAuth'] = self.private_auth
        else:
            xml_dict['FileMsgFlag'] = 101
            xml_dict['FileSize'] = os.path.getsize(self.client_file_name)
            xml_dict['ClientFileName'] = self.client_file_name
            xml_dict['continueFlag'] = self.continue_flag

        request_xml = dict_to_xml(xml_dict)
        request_str = self.byte_pack(request_xml)
        res = requests.post(self.url, data=request_str)
        xml_str_response = res.content[4:].decode('gb2312')

        response_dict = json.loads(json.dumps(xmltodict.parse(xml_str_response)))['FileRoot']
        print('下载文件，身份认证请求返回值：{}'.format(xml_str_response))

        if response_dict.get('AuthFlag') != 'true':
            if api_type == 'download':
                return -1, '附件下载用户认证失败，请查看 uid 和 passwd 是否正确', response_dict
            return -1, '附件上传用户认证失败', response_dict
        if api_type == 'download':
            target_dict = {
                'PieceNum': response_dict.get('PieceNum'),
                'sessionID':  response_dict.get('sessionID'),
                'FileName':  response_dict.get('FileName'),
                'privateAuth':  response_dict.get('privateAuth'),
                'Uid':  response_dict.get('Uid')
            }
        else:
            target_dict = {
                'FileSize': xml_dict.get('FileSize'),
                'FileMsgFlag': '201',
                'PieceNum': response_dict.get('PieceNum'),
                'sessionID': response_dict.get('sessionID'),
                'FileName': response_dict.get('FileName'),
                'Uid': response_dict.get('Uid'),
                'ClientFileName': response_dict.get('ClientFileName'),
                'continueFlag': xml_dict.get('continueFlag')
            }
        return 0, 'success', target_dict

    def get_file_execute(self, uid, passwd, file_name, private_auth, client_file_name):
        res = self.download_prepar(uid, passwd, file_name, private_auth, client_file_name)
        if res[0] != 0:
            return res

        code, msg, response_dict = self.get_file_right()
        if code != 0:
            return code, response_dict, None

        file_index = 0
        while True:
            data_xml = []
            file_index += 1
            data_xml.append('<FileMsgFlag>202</FileMsgFlag>')
            for key, value in response_dict.items():
                data_xml.append(f'<{key}>{value}</{key}>')

            data_xml.append(f'<FileIndex>{file_index}</FileIndex>')
            requests_xml_str = '<?xml version="1.0" encoding="UTF-8"?>\r\n<FileRoot>{}</FileRoot>'.format(
                ''.join(data_xml))
            request_str = self.byte_pack(requests_xml_str)
            response = requests.post(self.url, data=request_str).content

            code, res, _ = self.response_str_pro(response)
            if code == -1:
                return code, res, None

            with open(self.client_file_name, 'ab') as file_obj:
                file_obj.write(res['response_content_str'])

            xml_dict = res.get('response_dict')
            if xml_dict.get('LastPiece'):
                return 0, xml_dict, None
            response_dict['FileSize'] = xml_dict.get('FileSize')

    def put_file_execute(self, uid, passwd, file_name, private_auth, client_file_name):
        res = self.upload_prepar(uid, passwd, file_name, private_auth, client_file_name)
        if res[0] != 0:
            return res

        code, msg, data = self.get_file_right(api_type='upload')
        if code != 0:
            return code, msg, data

        return self.put_request_xml(data)

    def put_request_xml(self, response_dict):
        """
        分片上传的请求报文
        完整格式： xml字符串长度+xml字符串+当前分片读取的文件内容长度+当前分片读取的文件内容
        示例： 2345<?xml version="1.0" encoding="UTF-8">.....678765分片内容
        :param response_dict:
        :return:
        """
        piece_num = int(response_dict.get('PieceNum'))
        pices = math.ceil(int(response_dict.get('FileSize')) / piece_num)
        # 获取文件所有内容，用于生成md5编码, 在服务器上验证内容是否窜改
        file_content = read_file_content(self.client_file_name)
        md5 = hashlib.md5()
        md5.update(file_content)
        md5_content = md5.hexdigest()

        if response_dict.get('continueFlag') is not None and response_dict.get('continueFlag') == 'true':
            file_index = response_dict.get('startPiece')
        else:
            file_index = 0
        del response_dict['continueFlag']

        while True:
            data_xml = []
            offset = file_index * piece_num

            file_index += 1
            for key, value in response_dict.items():
                data_xml.append(f'<{key}>{value}</{key}>')

            data_xml.append(f'<FileIndex>{file_index}</FileIndex>')
            if file_index == pices:
                data_xml.append(f'<Md5>{md5_content}</Md5>')
                data_xml.append('<LastPiece>true</LastPiece>')
            requests_xml_str = '<?xml version="1.0" encoding="UTF-8"?>\r\n<FileRoot>{}</FileRoot>'.format(
                ''.join(data_xml))

            # 拼接报文
            byte_list = bytearray(requests_xml_str, 'utf-8')

            head_byte = self.get_padding_list(len(byte_list))

            head_byte.extend(byte_list)

            with open(self.client_file_name, 'rb') as file:
                file.seek(offset, 0)
                file_piece_content = file.read(piece_num)
            content_bytes = [item for item in file_piece_content]
            length = len(content_bytes)
            message_bytes = [length >> 24 & 0xff, length >> 16 & 0xff, length >> 8 & 0xff, length & 0xff]
            message_bytes.extend(content_bytes)

            head_byte.extend(message_bytes)

            request_str = ''.join([chr(item) for item in head_byte])
            response = requests.post(self.url, data=request_str)
            response_xml_str = response.content[4:].decode('gb2312')
            response_xml_dict = json.loads(json.dumps(xmltodict.parse(response_xml_str)))['FileRoot']
            if response_xml_dict.get('LastPiece') is not None and response_xml_dict.get('LastPiece') == 'true':
                break
        return 0, '文件上传成功', response_xml_dict

    @staticmethod
    def response_str_pro(response):
        bytes4 = response[:4]

        ret_len1 = 0
        for index, value in enumerate(bytes4):
            ret_len1 += (value & 0xFF) << ((4 - index - 1) * 8)

        xml_byte_range = response[4: 4 + ret_len1]
        response_xml_str = xml_byte_range.decode('utf-8')
        dict_data = json.loads(json.dumps(xmltodict.parse(response_xml_str)))

        if dict_data.get('FileRoot') is None or dict_data.get('FileRoot')['FileMsgFlag'] != '000000':
            return -1, dict_data, None

        response_bytes = response[ret_len1 + 4:]
        bytes5 = response_bytes[:4]

        ret_len = 0
        for index, value in enumerate(bytes5):
            ret_len += (value & 0xFF) << ((4 - index - 1) * 8)

        content_byte_range = response_bytes[4: ret_len + 4]
        return 0, {'response_dict': dict_data.get('FileRoot'), 'response_content_str': content_byte_range}, None

    @staticmethod
    def analyze_passwd(passwd):
        eg1 = EncryptDate("1234567890qwertyuiopzdlw")
        str1 = eg1.decrypt(passwd[6:])
        res = [i - 256 if i >= 128 else i for i in str1]
        return ''.join([chr(res[i * 2]) for i in range(len(res) // 2)])

    def byte_pack(self, request_xml):
        byte_list = bytearray(request_xml, 'utf-8')
        new_byte = self.get_padding_list(len(byte_list))
        new_byte.extend(byte_list)
        return ''.join([chr(item) for item in new_byte])

    @ staticmethod
    def get_padding_list(length):
        binary_str = str("{0:b}".format(length)).rjust(32, '0')
        res = []
        for i in range(4):
            sub_str = binary_str[i * 8: (i + 1) * 8]
            res.append(int(sub_str, 2))
        return res


class ApiServer:
    def __init__(self, url, key_path, public_key_path, client_pwd, fix_param):
        # 后续的key = value & 串严格按照数组元素定义的序列排序
        self.url = url
        self.key_path = key_path
        self.public_key_path = public_key_path
        self.client_pwd = client_pwd
        self.fix_param = fix_param
        self.sorted_params = None

        for key, value in self.fix_param.items():
            if key == '' or value is None:
                raise ValueError(f'{key} can not be empty!')

    def fix_query_param(self, server_id, change_param):
        self.url = f'{self.url}/{server_id}'
        date_str = datetime.datetime.strftime(datetime.datetime.now(), '%y%m%d')
        self.fix_param['CnsmrSeqNo'] = f"{USERMINNAME}{date_str}{random.randint(1000000000, 9999999999)}"
        change_param.update(self.fix_param)
        self.sorted_params = sorted(change_param.items(), key=lambda x: x[0])

    def execute(self, server_id, change_param):
        self.fix_query_param(server_id, change_param)

        key_value_list = []
        for item in self.sorted_params:
            if item[0] == '' or item[1] is None:
                continue
            key_value_list.append(f'{item[0]}={item[1]}')

        key_value_str = '&'.join(key_value_list)
        key_value_str = f'{key_value_str}&'

        pfx_content = read_file_content(self.key_path)
        pkcs12 = rsa_sign.load_pkcs12(pfx_content, self.client_pwd)
        sign = rsa_sign.sign(key_value_str, pkcs12, False)

        # 数组SDKType之前添加RsaSign元素（服务端验签有此顺序要求）
        d1 = collections.OrderedDict()
        for item in self.sorted_params:
            if item[0] == 'SDKType':
                d1['RsaSign'] = sign
            d1[item[0]] = item[1]

        json_data = json.dumps(d1)
        print('见证宝请求值：{}'.format(json_data))

        response = requests.post(self.url, data=json_data)
        print('见证宝api接口返回值：{}'.format(response.content.decode('utf-8')))
        code, result, _ = verify(response.json(), self.public_key_path)
        if result.get('tokenExpiryFlag') == 'true':
            from orange_bank_interface import orange_bank_interface
            self.fix_param['AppAccessToken'] = orange_bank_interface.get_token()
        if code == 0 and result.get('TxnReturnCode') and result.get('TxnReturnCode') != '000000':
            return -1, result, None
        return code, result, None


if __name__ == '__main__':
    pass
