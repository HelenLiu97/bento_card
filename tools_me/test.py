import re
import time
import requests


res_phone = re.match('^1(3[0-9]|4[5,7]|5[0-9]|6[2,5,6,7]|7[0,1,3,7,8]|8[0-9]|9[1,8,9])\d{8}$', '17326524952')
print(res_phone)


'''

def wirte_txt(String):
    with open('outlog.txt', 'a') as f:
        f.write(String + "\n")


wirte_txt("开始检测" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
while True:
    try:
        res = requests.get('http://47.115.119.11/admin/')
        # print(res.status_code)
        if res.status_code != 200:
            print('超时')
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    except:
        wirte_txt("超时！ 超时时间: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
'''