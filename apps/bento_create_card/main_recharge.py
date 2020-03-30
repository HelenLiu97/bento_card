import threading
import requests
import json
import time
import logging
# from apps.bento_create_card.sqldata import BentoCard, session
from apps.bento_create_card.config import bento_data, GetToken, cut_list, change_time
from requests.adapters import HTTPAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class RechargeCard(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": GetToken(),
            "Connection": "close"
        }
        requests.adapters.DEFAULT_RETRIES = 5
        self.requests = requests.session()
        self.requests.keep_alive = False

    def refund_data(self, cardid, recharge_amount):
        # 获取用户cardid
        # cardid = session.query(BentoCard.card_id).filter(BentoCard.alias=="{}".format(alias), BentoCard.card_number.ilike("%{}%".format(cardnumber))).first() if alias:
        url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
        r = self.requests.get(url=url, headers=self.headers, verify=False, timeout=14)
        data = r.json()
        if data:
            try:
                # 获取用户可用余额
                bento_availableAmount = data.get("availableAmount")
                # 获取用户可用余额额度
                spendingLimit_amount = data.get("spendingLimit").get("amount")
            except AttributeError as e:
                logging.warning(str(e))
                return {"error_msg": "bento账号查询数据异常"}
            else:
                # data["availableAmount"] = float("%.2f" % spendingLimit_amount) + int(recharge_amount)
                # 给可用余额充值
                bento_use_amount = bento_availableAmount - float(recharge_amount)
                # 判断可用余额额度与可用余额是否相等
                # if bento_use_amount = spendingLimit_amount:
                data["spendingLimit"]["amount"] = float("%.2f" % bento_use_amount) if float(
                    "%.2f" % bento_use_amount) != float("%.2f" % spendingLimit_amount) else float(
                    "%.2f" % bento_use_amount) - 0.01
                data["availableAmount"] = float("%.2f" % bento_use_amount)
                response = self.requests.put(url=url, headers=self.headers, data=json.dumps(data), verify=False, timeout=14)
                if response.json().get("availableAmount") > bento_availableAmount:
                    return {"error_msg": "转移失败, 所剩余额未扣减"}
                return {"msg": "已有金额: {}, 转移金额: {}, 卡内可用余额: {}".format(bento_availableAmount, recharge_amount,
                                                                   response.json().get("availableAmount"))}
        return {"error_msg": "bento后台数据查无此账号"}

    def recharge(self, cardid, recharge_amount):
        # 获取用户cardid
        # cardid = session.query(BentoCard.card_id).filter(BentoCard.alias=="{}".format(alias), BentoCard.card_number.ilike("%{}%".format(cardnumber))).first()
        # if alias:
        url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
        r = self.requests.get(url=url, headers=self.headers, timeout=15, verify=False)
        data = r.json()
        if data:
            try:
                # 获取用户可用余额
                # bento_availableAmount = data.get("availableAmount")
                # 获取用户可用余额额度
                spendingLimit_amount = data.get("spendingLimit").get("amount")
                # return
            except AttributeError as e:
                logging.warning(str(e))
                return {"error_msg": "bento账号查询数据异常"}
            else:
                # data["availableAmount"] = float("%.2f" % spendingLimit_amount) + int(recharge_amount)
                # 给可用余额充值
                bento_use_amount = spendingLimit_amount + float(recharge_amount)
                # 判断可用余额额度与可用余额是否相等
                # if bento_use_amount = spendingLimit_amount:
                data["spendingLimit"]["amount"] = bento_use_amount
                # data["availableAmount"] = 5
                response = self.requests.put(url=url, headers=self.headers, data=json.dumps(data), timeout=15, verify=False)
                print(response.json())
                if response.json().get("availableAmount") == bento_use_amount:
                    return {"error_msg": "充值失败, 所剩余额未扣减"}
                return {"msg": "已有金额: {}, 充值金额: {}, 可用余额: {}".format(spendingLimit_amount, recharge_amount,
                                                                     response.json().get("availableAmount"))}
        return {"error_msg": "bento后台数据查无此账号"}

    # 使用递归多次查询大于500条交易记录的卡交易数据
    def transaction_data(self, cards, end_time=0, transactions_datas=None):
        url = "https://api.bentoforbusiness.com/transactions"
        params = {
            "cards": "{}".format(cards),
            "dateStart": 1570032000000,
            "dateEnd": int(round(time.time() * 1000)) if end_time == 0 else end_time
        }
        r = self.requests.get(url=url, headers=self.headers, params=params, verify=False, timeout=14)
        size = r.json().get('size')
        if not transactions_datas:
            transactions_datas = []
        for transactions in r.json().get("cardTransactions"):
            transactions_datas.append({
                "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                "description": transactions.get("payee").get("name"),
                "alias": transactions.get("card").get("alias"),
                "amount": transactions.get("amount"),
                "status": transactions.get("status"),
                "cardTransactionId": transactions.get("cardTransactionId"),
                "lastFour": transactions.get("card").get("lastFour"),
                "originalCurrency": transactions.get("originalCurrency"),
                "businessId": transactions.get("business").get("businessId"),
                "availableAmount": transactions.get("availableAmount"),
            })
        if size > 500:
            end_data = transactions_datas[-1].get('date')
            date = int(time.mktime(time.strptime(end_data, "%Y-%m-%d %H:%M:%S")) - 1) * 1000
            transactions_datas = self.transaction_data(cards, date, transactions_datas)
        return transactions_datas

    def one_alias(self, alias):
        url = "https://api.bentoforbusiness.com/cards?index=0&limit=10000"
        headers = {
            "Authorization": GetToken()
        }
        params = {
            "cardName": "{}".format(alias),
        }
        r = self.requests.get(url=url, headers=headers, params=params, verify=False, timeout=14)
        try:
            for i in r.json().get("cards"):
                if i.get("alias") == str(alias):
                    return i.get("availableAmount")
        except Exception as e:
            logging.warning(str(e))
            return 0

    def del_card(self, cardid):
        try:
            url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
            r = self.requests.delete(url=url, headers=self.headers, verify=False, timeout=14)
            return 404
        except Exception as e:
            logging.warning(str(e))
            return 404

    # card
    def declined_statistics(self, card_id, ):
        cards_list = cut_list(card_id, 12)
        url = "https://api.bentoforbusiness.com/transactions"
        decline_sum = 0
        # dateStart = change_time(min_time) - 86400000 * 3
        # dateEnd = change_time(max_time)
        for card_list in cards_list:
            params = {
                "cards": card_list,
                # "dateStart": dateStart,
                # "dateEnd": dateEnd,
            }
            r = self.requests.get(url=url, headers=self.headers, params=params, verify=False, timeout=14)
            decline_sum += len(r.json().get("cardTransactions"))
        return decline_sum


