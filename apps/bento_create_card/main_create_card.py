import requests
import json
import time
from apps.bento_create_card.config import bento_data, GetToken
from apps.bento_create_card.sqldata_native import SqlDataNative


class CreateCard(object):
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "authorization": GetToken(),
        }

    def create_card(self, card_alias, card_amount, label, attribution):
        user_data = {}
        url = "https://api.bentoforbusiness.com/cards"
        r = requests.post(url=url, data=json.dumps(
            bento_data(card_alias=card_alias, card_amount=card_amount, attribution=attribution)), headers=self.headers)
        user_data["alias"] = r.json().get("alias")
        user_data["cardId"] = r.json().get("cardId")
        user_data["card_amount"] = card_amount
        if user_data.get("cardId"):
            pan_data = self.get_pan(cardid=user_data.get("cardId"))
            user_data.update(pan_data)
            expriation_data = self.get_expiration(cardid=user_data.get("cardId"))
            user_data.update(expriation_data)
            # update alias card_id, card_amount
            SqlDataNative().insert_new_account(alias=user_data.get("alias"), card_id=user_data.get("cardId"),
                                               card_amount=card_amount, card_number=user_data.get("pan"),
                                               card_cvv=user_data.get("cvv"), label=label,
                                               card_validity=user_data.get("expiration"), attribution=attribution,
                                               create_time=time.strftime('%Y-%m-%d %H:%M:%S',
                                                                         time.localtime(time.time())))
            self.billing_address(user_data.get("cardId"))
            """
            d = BentoCard(alias=user_data.get("alias"), card_id=user_data.get("cardId"), card_amount=card_amount, card_number=user_data.get("pan"),
                          card_cvv=user_data.get("cvv"), label=label,card_validity=user_data.get("expiration"),attribution=attribution, 
                          create_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            try:
                session.add(d)
                session.commit()
            except sqlalchemy.exc.InvalidRequestError as e:
                session.rollback()
            except Exception as e:
                session.rollback()
            finally:
                session.close()
            """
        return user_data

    # 获取pan cvv
    def get_pan(self, cardid):
        url = "https://api.bentoforbusiness.com/cards/{}/pan".format(cardid)
        time.sleep(3)
        response = requests.get(url=url, headers=self.headers)
        return {
            "pan": response.json().get("pan"),
            "cvv": response.json().get("cvv")
        }

    # 获取有效期
    def get_expiration(self, cardid):
        url = "https://api.bentoforbusiness.com/cards/{}".format(cardid)
        time.sleep(3)
        response = requests.get(url=url, headers=self.headers)
        return {
            "expiration": response.json().get("expiration")
        }

    def billing_address(self, card_id):
        url = "https://api.bentoforbusiness.com/cards/{}/billingaddress".format(card_id)
        data = {
                "id": 91308,
                "street": "1709 Elmwood Dr",
                "city": "Harlingen",
                "country": "US",
                "zipCode": "78550",
                "state": "TX",
                "addressType": "BUSINESS_ADDRESS",
                "bentoType": "com.bentoforbusiness.entity.business.BusinessAddress"
            }
        respone = requests.put(url, headers=self.headers, data=json.dumps(data))
        if respone.status_code == 200:
            return True
        else:
            return False


# 单张开卡
def main_createcard(limit_num, card_amount, label, attribution):
    """

    :param limit_num:开卡的数量
    :param card_amount: 开卡的金额
    :param label: 开卡的备注
    :return: 返回开卡的数据并入库
    """
    for i in SqlDataNative().search_data(limit_num=limit_num):
        c = CreateCard().create_card(card_alias=i.get("username"), card_amount=card_amount, label=label,
                                     attribution=attribution)
        return c


def get_bento_data(cardid):
    pan = CreateCard().get_pan(cardid)
    expiration = CreateCard().get_expiration(cardid)
    return {
        "pan": pan.get("pan"),
        "cvv": pan.get("cvv"),
        "expiration": expiration.get("expiration"),
    }


if __name__ == "__main__":
    s = CreateCard()
    s.billing_address(9898)
    print(s)
    # main(limit_num=3, card_amount=300, label="杨经理kevin")
    pass
