import re

import requests
import json
import datetime
import logging
import operator
import time
from apps.bento_create_card.public import change_today
from config import cache
from tools_me.other_tools import finance_required, sum_code, xianzai_time
from tools_me.parameter import RET, MSG
from flask import render_template, request, jsonify, session, url_for, redirect
from tools_me.mysql_tools import SqlData
from apps.bento_create_card.sqldata_native import SqlDataNative
from apps.bento_create_card.main_transactionrecord import TransactionRecord
from flask.views import MethodView
from . import finance_blueprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


@finance_blueprint.route('/logout/')
@finance_required
def logout():
    session.pop("finance")
    return redirect(url_for('finance.financelogin'))


class FinanceLogin(MethodView):

    def __init__(self):
        self.user_data = {
            "finance": "finance",
            "BentoKH": "2m83h2",
        }

    def get(self):
        finance_id = session.get("finance")
        if finance_id:
            return redirect(url_for('finance.financeindex'))
        return render_template('finance/admin_login.html')

    def post(self):
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        data = json.loads(request.form.get('data'))
        account = data.get('account')
        password = data.get('password')
        if account in self.user_data.keys() and self.user_data.get(account) == password:
            session['finance'] = account
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '账号或密码错误!'})


class FinanceIndex(MethodView):
    decorators = [finance_required]

    def get(self):
        admin_user = session.get("finance")
        sum_balance = SqlDataNative.count_admin_decline()
        card_use = SqlDataNative.count_bento_data(sqld="")
        card_no = SqlDataNative.count_bento_data(sqld="where label='已注销'")
        card_un = SqlDataNative.count_bento_data(sqld="where label!='已注销'")
        context = dict()
        context['admin_name'] = admin_user
        # context['spent'] = spent
        context['advance'] = sum_balance
        context['card_use'] = card_use
        context['card_no'] = card_no
        context['card_un'] = card_un
        return render_template('finance/index.html', **context)


@finance_blueprint.route('/add_account/', methods=['POST'])
@finance_required
def add_account():
    results = {"code": RET.OK, "msg": MSG.OK}
    try:
        data = json.loads(request.form.get('data'))
        name = data.get('name')
        account = data.get('account')
        password = data.get('password')
        phone_num = data.get('phone_num')
        create_price = float(data.get('create_price'))
        refund = float(data.get('refund'))
        min_top = float(data.get('min_top'))
        max_top = float(30000)
        note = data.get('note')
        ed_name = SqlData.search_user_field_name('account', name)
        if ed_name:
            results['code'] = RET.SERVERERROR
            results['msg'] = '该用户名已存在!'
            return jsonify(results)
        if phone_num:
            ret = re.match(r"^1[35789]\d{9}$", phone_num)
            if not ret:
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        else:
            phone_num = ""
        SqlData.insert_account(account, password, phone_num, name, create_price, refund, min_top, max_top, note)
        # 创建用户后插入充值数据
        pay_num = sum_code()
        t = xianzai_time()
        user_id = SqlData.search_user_field_name('id', name)
        SqlData.insert_top_up(pay_num, t, 0, 0, 0, user_id)
        SqlData.insert_account_trans(date=t, trans_type="充值", do_type="支出", num=0, card_no=0, do_money=0,
                                       hand_money=0, before_balance=0, balance=0, account_id=user_id)
        return jsonify(results)
    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@finance_blueprint.route('/account_info/', methods=['GET'])
