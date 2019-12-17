import pymysql
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")

class SqlData():
    def __init__(self):
        host = "rm-j6c3t1i83rgylsuamvo.mysql.rds.aliyuncs.com"
        port = 3306
        user = "wuanlin"
        password = "trybest_1"
        database = "email_test"
        self.connect = pymysql.Connect(
            host=host, port=port, user=user,
            passwd=password, db=database,
            charset='utf8'
                )
        self.cursor = self.connect.cursor()

    def search(self):
        sql = "SELECT name FROM reged_fr"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        for row in rows:
            yield {
                "username": row[0]
        }

class Sd():
    def __init__(self):
        host = "rm-j6c3t1i83rgylsuamvo.mysql.rds.aliyuncs.com"
        port = 3306
        user = "wuanlin"
        password = "trybest_1"
        database = "bento"
        self.connect = pymysql.Connect(
            host=host, port=port, user=user,
            passwd=password, db=database,
            charset='utf8'
                )
        self.cursor = self.connect.cursor()

    def aaa(self, username):
            sql = "INSERT INTO BENTO_CARD_NAME(USERNAME) values('{}')".format(username)
            try:
                self.cursor.execute(sql)
                self.connect.commit()
            except Exception as e:
                logging.warning("下单成功数据库更新数据失败" + str(e))
                self.connect.rollback()
            self.close_connect()

    def close_connect(self):
        if self.cursor:
            self.cursor.close()
        if self.connect:
            self.connect.close()

if __name__ == "__main__":
    for i in SqlData().search():
        try:
            Sd().aaa(username=i.get("username").strip())
        except Exception as e:
            pass
