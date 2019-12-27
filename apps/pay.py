import logging
import os
import re
import uuid
from flask import render_template, request, json, jsonify, session, redirect, url_for
from tools_me.mysql_tools import SqlData
from tools_me.other_tools import time_str, xianzai_time, pay_required, sum_code, dic_key
from tools_me.parameter import RET, MSG, DIR_PATH
from tools_me.send_email import send
from . import pay_blueprint
from concurrent.futures import ThreadPoolExecutor


executor = ThreadPoolExecutor(5)


@pay_blueprint.route('/logout/', methods=['GET'])
@pay_required
def logout():
    session.pop('pay_login')
    return render_template('pay/login.html')


@pay_blueprint.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('pay/login.html')
    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        login = data.get('login')
        pwd = data.get('pwd')
        code = data.get('code')
        ver_code = data.get('ver_code')
        account = SqlData.recharge_search_user(username=login)
        if ver_code != code:
            return jsonify({'code': RET.SERVERERROR, 'msg': '验证码错误!区分大小写!'})
        elif account and account.get("password") == pwd:
            session['pay_login'] = 'T'
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '账号或密码错误!'})


@pay_blueprint.route('/', methods=['GET'])
@pay_required
def index_pay():
    ex_change = SqlData.search_admin_field('ex_change')
    ex_range = SqlData.search_admin_field('ex_range')
    hand = SqlData.search_admin_field('hand')
    dollar_hand = SqlData.search_admin_field('dollar_hand')
    context = dict()
    context['ex_change'] = ex_change
    context['ex_range'] = ex_range
    context['hand'] = hand
    context['dollar_hand'] = dollar_hand
    return render_template('pay/index.html', **context)


@pay_blueprint.route('/acc_top_cn/', methods=['POST'])
@pay_required
def top_cn():
    if request.method == 'POST':
        '''
        1:校验前端数据是否正确
        2:查看实时汇率有没有变动
        3:核实客户是否存在
        '''
        data = json.loads(request.form.get('data'))
        sum_money = data.get('sum_money')
        top_money = data.get('top_money')
        cus_name = data.get('cus_name')
        cus_account = data.get('cus_account')
        phone = data.get('phone')
        phone2 = data.get("phone2")
        res = SqlData.search_user_check(cus_name, cus_account)
        if float(top_money) < 100:
            return jsonify({'code': RET.SERVERERROR, 'msg': '充值金额不能小于100$'})
        if not res:
            return jsonify({'code': RET.SERVERERROR, 'msg': '没有该用户!请核实后重试!'})
        if phone:
            ret = re.match(r"^1[35789]\d{9}$", phone)
            if not ret:
                results = dict()
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        if phone2:
            ret = re.match(r"^1[35789]\d{9}$", phone2)
            if not ret:
                results = dict()
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)

        ex_change = SqlData.search_admin_field('ex_change')
        ex_range = SqlData.search_admin_field('ex_range')
        hand = SqlData.search_admin_field('hand')
        _money_self = float(top_money) * (ex_change + ex_range) * (hand + 1)
        money_self = round(_money_self, 10)
        sum_money = round(float(sum_money), 10)
        if money_self == sum_money:
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '汇率已变动!请刷新界面后重试!'})


@pay_blueprint.route('/acc_top_dollar/', methods=['POST'])
@pay_required
def top_dollar():
    if request.method == 'POST':
        '''
        1:校验前端数据是否正确
        2:查看实时汇率有没有变动
        3:核实客户是否存在
        '''
        data = json.loads(request.form.get('data'))
        sum_money = data.get('sum_money')
        top_money = data.get('top_money')
        cus_name = data.get('cus_name')
        cus_account = data.get('cus_account')
        phone = data.get('phone')
        phone2 = data.get("phone2")
        res = SqlData.search_user_check(cus_name, cus_account)
        if float(top_money) < 2000:
            return jsonify({'code': RET.SERVERERROR, 'msg': '美金充值不可小于2000'})
        if not res:
            return jsonify({'code': RET.SERVERERROR, 'msg': '没有该用户!请核实后重试!'})
        if phone:
            ret = re.match(r"^1[35789]\d{9}$", phone)
            if not ret:
                results = dict()
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        if phone2:
            ret = re.match(r"^1[35789]\d{9}$", phone2)
            if not ret:
                results = dict()
                results['code'] = RET.SERVERERROR
                results['msg'] = '请输入符合规范的电话号码!'
                return jsonify(results)
        dollar = SqlData.search_admin_field('dollar_hand')
        _money_self = float(top_money) * (dollar + 1)
        money_self = round(_money_self, 10)
        sum_money = round(float(sum_money), 10)
        if money_self == sum_money:
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
        else:
            return jsonify({'code': RET.SERVERERROR, 'msg': '手续费已变动!请刷新界面后重试!'})


