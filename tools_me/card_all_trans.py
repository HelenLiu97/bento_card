# 这是一个非常重要的定时脚本

'''
    处理大量的交易数据，所以耗时较长，不能在接口直接处理，这样会导致服务器内存溢出(宕机)，所以用户定时更新
    将大量的数据保存在redis中，接口调用的时候直接在redis中获取data处理即可，历史遗留问题导致数据量太大没有
    太好的处理办法，调用处见：/admin/account_decline 和 /admin/all_trans
'''

import datetime
import operator
import time
from dateutil.relativedelta import relativedelta
import pymysql
import logging
import json
import redis
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


# 连接 Redis 数据库
class RedisTool(object):
    def __init__(self):

        pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
        self.r = redis.Redis(connection_pool=pool)

    def string_set(self, name, value):
        self.r.set(name, value)

    def string_get(self, name):
        return self.r.get(name)

    def string_del(self, name):
        self.r.delete(name)

    def hash_set(self, name, key, value, ):
        self.r.hset(name, key, json.dumps(value))

    def hash_get(self, name, key):
        res = self.r.hget(name, key)
        if not res:
            return None
        return json.loads(res)

    def hash_del(self, name, key):
        res = self.r.hdel(name, key)
        return res


# 连接mysql数据库
class SqlDataNative(object):
    def __init__(self):
        host = "127.0.0.1"
        port = 3306
        user = "root"
        password = "admin"
        database = "bento_card"
        self.connect = pymysql.Connect(
            host=host, port=port, user=user,
            passwd=password, db=database,
            charset='utf8'
                )
        self.cursor = self.connect.cursor()

    def close_connect(self):
        if self.cursor:
            self.cursor.close()
        if self.connect:
            self.connect.close()

    def search_card_number(self, field, alias):
        sql = "SELECT {} FROM bento_create_card WHERE alias='{}'".format(field, alias)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        return row

    def bento_alltrans(self):
        import json
        import time
        sql = "select alias, transactions_data,attribution from bento_user_decline where transactions_data_len != 0"
        self.cursor.execute(sql)
        i = self.cursor.fetchall()
        data = []
        for rows in i:
            try:
                for row in json.loads(rows[1]):
                    data.append({
                        "hand_money": rows[0],
                        "card_num": self.search_card_number("card_number", rows[0]),
                        "label": self.search_card_number("label", rows[0]),
                        "trans_type": row.get("payee").get("name"),
                        "do_type": row.get("status"),
                        "do_money": 0 if row.get('status') == 'DECLINED' else row.get('amount'),
                        "card_no": row.get("card").get("lastFour"),
                        "before_balance": rows[2],
                        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row.get("transactionDate") / 1000)),
                    })
                    # print(data)
                    # time.sleep(5)
            except Exception as e:
                print(e)
                logging.warning(str(e))
                continue
        self.close_connect()
        return data


# 时间格式转换的方法
def change_today(datatime, day):
    time_l = datatime.replace("-0", "-").split("-")
    d1 = datetime.datetime(int(time_l[0]), int(time_l[1]), int(time_l[2]))
    d2 = d1 + relativedelta(days=day)
    d3 = datetime.datetime.strptime(str(d2), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    return d3


# 统计每个用户近三天的decline
def user_decline(data):
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
        value['all_bili'] = float("%.4f" % (value.get('decl') / value.get('t_data') * 100)) if value.get(
            'decl') != 0 else 0
        value['bili'] = float("%.4f" % (value.get('three_decl') / value.get('three_tran') * 100)) if value.get(
            'three_tran') != 0 else 0
        if value.get('three_tran') != 0 and value.get('three_decl') / value.get('three_tran') > 0.1:
            value['show'] = 'T'
        else:
            value['show'] = 'F'
        res.append(value)
        # 设置缓存
    data = list(reversed(sorted(res, key=operator.itemgetter("bili"))))
    return data


# 使用redis缓存数据
RedisTool = RedisTool()


def run():

    # 查询所有卡的交易，数据量大所以用定时任务，定时更新。避免服务器内存溢出
    data = SqlDataNative().bento_alltrans()
    RedisTool.hash_set('admin_cache', 'card_all_trans', data)

    # 统计所有的用户的decline和所有卡交易信息关联，自处一并计算。避免服务器内存溢出
    decline_info = user_decline(data)
    RedisTool.hash_set('admin_cache', 'user_decline', decline_info)


if __name__ == '__main__':
    run()









