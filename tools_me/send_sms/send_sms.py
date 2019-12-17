# coding=utf-8
import logging

from tools_me.send_sms.CCPRestSDK import REST

# import ConfigParser

# 主帐号
accountSid = '8a216da862dcd1050162e7e08d2c061a';

# 主帐号Token
accountToken = 'd57e02fea2004335900ef93f37679792';

# 应用Id
appId = '8a216da86e011fa3016e5e4524293301';

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com';

# 请求端口
serverPort = '8883';

# REST版本号
softVersion = '2013-12-26';


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id


class CCP(object):
    '''自己封装的发送短信的辅助类'''
    # 用来保存对象的类属性
    instance = None

    def __new__(cls):
        # 判断CCP类有没有已经创建好的对象
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)

            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        return cls.instance

    def send_Template_sms(self, to, datas, temp_Id):
        # 初始化REST SDK

        result = self.rest.sendTemplateSMS(to, datas, temp_Id)

        # result返回的数据示例 {'statusCode': '000000', 'templateSMS': {'smsMessageSid': '74b8e58f80bf4484966b0cdaad82bc25', 'dateCreated': '20190923102711'}}

        status_code = result.get('statusCode')

        if status_code:
            return int(status_code)
        else:
            logging.error(result)
            return status_code


if __name__ == "__main__":
    ccp = CCP()
    # 1代表模板ID，下载SDK的官网api文档有说明
    ret = ccp.send_Template_sms("13590024395", ["123456", "2019-09-13", 10000], 485108)
    print(ret)

