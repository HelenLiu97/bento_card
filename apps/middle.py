import json
import logging
import operator

from tools_me.mysql_tools import SqlData
from flask import request, render_template, jsonify, session, g
from tools_me.other_tools import middle_required, get_nday_list, now_year, now_day, date_to_week, wed_to_tu
from tools_me.parameter import RET, MSG
from . import middle_blueprint


@middle_blueprint.route('/change_phone', methods=['GET'])
@middle_required
def change_phone():
    middle_id = g.middle_id
    phone_num = request.args.get('phone_num')
    results = dict()
    try:
        SqlData().update_middle_field('phone_num', phone_num, middle_id)
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        return jsonify(results)
    except Exception as e:
        logging.error(str(e))
        results['code'] = RET.SERVERERROR
        results['msg'] = MSG.SERVERERROR
        return jsonify(results)


@middle_blueprint.route('/logout', methods=['GET'])
@middle_required
def logout():
    session.pop('middle_id')
    return render_template('middle/login_middle.html')


@middle_blueprint.route('/money_detail', methods=['GET'])
# @middle_required
def money_detail():
    info_id = request.args.get('info_id')
    detail = SqlData().search_middle_money_field('detail', int(info_id))
    detail_list = json.loads(detail)
    context = dict()
    context['info_list'] = detail_list
    return render_template('middle/money_detail.html', **context)


@middle_blueprint.route('/middle_info', methods=['GET'])
@middle_required
def user_info():
    middle_id = g.middle_id
    dict_info = SqlData().search_middle_detail(middle_id)
    account = dict_info.get('account')
    phone_num = dict_info.get('phone_num')
    card_price = dict_info.get('card_price')
    context = {
        'account': account,
        'card_price': card_price,
        'phone_num': phone_num,
    }
    return render_template('middle/middle_info.html', **context)


@middle_blueprint.route('/middle_money', methods=['GET'])
@middle_required
def middle_money():
    # 编写定时脚本:每周三统计上周三至本周二中介下的客户开卡数量插入到middle_money表
    # 1,所有中介;2,每一个中介下的所有客户,计算费用和数量

    # 根据id查寻middle_money表返回统计的开卡数量
    try:
        middle_id = g.middle_id
        limit = request.args.get('limit')
        page = request.args.get('page')
        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        info_list = SqlData().search_middle_money(middle_id)
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


# 根据缓存中介缓存id查询客户,在根据客户id查询用的卡数量
@middle_blueprint.route('/customer_info', methods=['GET'])
@middle_required
def task_list():
    if request.method == 'GET':
        try:
            middle_id = g.middle_id
            limit = request.args.get('limit')
            page = request.args.get('page')
            account_list = SqlData().search_user_middle_info(middle_id)
            if not account_list:
                return jsonify({'code': RET.OK, 'msg': MSG.NODATA})
            info_list = list()
            for u in account_list:
                u_id = u.get('id')
                card_count = SqlData().search_card_count(u_id, '')
                u['card_num'] = card_count
                info_list.append(u)
            page_list = list()
            results = dict()
            results['code'] = RET.OK
            results['msg'] = MSG.OK
            info_list = list(reversed(info_list))
            for i in range(0, len(info_list), int(limit)):
                page_list.append(info_list[i:i + int(limit)])
            results['data'] = page_list[int(page) - 1]
            results['count'] = len(info_list)
            return jsonify(results)
        except Exception as e:
            logging.error(str(e))
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.SERVERERROR})


# 查询折线图数据(today, week, month)
@middle_blueprint.route('/line_chart/', methods=['GET'])
@middle_required
def test():
    today = request.args.get('today')
    week = request.args.get('week')
    middle_id = g.middle_id
    if today:
        n_day = now_day()
        one_time_range = "AND act_time BETWEEN '" + n_day + ' 00:00:00' + "'" + " and '" + n_day + " 05:59:59'"
        two_time_range = "AND act_time BETWEEN '" + n_day + ' 06:00:00' + "'" + " and '" + n_day + " 11:59:59'"
        three_time_range = "AND act_time BETWEEN '" + n_day + ' 12:00:00' + "'" + " and '" + n_day + " 17:59:59'"
        four_time_range = "AND act_time BETWEEN '" + n_day + ' 16:00:00' + "'" + " and '" + n_day + " 23:59:59'"

        account_list = SqlData().search_user_field_middle(middle_id)
        if account_list:
            data_info = list()
            for i in account_list:
                data_dict = dict()
                card_num_list = list()
                account_id = i.get('id')
                card_num_1 = SqlData().search_card_count(account_id, one_time_range)
                card_num_list.append(card_num_1)
                card_num_2 = SqlData().search_card_count(account_id, two_time_range)
                card_num_list.append(card_num_2)
                card_num_3 = SqlData().search_card_count(account_id, three_time_range)
                card_num_list.append(card_num_3)
                card_num_4 = SqlData().search_card_count(account_id, four_time_range)
                card_num_list.append(card_num_4)
                data_dict['name'] = i.get('name')
                data_dict['data'] = card_num_list
                data_info.append(data_dict)
        else:
            data_info = [{'name': '无客户', 'data': [0, 0, 0, 0]}]

        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        results['data'] = data_info
        return jsonify(results)
    if week:
        day_list = wed_to_tu()
        account_list = SqlData().search_user_field_middle(middle_id)
        data = list()
        if account_list:
            for u_id in account_list:
                info_dict = dict()
                count_list = list()
                for i in day_list:
                    sql_str = "AND act_time BETWEEN '" + str(i) + ' 00:00:00' + "'" + " and '" + str(i) + " 23:59:59'"
                    account_id = u_id.get('id')
                    card_count = SqlData().search_card_count(account_id, sql_str)
                    count_list.append(card_count)
                info_dict['name'] = u_id.get('name')
                info_dict['data'] = count_list
                data.append(info_dict)
        else:
            data = [{'name': '无客户', 'data': [0, 0, 0, 0, 0, 0, 0]}]

        results = dict()
        results['code'] = RET.OK
        results['msg'] = MSG.OK
        results['data'] = data
        return jsonify(results)


@middle_blueprint.route('/', methods=['GET', 'POST'])
@middle_required
def middle_index():
    if request.method == 'GET':
        middle_id = g.middle_id
        day_list = get_nday_list(30)
        year = now_year()
        context = dict()
        context['day_list'] = day_list
        context['year'] = year
        name = SqlData().search_middle_field('name', middle_id)
        context['name'] = name
        return render_template('middle/index.html', **context)


@middle_blueprint.route('/login', methods=['GET', 'POST'])
def middle_login():
    if request.method == 'GET':
        return render_template('middle/login_middle.html')
    if request.method == 'POST':
        data = json.loads(request.form.get('data'))
        account = data.get('account')
        pass_word = data.get('password')
        info = SqlData().search_middle_login(account)
        if not info:
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.PSWDERROR})
        middle_id = info[0][0]
        password = info[0][1]
        if pass_word != password:
            return jsonify({'code': RET.SERVERERROR, 'msg': MSG.PSWDERROR})
        else:
            session['middle_id'] = middle_id
            return jsonify({'code': RET.OK, 'msg': MSG.OK})
