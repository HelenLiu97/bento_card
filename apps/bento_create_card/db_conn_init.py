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
            database = "bento_card"
            self.__pool = PooledDB(pymysql, maxconnections=6, mincached=3, maxcached=5, maxshared=3, blocking=True,
                                   maxusage=None, ping=0, host=host, port=port, user=user, passwd=password, db=database,
                                   charset='utf8', setsession=[]
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
