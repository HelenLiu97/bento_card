import pymysql
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")

d = {
    "dd": 11,
}
print(d.get("dd"))

