import time
import json
import requests
from datetime import datetime
from apps.bento_create_card.public import Key, get_time

def change_time(dt):
    if dt:
        #转换成时间数组
        timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
        #转换成时间戳
        timestamp = time.mktime(timeArray)
        return int(timestamp * 1000)
    else:
        return int(time.time()*1000) 
        

def cut_list(ls, n):
    return [ls[i:i + n] for i in range(0, len(ls), n)]

def bento_data(card_alias, card_amount, attribution):
    customStartDate, customEndDate = get_time()
    data =  {
        "type":"CategoryCard",
        "virtualCard":True,
        "shippingMethod":"STANDARD",
        "blockInternationalTransactions":False,
        "blockOnlineTransactions":False,
        "allowedDaysActive":False,
        "allowedCategoriesActive":False,
        "alias": card_alias,
        "spendingLimit":{
            "active":True,
            "amount":card_amount,
            "period":"Custom",
            "customStartDate":customStartDate,
            "customEndDate":customEndDate},
        "allowedDays":[
            "MONDAY","TUESDAY",
            "WEDNESDAY","THURSDAY",
            "FRIDAY","SATURDAY","SUNDAY"],
        "allowedCategories":[
            {"transactionCategoryId":7,"name":"Business Services","type":"SPENDING","group":"Services","description":"Photography, Secretarial, Computer Consulting, etc.","mccs":[],"bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":7},

            {"transactionCategoryId":8,"name":"Professional Services","type":"SPENDING","group":"Services","description":"Insurance, Legal, Real Estate, Doctors, Medical, etc.","mccs":[],"bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":8},

            {"transactionCategoryId":16,"name":"Financial Services","type":"SPENDING","group":"Services","description":"Money order, OTC Cash Disbursement, etc.","mccs":[],"bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":16},

            {"transactionCategoryId":17,"name":"Amusement and Entertainment","type":"SPENDING","group":"Food & Drink","description":"Movie Theaters, Pool Halls, Bowling Alleys, etc.","mccs":[],"bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":17}
        ],
        "billingAddress":
            {
                "id":91308,
                "street":"61 Oxbow Rd",
                "city":"FRAMINGHAM",
                "country":"US",
                "zipCode":"01701",
                "state":"MA",
                "addressType":"BUSINESS_ADDRESS",
                "bentoType":"com.bentoforbusiness.entity.business.BusinessAddress"
            }
    }
    if attribution == "杨经理FB1" or attribution == "gt":
        data.update({
            "allowedCategories":  [
                {"transactionCategoryId":7,"name":"Business Services","group":"Services","bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":7},
                {"transactionCategoryId":8,"name":"Professional Services","group":"Services","bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":8},
                {"transactionCategoryId":11,"name":"Retail and Miscellaneous Stores","group":"Retail & Goods","bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":11},
                {"transactionCategoryId":16,"name":"Financial Services","group":"Services","bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":16},
                {"transactionCategoryId":17,"name":"Amusement and Entertainment","group":"Food & Drink","bentoType":"com.bentoforbusiness.entity.card.TransactionCategory","id":17}
            ]
        })
    return data

def RefreshToken():
    token_url = "{}{}".format(Key.URL, "sessions")
    data = {
        "accessKey": Key.ACCESSKEY,
        "secretKey": Key.SECRETKEY,
    }
    token = requests.post(url=token_url, data=json.dumps(data))
    d = {
        "token": token.headers.get("authorization"),
        "time": datetime.now().hour
    }
    with open("/bento_web_version/apps/bento_create_card/product_key.txt", "w") as f:
        f.write(json.dumps(d))
    return d.get("token")


def GetToken():
    with open("/bento_web_version/apps/bento_create_card/product_key.txt", "r") as f:
        token = f.read()
    if json.loads(token).get("time") != datetime.now().hour:
        bento_token = RefreshToken()
        return bento_token
    return json.loads(token).get("token")


if __name__ == "__main__":
    pass