@pay_blueprint.route('/pay_pic/', methods=['GET', 'POST'])
@pay_required
def pay_pic():
    if request.method == 'GET':
        sum_money = request.args.get('sum_money')
        top_money = request.args.get('top_money')
        cus_name = request.args.get('cus_name')
        cus_account = request.args.get('cus_account')
        phone = request.args.get('phone')
        phone2 = request.args.get("phone2")
        ex_change = request.args.get('ex_change')
        # 取出目前当前收款金额最低的收款码
        qr_info = SqlData.search_qr_code('WHERE status=0')
        if not qr_info:
            url = ''
        else:
            url = ''
            value_list = list()
            for i in qr_info:
                value_list.append(i.get('sum_money'))
            value = min(value_list)
            for n in qr_info:
                money = n.get('sum_money')
                if value == money:
                    url = n.get('qr_code')
                    break
        context = dict()
        bank_top_data = SqlData.search_bank_info(sql_line='WHERE status=2')
        if bank_top_data:
            data = bank_top_data[0]
            context['bank_name'] = data.get('bank_name')
            context['bank_number'] = data.get('bank_number')
            context['bank_address'] = data.get('bank_address')
        else:
            # 一下三个循环和判断为处理相同收款人，多个账号，取低于累计20万的中的最小收款账号
            bank_data = SqlData.search_bank_info(sql_line='WHERE status=0')
            # bank_info 整理为一个收款人对应多个收款卡号 {'':[],'':[]} 格式
            bank_info = dict()
            for n in bank_data:
                bank_name = n.get('bank_name')
                if bank_name in bank_info:
                    info_list = bank_info.get(bank_name)
                    info_list.append(n)
                else:
                    info_list = list()
                    info_list.append(n)
                    bank_info[bank_name] = info_list
            # sum_money_dict 为统计一个账号一共充值了多少元
            sum_money_dict = dict()
            for i in bank_info:
                value = bank_info.get(i)
                money = 0
                for m in value:
                    money += float(m.get('day_money'))
                sum_money_dict[i] = money
            # min_dict 为取出满足累计收款低于20万的账户，且最小的充值战账户
            min_dict = dict()
            for acc in sum_money_dict:
                if sum_money_dict.get(acc) < 200000:
                    min_dict[acc] = sum_money_dict.get(acc)
            if len(min_dict) == 0:
                context['bank_name'] = '无符合要求收款账户！'
                context['bank_number'] = '请联系管理员处理！'
                context['bank_address'] = '-------------'
            else:
                # 在最小充值账户中取出最小收款卡号推送
                min_acc = min(zip(min_dict.values(), min_dict.keys()))
                min_acc = min_acc[1]
                acc_list = bank_info.get(min_acc)
                data = min(acc_list, key=dic_key)
                context['bank_name'] = data.get('bank_name')
                context['bank_number'] = data.get('bank_number')
                context['bank_address'] = data.get('bank_address')

        context['sum_money'] = sum_money
        context['top_money'] = top_money
        context['cus_name'] = cus_name
        context['cus_account'] = cus_account
        context['phone'] = "{},{}".format(phone, phone2) if phone2 else phone
        context['url'] = url
        context['ex_change'] = ex_change
        return render_template('pay/pay_pic.html', **context)
    if request.method == 'POST':
        '''
        获取充值金额, 保存付款截图. 发送邮件通知管理员
        '''
        # try:
        # 两组数据,1,表单信息充值金额,等一下客户信息 2,截图凭证最多可上传5张
        # print(request.form)
        # print(request.files)
        data = json.loads(request.form.get('data'))
        top_money = data.get('top_money')
        sum_money = data.get('sum_money')
        cus_name = data.get('cus_name')
        cus_account = data.get('cus_account')
        phone = data.get('phone')
        exchange = data.get('exchange')
        url = json.loads(request.form.get('url'))
        change_type = json.loads(request.form.get("change_type"))
        bank_name = json.loads(request.form.get("bank_name"))
        bank_number = json.loads(request.form.get("bank_number"))
        bank_address = json.loads(request.form.get("bank_address"))
        results = {'code': RET.OK, 'msg': MSG.OK}
        try:
            # 保存所有图片
            file_n = 'file_'
            pic_list = list()
            # 判断有无上传图片
            f_obj = request.files.get("{}{}".format(file_n, 1))
            if not f_obj:
                return jsonify({'code': RET.SERVERERROR, 'msg': "请先上传图片再操作"})
            for i in range(5):
                file_name = "{}{}".format(file_n, i + 1)
                fileobj = request.files.get(file_name)
                if fileobj:
                    now_time = sum_code()
                    file_name = cus_account + "_" + str(now_time) + str(i) + ".png"
                    file_path = os.path.join(DIR_PATH.PHOTO_DIR, file_name)
                    fileobj.save(file_path)
                    pic_list.append(file_path)
            n_time = xianzai_time()
            vir_code = str(uuid.uuid1())[:6]
            context = "客户:  " + cus_name + " , 于<span style='color:red'>" + n_time + "</span>在线申请充值: " \
                      + top_money + "美元, 折和人名币: <span style='color:red'>" + sum_money + "</span>元。本次计算汇率为: " + exchange + ", 验证码为: " + vir_code

            cus_id = SqlData.search_user_check(cus_name, cus_account)
            sum_money = float(sum_money)
            top_money = float(top_money)
            if change_type == "pic":
                SqlData.insert_pay_log(n_time, sum_money, top_money, vir_code, '待充值', phone, url, cus_id)
            elif change_type == "bank":
                SqlData.insert_pay_log(n_time, sum_money, top_money, vir_code, '待充值', phone,
                                         "{},{},{}".format(bank_name, bank_number, bank_address), cus_id)
            # 获取要推送邮件的邮箱
            top_push = SqlData.search_admin_field('top_push')
            top_dict = json.loads(top_push)
            email_list = list()
            for i in top_dict:
                email_list.append(top_dict.get(i))
            for p in email_list:
                executor.submit(send, context, pic_list, p)
                # send(context, pic_list, p)

            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': str(e)})
