from tools_me.RSA_NAME.helen import QuanQiuFu
from tools_me.mysql_tools import SqlData


def make_card(n):

    for i in range(n):
        # 取出数据库信息激活码

        card_num = 'dddddddd'

        # 开卡

        resp = QuanQiuFu().create_card(card_num, )

        resp_code = resp.get('resp_code')

        if int(resp_code) != 0000:
            print(resp['resp_msg'])
            return

        resp_detail = resp.get('response_detail')
        card_no = resp_detail.get('card_no')

        rs = QuanQiuFu().trans_account_recharge(card_no, '金额')
        if int(rs.get('resp_code') != 0000):
            print('充值卡: ' + card_no + '失败!')

        resp_card_info = QuanQiuFu().query_card_info(card_no)
        if int(resp_card_info.get('resp_code')) != 0000:
            print('获取卡: ' + card_no + '信息失败!')

        re_de = resp_card_info.get('response_detail')
        expire_date = re_de.get('expire_date')
        card_verify_code = re_de.get('card_verify_code')
        freeze_fee_all = int(re_de.get('freeze_fee_all'))
        balance = int(re_de.get('balance'))
        real_balance = freeze_fee_all - balance

