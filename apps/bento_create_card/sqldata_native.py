import time
import pymysql
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


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

    def count_bento_data(self, sqld):
        sql = "select COUNT(*) from bento_create_card {}".format(sqld)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        return rows

    def admin_search_data(self):
        sql = "SELECT * FROM bento_create_card where label='王先生大玩家3'"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        try:
            for i in rows:
                data.append({
                    "account_name": i[8],
                    "act_time": str(i[7]),
                    "card_name": i[1],
                    "card_no": "{}{}".format("\t", i[3]),
                    "cvv": "{}{}".format("\t", i[5]),
                    "expire": i[6],
                    "label": "",
                    "pay_passwd": "",
                })
        except Exception as e:
            logging.warning(str(e))
        finally:
            self.close_connect()
        return data

    def admin_alias_data(self, sqld):
        sql = "SELECT * FROM bento_create_card {}".format(sqld)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        try:
            for i in rows:
                data.append({
                    "account_name": i[8],
                    "act_time": str(i[7]),
                    "card_name": i[1],
                    "card_no": "{}{}".format("\t", i[3]),
                    "cvv": "{}{}".format("\t", i[5]),
                    "expire": i[6],
                    "label": i[9],
                    "pay_passwd": "",
                    "activation": i[2]
                })
        except Exception as e:
            logging.warning(str(e))
        finally:
            self.close_connect()
        return data

    def search_alias_data(self, user_label, attribution):
        # sql = "SELECT * FROM bento_create_card WHERE label='{}' and attribution='{}'".format(user_label, attribution)
        # if not user_label: 
        sql = "SELECT * FROM bento_create_card WHERE attribution='{}'".format(attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        n = 1
        try:
            for i in rows:
                data.append({
                    # "card_no": "{}{}".format("\t",i[3]),
                    "card_no": "{}{}".format("\t", i[3]) if i[10] != "已注销" else "{}{}".format("****", i[3][-4:]),
                    "act_time": str(i[7]),
                    "card_name": i[1],
                    "label": i[8],
                    "status": i[10],
                    "cvv": "{}{}".format("\t", i[5]),
                    "expire": i[6],
                    "number": n,
                    "remain": "双击查看",
                })
                n += 1
        except Exception as e:
            logging.warning(str(e))
        finally:
            self.close_connect()
        return data

    def search_data(self, limit_num):
        sql = "SELECT * FROM bento_card_name WHERE state='' order by rand() limit {}".format(limit_num)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        for i in rows:
            update_sql = "UPDATE bento_card_name SET state='已使用' WHERE id={}".format(i[0])
            try:
                self.cursor.execute(update_sql)
                self.connect.commit()
            except Exception as e:
                logging.warning("下单成功数据库更新数据失败" + str(e))
                self.connect.rollback()
            yield {
                "id": i[0],
                "username": i[1]
            }
        self.close_connect()

    def cardnum_fount_cardid(self, cardnum):
        sql = "SELECT card_id FROM bento_create_card WHERE card_number='{}'".format(cardnum)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows[0]

    def del_bencard(self, cardnumber):
        sql = 'UPDATE bento_create_card set label="已注销" where card_number="{}";'.format(cardnumber)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.warning("删除更新失败")
            self.connect.rollback()
        finally:
            self.close_connect()

    def cardnum_fount_alias(self, cardnum):
        sql = "SELECT alias FROM bento_create_card WHERE card_number='{}'".format(cardnum)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows[0]

    def fount_cardid_alias(self, card_no):
        sql = "SELECT card_id,alias FROM bento_create_card WHERE card_number='{}'".format(card_no)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows

    def close_connect(self):
        if self.cursor:
            self.cursor.close()
        if self.connect:
            self.connect.close()

    def alias_fount_cardid(self, alias):
        sql = "SELECT card_id FROM bento_create_card WHERE alias='{}'".format(alias)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows[0]

    def attribution_fount_cardid(self, alias):
        sql = "SELECT card_id FROM bento_create_card WHERE attribution='{}' and label != '已注销'".format(alias)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        self.close_connect()
        data = []
        for s in rows:
            data.append(int(s[0]))
        if data:
            return data
        return data

    def update_card_Balance(self, cardid, availableAmount, create_time):
        sql = "UPDATE bento_create_card set card_amount='{}', create_time='{}' where card_id='{}'".format(
            availableAmount, create_time, cardid)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.warning("更新卡上余额失败")
            self.connect.rollback()
        finally:
            self.close_connect()

    def update_card_data(self, pan, cvv, expiration, alias):
        sql = 'UPDATE bento_create_card set card_number="{}",card_cvv="{}",card_validity="{}" where alias="{}";'.format(
            pan, cvv, expiration, alias)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.warning("更新卡号卡密码及有效期失败")
            self.connect.rollback()
        finally:
            self.close_connect()

    def count_alias_data(self, attribution):
        sql = "select count(*) from bento_create_card where attribution='{}' and label!='已注销';".format(attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows

    def select_transaction_data(self, attribution, name_sql, card_sql, label_sql, time_sql):
        sql = "SELECT * FROM bento_create_card WHERE attribution='{}' {} {} {} {}".format(attribution, name_sql,
                                                                                          card_sql, label_sql, time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        n = 1
        try:
            for i in rows:
                data.append({
                    "card_no": "{}{}".format("\t", i[3]) if i[10] != "已注销" else "{}{}".format("****", i[3][-4:]),
                    "act_time": str(i[7]),
                    "card_name": i[1],
                    "label": i[8],
                    "status": i[10],
                    "cvv": "{}{}".format("\t", i[5]),
                    "expire": i[6],
                    "number": n,
                    "remain": "双击查看余额及交易记录",
                })
                n += 1
        except Exception as e:
            logging.warning(str(e))
        finally:
            self.close_connect()
        return data

    def bento_chart_data(self, alias, time_range):
        sql = "SELECT COUNT(*) FROM bento_create_card WHERE attribution='{}' {}".format(alias, time_range)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows[0][0]

    def insert_new_account(self, alias, card_id, card_amount, card_number, card_cvv, label, card_validity, attribution,
                           create_time):
        sql = "INSERT INTO bento_create_card(alias, card_id, card_amount, card_number, card_cvv, label, card_validity," \
              " attribution, create_time, card_status) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}','正常')".format(
            alias, card_id, card_amount, card_number, card_cvv, label, card_validity, attribution, create_time)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加用户交易记录失败!" + str(e))
            self.connect.rollback()
        finally:
            self.close_connect()

    def count_decline_data(self, attribution, min_today, max_today):
        sql = "SELECT count(*) FROM bento_declined_data WHERE attribution='{}' and date BETWEEN '{}' and '{}'".format(
            attribution, min_today, max_today)
        # sql = "SELECT count(*) FROM bento_declined_data WHERE attribution='{}'".format(attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        return rows[0]

    def search_decline_data(self, attribution, card_sql, time_sql):
        sql = "SELECT * FROM bento_declined_data WHERE attribution='{}' {} {}".format(attribution, card_sql, time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        for i in rows:
            data.append({
                "hand_money": i[1],
                'label': self.search_card_number('label', i[1]),
                'card_num': self.search_card_number('card_number', i[1]),
                "date": str(i[5]),
                "trans_type": i[2],
                "do_type": i[4],
                "card_no": i[7],
                "do_money": i[3],
                "before_balance": i[9],
                "reason": i[10],
            })
        return data

    def admin_decline_data(self, attribution, card_sql, time_sql):
        sql = "SELECT * FROM bento_declined_data WHERE status='DECLINED' {} {} {}".format(attribution, card_sql,
                                                                                          time_sql)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        data = []
        for i in rows:
            data.append({
                "hand_money": i[1],
                "date": str(i[5]),
                "trans_type": i[2],
                "do_type": i[4],
                "card_no": i[7],
                "do_money": i[3],
                "before_balance": i[9],
                "reason": i[10],
            })
        return data

    def count_admin_decline(self):
        sql = "SELECT count(*) FROM bento_declined_data"
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        return rows[0]

    def account_sum_transaction(self, attribution):
        sql = "select sum(transactions_data_len) from bento_user_decline where attribution='{}'".format(attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        try:
            return int(rows[0])
        except Exception as e:
            return 0

    def account_sum_decline_transaction(self, attribution):
        sql = "select COUNT(*) from bento_declined_data where attribution='{}'".format(attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchone()
        self.close_connect()
        return rows[0]

    def bento_all_alias(self):
        sql = "select attribution from bento_create_card"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        self.close_connect()
        data = []
        for row in rows:
            if row[0] not in data:
                data.append(row[0])
        return data

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

    def one_bento_alltrans(self, alias):
        import json
        import time
        sql = "select alias, transactions_data,attribution from bento_user_decline where transactions_data_len != 0 and attribution='{}'".format(
            alias)
        self.cursor.execute(sql)
        i = self.cursor.fetchall()
        data = []
        for rows in i:
            try:
                for row in json.loads(rows[1]):
                    data.append({
                        "hand_money": rows[0],
                        "label": self.search_card_number("label", rows[0]),
                        "card_num": self.search_card_number("card_number", rows[0]),
                        "trans_type": row.get("payee").get("name"),
                        "do_type": row.get("status"),
                        "do_money": row.get("amount"),
                        "card_no": row.get("card").get("lastFour"),
                        "before_balance": rows[2],
                        "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(row.get("transactionDate") / 1000)),
                    })
            except Exception as e:
                logging.warning(str(e))
                continue
        self.close_connect()
        return data

    def bento_notice(self):
        sql = "select notice from bento_notice"
        self.cursor.execute(sql)
        i = self.cursor.fetchone()
        self.close_connect()
        if i[0]:
            return i[0]
        else:
            return 0

    def update_bento_notice(self, value):
        sql = "UPDATE bento_notice SET notice = '{}'".format(value)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("更新ADMIN字段失败!" + str(e))
            self.connect.rollback()
        self.close_connect()

    def search_d(self, attribution):
        import json
        t = int(time.time()) * 1000
        sql = "select transactions_data from bento_user_decline where attribution='{}' and transactions_data_len != 0".format(
            attribution)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        n = 0
        for row in rows:
            for data in row:
                try:
                    for i in json.loads(data):
                        if i.get("transactionDate") > t - 259200000:
                            n += 1
                except Exception as e:
                    print(str(e))
        return n

    def select_label_status(self, card_no):
        sql = "SELECT label from bento_create_card where card_number='{}'".format(card_no.strip())
        self.cursor.execute(sql)
        i = self.cursor.fetchone()
        self.close_connect()
        return i[0]

    def update_bento_label(self, label_name, card_no):
        sql = "UPDATE bento_create_card SET label='{}' WHERE alias='{}'".format(label_name, card_no.strip())
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("update label failed" + str(e))
            self.connect.rollback()
        self.close_connect()

    def update_bento_status(self, status, card_no):
        sql = "UPDATE bento_create_card SET card_status='{}' WHERE card_number='{}'".format(status, card_no.strip())
        print(sql)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("update label failed" + str(e))
            self.connect.rollback()
        self.close_connect()

    # account operating log
    def insert_operating_log(self, cardid, operating_log, operating_time):
        sql = "INSERT INTO bento_card_operating_log(cardid, operating_log, operating_time) VALUES('{}', '{}', '{}')".format(
            cardid, operating_log, operating_time)
        try:
            self.cursor.execute(sql)
            self.connect.commit()
        except Exception as e:
            logging.error("添加用户交易记录失败!" + str(e))
            self.connect.rollback()
        finally:
            self.close_connect()

    # bento alias balance
    def select_alias_balance(self, attribution):
        sql = "select balance from bento_alias_balance where attribution='{}'".format(attribution)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        self.close_connect()
        if row:
            return row[0]
        return 0

    def cardid_fount_label(self, cardid):
        sql = "select label from bento_create_card where card_id = '{}'".format(cardid)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        self.close_connect()
        return row[0]

    def count_del_data(self, alias):
        sql = "select COUNT(label) from bento_create_card where label='已注销' and attribution='{}'".format(alias)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        self.close_connect()
        return row[0]

    def search_sum_remain(self):
        sql = "SELECT SUM(balance) FROM bento_alias_balance"
        self.cursor.execute(sql)
        row = self.cursor.fetchall()
        return row[0][0]


def main():
    card_name = ""
    attribution = "大龙"
    card_num = ""
    label = ""
    range_time = "2019-10-29 - 2019-10-25"

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
        time_sql = "AND create_time BETWEEN '{}' AND '{}'".format(max_time, min_time)

    print(SqlDataNative().select_transaction_data(attribution, name_sql, card_sql, label_sql, time_sql))


if __name__ == "__main__":
    print(SqlDataNative().cardid_fount_label(cardid=878521))
