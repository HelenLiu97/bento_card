import json
import datetime
import logging
import operator
import re
import time
import os
from apps.bento_create_card.public import change_today
from flask import request, render_template, jsonify, session, g
from tools_me.mysql_tools import SqlData
from tools_me.other_tools import admin_required, sum_code, xianzai_time, get_nday_list, check_float
from tools_me.parameter import RET, MSG, DIR_PATH
from tools_me.redis_tools import RedisTool
from tools_me.send_sms.send_sms import CCP
from tools_me.sm_photo import sm_photo
from apps.bento_create_card.sqldata_native import SqlDataNative
from . import admin_blueprint
from config import cache


@admin_blueprint.route('/xiao_ma/', methods=['GET'])
def xiaoma():
    res = SqlData.search_account_info('')
    info_list = list()
    # 去除密码信息
    for i in res:
        i.pop('password')
        i.pop('u_id')
        info_list.append(i)
    context = dict()
    context['accounts'] = info_list
    return render_template('admin/account_xiaoma.html', **context)


@admin_blueprint.route('/account_chart_line/', methods=['GET', 'POST'])
@admin_required
def account_chart_line():
    if request.method == 'GET':
        account_name = request.args.get('user_name')
        context = dict()
        context['user_name'] = account_name
        return render_template('admin/account_chart_line.html', **context)
    if request.method == 'POST':
        account_name = request.args.get('user_name')
        info = SqlDataNative.one_bento_alltrans(account_name)
        day_list = get_nday_list(10)
        day_dict = dict()
        for d in day_list:
            day_dict.update({d: 0})
        for i in info:
            do_money = i.get('do_money')
            date = i.get('date').split(' ')[0]
            if date in day_list:
                day_dict[date] = day_dict.get(date) + do_money
        res_list = list()
        for k in day_dict:
            res_l = list()
            res_l.append(k)
            res_l.append(day_dict.get(k))
            res_list.append(res_l)
        return jsonify({'code': RET.OK, 'data': res_list})


@admin_blueprint.route('/acc_pay/', methods=['POST'])
@admin_required
def acc_pay():
    if request.method == 'POST':
        money = request.form.get('money')
        name = request.form.get('name')
        try:
            _money = float(money)
            f_money = round(_money, 2)
            if f_money < 0:
                return jsonify({'code': RET.SERVERERROR, 'msg': '请输入正数金额！'})
            balance = SqlData.search_user_field_name('balance', name)
            if f_money > balance:
                return jsonify({'code': RET.SERVERERROR, 'msg': '扣费余额不足！'})
            user_id = SqlData.search_user_field_name('id', name)
            SqlData.update_balance(-f_money, user_id)
            a_balance = SqlData.search_user_field("balance", user_id)
            # balance = before_balance - create_price
            n_time = xianzai_time()
            SqlData.insert_account_trans(n_time, '支出', '系统扣费', 0000, '后台手工扣费',
                                         f_money, 0, balance, a_balance, user_id)
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': '请输入正确的消费金额！'})


@admin_blueprint.route('/edit_bank_money/', methods=['POST'])
@admin_required
def edit_bank_money():
    bank_number = request.form.get('bank_number')
    money = request.form.get('money')
    SqlData.update_bank_day_top(bank_number, float(money))
    return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/top_bank/', methods=['GET'])
@admin_required
def top_bank():
    bank_number = request.args.get('bank_number')
    status = SqlData.search_bank_status(bank_number)
    # status:1为锁定，0为正常，2为置顶
    if status == 2:
        SqlData.update_bank_status(bank_number, 0)
    else:
        res = SqlData.search_bank_info('WHERE status=2')
        if res:
            return jsonify({'code': RET.SERVERERROR, 'msg': '请取消已置顶银行卡后重试！'})
        SqlData.update_bank_status(bank_number, 2)
    return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/lock_bank/', methods=['GET'])
