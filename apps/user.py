import json
import datetime
import logging
import operator
import time
from apps.bento_create_card.public import change_today
from tools_me.other_tools import xianzai_time, login_required, check_float
from tools_me.parameter import RET, MSG, TRANS_TYPE, DO_TYPE
from tools_me.redis_tools import RedisTool
from tools_me.remain import get_card_remain
from . import user_blueprint
from flask import render_template, request, jsonify, session, g
from tools_me.mysql_tools import SqlData
from apps.bento_create_card.main_create_card import main_createcard, CreateCard, get_bento_data
from apps.bento_create_card.sqldata_native import SqlDataNative
from apps.bento_create_card.main_recharge import main_transaction_data, RechargeCard

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


@user_blueprint.route('/update_vice/', methods=['GET', 'POST'])
@login_required
def update_vice():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        return render_template('user/no_auth.html')
    if request.method == 'GET':
        user_id = g.user_id
        res = SqlData().search_acc_vice(user_id)
        context = dict()
        if res:
            context['account'] = res.get('v_account')
            context['password'] = res.get('v_password')
            context['c_card'] = 'checked=""' if res.get('c_card') == 'T' else ''
            context['c_s_card'] = 'checked=""' if res.get('c_s_card') == 'T' else ''
            context['top_up'] = 'checked=""' if res.get('top_up') == 'T' else ''
            context['refund'] = 'checked=""' if res.get('refund') == 'T' else ''
            context['del_card'] = 'checked=""' if res.get('del_card') == 'T' else ''
            context['up_label'] = 'checked=""' if res.get('up_label') == 'T' else ''
        return render_template('user/update_vice.html', **context)
    if request.method == 'POST':
        user_id = g.user_id
        data = json.loads(request.form.get('data'))
        v_account = data.get('account')
        v_password = data.get('password')
        c_card = data.get('c_card')
        c_s_card = data.get('c_s_card')
        top_up = data.get('top_up')
        refund = data.get('refund')
        del_card = data.get('del_card')
        up_label = data.get('up_label')
        account = v_account.strip()
        password = v_password.strip()
        if len(account) < 6 or len(password) < 6:
            return jsonify({"code": RET.SERVERERROR, 'msg': '账号或密码长度小于6位！'})
        # 判断用户选择可哪些权限开启
        c_card_status = 'T' if c_card else 'F'
        c_s_card_status = 'T' if c_s_card else 'F'
        top_up_status = 'T' if top_up else 'F'
        refund_status = 'T' if refund else 'F'
        del_card_status = 'T' if del_card else 'F'
        up_label_status = 'T' if up_label else 'F'
        res = SqlData().search_acc_vice(user_id)
        # 判断是否已经添加子账号，已添加则更新
        if res:
            try:
                SqlData().update_account_vice(account, password, c_card_status, c_s_card_status, top_up_status,
                                              refund_status, del_card_status, up_label_status, user_id)
                res = SqlData().search_acc_vice(user_id)
                RedisTool().hash_set('vice_auth', res.get('vice_id'), res)
                return jsonify({'code': RET.OK, 'msg': MSG.OK})
            except Exception as e:
                print(e)
                return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})
        else:
            if SqlData().search_value_in('vice_account', account, 'v_account'):
                return jsonify({'code': RET.SERVERERROR, 'msg': '用户名已存在！或已创建子账号！'})
            try:
                SqlData().insert_account_vice(account, password, c_card_status, c_s_card_status, top_up_status,
                                              refund_status, del_card_status, up_label_status, user_id)
                return jsonify({'code': RET.OK, 'msg': MSG.OK})
            except Exception as e:
                print(e)
                return jsonify({'code': RET.SERVERERROR, 'msg': '您的账号已添加子账号，不可重复添加，或账号重复请重试！'})


