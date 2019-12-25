# coding:utf-8
# 以下是一些常用参数

# 保存excel文件的路径


ACCOUNT_DIR = ""
TASK_DIR = ""
DW_TASK = ""
DW_ACCOUNT = ""
SMT_TASK = ""


class DIR_PATH:
    # LOG_PATH = "G:/world_pay/static/log/card.log"
    LOG_PATH = "/bento_web_version2/static/log/card.log"

    # PRI_PEM = "G:\\world_pay\\tools_me\\RSA_NAME\\privkey_henry.pem"
    PRI_PEM = "/var/www/bento_web_version/tools_me/RSA_NAME/privkey_henry.pem"

    # PUB_PEM = 'G:\\world_pay\\tools_me\\RSA_NAME\\pro_epaylinks_publickey.pem'
    PUB_PEM = "/var/www/bento_web/tools_me/RSA_NAME/pro_epaylinks_publickey.pem"

    PHOTO_DIR = "/bento_web_version2/static/pay_pic"


class RET:
    OK = 0
    SERVERERROR = 502


class MSG:
    OK = '完成'
    SERVERERROR = 'SERVER ERROR'
    NODATA = 'NODATA'
    DATAERROR = '参数错误!'
    PSWDERROR = 'PASS_WORD ERROR'
    PSWDLEN = '密码长度不得小于6位数!'


class CACHE:
    TIMEOUT = 15


class TASK:
    SUM_ORDER_CODE = ''


class ORDER:
    TASK_CODE = ''
    BUY_ACCOUNT = ''
    TERRACE = ''
    COUNTRY = ''
    LAST_BUY = ''
    STORE = ''
    ASIN = ''
    STORE_GROUP = ''
    ASIN_GROUP = ''


TRANS_STATUS = {
    'WAIT': '待付款',
    'PROCESS': '处理中',
    'PAID': '已付款',
    'SUBBANK': '已提交银行卡',
    'SUCC': '交易成功',
    'FINISH': '交易成功',
    'AUTH': '已授权',
    'FAIL': '交易失败',
    'CLOSED': '交易关闭'
}


class TRANS_TYPE:
    IN = "收入"
    OUT = "支出"


class DO_TYPE:
    CREATE_CARD = "开卡"
    TOP_UP = "充值"
    REFUND = "退款"
