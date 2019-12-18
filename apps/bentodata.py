import requests
import json
import datetime
import logging
import operator
import time
from apps.bento_create_card.public import change_today
from tools_me.other_tools import xianzai_time, login_required, check_float, make_name, choke_required, sum_code
from tools_me.parameter import RET, MSG, TRANS_STATUS, TRANS_TYPE, DO_TYPE
# from tools_me.RSA_NAME.helen import QuanQiuFu
from tools_me.remain import get_card_remain
from . import user_blueprint
from flask import render_template, request, jsonify, session, g
from tools_me.mysql_tools import SqlData
from apps.bento_create_card.main_create_card import main_createcard, CreateCard, get_bento_data
from apps.bento_create_card.sqldata_native import SqlDataNative
from apps.bento_create_card.main_transactionrecord import main_alias_datas, TransactionRecord
from apps.bento_create_card.main_recharge import main_transaction_data, RechargeCard
from flask.views import MethodView
from . import bentodata_blueprint
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class BentoIndex(MethodView):
    def get(self):
        username = request.args.get("username")
        username_list = []
        info_list=[]
        if username:
            try:
                cardid = SqlDataNative().alias_fount_cardid(alias=username)
            except Exception as e:
                return "信用卡数据不存在"
            transaction_data, availableAmount = main_transaction_data(cards=cardid, alias=username)
            context = {}
            context['balance'] = "f_balance"
            context['remain'] = availableAmount
            for td in transaction_data:
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
            context['pay_list'] = info_list
            return render_template('user/card_detail.html', **context)
        return render_template("/bento/bentoupload.html")
    
    def post(self):
        import os
        import xlrd
        fileobj = request.files["file"]
        fname, fext = os.path.splitext(fileobj.filename)
        upload_name = [".xls", ".xlsx",]
        if upload_name.count(fext) == 1:
            info_list = []
            f = fileobj.read()
            data = xlrd.open_workbook(file_contents=f)
            table = data.sheets()[0]
            cardnames = table.col_values(0)
            context = {}
            context['balance'] = "f_balance"
            context['remain'] = 0
            for cardname in cardnames:
                try:
                    cardid = SqlDataNative().alias_fount_cardid(alias=cardname)
                except Exception as e:
                    continue
                else:
                    transaction_data, availableAmount = main_transaction_data(cards=cardid, alias=cardname)
                    for td in transaction_data:
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
            context['pay_list'] = info_list
            return render_template('user/card_detail.html', **context)
        return "上传文件异常"


bentodata_blueprint.add_url_rule("/bentoindex/", view_func=BentoIndex.as_view("bentoindex"))