@user_blueprint.route('/refund/', methods=['POST'])
@login_required
def bento_refund():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('refund')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    data = json.loads(request.form.get("data"))
    card_no = json.loads(request.form.get("card_no"))
    user_id = g.user_id
    if "-" in str(data):
        return jsonify({"code": RET.SERVERERROR, 'msg': "请输入正确金额!"})
    # results = {"code": RET.OK, "msg": MSG.OK}
    cardid = SqlDataNative().cardnum_fount_cardid(cardnum=card_no)
    alias = SqlDataNative().cardnum_fount_alias(cardnum=card_no)
    availableAmount = RechargeCard().one_alias(alias)
    # 更新卡余额信息
    if not availableAmount:
        return jsonify({"code": RET.OK, "msg": "该卡余额异常, 无法进行退款转移操作"})
    # if float("%.2f"%data) - float("%.2f"%availableAmount) < 1:
    if float("%.2f" % availableAmount) - float("%.2f" % data) < 1:
        return jsonify({"code": RET.OK, "msg": "该卡导出余额后需保持卡余额大于等于1, 若需全部退款, 可执行删卡"})
    # SqlDataNative().update_card_Balance(cardid=cardid, availableAmount=availableAmount)
    if cardid:
        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        SqlDataNative().update_card_Balance(cardid=cardid, availableAmount=availableAmount, create_time=create_time)
        try:
            result_msg = RechargeCard().refund_data(cardid=cardid, recharge_amount=data)
        except Exception as e:
            logging.exception(str(e))
            return jsonify({"code": RET.OK, "msg": "网络繁忙, 请稍后重试"})
        else:
            if result_msg.get("msg"):
                before_balance = SqlData().search_user_field('balance', user_id)
                SqlData().update_balance(float(data), user_id)
                balance = SqlData().search_user_field("balance", user_id)
                # balance = round(before_balance + float(data), 2)
                # 手续费
                account_refund = SqlData().search_user_field('refund', user_id)
                new_account_refund = account_refund * data
                new_balance = round(balance - account_refund * data, 2)
                SqlData().update_user_field_int('balance', new_balance, user_id)
                n_time = xianzai_time()
                SqlData().insert_account_trans(n_time, TRANS_TYPE.IN, "转移退款", cardid, card_no, float(data),
                                               new_account_refund, before_balance, new_balance, user_id)
                SqlDataNative().insert_operating_log(cardid=cardid, operating_time=create_time,
                                                     operating_log="{}, 转移退款".format(result_msg.get("msg")))

                return jsonify({"code": RET.OK, "msg": result_msg.get("msg")})
            else:
                return jsonify({"code": RET.SERVERERROR, "msg": result_msg.get("error_msg")})
    else:
        return jsonify({"code": RET.OK, 'msg': "转移失败, 该卡号不存在, 请联系管理员"})


@user_blueprint.route('/all_trans/', methods=['GET'])
@login_required
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

    user_name = g.user_name
    data = SqlDataNative().one_bento_alltrans(alias=user_name)
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(data) == 0:
        results["MSG"] = MSG.MODATA
        return jsonify(results)
    args_list = []
    new_data = []
    if acc_name:
        args_list.append(acc_name)
    if order_num:
        args_list.append(order_num)
    if trans_status:
        args_list.append(trans_status)

    if args_list and time_range == "":
        for d in data:
            if set(args_list) < set(d.values()):
                new_data.append(d)
    elif args_list and time_range != "":
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        min_tuple = datetime.datetime.strptime(min_time, '%Y-%m-%d %H:%M:%S')
        max_tuple = datetime.datetime.strptime(max_time, '%Y-%m-%d %H:%M:%S')
        for d in data:
            dat = datetime.datetime.strptime(d.get("date"), '%Y-%m-%d %H:%M:%S')
            if (min_tuple < dat and max_tuple > dat) and set(args_list) < set(d.values()):
                new_data.append(d)
    elif time_range and len(args_list) == 0:
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        min_tuple = datetime.datetime.strptime(min_time, '%Y-%m-%d %H:%M:%S')
        max_tuple = datetime.datetime.strptime(max_time, '%Y-%m-%d %H:%M:%S')
        for d in data:
            dat = datetime.datetime.strptime(d.get("date"), '%Y-%m-%d %H:%M:%S')
            if min_tuple < dat and max_tuple > dat:
                new_data.append(d)

    page_list = list()
    if new_data:
        data = sorted(new_data, key=operator.itemgetter("date"))
    data = sorted(data, key=operator.itemgetter("date"))
    data = list(reversed(data))
    for i in range(0, len(data), int(limit)):
        page_list.append(data[i: i + int(limit)])
    results["data"] = page_list[int(page) - 1]
    results["count"] = len(data)
    # results = {"code": RET.OK, "msg": MSG.OK, "count": len(data), "data": page_list[int(page)-1]}
    return jsonify(results)


