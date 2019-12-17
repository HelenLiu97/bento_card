import logging
import datetime
from .mysql_tools import SqlData


def xianzai_time():
    now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now_datetime


def customer_money_log():
    try:
        task_one = SqlData().search_account_info("")
        if len(task_one) == 0:
            return
        for u in task_one:
            u_id = u.get('u_id')
            out_money = SqlData().search_trans_sum(u_id)
            balance = u.get('balance')
            sum_balance = u.get('sum_balance')
            customer = u.get('name')
            n_time = xianzai_time()
            SqlData().insert_account_log(n_time, customer, balance, out_money, sum_balance)
        return
    except Exception as e:
        logging.error("记录客户当前余额信息失败!"+str(e))
        return


if __name__ == "__main__":
    customer_money_log()
