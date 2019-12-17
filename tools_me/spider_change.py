import datetime
import re
import requests
from mysql_tools import SqlData


def xianzai_time():
    now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now_datetime


def ex_change():
    try:

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/54.0.2840.99 Safari/537.36'}

        url = 'http://www.boc.cn/sourcedb/whpj/'

        resp = requests.get(url, headers=headers)

        resp_text = resp.text

        title = re.findall('<td>(.*?)</td>', resp_text)

        country_iso = title[-16]

        s = country_iso.encode('ISO-8859-1')

        country_cn = s.decode('utf-8')

        if country_cn == '美元':

            return title[-13]
        else:
            return '9999999'

    except Exception as e:
        print(e)
        return '9999999'


if __name__ == '__main__':
    res = ex_change()
    print(res)
    res = round(float(res)/100, 4)
    SqlData().update_admin_field('ex_change', res)
    with open("/root/liuxiao/world_pay/tools_me/spider.txt", 'a') as f:
        t = xianzai_time()
        f.write(t + " " + str(res) + '\n')