@user_blueprint.route('/bento_decline/', methods=['GET'])
@login_required
def bento_decline():
    page = request.args.get('page')
    limit = request.args.get('limit')

    time_range = request.args.get('time_range')
    card_num = request.args.get('card_num')
    time_sql = ""
    card_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0] + ' 00:00:00'
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND date BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    else:
        min_time = ""
        max_time = ""
    if card_num:
        # card_sql = "AND card_no = '" + card_num + "'"
        card_sql = "AND last_four LIKE '%{}%'".format(card_num)

    alias = g.user_name
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    task_info = SqlDataNative().search_decline_data(alias, card_sql, time_sql)
    task_info = sorted(task_info, key=operator.itemgetter("date"))
    task_info = list(reversed(task_info))
    # cardid_list = SqlDataNative().attribution_fount_cardid(alias)
    # decline_ratio = RechargeCard().declined_statistics(cardid_list[1: 50], min_time, max_time)
    if len(task_info) == 0:
        results["MSG"] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results["data"] = page_list[int(page) - 1]
    results["count"] = len(task_info)
    return jsonify(results)


@user_blueprint.route('/bento_update/', methods=['GET'])
@login_required
def bento_update():
    alias = request.args.get("account")
    s = SqlDataNative().alias_fount_cardid(alias)
    data = get_bento_data(cardid=s)
    if data.get("pan"):
        SqlDataNative().update_card_data(pan=data.get("pan"), cvv=data.get("cvv"), expiration=data.get("expiration"),
                                         alias=alias)
        return jsonify({"code": RET.OK, "msg": "更新成功"})
    else:
        return jsonify({"code": RET.OK, "msg": "更新失败, 请稍后再试"})


@user_blueprint.route('/delcard/', methods=['GET'])
@login_required
def del_account():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('del_card')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    cardnumber = request.args.get('account')
    user_id = g.user_id
    # 获取cardid, 用于删除卡
    cardid = SqlDataNative().cardnum_fount_cardid(cardnum=cardnumber)
    alias = SqlDataNative().cardnum_fount_alias(cardnum=cardnumber)
    availableAmount = RechargeCard().one_alias(alias)
    # 更新卡余额
    # SqlDataNative().update_card_Balance(cardid=cardid, availableAmount=availableAmount)
    if not availableAmount:
        return jsonify({"code": RET.OK, "msg": "该卡余额异常, 无法进行删卡操作"})

    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    SqlDataNative().update_card_Balance(cardid=cardid, availableAmount=availableAmount, create_time=create_time)
    del_status = RechargeCard().del_card(cardid)
    if del_status == 404:
        # 获取alias, 用户获取卡余额
        # sql修改字段为已删除
        SqlDataNative().del_bencard(cardnumber)
        before_balance = SqlData().search_user_field('balance', user_id)
        SqlData().update_balance(float(availableAmount), user_id)
        balance = SqlData().search_user_field("balance", user_id)
        # balance = round(before_balance + availableAmount, 2)
        SqlData().update_user_field_int('balance', balance, user_id)
        n_time = xianzai_time()
        SqlData().insert_account_trans(n_time, TRANS_TYPE.IN, DO_TYPE.REFUND, cardid, cardnumber, availableAmount, 0,
                                       before_balance, balance, user_id)
        SqlDataNative().insert_operating_log(cardid=cardid, operating_time=create_time,
                                             operating_log="原有金额{}, 卡上余额{}, 现有额度{}, 删卡退款".format(before_balance,
                                                                                                 availableAmount,
                                                                                                 balance))
        SqlDataNative().update_bento_status('已注销', cardnumber.strip())
        return jsonify(
            {"code": RET.OK, "msg": "原有金额{}, 卡上余额{}, 现有额度{}".format(before_balance, availableAmount, balance)})
    else:
        return jsonify({"code": RET.OK, "msg": "删卡失败, 请重试, 如若多次不行, 请联系管理员"})


