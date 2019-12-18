import requests
import json
import time
import logging
from .config import bento_data, GetToken
# from .bento_create_card.sqldata import BentoCard, session
from .sqldata_native import SqlDataNative
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class TransactionRecord(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": GetToken(),
        }

    # 所有的用户与金额
    def alias_data(self):
        url = "https://api.bentoforbusiness.com/cards?index=0&limit=10000"
        headers = {
            "Authorization": GetToken()
        }
        r = requests.get(url=url, headers=headers)
        d = []
        for i in r.json().get("cards"):
            d.append({
                "alias": i.get("alias"),
                "availableAmount": i.get("availableAmount"),
                # "lastFour": i.get("lastFour")
            })
        # d.append({"sum": len(r.json().get("cards"))})
        return d


    # 查询指定用户的交易记录, 仅查询COMPLETE，PENDING或DECLINED事务。
    def card_transactions(self, *args):
        """
        :param args: 查询的用户名
        :return: 时间, 用途, 卡的名字, 卡的消费金额, 卡的状态, 卡的可用余额
        """
        url = "https://api.bentoforbusiness.com/transactions"
        r = requests.get(url=url, headers=self.headers)
        transactions_datas = []
        for transactions in r.json().get("cardTransactions"):
            try:
                if transactions.get("card").get("alias") in args:
                    transactions_datas.append({
                        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                        "description": transactions.get("payee").get("name"),
                        "alias": transactions.get("card").get("alias"),
                        "amount": transactions.get("amount"),
                        "status": transactions.get("status"),
                        "cardTransactionId": transactions.get("cardTransactionId"),
                        "lastFour": transactions.get("card").get("lastFour"),
                    })
            except AttributeError as e:
                logging.warning(str(e))
        for alias_data in self.alias_data():
            for transactions_data in transactions_datas:
                if transactions_data.get("card") == alias_data.get("alias"):
                    transactions_data.update({
                        "availableAmount": alias_data.get("availableAmount")
                    })
        return transactions_datas

    def retrieve_card(self, cardid=896434):
        url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
        r = requests.get(url=url, headers=self.headers)
        print(r.json())

    # 查询用户的所有金额
    def all_alias_money(self):
        try:
            url = [
                "https://api.bentoforbusiness.com/cards?index=0&limit=1000",
                "https://api.bentoforbusiness.com/cards?index=500&limit=1000",
                ]
            headers = {
                "Authorization": GetToken()
            }
            data = []
            r1 = requests.get(url=url[0], headers=headers)
            for i1 in r1.json().get("cards"):
                data.append({
                    "availableAmount": i1.get("availableAmount"),
                    "cardid": i1.get("cardId"),
                })
            r2 = requests.get(url=url[1], headers=headers)
            for i2 in r2.json().get("cards"):
                data.append({
                    "availableAmount": i2.get("availableAmount"),
                    "cardid": i2.get("cardId"),
                })
            data.append({
                "len": len(data)
            })
            return data
        except Exception as e:
            logging.warning(str(e))
            return []


def main_alias_datas():
    t = TransactionRecord().alias_data()
    return t


if __name__ == "__main__":
    print(TransactionRecord().alias_data())
    # print(TransactionRecord().card_transactions("Dan Pham"))
    # TransactionRecord().retrieve_card()
