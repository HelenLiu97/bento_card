import json
import time
import re
import logging
from flask import render_template, request, jsonify, redirect, session
from tools_me.mysql_tools import SqlData
from tools_me.other_tools import sum_code, xianzai_time, verify_required
from tools_me.parameter import RET, MSG
from tools_me.send_sms.send_sms import CCP
from . import verify_pay_blueprint


@verify_pay_blueprint.route('/del_log/', methods=['GET'])
@verify_required
def del_log():
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    limit = request.args.get('limit')
    page = request.args.get('page')
    status = request.args.get('status')
    data = SqlData().search_pay_log(status)
    if not data:
        results['msg'] = MSG.NODATA
        return jsonify(results)
    info = list(reversed(data))
    page_list = list()
    for i in range(0, len(info), int(limit)):
        page_list.append(info[i:i + int(limit)])
    info_list = page_list[int(page) - 1]

    # 查询当次充值时的账号总充值金额
    new_list = list()
    for o in info_list:
        x_time = o.get('ver_time')
        user_id = o.get('cus_id')
        sum_money = SqlData().search_time_sum_money(x_time, user_id)
        o['sum_balance'] = round(sum_money, 2)
        new_list.append(o)

    results['data'] = new_list
    results['count'] = len(data)
    return jsonify(results)


@verify_pay_blueprint.route('/all_account/', methods=['GET'])
@verify_required
def all_account():
    data = SqlData().recharge_all_account()
    return jsonify({
        "code": RET.OK,
        "msg": MSG.OK,
        "count": len(data),
        "data": data,
    })


@verify_pay_blueprint.route('/add_account/', methods=['POST'])
@verify_required
def add_account():
    results = {"code": RET.OK, "msg": MSG.OK}
    try:
        data = json.loads(request.form.get('data'))
        name = data.get('name')
        account = data.get('username')
        password = data.get('password')
        SqlData().recharge_add_account(name=name, username=account, password=password)
        return jsonify(results)
    except Exception as e:
        logging.error(e)
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@verify_pay_blueprint.route('/login/', methods=['GET', 'POST'])
def verify_login():
    if request.method == 'GET':
        return render_template('verify_pay/login.html')
    if request.method == 'POST':
        data = request.values.to_dict()
        user_name = data.get('username')
        pass_word = data.get('password')
        if user_name == "GUTE123" and pass_word == "trybest":
            session['verify_pay'] = 'T'
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '账号或密码错误!'})


@verify_pay_blueprint.route('/')
@verify_required
def verify_index():
    return render_template('verify_pay/index.html')


@verify_pay_blueprint.route('/pay_log/', methods=['GET'])
@verify_required
def pay_log():
    results = dict()
    results['code'] = RET.OK
    results['msg'] = MSG.OK
    limit = request.args.get('limit')
    page = request.args.get('page')
    status = request.args.get('status')
    data = SqlData().search_pay_log(status)
    if not data:
        results['msg'] = MSG.NODATA
        return jsonify(results)
    info = list(reversed(data))
    page_list = list()
    for i in range(0, len(info), int(limit)):
        page_list.append(info[i:i + int(limit)])
    info_list = page_list[int(page) - 1]

    # 查询当次充值时的账号总充值金额
    new_list = list()
    for o in info_list:
        x_time = o.get('ver_time')
        user_id = o.get('cus_id')
        sum_money = SqlData().search_time_sum_money(x_time, user_id)
        o['sum_balance'] = round(sum_money, 2)
        new_list.append(o)

    results['data'] = new_list
    results['count'] = len(data)
    return jsonify(results)


