import threading
import requests
import json
import time
import logging
# from apps.bento_create_card.sqldata import BentoCard, session
from apps.bento_create_card.config import bento_data, GetToken, cut_list, change_time

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class RechargeCard(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": GetToken(),
        }

    def refund_data(self, cardid, recharge_amount):
        # 获取用户cardid
        # cardid = session.query(BentoCard.card_id).filter(BentoCard.alias=="{}".format(alias), BentoCard.card_number.ilike("%{}%".format(cardnumber))).first()
        # if alias:
        url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
        r = requests.get(url=url, headers=self.headers)
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
                response = requests.put(url=url, headers=self.headers, data=json.dumps(data))
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
        r = requests.get(url=url, headers=self.headers)
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
                bento_use_amount = bento_availableAmount + float(recharge_amount)
                # 判断可用余额额度与可用余额是否相等
                # if bento_use_amount = spendingLimit_amount:
                data["spendingLimit"]["amount"] = float("%.2f" % bento_use_amount) if float(
                    "%.2f" % bento_use_amount) != float("%.2f" % spendingLimit_amount) else float(
                    "%.2f" % bento_use_amount) - 0.01
                data["availableAmount"] = float("%.2f" % bento_use_amount)
                response = requests.put(url=url, headers=self.headers, data=json.dumps(data))
                if response.json().get("availableAmount") == bento_availableAmount:
                    return {"error_msg": "充值失败, 所剩余额未扣减"}
                return {"msg": "已有金额: {}, 充值金额: {}, 可用余额: {}".format(bento_availableAmount, recharge_amount,
                                                                     response.json().get("availableAmount"))}
        return {"error_msg": "bento后台数据查无此账号"}

    def transaction_data(self, cards):
        url = "https://api.bentoforbusiness.com/transactions"
        params = {
            "cards": "{}".format(cards),
            "dateStart": 1570032000000,
            "size": 1000
        }
        r = requests.get(url=url, headers=self.headers, params=params)
        transactions_datas = []
        print(r.json().get('size'), r.json().get('cardTransactions'))
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
        return transactions_datas

    def one_alias(self, alias):
        url = "https://api.bentoforbusiness.com/cards?index=0&limit=10000"
        headers = {
            "Authorization": GetToken()
        }
        params = {
            "cardName": "{}".format(alias),
        }
        r = requests.get(url=url, headers=headers, params=params)
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
            r = requests.delete(url=url, headers=self.headers)
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
            r = requests.get(url=url, headers=self.headers, params=params)
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


if __name__ == "__main__":
    # r = RechargeCard().recharge(cardnumber="9845", recharge_amount=0.1, alias="Margie Simpson")
    # l = ['913207', '913206', '913488', '913487', '913486', '913485', '913491', '913490', '915438', '915437', '915436', '915435', '915434', '915433', '915432', '915430', '915429', '915428', '915462', '915461', '916536', '916540', '916539', '916561', '920180', '929967', '943096', '967596', '990349', '990751', '990786', '989822', '989823', '990368', '943107', '993228', '994631', '994623', '994616', '994615', '994614', '993773', '993772', '993130', '990358', '989835', '996182', '995318', '996863', '997194', '996601', '997069', '998923', '998924', '996207', '996211', '998041', '1000311', '1000238']
    # card_trans(l)
    trans, remain = main_transaction_data(1043609, 'Morris Gerardo')
    print(len(trans), trans, remain)
    pass