@finance_required
def account_info():
    page = request.args.get('page')
    limit = request.args.get('limit')
    customer = request.args.get('customer')
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if customer:
        sql = "WHERE name LIKE '%" + customer + "%'"
    else:
        sql = ''
    task_one = SqlData.search_account_info(sql)
    if len(task_one) == 0:
        results['MSG'] = MSG.NODATA
        return results
    task_info = list()
    all_moneys = TransactionRecord().all_alias_money()
    for u in task_one:
        u_id = u.get('u_id')
        # card_count = SqlData.search_card_count(u_id, '')
        out_money = SqlData.search_trans_sum(u_id)
        bento_income_money = SqlData.search_income_money(u_id)
        # u['card_num'] = card_count
        u['out_money'] = float("%.2f" % float(out_money - bento_income_money))

        account_all_amount = 0
        # all_moneys = TransactionRecord().all_alias_money()
        all_cardids = SqlDataNative.attribution_fount_cardid(alias=u.get("name"))
        if len(all_moneys) > 0 and len(all_cardids) > 0:
            for all_cardid in all_cardids:
                for all_money in all_moneys:
                    if all_cardid == all_money.get("cardid"):
                        account_all_amount = account_all_amount + all_money.get("availableAmount")
        count_del_quant = SqlDataNative.count_del_data(alias=u.get("name"))
        u['del_card_num'] = count_del_quant
        u['account_all_money'] = float("%.2f" % account_all_amount)
        u['card_balance'] = float("%.2f" % float(out_money - bento_income_money - account_all_amount))
        u['in_card_num'] = len(all_cardids)
        task_info.append(u)
    page_list = list()
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@finance_blueprint.route('/card_all/', methods=['GET'])
@finance_required
def card_info_all():
    try:
        limit = request.args.get('limit')
        page = request.args.get('page')

        field = request.args.get('field')
        value = request.args.get('value')

        if field == "card_cus":
            sql = "WHERE label LIKE'%{}%'".format(value)
        elif field == "card_no":
            sql = "WHERE card_number LIKE '%{}%'".format(value)
        elif field == "account_no":
            sql = "WHERE attribution LIKE '%{}%'".format(value)
        else:
            sql = ""

        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        # info_list = SqlData.search_card_info_admin(sql)
        info_list = SqlDataNative.admin_alias_data(sqld=sql)
        if not info_list:
            results['code'] = RET.OK
            results['msg'] = MSG.NODATA
            return jsonify(results)
        # info_list = sorted(info_list, key=operator.itemgetter('start_time'))
        page_list = list()
        for i in range(0, len(info_list), int(limit)):
            page_list.append(info_list[i:i + int(limit)])
        results['data'] = page_list[int(page) - 1]
        results['count'] = len(info_list)
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@finance_blueprint.route('/decline_data/', methods=['GET'])
@finance_required
def decline_data():
    page = request.args.get('page')
    limit = request.args.get('limit')

    time_range = request.args.get('time_range')
    card_num = request.args.get('order_num')
    acc_name = request.args.get('acc_name')
    time_sql = ""
    card_sql = ""
    accname_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND date BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    if card_num:
        card_sql = "AND last_four LIKE '%{}%'".format(card_num)
    if acc_name:
        accname_sql = "AND attribution LIKE '%{}%'".format(acc_name)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    task_info = SqlDataNative.admin_decline_data(accname_sql, card_sql, time_sql)
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter("date"))
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results["data"] = page_list[int(page) - 1]
    results["count"] = len(task_info)
    return jsonify(results)


@finance_blueprint.route('/account_decline/', methods=['GET'])
@finance_required
def account_decline():
    page = request.args.get('page')
    limit = request.args.get('limit')
    alias_name = request.args.get("acc_name")
    ca_data = cache.get('finance_decline_data')
    if not ca_data:
        data = SqlDataNative.bento_alltrans()
        acc_sum_trans = dict()
        for i in data:
            cus = i.get('before_balance')
            if cus not in acc_sum_trans:
                cus_dict = dict()
                cus_dict[cus] = {'decl': 0, 't_data': 0, 'three_decl': 0, 'three_tran': 0}
                acc_sum_trans.update(cus_dict)
        for n in data:
            date = n.get('date')
            do_type = n.get('do_type')
            cus = n.get('before_balance')
            value = {'t_data': acc_sum_trans.get(cus).get('t_data') + 1}
            acc_sum_trans.get(cus).update(value)
            if do_type == 'DECLINED':
                value = {'decl': acc_sum_trans.get(cus).get('decl') + 1}
                acc_sum_trans.get(cus).update(value)
            today_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            max_today = datetime.datetime.strptime("{} {}".format(change_today(today_time, 0), "23:59:59"),
                                                   '%Y-%m-%d %H:%M:%S')
            min_today = datetime.datetime.strptime("{} {}".format(change_today(today_time, -3), "23:59:59"),
                                                   '%Y-%m-%d %H:%M:%S')
            trans_t = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            if min_today <= trans_t <= max_today:
                value = {'three_tran': acc_sum_trans.get(cus).get('three_tran') + 1}
                acc_sum_trans.get(cus).update(value)
            if min_today < trans_t < max_today and do_type == 'DECLINED':
                value = {'three_decl': acc_sum_trans.get(cus).get('three_decl') + 1}
                acc_sum_trans.get(cus).update(value)
        res = list()
        for n in acc_sum_trans:
            value = acc_sum_trans.get(n)
            value['alias'] = n
            value['all_bili'] = "{} {}".format(float("%.4f" % (value.get('decl') / value.get('t_data') * 100)),
                                               "%") if value.get('decl') != 0 else 0
            value['bili'] = "{} {}".format(float("%.4f" % (value.get('three_decl') / value.get('three_tran') * 100)),
                                           "%") if value.get('three_tran') != 0 else 0
            if value.get('three_tran') != 0 and value.get('three_decl') / value.get('three_tran') > 0.1:
                value['show'] = 'T'
            else:
                value['show'] = 'F'
            res.append(value)
            # 设置缓存
        cache.set('finance_decline_data', res, timeout=60 * 60 * 6)

    else:
        res = ca_data
        if alias_name:
            res_alias = list()
            for i in res:
                if alias_name in i.get('alias'):
                    res_alias.append(i)
            return jsonify({"code": 0, "count": len(res_alias), "data": res_alias, "msg": "SUCCESSFUL"})
        return jsonify({"code": 0, "count": len(res), "data": res, "msg": "SUCCESSFUL"})


