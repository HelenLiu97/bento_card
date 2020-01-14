import pymysql
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")



class SqlData(object):
     def __init__(self):
         host = "127.0.0.1"
         port = 3306
         user = "root"
         password = "baocui123"
         database = "bento"
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

     def update_admin_field(self, field, value):
         sql = "UPDATE admin_info SET {}='{}'".format(field, value)
         try:
             self.cursor.execute(sql)
             self.connect.commit()
         except Exception as e:
             logging.error("更新ADMIN字段失败!" + str(e))
             self.connect.rollback()
         self.close_connect()

     def search_set_change(self):
         sql = "SELECT set_change, set_range FROM admin_info"
         self.cursor.execute(sql)
         rows = self.cursor.fetchone()
         self.close_connect()
         return rows[0], rows[1]
