import requests
import time
import logging
from config import GetToken
from sqldata import SqlDataNative
from sqlalchemy_data import session, DeclinedData
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")

class RechargeCard(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": GetToken(),
        }

    def declined_data(self):
        url = "https://api.bentoforbusiness.com/transactions"
        params = {
            "cards": "878540",
        }
        r = requests.get(url=url, headers=self.headers, params=params)
        print(r.status_code)
        transactions_datas = []
        for transactions in r.json().get("cardTransactions"):
            if transactions.get("status") == "DECLINED":
                transactions_datas.append({
                "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                "description": transactions.get("payee").get("name"),
                "alias": transactions.get("card").get("alias"),
                "amount": transactions.get("amount"),
                "status": transactions.get("status"),
                "cardTransactionId": transactions.get("cardTransactionId"),
                "lastFour": transactions.get("card").get("lastFour"),
            })
                d1 = DeclinedData(alias=transactions.get("card").get("alias"), description=transactions.get("payee").get("name"), amount=transactions.get("amount"),
                                  status=transactions.get("status"), date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                                  transaction_id=transactions.get("cardTransactionId"), last_four=transactions.get("card").get("lastFour"), cardid="887490")


        print(transactions_datas)

def bento_declined(cardid):
    url="https://api.bentoforbusiness.com/transactions",
    headers={
        "Content-Type": "application/json",
        "authorization": GetToken(),
    }
    params={
        "cards": "{}".format(cardid),
    }
    res = requests.get(url=url, headers=headers, params=params)
    print(res.url)
    if res:
        return res.json()


def bento_declined_data(response, cardid):
    transactions_datas = []
    for transactions in response.get("cardTransactions"):
        if transactions.get("status") == "DECLINED":
            transactions_datas.append({
                "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                "description": transactions.get("payee").get("name"),
                "alias": transactions.get("card").get("alias"),
                "amount": transactions.get("amount"),
                "status": transactions.get("status"),
                "cardTransactionId": transactions.get("cardTransactionId"),
                "lastFour": transactions.get("card").get("lastFour"),
                "cardid": cardid
            })
            d1 = DeclinedData(alias=transactions.get("card").get("alias"),
                              description=transactions.get("payee").get("name"), amount=transactions.get("amount"),
                              status=transactions.get("status"), date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(transactions.get("transactionDate") / 1000)),
                              transaction_id=transactions.get("cardTransactionId"),last_four=transactions.get("card").get("lastFour"), cardid=cardid, reason="")
            try:
                session.add(d1)
                session.commit()
            except Exception as e:
                logging.warning(str(e))
                session.rollback()
            finally:
                session.close()


def main():
    cardids = SqlDataNative().search_data()
    for i in cardids:
        res = bento_declined(i[0])
        print(res)
        bento_declined_data(res, i[0])


if __name__ == "__main__":
    main()
    # RechargeCard().declined_data()