@finance_blueprint.route('/all_trans/', methods=['GET'])
@finance_required
def all_trans():
    page = request.args.get("page")
    limit = request.args.get("limit")
    # 客户名
    acc_name = request.args.get("acc_name")
    # 卡的名字
    order_num = request.args.get("order_num")
    # 时间范围
    time_range = request.args.get("time_range")
    # 操作状态
    trans_status = request.args.get("trans_status")
    # 交易类型
    trans_store = request.args.get("trans_store")

    args_list = []
    ca_data = cache.get('all_trans')
    # 设置缓存处理查询到的大量数据(6小时)
    if ca_data:
        data = ca_data
    else:
        data = SqlDataNative.bento_alltrans()
        cache.set('all_trans', data, timeout=60 * 60 * 6)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(data) == 0:
        results["MSG"] = MSG.NODATA
        return jsonify(results)

    # 下列判断为判断是否有搜索条件根据条件过滤
    acc_list = list()
    if acc_name:
        # args_list.append(acc_name)
        for i in data:
            cus = i.get('before_balance')
            if acc_name == cus:
                acc_list.append(i)
    else:
        acc_list = data

    order_list = list()
    if order_num:
        # args_list.append(order_num)
        for c in acc_list:
            card_name = c.get('hand_money')
            if order_num in card_name:
                order_list.append(c)
    else:
        order_list = acc_list

    trans_list = list()
    if trans_status:
        args_list.append(trans_status)
        for i in order_list:
            do_type = i.get('card_num')
            if trans_status in do_type:
                trans_list.append(i)
    else:
        trans_list = order_list

    time_list = list()
    if time_range:
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        min_tuple = datetime.datetime.strptime(min_time, '%Y-%m-%d %H:%M:%S')
        max_tuple = datetime.datetime.strptime(max_time, '%Y-%m-%d %H:%M:%S')
        for d in trans_list:
            dat = datetime.datetime.strptime(d.get("date"), '%Y-%m-%d %H:%M:%S')
            if min_tuple < dat < max_tuple:
                time_list.append(d)
    else:
        time_list = trans_list

    store_list = list()
    if trans_store:
        for i in time_list:
            trans_type = i.get('trans_type')
            if trans_store in trans_type:
                store_list.append(i)
    else:
        store_list = trans_list

    if not store_list:
        return jsonify({'code': RET.OK, 'msg': MSG.NODATA})
    page_list = list()
    data = sorted(store_list, key=operator.itemgetter("date"))
    data = list(reversed(data))
    for i in range(0, len(data), int(limit)):
        page_list.append(data[i: i + int(limit)])
    results["data"] = page_list[int(page) - 1]
    results["count"] = len(data)
    return jsonify(results)


