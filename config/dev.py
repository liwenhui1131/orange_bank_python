import os

current_pwd = os.path.dirname(__file__)

APP_ID = '9432ddce-a398-41b7-b160-30d3258dec59'
BASE_URL = 'https://my-st1.orangebank.com.cn:567'
KEYPATH = os.path.join(current_pwd, '2000911720@78.pfx')
CLIENT_PWD = '1'  # 商户证书密码（证书导出时用户自己设置，仅供测试使用），生产环境建议在调用接口时直接在方法PaopClient()中赋值
PUBLIC_KEY_PATH = os.path.join(current_pwd, 'publickey.cer')
TYPE = 'PKCS12'
USERMINNAME = 'J72986'
FILE_PASSWORD = '${3DES}FiubRstKfRA2O4T9mGj8g=='
MRCHCODE = '3862'  # 商户号
FUNDSUMMARYACCTNO = '15000115296119'
VALID_TERM = 20210712
UID = 'H22285'
URL_DICT = {
    'login_url': '/api/approveDev',
    'file_upload_auth_url': '/file/auth',
    'file_upload_url': '/file/auth',
    'group': '/api/group'
}

SUPPLIER_DIR = 'D:\\var'