@user_blueprint.route('/card_remain/', methods=['GET'])
def card_remain():
    results = dict()
    try:
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        data = request.args.get('data')
        data = json.loads(data)
        info = get_card_remain(data)
        results['data'] = info
        results['count'] = len(info)
        return results
    except Exception as e:
        logging.error(str(e))
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@user_blueprint.route('/account_trans/', methods=['GET'])
@login_required
def account_trans():
    page = request.args.get('page')
    limit = request.args.get('limit')

    time_range = request.args.get('time_range')
    card_num = request.args.get('card_num')
    do_type = request.args.get('do_type')
    time_sql = ""
    card_sql = ""
    do_sql = ""
    if time_range:
        min_time = time_range.split(' - ')[0]
        max_time = time_range.split(' - ')[1] + ' 23:59:59'
        time_sql = "AND do_date BETWEEN " + "'" + min_time + "'" + " and " + "'" + max_time + "'"
    if card_num:
        # card_sql = "AND card_no = '" + card_num + "'"
        card_sql = "AND card_no LIKE '%{}%'".format(card_num)

    if do_type:
        do_sql = "AND do_type='" + do_type + "'"

    user_id = g.user_id
    task_info = SqlData().search_account_trans(user_id, card_sql, time_sql, type_sql=do_sql)

    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
    if len(task_info) == 0:
        results['MSG'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    task_info = list(reversed(task_info))
    for i in range(0, len(task_info), int(limit)):
        page_list.append(task_info[i:i + int(limit)])
    results['data'] = page_list[int(page) - 1]
    results['count'] = len(task_info)
    return jsonify(results)


@user_blueprint.route('/update_label/', methods=['GET'])
@login_required
def update_label():
    card_name = request.args.get('card_name')
    context = dict()
    context['card_name'] = card_name
    return render_template('user/update_label.html', **context)


@user_blueprint.route('/label_update/', methods=['POST'])
@login_required
def label_update():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('up_label')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    data = json.loads(request.form.get('data'))
    # 卡名
    card_name = data.get('card_name')

    # 修改的标签名
    label_name = data.get("top_money")
    # label_status = SqlDataNative().select_label_status(card_no=card_no)

    SqlDataNative().update_bento_label(card_no=card_name, label_name=label_name)

    return jsonify({"code": RET.OK, "msg": "修改标签成功"})


# 充值
@user_blueprint.route('/top_up/', methods=['POST'])
@login_required
def top_up():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('top_up')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    data = json.loads(request.form.get('data'))
    user_id = g.user_id
    card_no = data.get('card_no')
    top_money = data.get('top_money')
    user_data = SqlData().search_user_index(user_id)
    balance = user_data.get('balance')
    if not check_float(top_money):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)
    if int(top_money) > balance:
        results = {"code": RET.SERVERERROR, "msg": "本次消费金额:" + str(top_money) + ",账号余额不足!"}
        return jsonify(results)
    cardid = SqlDataNative().cardnum_fount_cardid(str(card_no.strip()))
    if cardid:
        # 进行充值
        try:
            result_msg = RechargeCard().recharge(cardid=cardid, recharge_amount=top_money)
        except Exception as e:
            logging.exception(str(e))
            # return jsonify({"code": RET.OK, "msg": str(e)})
            return jsonify({"code": RET.SERVERERROR, "msg": "网络繁忙, 请稍后再试, 所剩余额未扣取"})
        else:
            if result_msg.get("msg"):
                before_balance = SqlData().search_user_field('balance', user_id)
                # balance = round(before_balance - int(top_money), 2)
                bento_do_money = float(top_money) - float(top_money) * 2
                SqlData().update_balance(bento_do_money, user_id)
                balance = SqlData().search_user_field("balance", user_id)
                # SqlData().update_user_field_int('balance', balance, user_id)

                n_time = xianzai_time()
                SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, cardid, card_no,
                                               float(top_money), 0, before_balance,
                                               balance, user_id)
                SqlDataNative().insert_operating_log(cardid=cardid, operating_time=n_time,
                                                     operating_log="{}, 用户充值".format(result_msg.get("msg")))
                return jsonify({"code": RET.OK, "msg": result_msg.get("msg")})
            else:
                return jsonify({"code": RET.SERVERERROR, "msg": result_msg.get("error_msg")})
    else:
        return jsonify({"code": RET.SERVERERROR, "msg": "充值失败, 该卡号不存在, 请联系管理员"})


