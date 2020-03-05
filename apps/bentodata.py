import datetime
import logging
from flask import render_template, request
from apps.bento_create_card.sqldata_native import SqlDataNative
from apps.bento_create_card.main_recharge import main_transaction_data, card_trans
from flask.views import MethodView
from . import bentodata_blueprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class BentoIndex(MethodView):
    def get(self):
        username = request.args.get("username")
        range_time = request.args.get("range_time")
        info_list = []
        if username:
            try:
                cardid = SqlDataNative.alias_fount_cardid(alias=username)
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
            # 判断是否需要根据时间过滤交易信息
            if range_time:
                info_list_t = list()
                start_time = range_time.split(' - ')[0] + ' 00:00:00'
                end_time = range_time.split(' - ')[1] + ' 23:59:59'
                start_t = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                end_t = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                for i in info_list:
                    date = i.get('date')
                    trans_t = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                    if start_t <= trans_t <= end_t:
                        info_list_t.append(i)

                context['pay_list'] = info_list_t
            else:
                context['pay_list'] = info_list
            return render_template('user/card_detail.html', **context)
        return render_template("/bento/bentoupload.html")

    def post(self):
        import os
        import xlrd
        fileobj = request.files["file"]
        fname, fext = os.path.splitext(fileobj.filename)
        upload_name = [".xls", ".xlsx", ]
        if upload_name.count(fext) == 1:
            f = fileobj.read()
            data = xlrd.open_workbook(file_contents=f)
            table = data.sheets()[0]
            cardnames = table.col_values(0)
            context = {}
            context['balance'] = "f_balance"
            context['remain'] = 0
            card_list = list()
            for cardname in cardnames:
                try:
                    cardid = SqlDataNative.alias_fount_cardid(alias=cardname)
                    card_list.append(cardid)
                except Exception as e:
                    continue
            info_list = card_trans(card_list)
            context['pay_list'] = info_list
            return render_template('user/card_detail.html', **context)
        return "上传文件异常"


bentodata_blueprint.add_url_rule("/search/", view_func=BentoIndex.as_view("bentoindex"))
