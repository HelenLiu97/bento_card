import pymysql
from DBUtils.PooledDB import PooledDB


class ConnMysql(object):
    __pool = None

    def __enter__(self):
        self.conn = self.__getconn()
        self.cursor = self.conn.cursot()

    def __getconn(self):
        if self.__pool is None:
            host = "127.0.0.1"
            port = 3306
            user = "root"
            password = "admin"
            database = "bento"
            self.__pool = PooledDB(pymysql, 6, host=host, port=port,
                                 user=user, passwd=password, db=database,
                                 charset='utf8', setsession=['SET AUTOCOMMIT = 1']
                                 )
        return self.__pool.connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    def getconn(self):
        conn = self.__getconn()
        cursor = conn.cursor()
        return conn, cursor


def get_my_connection():
    return ConnMysql()