@admin_required
def lock_bank():
    bank_number = request.args.get('bank_number')
    status = SqlData.search_bank_status(bank_number)
    if status == 0:
        SqlData.update_bank_status(bank_number, 1)
    else:
        SqlData.update_bank_status(bank_number, 0)
    return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/del_bank/', methods=['GET'])
@admin_required
def del_bank():
    bank_number = request.args.get("bank_number")
    SqlData.del_benk_data(bank_number=bank_number)
    return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/bank_info/', methods=['GET', 'POST'])
@admin_required
def bank_info():
    if request.method == "GET":
        results = {}
        push_json = SqlData.search_bank_info()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        if not push_json:
            results['msg'] = MSG.NODATA
            return jsonify(results)
        results['data'] = push_json
        results['count'] = len(push_json)
        return jsonify(results)


@admin_blueprint.route('/bank_msg/', methods=['GET', 'POST'])
@admin_required
def bank_msg():
    if request.method == 'GET':
        return render_template('admin/bank_info.html', )
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('data'))
            results = {"code": RET.OK, "msg": MSG.OK}
            bank_name = data.get("bank_people")
            bank_number = data.get("bank_email")
            bank_address = data.get("bank_address")
            # 插入数据
            SqlData.insert_bank_info(bank_name=bank_name, bank_number=bank_number, bank_address=bank_address)
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@admin_blueprint.route('/edit_code/', methods=['GET', 'POST'])
@admin_required
def edit_code():
    if request.method == 'GET':
        try:
            url = request.args.get('url')
            status = SqlData.search_qr_field('status', url)
            if status == 1:
                now_status = 0
            else:
                now_status = 1
            SqlData.update_qr_info('status', now_status, url)
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})
    if request.method == 'POST':
        url = request.args.get('url')
        SqlData.del_qr_code(url)
        return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/ex_change/', methods=['GET', 'POST'])
@admin_required
def ex_change():
    if request.method == 'GET':
        return render_template('admin/exchange_edit.html')
    if request.method == 'POST':
        try:
            results = {"code": RET.OK, "msg": MSG.OK}
            data = json.loads(request.form.get('data'))
            exchange = data.get('exchange')
            ex_range = data.get('ex_range')
            hand = data.get('hand')
            dollar_hand = data.get('dollar_hand')
            if exchange:
                SqlData.update_admin_field('ex_change', float(exchange))
            if ex_range:
                SqlData.update_admin_field('ex_range', float(ex_range))
            if hand:
                SqlData.update_admin_field('hand', float(hand))
            if dollar_hand:
                SqlData.update_admin_field('dollar_hand', float(dollar_hand))
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@admin_blueprint.route('/upload_code/', methods=['POST'])
@admin_required
def up_pay_pic():
    results = {'code': RET.OK, 'msg': MSG.OK}
    file = request.files.get('file')
    file_name = sum_code() + ".png"
    # file_path = DIR_PATH.PHOTO_DIR + "/" + file_name
    file_path = os.path.join(DIR_PATH.PHOTO_DIR, file_name)
    file.save(file_path)
    filename = sm_photo(file_path)
    if filename == 'F':
        os.remove(file_path)
        return jsonify({'code': RET.SERVERERROR, 'msg': '不可上传相同图片,请重新上传!'})
    if filename:
        # 上传成功后插入信息的新的收款方式信息
        os.remove(file_path)
        t = xianzai_time()
        SqlData.insert_qr_code(filename, t)
        return jsonify(results)
    else:
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@admin_blueprint.route('/qr_info/', methods=['GET'])
@admin_required
def qr_info():
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    info_list = SqlData.search_qr_code('')
    if not info_list:
        results['msg'] = MSG.NODATA
        return jsonify(results)
    results['data'] = info_list
    results['count'] = len(info_list)
    return jsonify(results)