# 批量建卡
@user_blueprint.route('/create_some/', methods=['POST'])
@login_required
# @choke_required
def create_some():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('c_s_card')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    data = json.loads(request.form.get('data'))
    card_num = data.get('card_num')
    content = data.get('content')
    limit = data.get('limit')
    label = data.get('label')
    user_id = g.user_id
    user_data = SqlData().search_user_index(user_id)
    create_price = user_data.get('create_card')
    min_top = user_data.get('min_top')
    max_top = user_data.get('max_top')
    balance = user_data.get('balance')
    attribution = SqlData().search_user_field("name", user_id)
    # 比较可开卡数量与已开卡数量
    user_name = g.user_name
    use_card_num = SqlDataNative().count_alias_data(user_name)
    create_card_num = SqlData().label_data(user_id)
    if int(create_card_num[0]) - int(use_card_num[0]) < int(card_num):
        results = {"code": RET.SERVERERROR, "msg": "可开卡数量不足, 请联系管理员"}
        return jsonify(results)

    card_num = int(card_num)
    if card_num > 10:
        results = {"code": RET.SERVERERROR, "msg": "批量开卡数量不得超过10张!"}
        return jsonify(results)
    if not check_float(limit):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)
    sum_money = card_num * int(limit) + card_num * create_price

    # 本次开卡需要的费用,计算余额是否充足
    if sum_money > balance:
        results = {"code": RET.SERVERERROR, "msg": "本次消费金额:" + str(sum_money) + ",账号余额不足!"}
        return jsonify(results)

    # 计算充值金额是否在允许范围
    # if not min_top <= int(limit) <= max_top:
    if not min_top <= int(limit):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不在允许范围内!"}
        return jsonify(results)

    try:
        data_list = []
        for i in range(card_num):
            # d = SqlDataNative().search_data(limit_num=1)
            # status = CreateCard().create_card(card_alias=d, card_amount=int(limit), label=label)
            status = main_createcard(limit_num=1, card_amount=int(limit), label=label, attribution=attribution)
            if status:
                # 开卡费用
                n_time = xianzai_time()
                card_no = status.get("pan")
                card_card_id = status.get("cardId")
                before_balance = SqlData().search_user_field('balance', user_id)

                create_price_do_money = float(create_price) - float(create_price) * 2
                SqlData().update_balance(create_price_do_money, user_id)
                balance = SqlData().search_user_field("balance", user_id)
                # balance = before_balance - create_price
                SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.CREATE_CARD, card_card_id, card_no,
                                               create_price, 0, before_balance, balance, user_id)
                SqlData().update_user_field_int('balance', balance, user_id)
                # 充值费用
                before_balance = SqlData().search_user_field('balance', user_id)
                top_money = int(limit)
                top_money_do_money = float(limit) - float(limit) * 2
                SqlData().update_balance(top_money_do_money, user_id)
                balance = SqlData().search_user_field("balance", user_id)
                # balance = round(before_balance - float(top_money), 2)
                SqlData().update_user_field_int('balance', balance, user_id)
                n_time = xianzai_time()
                card_no = status.get("pan")
                SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, card_card_id, card_no, top_money,
                                               0, before_balance, balance, user_id)
                data_list.append(status.get("pan"))
        return jsonify({"code": RET.OK, "msg": "成功开卡" + str(len(data_list)) + "张!请刷新界面!"})
    except Exception as e:
        logging.error(e)
        results = {"code": RET.SERVERERROR, "msg": str(e)}
        return jsonify(results)


