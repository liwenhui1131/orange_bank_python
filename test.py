import time

from orange_bank_interface import orange_bank_interface


def open_account():
    user_id = str(int(time.time()))
    print(user_id)
    print(orange_bank_interface.open_cust_acct_id({
        'member_property': 'SH',
        'user_id': user_id,
        'user_name': '张三',
        'mobile': '13710064235'
    }))


def bind_card():
    print(orange_bank_interface.bind_card({
        'sub_acct_no': '3862000000006117',
        'user_id': '1596707342',
        'global_type': '73',
        'global_id': '9144898823XG',
        'member_name': '平安测试专用19',
        'mobile': '11111111111',
        'acct_no': '15000100723427',
        'open_branch_name': '平安银行股份有限公司北京上地支行',
        'transfer_method': '1',
        'cnaps_branch_id': '307100030696',
        'bank_type': '1'
    }))


def document_query():
    print(111, orange_bank_interface.document_query_and_download({"file_type": "YE", "file_date": 1596124800000}))


if __name__ == '__main__':
    open_account()
    # bind_card()
    # document_query()
