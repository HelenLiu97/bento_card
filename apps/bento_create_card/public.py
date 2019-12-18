import time
import datetime
from dateutil.relativedelta import relativedelta


def change_today(datatime, day):
    time_l = datatime.replace("-0", "-").split("-")
    d1 = datetime.datetime(int(time_l[0]), int(time_l[1]), int(time_l[2]))
    d2 = d1 + relativedelta(days=day)
    d3 = datetime.datetime.strptime(str(d2), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    return d3


def cut_list(ls, n):
    return [ls[i:i + n] for i in range(0, len(ls), n)]


class Key():
    ACCESSKEY = "4IEqK6pqfbC6CH8uf4oSXA"
    SECRETKEY = "XQH2NVKqTOdbKO3jIf1F1g"
    URL = "https://api.bentoforbusiness.com/"
    SANDBOX = "https://api.sandbox.bentoforbusiness.com/"


def get_time():
    customStartDate = int(round(time.time() * 1000))

    y = datetime.datetime.now().year
    m = datetime.datetime.now().month
    d = datetime.datetime.now().day
    end_time = "{}-{}-{} 00:00:00".format(y + 1, m, d)
    customEndDate = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S"))) * 1000
    return customStartDate, customEndDate


if __name__ == "__main__":
    g, t = get_time()
    print(g, t)