def main_transaction_data(cards, alias):
    transactions_datas = RechargeCard().transaction_data(cards=cards)
    availableAmount = RechargeCard().one_alias(alias=alias)
    return transactions_datas, availableAmount


# 批量查询卡消费记录的方法(使用多线程处理数据，所以写在此方法内)
def some_transaction_data(cards):
    transactions_datas = RechargeCard().transaction_data(cards=cards)
    info_list = list()
    for td in transactions_datas:
        info_list.append({
            "status": td.get("status"),
            "amount": td.get("amount"),
            "description": td.get("description"),
            "date": td.get("date"),
            "cardTransactionId": td.get("cardTransactionId"),
            "lastFour": td.get("lastFour"),
            "alias": td.get("alias"),
            "originalCurrency": td.get("originalCurrency"),
        })
    return info_list


# 继承threading模块重写run方法获取返回值
class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


# 使用多线程并发查询卡的交易记录，提高批量查询效率
def card_trans(card_list):
    threads = []
    nloops = range(len(card_list))
    for i in nloops:
        cardid = card_list[i]
        t = MyThread(some_transaction_data, (cardid, ), main_transaction_data.__name__)
        threads.append(t)
    for i in nloops:  # start threads 此处并不会执行线程，而是将任务分发到每个线程，同步线程。等同步完成后再开始执行start方法
        threads[i].start()
    info_list = list()
    for i in nloops:  # jion()方法等待线程完成
        threads[i].join()
        res = threads[i].get_result()
        info_list.extend(res)
    return info_list


def web_hook():
    headers = {
        # "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(GetToken()),
        # "Connection": "close"
    }
    url = "https://api.bentoforbusiness.com/webhooks"
    response = requests.post(url, headers=headers)
    print(response.json())


if __name__ == "__main__":
    web_hook()
    '''
    r = RechargeCard().transaction_data(887551)
    n = 1
    while True:
        try:
            r = RechargeCard().transaction_data(887551)
            print(r)
            print(n)
            n += 1
        except Exception as e:
            print(e)
    # trans, remain = main_transaction_data(1043609, 'Morris Gerardo')
    # print(len(trans), trans, remain)
    '''