@verify_pay_blueprint.route('/top_up/', methods=['GET', 'POST'])
@verify_required
def top_up():
    if request.method == 'GET':
        pay_time = request.args.get('pay_time')
        cus_name = request.args.get('cus_name')
        bank_msg = request.args.get('bank_msg')
        context = dict()
        context['pay_time'] = pay_time
        context['cus_name'] = cus_name
        context['bank_msg'] = bank_msg
        return render_template('verify_pay/check.html', **context)
    if request.method == 'POST':
        try:
            results = dict()
            data = json.loads(request.form.get('data'))
            pay_time = data.get('pay_time')
            cus_name = data.get('cus_name')
            check = data.get('check')
            ver_code = data.get('ver_code')
            bank_address = data.get("bank_msg")

            # 校验参数验证激活码
            if check != 'yes':
                results['code'] = RET.SERVERERROR
                results['msg'] = '请确认已收款!'
                return jsonify(results)
            pass_wd = SqlData().search_pay_code('ver_code', cus_name, pay_time)
            if pass_wd != ver_code:
                results['code'] = RET.SERVERERROR
                results['msg'] = '验证码错误!'
                return jsonify(results)

            status = SqlData().search_pay_code('status', cus_name, pay_time)
            if status != '待充值':
                results['code'] = RET.SERVERERROR
                results['msg'] = '该订单已充值,请刷新界面!'
                return jsonify(results)

            # 验证成功后,做客户账户充值
            cus_id = SqlData().search_user_field_name('id', cus_name)

            '''
            # 判断是否需要更改充值金额(取消改动充值金额权限)
            if not money:
                money = SqlData().search_pay_code('top_money', cus_name, pay_time)
            else:
                money = float(money)
                # 更新新的充值金额
                SqlData().update_pay_money(money, cus_id, pay_time)
            '''

            money = SqlData().search_pay_code('top_money', cus_name, pay_time)
            pay_num = sum_code()
            t = xianzai_time()
            before = SqlData().search_user_field_name('balance', cus_name)
            balance = before + money
            user_id = SqlData().search_user_field_name('id', cus_name)
            pay_money = SqlData().search_pay_code('pay_money', cus_name, pay_time)
            # 更新银行卡收款金额
            if bank_address:
                pattern = re.compile(r'\d+\.?\d*')
                bank_number = pattern.findall(bank_address)
                bank_money = SqlData().search_bank_top(bank_number)
                update_money = float(pay_money) + float(bank_money)
                SqlData().update_bank_top(bank_number, update_money)
            else:
                # 更新首款码收款金额
                # pay_money = SqlData().search_pay_code('pay_money', cus_name, pay_time)
                url = SqlData().search_pay_code('url', cus_name, pay_time)
                SqlData().update_qr_money('top_money', pay_money, url)

            # 更新账户余额
            SqlData().update_user_balance(money, user_id)

            # 更新客户充值记录
            SqlData().insert_top_up(pay_num, t, money, before, balance, user_id)

            # 更新pay_log的订单的充值状态
            SqlData().update_pay_status('已充值', t, cus_id, pay_time)


            phone = SqlData().search_user_field_name('phone_num', cus_name)
            mid_phone = SqlData().search_pay_code('phone', cus_name, pay_time)

            # 给客户和代充值人发送短信通知
            money_msg = "{}元, 可用余额{}".format(money, balance)
            if phone:
                phone_list = phone.split(",")
                for p in phone_list:
                    CCP().send_Template_sms(p, [cus_name, t, money_msg], 485108)
            if mid_phone:
                CCP().send_Template_sms(mid_phone, [cus_name, t, money_msg], 485108)
            results['code'] = RET.OK
            results['msg'] = MSG.OK
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            results = dict()
            results['code'] = RET.SERVERERROR
            results['msg'] = str(e)
            return jsonify(results)


@verify_pay_blueprint.route('/del_pay/', methods=['POST'])
@verify_required
def del_pay():
    try:
        data = json.loads(request.form.get('data'))
        user_name = data.get('user_name')
        pay_time = data.get('pay_time')
        user_id = SqlData().search_user_field_name('id', user_name)
        SqlData().del_pay_log(user_id, pay_time)
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results = dict()
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)