# 单张卡
@user_blueprint.route('/create_card/', methods=['POST'])
@login_required
def create_card():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        auth_dict = RedisTool().hash_get('vice_auth', vice_id)
        c_card = auth_dict.get('c_card')
        if c_card == 'F':
            return jsonify({'code': RET.SERVERERROR, 'msg': '抱歉您没有权限执行此操作！'})
    data = json.loads(request.form.get('data'))
    # card_name = data.get('card_name')
    top_money = data.get('top_money')
    label = data.get('label')
    user_id = g.user_id
    user_data = SqlData().search_user_index(user_id)
    create_price = user_data.get('create_card')
    min_top = user_data.get('min_top')
    max_top = user_data.get('max_top')
    balance = user_data.get('balance')
    attribution = SqlData().search_user_field("name", user_id)
    # 比较可开卡数量与已开卡数量
    user_name = g.user_name
    use_card_num = SqlDataNative().count_alias_data(user_name)
    create_card_num = SqlData().label_data(user_id)
    if int(create_card_num[0]) - int(use_card_num[0]) < 1:
        results = {"code": RET.SERVERERROR, "msg": "可开卡数量不足, 请联系管理员"}
        return jsonify(results)

    if not check_float(top_money):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不能为小数!"}
        return jsonify(results)

    # 本次开卡需要的费用,计算余额是否充足
    money_all = int(top_money) + create_price
    if money_all > balance:
        results = {"code": RET.SERVERERROR, "msg": "本次消费金额:" + str(money_all) + ",账号余额不足!"}
        return jsonify(results)

    # 计算充值金额是否在允许范围
    # if not min_top <= int(top_money) <= max_top:
    if not min_top <= int(top_money):
        results = {"code": RET.SERVERERROR, "msg": "充值金额不在允许范围内!"}
        return jsonify(results)
    # 该处修改开卡
    try:
        status = main_createcard(limit_num=1, card_amount=int(top_money), label=label, attribution=attribution)
        if status:
            card_no = status.get("pan")
            card_card_id = status.get("cardId")
            before_balance = SqlData().search_user_field('balance', user_id)
            create_price_do_money = float(create_price) - float(create_price) * 2
            SqlData().update_balance(create_price_do_money, user_id)
            balance = SqlData().search_user_field("balance", user_id)
            # balance = before_balance - create_price
            # 更新开卡费用
            n_time = xianzai_time()
            SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.CREATE_CARD, card_card_id, card_no,
                                           create_price, 0, before_balance, balance, user_id)
            SqlData().update_user_field_int('balance', balance, user_id)

            # 更新充值费用
            before_balance = SqlData().search_user_field('balance', user_id)
            top_money_do_money = float(top_money) - float(top_money) * 2
            SqlData().update_balance(top_money_do_money, user_id)
            balance = SqlData().search_user_field("balance", user_id)
            # balance = round(before_balance - float(top_money), 2)
            SqlData().update_user_field_int('balance', balance, user_id)
            SqlData().insert_account_trans(n_time, TRANS_TYPE.OUT, DO_TYPE.TOP_UP, card_card_id, card_no, top_money, 0,
                                           before_balance, balance, user_id)
            return jsonify({"code": RET.OK, "msg": "开卡成功"})
        else:
            return jsonify({"code": RET.SERVERERROR, "msg": "开卡成功, 进入process状态, 需等待卡号和安全码生成"})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"code": RET.SERVERERROR, "msg": "网络繁忙, 开卡失败, 请稍后再试"})


@user_blueprint.route('/top_history/', methods=['GET'])
@login_required
def top_history():
    page = request.args.get('page')
    limit = request.args.get('limit')
    user_id = g.user_id
    task_info = SqlData().search_top_history_acc(user_id)
    task_info = sorted(task_info, key=operator.itemgetter('time'))
    results = {"code": RET.OK, "msg": MSG.OK, "count": 0, "data": ""}
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


@user_blueprint.route('/', methods=['GET'])
@login_required
def account_html():
    user_name = g.user_name
    user_id = g.user_id
    dict_info = SqlData().search_user_index(user_id)
    create_card = dict_info.get('create_card')
    refund = dict_info.get('refund') * 100
    min_top = dict_info.get('min_top')
    max_top = dict_info.get('max_top')
    balance = dict_info.get('balance')
    sum_balance = dict_info.get('sum_balance')
    out_money = SqlData().search_trans_sum(user_id)
    bento_income_money = SqlData().search_income_money(user_id)
    # 获取交易数量
    # cardid_list = SqlDataNative().attribution_fount_cardid(user_name)
    # decline_rati = RechargeCard().declined_statistics(cardid_list[1: 100])

    t_data = SqlDataNative().account_sum_transaction(attribution=user_name)

    # 获取decline数量
    today_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    max_today = "{} {}".format(change_today(today_time, 0), "23:59:59")
    min_today = "{} {}".format(change_today(today_time, -3), "00:00:00")
    decline_data = SqlDataNative().count_decline_data(attribution=user_name, min_today=min_today, max_today=max_today)
    # decline_data = SqlDataNative().count_decline_data(user_name)

    # decline / 交易总量
    # decline_ratio = "{}{}".format(float("%.4f"%(decline_data / t_data))) if t_data != 0 else 0

    # one_t_data = SqlDataNative().account_sum_transaction(attribution=user_name)
    three_data = SqlDataNative().count_decline_data(attribution=user_name, min_today=min_today, max_today=max_today)
    three_tran_data = SqlDataNative().search_d(user_name)
    decline_ratio = "{}{}".format(float("%.4f" % (three_data / three_tran_data * 100)),
                                  '%') if three_tran_data != 0 else 0

    # decline_ratio = "{}{}".format(float("%.4f"%(decline_data / t_data * 100)), '%') if t_data != 0 else 0
    # 获取已开卡数量
    use_label = SqlDataNative().count_alias_data(user_name)
    context = dict()
    # label为开卡数量
    label = SqlData().label_data(user_id)
    # 公告
    notice = SqlDataNative().bento_notice()
    # 用户的所有卡金额
    """
    account_all_amount = 0
    all_moneys = TransactionRecord().all_alias_money()
    all_cardids = SqlDataNative().attribution_fount_cardid(alias=user_name)
    if len(all_moneys) > 0 and len(all_cardids) > 0:
        for all_cardid in all_cardids:
            for all_money in all_moneys:
                if all_cardid == all_money.get("cardid"):
                    account_all_amount = account_all_amount + all_money.get("availableAmount")
    """
    bento_allias_balance = SqlDataNative().select_alias_balance(attribution=user_name)
    context['all_money'] = bento_allias_balance

    # 查询上次卡余额统计时间
    card_remain_time = SqlData().search_admin_field('up_remain_time')
    if card_remain_time:
        up_remain_time = str(card_remain_time)
    else:
        up_remain_time = '上次获取时间异常'
    context['up_remain_time'] = up_remain_time

    if label:
        context["bento_label"] = label[0]
    else:
        context["bento_label"] = 50
    if use_label:
        context['use_label'] = use_label[0]
    else:
        context['use_label'] = "异常, 请联系管理员"
    context['decline_data'] = decline_data

    if g.vice_id:
        context['bg_color'] = 'layui-bg-blue'
    # 所拥有的总余额参数
    context['decline_ratio'] = decline_ratio
    context['user_name'] = user_name
    context['balance'] = balance
    context['refund'] = refund
    context['create_card'] = create_card
    context['min_top'] = min_top
    context['max_top'] = max_top
    context['sum_balance'] = sum_balance
    context['out_money'] = float("%.2f" % float(out_money - bento_income_money))
    context['notice'] = notice
    return render_template('user/index.html', **context)


