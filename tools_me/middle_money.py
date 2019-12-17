import json
import logging
import datetime
from .mysql_tools import SqlData


def xianzai_time():
    now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now_datetime


def date_to_week(t):
    date = datetime.datetime.strptime(t, '%Y-%m-%d')
    week = date.weekday()
    return week


def get_day_ago(day_number):
    yesterday = datetime.date.today() + datetime.timedelta(-day_number)
    return str(yesterday)


def sum_middle_money():
    try:
        wed_day = get_day_ago(7)
        thues_day = get_day_ago(1)

        # 判断是否是星期三和星期二
        value_start = date_to_week(wed_day) + 1
        value_end = date_to_week(thues_day) + 1
        if value_start != 3 or value_end != 2:
            logging.error('统计时间异常, 开始时间为: ' + wed_day + ';结束时间为: ' + thues_day)

        logging.error('开始统计计算中介费用!开始时间为: ' + wed_day + ';结束时间为: ' + thues_day)
        time_range = "AND act_time BETWEEN '" + wed_day + ' 00:00:00' + "'" + " and '" + thues_day + " 23:59:59'"
        middle_list = SqlData().search_middle_id()

        info_dict = dict()
        for middle_id in middle_list:
            card_price = SqlData().search_middle_field('card_price', middle_id)
            account_list = SqlData().search_user_field_middle(middle_id)
            one_cus = list()
            if account_list:
                for u in account_list:
                    u_id = u.get('id')
                    card_count = SqlData().search_card_count(u_id, time_range)
                    u['count'] = card_count
                    sum_money = card_count * card_price
                    u['sum_money'] = sum_money
                    if u:
                        one_cus.append(u)
                info_dict[middle_id] = one_cus
        _middle_list = list(info_dict.keys())
        for i in _middle_list:
            card_num = 0
            sum_money = 0
            card_price = SqlData().search_middle_field('card_price', i)
            detail = info_dict.get(i)
            for one in detail:
                num = one.get('count')
                money = one.get('sum_money')
                card_num += num
                sum_money += money
            now_time = xianzai_time()
            detail = json.dumps(detail, ensure_ascii=False)
            thues_day = thues_day
            SqlData().insert_middle_money(i, wed_day, thues_day, card_num, card_price, sum_money, now_time, '待确认', detail)
            # print(wed_day, thues_day, card_num, sum_money, now_time, card_price)
        return
    except Exception as e:
        logging.error('计算中介费,插入中介费失败!' + str(e))
        return


if __name__ == '__main__':
    sum_middle_money()
