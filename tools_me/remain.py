import operator
import threading
# from tools_me.RSA_NAME.helen import QuanQiuFu


info = list()


def loop(card_info):
    global info
    card_no = card_info.get('card_no')
    try:
        resp = QuanQiuFu().query_card_info(card_no)
        if resp.get('resp_code') == '0000':
            detail = resp.get('response_detail')
            freeze_fee_all = detail.get('freeze_fee_all')
            balance = detail.get('balance')
            f_freeze = int(freeze_fee_all) / 100
            f_balance = int(balance) / 100
            remain = round(f_balance - f_freeze, 2)
        else:
            msg = resp.get('resp_msg')
            remain = msg
    except:
        remain = '查询失败!'
    card_info['remain'] = remain
    # print(card_info)
    info.append(card_info)


def get_card_remain(loops):
    global info
    threads = []
    n = 1
    for i in loops:
        i['number'] = n
        n += 1
    nloops = range(len(loops))
    for i in nloops:
        t = threading.Thread(target=loop, args=(loops[i], ))
        threads.append(t)
    for i in nloops:  # start threads 此处并不会执行线程，而是将任务分发到每个线程，同步线程。等同步完成后再开始执行start方法
        threads[i].start()
    for i in nloops:  # jion()方法等待线程完成
        threads[i].join()

    res = sorted(info, key=operator.itemgetter('number'))
    info = list()
    return res


if __name__ == '__main__':
    get_card_remain([{}, {}])