@user_blueprint.route('/change_phone', methods=['GET'])
@login_required
def change_phone():
    # 判断是否是子账号用户
    vice_id = g.vice_id
    if vice_id:
        return jsonify({'code': RET.SERVERERROR, 'msg': '您没有权限操作！请切换主账号后重试！'})
    user_id = g.user_id
    phone_num = request.args.get('phone_num')
    results = dict()
    try:
        SqlData().update_user_field('phone_num', phone_num, user_id)
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


# 卡的交易记录
@user_blueprint.route('/one_card_detail', methods=['GET'])
# @login_required
def one_detail():
    try:
        context = {}
        info_list = []
        card_no = request.args.get('card_no')
        """
        if "****" in card_no:
            context['remain'] = "该卡已注销, 余额为0"
            context['balance'] = "f_balance"
            context['pay_list'] = []
            return render_template('user/card_detail.html', **context)
        """
        # sqldata = Sql_Session.query(BentoCard.card_id, BentoCard.alias).filter(BentoCard.card_number==card_no).first()
        # sqldata = SqlDataNative().fount_cardid_alias(card_no=card_no)
        sqldata = SqlDataNative().alias_fount_cardid(alias=card_no)
        if not sqldata:
            return jsonify({"code": RET.SERVERERROR, "msg": "数据库没有该用户数据, 可联系管理员添加"})
        label_status = SqlDataNative().cardid_fount_label(cardid=sqldata)
        transaction_data, availableAmount = main_transaction_data(cards=sqldata, alias=card_no)
        context['balance'] = "f_balance"
        context['remain'] = availableAmount if label_status != "已注销" else "该卡已注销, 余额为0"
        # context['remain'] = transaction_data[0].get("availableAmount")
        n = 1
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
    except Exception as e:
        logging.error((str(e)))
        # return jsonify({'code': RET.SERVERERROR, 'msg': str(e)})
        return render_template('user/404.html')
        # return jsonify({'code': RET.SERVERERROR, 'msg': "网络繁忙, 稍后再试"})


@user_blueprint.route('/change_detail', methods=['GET'])
@login_required
def change_detail():
    return render_template('user/edit_account.html')