@admin_blueprint.route('/top_msg/', methods=['GET', 'POST'])
@admin_required
def top_msg():
    if request.method == 'GET':
        push_json = SqlData.search_admin_field('top_push')
        info_list = list()
        if push_json:
            push_dict = json.loads(push_json)
            for i in push_dict:
                info_dict = dict()
                info_dict['user'] = i
                info_dict['email'] = push_dict.get(i)
                info_list.append(info_dict)
        context = dict()
        context['info_list'] = info_list
        return render_template('admin/top_msg.html', **context)
    if request.method == 'POST':
        try:
            results = {"code": RET.OK, "msg": MSG.OK}
            data = json.loads(request.form.get('data'))
            top_people = data.get('top_people')
            email = data.get('email')
            push_json = SqlData.search_admin_field('top_push')
            if not push_json:
                info_dict = dict()
                info_dict[top_people] = email
            else:
                info_dict = json.loads(push_json)
                if top_people in info_dict and email == '删除':
                    info_dict.pop(top_people)
                else:
                    info_dict[top_people] = email
            json_info = json.dumps(info_dict, ensure_ascii=False)
            SqlData.update_admin_field('top_push', json_info)
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@admin_blueprint.route('/qr_code/', methods=['GET', 'POST'])
@admin_required
def qr_code():
    if request.method == 'GET':
        return render_template('admin/qr_code.html')


@admin_blueprint.route('/notice_edit/', methods=['GET', 'POST'])
@admin_required
def notice():
    if request.method == 'GET':
        note = SqlDataNative.bento_notice()
        context = dict()
        context['note'] = note
        return render_template('admin/notice.html', **context)
    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        note = data.get('note')
        SqlDataNative.update_bento_notice(note)
        return jsonify({"code": RET.OK, "msg": MSG.OK})


@admin_blueprint.route('/all_trans', methods=['GET'])
@admin_required
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
        cache.set('all_trans', data, timeout=60*60*6)
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
        store_list = time_list

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


@admin_blueprint.route('/account_decline', methods=['GET'])
@admin_required
def account_decline():
    # 当前用户较少不采取分页
    page = request.args.get('page')
    limit = request.args.get('limit')
    alias_name = request.args.get("acc_name")
    ca_data = cache.get('decline_data')
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
        cache.set('decline_data', res, timeout=60 * 60 * 6)

    else:
        res = ca_data
        if alias_name:
            res_alias = list()
            for i in res:
                if alias_name in i.get('alias'):
                    res_alias.append(i)
            return jsonify({"code": 0, "count": len(res_alias), "data": res_alias, "msg": "SUCCESSFUL"})
        return jsonify({"code": 0, "count": len(res), "data": res, "msg": "SUCCESSFUL"})


@admin_blueprint.route('/decline_data', methods=['GET'])
@admin_required
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
    # task_info = SqlDataNative.search_decline_data("大龙", "", "")
    task_info = SqlDataNative.admin_decline_data(accname_sql, card_sql, time_sql)
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter("date"))
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results["data"] = page_list[int(page) - 1]
    results["count"] = len(task_info)
    return jsonify(results)


@admin_blueprint.route('/bento_refund', methods=['GET'])
@admin_required
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
    # 处理不同充值类型的显示方式(系统, 退款)
    """
    sum_data = 0
    for i in list(reversed(data)):
        sum_data = float(i.get("money")) + sum_data
        i.update({
            "sum_balance": sum_data
        })
    info_list_1 = list()
    for n in data:
        trans_type = n.get('trans_type')
        if trans_type == '退款':
            n['refund'] = ''
            info_list_1.append(n)
    # 查询当次充值时的账号总充值金额
    info_list = list()
    for o in info_list_1:
        x_time = o.get('time')
        user_id = o.get('user_id')
        sum_money = SqlData.search_time_sum_money(x_time, user_id)
        o['sum_balance'] = round(sum_money, 2)
        info_list.append(o)
    """
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


