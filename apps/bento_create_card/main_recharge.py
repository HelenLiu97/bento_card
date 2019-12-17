import requests
import json
import time
import logging
# from apps.bento_create_card.sqldata import BentoCard, session
from apps.bento_create_card.config import bento_data, GetToken, cut_list, change_time
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")

class RechargeCard():
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
                data["spendingLimit"]["amount"] = float("%.2f"%bento_use_amount) if float("%.2f"%bento_use_amount) != float("%.2f"%spendingLimit_amount) else float("%.2f"%bento_use_amount) - 0.01
                data["availableAmount"] = float("%.2f"%bento_use_amount)
                response = requests.put(url=url, headers=self.headers, data=json.dumps(data))
                if response.json().get("availableAmount") > bento_availableAmount:
                    return {"error_msg": "转移失败, 所剩余额未扣减"}
                return {"msg": "已有金额: {}, 转移金额: {}, 卡内可用余额: {}".format(bento_availableAmount, recharge_amount,response.json().get("availableAmount"))}
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
                data["spendingLimit"]["amount"] = float("%.2f"%bento_use_amount) if float("%.2f"%bento_use_amount) != float("%.2f"%spendingLimit_amount) else float("%.2f"%bento_use_amount) - 0.01 
                data["availableAmount"] = float("%.2f"%bento_use_amount)
                response = requests.put(url=url, headers=self.headers, data=json.dumps(data))
                if response.json().get("availableAmount") == bento_availableAmount:
                    return {"error_msg": "充值失败, 所剩余额未扣减"}
                return {"msg": "已有金额: {}, 充值金额: {}, 可用余额: {}".format(bento_availableAmount, recharge_amount,response.json().get("availableAmount"))}
        return {"error_msg": "bento后台数据查无此账号"}

    def transaction_data(self, cards):
        url = "https://api.bentoforbusiness.com/transactions"
        params = {
            "cards": "{}".format(cards),
            "dateStart": 1570032000000,
        }
        r = requests.get(url=url, headers=self.headers, params=params)
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
    def declined_statistics(self, card_id,):
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





if __name__ == "__main__":
    # r = RechargeCard().recharge(cardnumber="9845", recharge_amount=0.1, alias="Margie Simpson")
    RechargeCard().test()
