import datetime
import random
import time

import pandas

from bank_utils.file_handle import file_handle
from config.dev import *
from orange_bank_utils import AuthHandler, ApiServer, FileDownloadHandler


class OrangeBankInterface:
    def __init__(self):
        self.app_id = APP_ID
        self.key_path = KEYPATH
        self.public_key_path = PUBLIC_KEY_PATH
        self.client_pwd = CLIENT_PWD
        self.token = self.get_token()
        self.url = BASE_URL + URL_DICT.get('group')
        self.api_server = ApiServer(self.url, self.key_path, self.public_key_path, self.client_pwd,
                                    self.get_fix_param())

    def get_token(self):
        auth_url = BASE_URL + URL_DICT.get('login_url')
        auth_handler = AuthHandler(self.app_id, auth_url, self.key_path, self.client_pwd, self.public_key_path)
        response = auth_handler.get_token()

        if response[0] != 0:
            return response
        return response[2].get('appAccessToken')

    def get_fix_param(self):
        now = datetime.datetime.now()
        date_str = datetime.datetime.strftime(now, '%y%m%d')
        cnsmr_seq_no = f"{USERMINNAME}{date_str}{random.randint(1000000000, 9999999999)}"
        valid_term = datetime.datetime.strftime(now, '%Y%m%d')
        fix_param = {
            'ApiVersionNo': '1.1.1',
            'AppAccessToken': self.token,
            'ApplicationID': self.app_id,
            'RequestMode': 'json',
            'SDKType': 'api',
            'SdkSeid': '4984hq-pad39401',
            'SdkVersionNo': '1.1.1',
            'TranStatus': '0',  # string类型，而并非int类型
            'TxnTime': f"{datetime.datetime.strftime(now, '%Y%m%d%H%M%S')}000",
            'ValidTerm': valid_term,
            'TxnCode': valid_term,  #
            'TxnClientNo': valid_term,  #
            'CnsmrSeqNo': cnsmr_seq_no,  # 交易流水号
            'MrchCode': MRCHCODE,  # 商户号
        }

        return fix_param

    def open_cust_acct_id(self, params):
        """
        会员子账户开立——见证宝接口码：KFEJZB6000
        服务id：OpenCustAcctId. 记录返回值中的见证子账户的账号（SubAcctNo）
        :return:
        """
        change_param = {
            'FunctionFlag': '1',  # 功能标志，1:开户3:销户
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'TranNetMemberCode': params.get('user_id'),  # 交易网会员代码
            'MemberProperty': params.get('member_property'),  # 会员属性
            'UserNickname': params.get('user_name'),  # N 用户昵称
            'Mobile': params.get('mobile'),  # N 手机号码
        }
        return self.api_server.execute('OpenCustAcctId', change_param)

    def bind_card(self, params):
        """
        会员绑定提现账户-小额鉴权——见证宝接口码：KFEJZB6055
        服务id：BindRelateAcctSmallAmount. 转账方式使用【往账鉴权】
        :return:
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'SubAcctNo': params.get('sub_acct_no'),  # 见证子账户的账号
            'TranNetMemberCode': str(params.get('user_id')),  # 交易网会员代码
            'MemberName': params.get('member_name'),  # 见证子账户的户名
            'MemberGlobalType': params.get('global_type'),  # 会员证件类型 1:身份证 73:统一社会信用代码
            'MemberGlobalId': params.get('global_id'),  # 会员证件号码
            'MemberAcctNo': params.get('acct_no'),  # 银行卡的账号
            'BankType': params.get('bank_type'),  # 本他行类型 1:本行 2:他行. 他行时CnapsBranchId，EiconBankBranchId至少一个不为空
            'AcctOpenBranchName': params.get('open_branch_name'),  # 开户行名称
            'CnapsBranchId': params.get('cnaps_branch_id'),  # 开户行的联行号
            'EiconBankBranchId': params.get('eicon_bank_branch_id'),  # N 开户行的超级网银行号
            'Mobile': params.get('mobile'),  # 银行卡手机号
            'ReservedMsg': '1',  # N 转账方式 1:往账鉴权(测试环境：默认值0.01) 2:来账鉴权
        }
        return self.api_server.execute('BindRelateAcctSmallAmount', change_param)

    def small_amount_transfer_query(self, params):
        """
        查询小额鉴权转账结果——见证宝接口码：KFEJZB6061
        服务id：SmallAmountTransferQuery
        :return:
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'OldTranSeqNo': params.get('old_tran_seq_no'),  # 原交易流水号 小额鉴权交易请求时的CnsmrSeqNo值
            'TranDate': params.get('tran_date'),  # 交易日期 格式：20181201
        }
        return self.api_server.execute('SmallAmountTransferQuery', change_param)

    def check_amount(self, params):
        """
        验证鉴权金额——见证宝接口码：KFEJZB6064
        服务id：CheckAmount. 记录返回值中的见证系统流水号（FrontSeqNo）
        :return:
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'TranNetMemberCode': params.get('user_id'),  # 交易网会员代码
            'SubAcctNo': params.get('sub_acct_no'),  # 见证子账户的账号
            'TakeCashAcctNo': params.get('acct_no'),  # 会员的待绑定的银行卡账号
            'AuthAmt': params.get('auth_amt'),  # 鉴权验证金额
            'Ccy': 'RMB',  # 币种默认为RMB
            'ReservedMsg': '1',  # N 原小额转账方式 1:往账鉴权，此为默认值 2:来账鉴权
        }
        return self.api_server.execute('CheckAmount', change_param)

    def cust_acct_id_balance_query(self, params):
        """
        查询银行子账户余额——见证宝接口码：KFEJZB6010
        服务id：CustAcctIdBalanceQuery. 记录返回值中的
        ResultNum 本次交易返回查询结果记录数
        StartRecordNo 起始记录号
        EndFlag 结束标志
        TotalNum 符合业务查询条件的记录总数
        AcctArray 账户信息数组 start
        SubAcctNo 见证子账户的账号
        SubAcctProperty 见证子账户的属性
        TranNetMemberCode 交易网会员代码
        SubAcctName 见证子账户的名称
        AcctAvailBal 见证子账户可用余额
        CashAmt 见证子账户可提现金额
        MaintenanceDate 维护日期
        AcctArray 账户信息数组 end
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'SubAcctNo': params.get('sub_acct_no', '3862000000001067'),  # N 若SelectFlag为2时，子账号必输
            'QueryFlag': params.get('query_flag', '2'),  # 2：普通会员子账号 3：功能子账号
            'PageNum': '1',  # 起始值为1，每次最多返回20条记录，第二页返回的记录数为第21至40条记录，第三页为41至60条记录，顺序均按照建立时间的先后
        }
        return self.api_server.execute('CustAcctIdBalanceQuery', change_param)

    def single_transaction_status_query(self, params):
        """
        查询银行单笔交易状态——见证宝接口码：KFEJZB6110
        服务id：SingleTransactionStatusQuery.
        返回值
        BookingFlag 记账标志
        TranStatus 交易状态
        TranAmt 交易金额
        TranDate 交易日期
        TranTime 交易时间
        InSubAcctNo 转入子账户账号
        OutSubAcctNo 转出子账户账号
        FailMsg 失败信息
        OldTranFrontSeqNo 原交易前置流水号
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'FunctionFlag': params.get('function_flag', '4'),  # 2:会员间交易 3:提现 4:充值
            'TranNetSeqNo': params.get('tran_net_seq_no', 'J729862007303140517306'),  # 交易网流水号
            'SubAcctNo': None,  # N 见证子帐户的帐号
            'TranDate': None,  # N 交易日期
            'ReservedMsg': None,  # N 保留域
        }
        return self.api_server.execute('SingleTransactionStatusQuery', change_param)

    def draw_cash(self, params):
        """
        会员提现-不验证——见证宝接口码：KFEJZB6033
        服务id：MembershipWithdrawCash. 记录返回值中的见证系统流水号（FrontSeqNo），转账手续费（TransferFee）
        :return:
        """
        change_param = {
            'TranWebName': '易工品',  # 交易网名称
            'SubAcctNo': params.get('sub_acct_no'),  # 见证子账户的账号
            'MemberGlobalType': params.get('member_global_type'),  # 会员证件类型
            'MemberGlobalId': params.get('member_global_id'),  # 会员证件号码
            'TranNetMemberCode': params.get('user_id'),  # 交易网会员代码
            'MemberName': params.get('supplier_name'),  # 会员名称
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'TakeCashAcctNo': params.get('member_acct_no'),  # 提现账号 银行卡
            'OutAmtAcctName': params.get('member_name'),  # 出金账户名称 银行卡户名
            'Ccy': 'RMB',  # 币种 默认为RMB
            'CashAmt': str(params.get('cash_amt')),  # 可提现金额
            'Remark': None,  # N 备注 建议可送订单号，可在对账文件的备注字段获取到
            'ReservedMsg': None,  # N 保留域 提现手续费，格式0.00
            'WebSign': None,  # N 网银签名
        }
        return self.api_server.execute('MembershipWithdrawCash', change_param)

    def transaction(self, params):
        """
        会员间交易-不验证——见证宝接口码：KFEJZB6034
        服务id：MemberTransaction. 记录返回值中的见证系统流水号（FrontSeqNo）
        :return:
        """
        change_param = {
            'FunctionFlag': '9',  # 功能标志 1:下单预支付 2:确认并付款 3:退款 6:直接支付T+1 9:直接支付T+0
            'OutSubAcctNo': params.get('out_account_sub_acct_no'),  # 转出方的见证子账户的账号
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'OutMemberCode': params.get('out_menber_id'),  # 转出方的交易网会员代码
            'OutSubAcctName': params.get('out_menber_user_name'),  # 转出方的见证子账户的户名
            'InSubAcctNo': params.get('sub_acct_no'),  # 转入方的见证子账户的账号
            'InMemberCode': params.get('supplier.id'),  # 转入方的交易网会员代码
            'InSubAcctName': params.get('user_name'),  # 转入方的见证子账户的户名
            'TranAmt': params.get('tran_amt'),  # 交易金额
            'TranFee': '0',  # 交易费用
            'TranType': '01',  # 交易类型
            'Ccy': 'RMB',  # 币种 默认为RMB
            'OrderNo': None,  # 订单号 功能标志为1,2,3时必输
            'OrderContent': None,  # N 订单内容
            'Remark': None,  # N 备注
            'ReservedMsg': None,  # N 保留域 提现手续费，格式0.00
            'WebSign': None,  # N 网银签名
        }
        return self.api_server.execute('MemberTransaction', change_param)

    def document_query(self, params):
        """
        查询对账文件信息——见证宝接口码：KFEJZB6103
        服务id：ReconciliationDocumentQuery. 记录返回值中的
        ResultNum	本次交易返回查询结果记录数
        TranItemArray	交易信息数组
        FileName	文件名称
        RandomPassword	随机密码
        FilePath	文件路径
        DrawCode	提取码
        TranItemArray 	交易信息数组
        :return:
        """
        return self.api_server.execute('ReconciliationDocumentQuery', params)

    def apnt_transfer(self, params):
        """
        指定转账划款（测试专用，不能投产）——见证宝接口码：KFEJZB6211
        服务id：ApntTransfer. 记录返回值中的
        WitnessSysSeqNo	见证系统流水号
        :return:
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'RecvAcctNo': params.get('member_acct_no'),  # 收款账户的账号
            'RecvAcctName': params.get('member_name'),  # 收款账户的户名
            'RecvAcctOpenBranchName': params.get('open_branch_name'),  # 收款账户的开户行行名
            'RecvAcctOpenBranchInterbankId': params.get('cnaps_branch_id'),  # 收款账户的联行号
            'ApplyTakeCashAmt': '10000.0',  # 申请提现的金额
            'MarketChargeCommission': '0.0'  # 市场收取的手续费
        }
        return self.api_server.execute('ApntTransfer', change_param)

    def unbind_relate_acct(self, params):
        """
        会员解绑提现账户——见证宝接口码：KFEJZB6065
        服务id：UnbindRelateAcct. 记录返回值中的
        FrontSeqNo	见证系统流水号
        :return:
        """
        change_param = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'FunctionFlag': '1',  # 功能标志 1：解绑
            'TranNetMemberCode': params.get('user_id'),  # 交易网会员代码
            'SubAcctNo': params.get('sub_acct_no'),  # 见证子账户的账号
            'MemberAcctNo': params.get('member_acct_no'),  # 待解绑的提现账户的账号
        }
        return self.api_server.execute('UnbindRelateAcct', change_param)

    def file_download(self, params):
        uid = 'H22285'  # 平台提供
        passwd = '${3DES}x37f1pwrniivZxK6jWqqfQ=='  # 平台提供，需要使用3des算法进行解密
        client_file_path = os.path.join(SUPPLIER_DIR, params.get('FileName'))
        url = BASE_URL + URL_DICT.get('file_upload_auth_url')

        file_upload_handler = FileDownloadHandler(self.token, self.app_id, url)
        res = file_upload_handler.get_file_execute(uid, passwd, params.get('FilePath'), params.get('DrawCode'),
                                                   client_file_path)
        if res[0] != 0:
            return res

        return 0, 'success', {'file_path': client_file_path, 'file_name': params.get('FileName'),
                              'random_pwd': params.get('RandomPassword')}

    def file_upload(self, params):
        continue_flag = 'true'
        uid = 'H22285'  # 平台提供
        passwd = '${3DES}x37f1pwrniivZxK6jWqqfQ=='  # 平台提供，需要使用3des算法进行解密
        client_file_path = os.path.join(SUPPLIER_DIR, params.get('FileName'))
        url = BASE_URL + URL_DICT.get('file_upload_auth_url')

        file_upload_handler = FileDownloadHandler(self.token, self.app_id, url)
        if continue_flag == 'true':
            code, mes, upload_res = file_upload_handler.put_file_execute(uid, passwd, params.get('FilePath'),
                                                                         client_file_path, continue_flag)
            if upload_res.get('FileMsgFlag') != '000000':
                # 返回错误码EFS0071，说明文件已经完整上传了无需续传。停止上传操作，当然你也可以重新上传，$continueFlag=false（重新上传）
                if upload_res.get('FileMsgFlag') == 'EFS0071':
                    return 0, '文件已经上传成功，无需重复上传', None
                else:
                    return file_upload_handler.put_file_execute(uid, passwd, params.get('FilePath'), client_file_path,
                                                                'false')
        else:
            return file_upload_handler.put_file_execute(uid, passwd, params.get('FilePath'), client_file_path,
                                                        continue_flag)

    def document_query_and_download(self, params):
        time1 = params.get('file_date') // 1000
        time_array = time.localtime(time1)
        date = time.strftime('%Y%m%d', time_array)

        params = {
            'FundSummaryAcctNo': FUNDSUMMARYACCTNO,  # 资金汇总账号
            'FileType': params.get('file_type'),  # 文件类型充值文件-CZ 提现文件-TX 交易文件-JY 余额文件-YE 合约文件-HY
            'FileDate': str(date),  # 文件日期
        }
        code, res, _ = self.document_query(params)
        if code == -1 and res.get('ResultNum') == '':
            return 0, res.get('TxnReturnMsg'), None

        code, meg, data = self.file_download(res.get('TranItemArray')[0])
        if code == -1:
            return code, meg, data
        src_file = data.get('file_path').replace('.enc', '')
        target_file = src_file.replace('txt', 'xlsx')
        res = file_handle.unzip(src_file, data.get('random_pwd'))
        if res[0] == -1:
            return res

        if params.get('file_type') == 'YE':
            header = ['序号', '网站会员代码', '子账户', '金额', '备注', '']
        elif params.get('file_type') == 'CZ':
            header = ['序号', '网站会员代码', '子账户', '交易金额', '手续费', '交易日期', '交易时间', '银行见证系统流水号', '交易网流水号', '备注', '记账类型', '订单号',
                      '']
        elif params.get('file_type') == 'TX':
            header = ['序号', '网站会员代码', '子账户', '子账户名称', '交易金额', '手续费', '交易日期', '交易时间', '银行见证系统流水号', '交易网流水号', '备注',
                      '记账类型', '订单号', '']
        elif params.get('file_type') == 'JY':
            header = ['序号', '记账标志', '转出交易网会员代码', '转出子账户', '转出子账户名称', '转入交易网会员代码', '转入子账户', '转入子账户名称', '交易金额', '手续费',
                      '交易日期', '交易时间', '银行见证系统流水号', '交易网流水号', '备注', '订单号', '']
        else:
            header = None

        df = pandas.read_table(src_file, sep='&', names=header, dtype='object', encoding='gb2312')
        df.to_excel(target_file, index=False)

        return 0, 'success', {'target_file': target_file}


orange_bank_interface = OrangeBankInterface()

if __name__ == '__main__':
    pass
    print(orange_bank_interface.file_upload({
        "FileName": "TX20200731386211.txt.zip",
        "FilePath": "/H22285/TX20200731386211.txt.zip",
    }))