@admin_blueprint.route('/cus_log', methods=['GET'])
@admin_required
def cus_log():
    page = request.args.get('page')
    limit = request.args.get('limit')

    cus_name = request.args.get('cus_name')
    time_range = request.args.get('time_range')
    time_sql = ""
    cus_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0]
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND log_time BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    if cus_name:
        cus_sql = "AND customer='" + cus_name + "'"

    task_info = SqlData.search_account_log(cus_sql, time_sql)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return results
    page_list = list()
    task_info = sorted(task_info, key=operator.itemgetter('log_time'))
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@admin_blueprint.route('/account_trans/', methods=['GET'])
@admin_required
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
    """
    for task_inf in task_info:
        bento_card_number = task_inf.get("card_no")
        if bento_card_number:
            bento_alias = SqlDataNative.cardnum_fount_alias(bento_card_number.strip())
            task_inf.update({
                "do_type": bento_alias
            })
        else:
            task_inf.update({
                "do_type": ""
            })
    """
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


@admin_blueprint.route('/card_all', methods=['GET'])
@admin_required
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
        elif field == "card_name":
            sql = "WHERE alias LIKE '%{}%'".format(value)
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


@admin_blueprint.route('/sub_middle_money', methods=['POST'])
@admin_required
def sub_middle_money():
    info_id = request.args.get('id')
    n_time = xianzai_time()
    SqlData.update_middle_sub('已确认', n_time, int(info_id))
    return jsonify({"code": RET.OK, "msg": MSG.OK})


@admin_blueprint.route('/middle_money', methods=['GET'])
@admin_required
def middle_money():
    try:
        limit = request.args.get('limit')
        page = request.args.get('page')
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        info_list = SqlData.search_middle_money_admin()
        if not info_list:
            results['code'] = RET.OK
            results['msg'] = MSG.NODATA
            return jsonify(results)
        info_list = sorted(info_list, key=operator.itemgetter('start_time'))
        page_list = list()
        info_list = list(reversed(info_list))
        for i in range(0, len(info_list), int(limit)):
            page_list.append(info_list[i:i + int(limit)])
        results['data'] = page_list[int(page) - 1]
        results['count'] = len(info_list)
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