# 余额
@user_blueprint.route('/card_info', methods=['GET'])
@login_required
def card_info():
    card_name = request.args.get('card_name')
    card_num = request.args.get('card_num')
    limit = request.args.get('limit')
    page = request.args.get('page')
    label = request.args.get('label')
    range_time = request.args.get('range_time')
    results = {}
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    user_id = g.user_id
    if not label and not card_name and not card_num and not range_time:
        # 这里gt需修改成查询全部数据
        attribution = SqlData().search_user_field("name", user_id)
        data = SqlDataNative().search_alias_data(label, attribution)
    else:
        name_sql = ""
        if card_name:
            name_sql = "AND alias LIKE '%{}%'".format(card_name)
        card_sql = ""
        if card_num:
            card_sql = "AND card_number LIKE '%{}%'".format(card_num)
        label_sql = ""
        if label:
            label_sql = "AND label LIKE '%{}%'".format(label)
        time_sql = ""
        if range_time:
            min_time = range_time.split(' - ')[0] + ' 23:59:59'
            max_time = range_time.split(' - ')[1] + ' 23:59:59'
            time_sql = "AND create_time BETWEEN '{}' AND '{}'".format(min_time, max_time)
        attribution = SqlData().search_user_field("name", user_id)
        # data = SqlDataNative().search_alias_data(label, attribution)
        data = SqlDataNative().select_transaction_data(attribution, name_sql, card_sql, label_sql, time_sql)
    if not data:
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.NODATA
        return jsonify(results)
    page_list = list()
    info = list(reversed(data))
    for i in range(0, len(info), int(limit)):
        page_list.append(info[i:i + int(limit)])
    data = page_list[int(page) - 1]
    # data = get_card_remain(data)
    results['data'] = data
    results['count'] = len(info)
    return jsonify(results)


@user_blueprint.route('/edit_user', methods=['GET'])
@login_required
def ch_pass_html():
    vice_id = g.vice_id
    print(vice_id)
    if vice_id:
        return render_template('user/no_auth.html')
    return render_template('user/edit_user.html')


@user_blueprint.route('/change_pass', methods=["POST"])
@login_required
def change_pass():
    data = json.loads(request.form.get('data'))
    old_pass = data.get('old_pass')
    new_pass_one = data.get('new_pass_one')
    new_pass_two = data.get('new_pass_two')
    user_id = g.user_id
    pass_word = SqlData().search_user_field('password', user_id)
    results = {'code': RET.OK, 'msg': MSG.OK}
    if not (old_pass == pass_word):
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDERROR
        return jsonify(results)
    if not (new_pass_one == new_pass_two):
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDERROR
        return jsonify(results)
    if len(new_pass_one) < 6:
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.PSWDLEN
        return jsonify(results)
    try:
        SqlData().update_user_field('password', new_pass_one, g.user_id)
        session.pop('user_id')
        session.pop('name')
        return jsonify(results)
    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@user_blueprint.route('/user_info', methods=['GET'])
@login_required
def user_info():
    user_name = g.user_name
    user_id = g.user_id
    dict_info = SqlData().search_user_detail(user_id)
    account = dict_info.get('account')
    phone_num = dict_info.get('phone_num')
    balance = dict_info.get('balance')
    context = {
        'user_name': user_name,
        'account': account,
        'balance': balance,
        'phone_num': phone_num,
    }
    return render_template('user/user_info.html', **context)


@user_blueprint.route('/logout', methods=['GET'])
@login_required
def logout():
    session.pop('user_id')
    session.pop('name')
    return render_template('user/login.html')


@user_blueprint.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('user/login.html')

    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        user_name = data.get('user_name')
        user_pass = data.get('pass_word')
        cus_status = data.get('cus_status')
        results = {'code': RET.OK, 'msg': MSG.OK}
        try:
            if cus_status == "main":
                user_data = SqlData().search_user_info(user_name)
                user_id = user_data.get('user_id')
                pass_word = user_data.get('password')
                name = user_data.get('name')
                if user_pass == pass_word:
                    session['user_id'] = user_id
                    session['name'] = name
                    session['vice_id'] = None
                    session.permanent = True
                    return jsonify(results)
                else:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = MSG.PSWDERROR
                    return jsonify(results)
            if cus_status == 'vice':
                user_data = SqlData().search_user_vice_info(user_name)
                user_id = user_data.get('user_id')
                password = user_data.get('password')
                vice_id = user_data.get('vice_id')
                if password == user_pass:
                    # 存储到缓存
                    session['user_id'] = user_id
                    session['name'] = user_name
                    session['vice_id'] = vice_id
                    session.permanent = True
                    # 存储子子账号操作权限到redis
                    res = SqlData().search_acc_vice(user_id)
                    RedisTool().hash_set('vice_auth', res.get('vice_id'), res)
                    return jsonify(results)
                else:
                    results['code'] = RET.SERVERERROR
                    results['msg'] = MSG.PSWDERROR
                    return jsonify(results)

        except Exception as e:
            logging.error(str(e))
            results['code'] = RET.SERVERERROR
            results['msg'] = MSG.DATAERROR
            return jsonify(results)