@finance_blueprint.route('/top_history/', methods=['GET'])
@finance_required
def top_history():
    page = request.args.get('page')
    limit = request.args.get('limit')

    acc_name = request.args.get('acc_name')
    order_num = request.args.get('order_num')
    time_range = request.args.get('time_range')

    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}

    name_sql = ""
    order_sql = ""
    time_sql = ""
    if acc_name:
        name_sql = "account.name ='" + acc_name + "'"
    if order_num:
        order_sql = "top_up.pay_num = '" + order_num + "'"
    if time_range:
        min_time = time_range.split(' - ')[0]
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "top_up.time BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"

    if name_sql and time_sql and order_sql:
        sql_all = "WHERE " + name_sql + " AND " + order_sql + " AND " + time_sql
    elif name_sql and order_sql:
        sql_all = "WHERE " + name_sql + " AND " + order_sql
    elif time_sql and order_sql:
        sql_all = "WHERE " + time_sql + " AND " + order_sql
    elif name_sql and time_sql:
        sql_all = "WHERE " + name_sql + " AND " + time_sql
    elif name_sql:
        sql_all = "WHERE " + name_sql
    elif order_sql:
        sql_all = "WHERE " + order_sql
    elif time_range:
        sql_all = "WHERE " + time_sql
    else:
        sql_all = ""

    task_info = SqlData.search_top_history(sql_all)

    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter('time'))
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    data = page_list[int(page) - 1]
    # 处理不同充值类型的显示方式(系统, 退款)
    info_list_1 = list()
    for n in data:
        trans_type = n.get('trans_type')
        # if trans_type == '系统':
        n['refund'] = ''
        info_list_1.append(n)
        """
        elif trans_type == '退款':
            n['refund'] = n.get('money')
            n['money'] = ''
            continue 
        info_list_1.append(n)
        """
    # 查询当次充值时的账号总充值金额
    info_list = list()
    for o in info_list_1:
        x_time = o.get('time')
        user_id = o.get('user_id')
        sum_money = SqlData.search_time_sum_money(x_time, user_id)
        o['sum_balance'] = round(sum_money, 2)
        info_list.append(o)
    results['data'] = info_list_1
    results['count'] = len(task_info)
    return jsonify(results)


@finance_blueprint.route('/bento_refund/', methods=['GET'])
@finance_required
def bento_refund():
    page = request.args.get('page')
    limit = request.args.get('limit')
    acc_name = request.args.get('acc_name')
    order_num = request.args.get('order_num')
    time_range = request.args.get('time_range')

    name_sql = ""
    order_sql = ""
    time_sql = ""

    if acc_name:
        name_sql = "account.name='{}'".format(acc_name)
    if order_num:
        order_sql = "account_trans.card_no='{}'".format(order_num)
    if time_range:
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "account_trans.do_date BETWEEN '{}' and '{}'".format(min_time, max_time)

    if name_sql and time_sql and order_sql:
        sql_all = "AND " + name_sql + " AND " + order_sql + " AND " + time_sql
    elif name_sql and order_sql:
        sql_all = "AND " + name_sql + " AND " + order_sql
    elif time_sql and order_sql:
        sql_all = "AND " + time_sql + " AND " + order_sql
    elif name_sql and time_sql:
        sql_all = "AND " + name_sql + " AND " + time_sql
    elif name_sql:
        sql_all = "AND " + name_sql
    elif order_sql:
        sql_all = "AND " + order_sql
    elif time_range:
        sql_all = "AND " + time_sql
    else:
        sql_all = ""
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    task_info = SqlData.bento_refund_data(sql_all)
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter('time'))
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    data = page_list[int(page) - 1]

    for o in data:
        x_time = o.get("time")
        user_id = o.get("user_id")
        sum_money = SqlData.search_bento_sum_money(user_id=user_id, x_time=x_time)
        sum_refund = SqlData.search_bento_sum_refund(user_id=user_id, x_time=x_time)
        o["sum_balance"] = round(sum_money, 2)
        o["sum_refund"] = round(sum_refund, 2)
    results['data'] = data
    results['count'] = len(task_info)
    return jsonify(results)


@finance_blueprint.route('/account_trans/', methods=['GET'])
@finance_required
def account_trans():
    page = request.args.get('page')
    limit = request.args.get('limit')

    time_range = request.args.get('time_range')
    cus_name = request.args.get('cus_name')
    trans_card = request.args.get('trans_card')
    trans_type = request.args.get('trans_do_type')
    time_sql = ""
    card_sql = ""
    cus_sql = ""
    type_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0]
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND account_trans.do_date BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    if trans_card:
        # card_sql = "AND account_trans.card_no = '" + trans_card.lstrip() + "'"
        card_sql = "AND account_trans.card_no LIKE '%{}%'".format(trans_card.strip())
    if cus_name:
        cus_sql = "AND account.name='" + cus_name + "'"
    if trans_type:
        # type_sql = "AND account_trans.do_type = '" + trans_type + "'"
        type_sql = "AND account_trans.do_type LIKE '%{}%'".format(trans_type)

    task_info = SqlData.search_trans_admin(cus_sql, card_sql, time_sql, type_sql)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter('date'))

    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


finance_blueprint.add_url_rule("/login/", view_func=FinanceLogin.as_view("financelogin"))
finance_blueprint.add_url_rule("/index/", view_func=FinanceIndex.as_view("financeindex"))