@admin_blueprint.route('/card_info/', methods=['GET'])
@admin_required
def card_info():
    limit = request.args.get('limit')
    page = request.args.get('page')
    user_id = request.args.get('u_id')
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    data = SqlData.search_card_info(user_id)
    if len(data) == 0:
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.NODATA
        return results
    data = sorted(data, key=operator.itemgetter('act_time'))
    page_list = list()
    data = list(reversed(data))
    for i in range(0, len(data), int(limit)):
        page_list.append(data[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(data)
    return jsonify(results)


@admin_blueprint.route('/acc_to_middle/', methods=['GET', 'POST'])
@admin_required
def acc_to_middle():
    if request.method == 'GET':
        middle_id = request.args.get('middle_id')
        middle_sql = "WHERE middle_id=" + middle_id + ""
        cus_list = SqlData.search_cus_list(sql_line=middle_sql)
        null_list = SqlData.search_cus_list(sql_line="WHERE middle_id is null")
        context = dict()
        context['cus_list'] = cus_list
        context['null_list'] = null_list
        return render_template('admin/acc_to_middle.html', **context)
    if request.method == 'POST':
        results = {"code": RET.OK, "msg": MSG.OK}
        data = json.loads(request.form.get('data'))
        name = data.get('name')
        field = data.get('field')
        value = data.get('value')
        if value:
            if field != 'account' and field != 'password':
                try:
                    value = float(value)
                    SqlData.update_middle_field_int(field, value, name)
                except:
                    return jsonify({'code': RET.SERVERERROR, 'msg': '提成输入值错误!请输入数字类型!'})
            else:
                SqlData.update_middle_field_str(field, value, name)

        bind_cus = [k for k, v in data.items() if v == 'on']
        del_cus = [k for k, v in data.items() if v == 'off']

        if bind_cus:
            for i in bind_cus:
                middle_id_now = SqlData.search_user_field_name('middle_id', i)
                # 判断该客户是否已经绑定中介账号
                if middle_id_now:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '该客户已经绑定中介!请解绑后重新绑定!'
                    return jsonify(results)
                middle_id = SqlData.search_middle_name('id', name)
                user_id = SqlData.search_user_field_name('id', i)
                SqlData.update_user_field_int('middle_id', middle_id, user_id)
        if del_cus:
            for i in del_cus:
                user_id = SqlData.search_user_field_name('id', i)
                middle_id_now = SqlData.search_user_field_name('middle_id', i)
                middle_id = SqlData.search_middle_name('id', name)
                # 判断这个客户是不是当前中介的客户,不是则无权操作
                if middle_id_now != middle_id:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = '该客户不是当前中介客户!无权删除!'
                    return jsonify(results)
                SqlData.update_user_field_int('middle_id', 'NULL', user_id)
        return jsonify(results)


@admin_blueprint.route('/middle_info/', methods=['GET'])
@admin_required
def middle_info():
    page = request.args.get('page')
    limit = request.args.get('limit')
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    task_info = SqlData.search_middle_info()
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return results
    page_list = list()
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@admin_blueprint.route('/add_middle/', methods=['POST'])
@admin_required
def add_middle():
    results = {"code": RET.OK, "msg": MSG.OK}
    try:
        data = json.loads(request.form.get('data'))
        name = data.get('name')
        account = data.get('account')
        password = data.get('password')
        phone_num = data.get('phone_num')
        price_one = float(data.get('price_one'))
        price_two = float(data.get('price_two'))
        price_three = float(data.get('price_three'))
        ret = SqlData.search_middle_ed(name)
        if ret:
            results['code'] = RET.SERVERERROR
            results['msg'] = '该中介名已存在!'
            return jsonify(results)
        if phone_num:
            ret = re.match(r"^1[35789]\d{9}$", phone_num)
            if not ret:
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        SqlData.insert_middle(account, password, name, phone_num, price_one, price_two, price_three)
        return jsonify(results)
    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = RET.SERVERERROR
        return jsonify(results)


@admin_blueprint.route('/add_account/', methods=['POST'])
@admin_required
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


@admin_blueprint.route('/change_pass', methods=['GET', 'POST'])
@admin_required
def change_pass():
    if request.method == 'GET':
        return render_template('admin/admin_edit.html')
    if request.method == 'POST':
        results = {"code": RET.OK, "msg": MSG.OK}
        data = json.loads(request.form.get('data'))
        old_pass = data.get('old_pass')
        new_pass_one = data.get('new_pass_one')
        new_pass_two = data.get('new_pass_two')
        if new_pass_two != new_pass_one:
            results['code'] = RET.SERVERERROR
            results['msg'] = '两次输入密码不一致!'
            return jsonify(results)
        password = SqlData.search_admin_field('password')
        if old_pass != password:
            results['code'] = RET.SERVERERROR
            results['msg'] = '密码错误!'
            return jsonify(results)
        SqlData.update_admin_field('password', new_pass_one)
        session.pop('admin_id')
        session.pop('admin_name')
        return jsonify(results)


@admin_blueprint.route('/admin_info', methods=['GET'])
@admin_required
def admin_info():
    account, password, name, balance = SqlData.admin_info()
    context = dict()
    context['account'] = account
    context['password'] = password
    context['name'] = name
    context['balance'] = balance
    return render_template('admin/admin_info.html', **context)


@admin_blueprint.route('/top_history', methods=['GET'])
@admin_required
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


@admin_blueprint.route('/top_up', methods=['POST'])
@admin_required
def top_up():
    results = {"code": RET.OK, "msg": MSG.OK}
    try:
        data = request.form.get('money')
        name = request.form.get('name')
        pay_num = sum_code()
        t = xianzai_time()
        money = float(data)
        before = SqlData.search_user_field_name('balance', name)
        balance = before + money
        user_id = SqlData.search_user_field_name('id', name)
        # 更新账户余额
        SqlData.update_user_balance(money, user_id)
        # 更新客户充值记录
        SqlData.insert_top_up(pay_num, t, money, before, balance, user_id)

        phone = SqlData.search_user_field_name('phone_num', name)

        if phone:
            CCP().send_Template_sms(phone, [name, t, money], 485108)

        return jsonify(results)

    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@admin_blueprint.route('/edit_parameter', methods=['GET', 'POST'])
@admin_required
def edit_parameter():
    if request.method == 'GET':
        return render_template('admin/edit_parameter.html')
    if request.method == 'POST':
        results = {"code": RET.OK, "msg": MSG.OK}
        try:
            data = json.loads(request.form.get('data'))
            name = data.get('name_str')
            create_price = data.get('create_price')
            refund = data.get('refund')
            min_top = data.get('min_top')
            max_top = data.get('max_top')
            password = data.get('password')
            card_q = data.get("card_q")
            if create_price:
                SqlData.update_account_field('create_price', create_price, name)
            if refund:
                SqlData.update_account_field('refund', refund, name)
            if min_top:
                SqlData.update_account_field('min_top', min_top, name)
            if max_top:
                SqlData.update_account_field('max_top', max_top, name)
            if password:
                SqlData.update_account_field('password', password, name)
            if card_q:
                SqlData.update_account_field("label", card_q, name)
            return jsonify(results)
        except Exception as e:
            logging.error(e)
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.SERVERERROR
            return jsonify(results)


@admin_blueprint.route('/lock_acc/')
@admin_required
def lock_acc():
    acc_name = request.args.get('acc_name')
    u_id = SqlData.search_user_field_name('id', acc_name)
    check = request.args.get('check')
    if check == 'true':
        RedisTool.string_del(u_id)
    elif check == 'false':
        RedisTool.string_set(u_id, 'F')
    return jsonify({'code': RET.OK, 'msg': MSG.OK})


@admin_blueprint.route('/account_info/', methods=['GET'])
@admin_required
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
    for u in task_one:
        u_id = u.get('u_id')
        # card_count = SqlData.search_card_count(u_id, '')
        out_money = SqlData.search_trans_sum(u_id)
        bento_income_money = SqlData.search_income_money(u_id)
        # u['card_num'] = card_count
        u['out_money'] = float("%.2f" % float(out_money - bento_income_money))

        account_all_amount = SqlDataNative.select_alias_balance(u.get("name"))
        count_del_quant = SqlDataNative.count_del_data(alias=u.get("name"))
        all_cardids = SqlDataNative.attribution_fount_cardid(alias=u.get("name"))

        '''
        if len(all_moneys) > 0 and len(all_cardids) > 0:
            for all_cardid in all_cardids:
                for all_money in all_moneys:
                    if all_cardid == all_money.get("cardid"):
                        account_all_amount = account_all_amount + all_money.get("availableAmount")
        count_del_quant = SqlDataNative.count_del_data(alias=u.get("name"))
        '''

        u['del_card_num'] = count_del_quant
        u['account_all_money'] = account_all_amount
        u['in_card_num'] = len(all_cardids)
        task_info.append(u)
    page_list = list()
    task_info_status = list()
    for c in task_info:
        u_id = c.get('u_id')
        r = RedisTool.string_get(u_id)
        if not r:
            c['status'] = 'T'
        else:
            c['status'] = 'F'
        task_info_status.append(c)
    task_info = list(reversed(task_info_status))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@admin_blueprint.route('/account_card/', methods=['GET'])
@admin_required
def account_card():
    page = request.args.get('page')
    limit = request.args.get('limit')
    user_name = request.args.get('user_name')
    card_info = SqlDataNative.search_alias_data('', user_name)
    if not card_info:
        return jsonify({'code:': RET.SERVERERROR, 'msg': MSG.NODATA})
    page_list = list()
    task_info = list(reversed(card_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results = dict()
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(card_info)
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    return jsonify(results)


@admin_blueprint.route('/account_card_list', methods=['GET'])
@admin_required
def account_card_list():
    attribution = request.args.get('user_name')
    context = dict()
    context['user_name'] = attribution
    return render_template('admin/card_list.html', **context)


@admin_blueprint.route('/middle_info_html', methods=['GET'])
@admin_required
def middle_info_html():
    user_id = request.args.get('user_id')
    middle_user_id = SqlData.middle_user_id(name=user_id)
    middle_data = SqlData.middle_user_data(middle_id=middle_user_id)
    context = dict()
    context['pay_list'] = middle_data
    return render_template('admin/middle_info.html', **context)


@admin_blueprint.route('/line_chart', methods=['GET'])
@admin_required
@cache.cached(timeout=21600, key_prefix='GuteHelen')
def test():
    # 展示近三十天开卡数量
    day_num = 30
    day_list = get_nday_list(day_num)
    account_list = SqlData.search_user_field_admin()
    data = list()
    if account_list:
        for u_id in account_list:
            info_dict = dict()
            count_list = list()
            for i in day_list:
                sql_str = "AND do_date BETWEEN '{} 00:00:00' AND '{} 23:59:59'".format(i, i)
                alias = u_id.get("id")
                card_count = SqlData.bento_chart_data(alias=alias, time_range=sql_str)
                if card_count == 0:
                    card_count = ""
                count_list.append(card_count)
            info_dict['name'] = u_id.get('name')
            info_dict['data'] = count_list
            data.append(info_dict)
    else:
        data = [{'name': '无客户',
                 'data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}]

    sum_list = list()
    for i in data:
        one_cus = i.get('data')
        sum_list.append(one_cus)

    res_list = list()
    for n in range(30):
        res = 0
        for i in range(len(sum_list)):
            card_num = sum_list[i][n]
            if card_num != "":
                res += card_num
        res_list.append(res)

    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    results['data'] = data
    results['xAx'] = day_list
    results['column'] = res_list
    return jsonify(results)


@admin_blueprint.route('/logout', methods=['GET'])
@admin_required
def logout():
    session.pop('admin_id')
    session.pop('admin_name')
    return render_template('admin/admin_login.html')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return render_template('admin/admin_login.html')

    if request.method == 'POST':
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        try:
            data = json.loads(request.form.get('data'))
            account = data.get('account')
            password = data.get('password')
            admin_id, name = SqlData.search_admin_login(account, password)
            session['admin_id'] = admin_id
            session['admin_name'] = name
            session.permanent = True
            return jsonify(results)

        except Exception as e:
            logging.error(str(e))
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.PSWDERROR
            return jsonify(results)


@admin_blueprint.route('/', methods=['GET'])
@admin_required
def index():
    admin_name = g.admin_name
    # spent = SqlData.search_trans_sum_admin()
    # sum_balance = SqlData.search_user_sum_balance()
    decline = SqlDataNative.count_admin_decline()
    card_remain = SqlDataNative.search_sum_remain()
    sum_top = SqlData.search_table_sum('sum_balance', 'account', '')
    sum_remain = SqlData.search_table_sum('balance', 'account', '')
    card_use = SqlDataNative.count_bento_data(sqld="")
    card_no = SqlDataNative.count_bento_data(sqld="where label='已注销'")
    card_un = SqlDataNative.count_bento_data(sqld="where label!='已注销'")
    up_remain_time = SqlData.search_admin_field('up_remain_time')
    context = dict()
    context['admin_name'] = admin_name
    context['up_remain_time'] = up_remain_time
    # context['spent'] = spent
    context['advance'] = decline
    context['sum_top'] = sum_top
    context['sum_remain'] = sum_remain
    context['card_remain'] = round(card_remain, 3)
    context['card_use'] = card_use
    context['card_no'] = card_no
    context['card_un'] = card_un
    return render_template('admin/index.html', **context)
