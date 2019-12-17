from email.header import Header
from smtplib import SMTP_SSL
from email.mime.text import MIMEText

# 用什么邮箱发
my_sender = "iuwby@qq.com"

# 发送给谁
send_her = "buysys@163.com"

# 密钥
s_keys = "gxzegzuvcnvrdjjg"

# 要发送的内容
context = "测试"

# 邮件头部信息
header_info = "测试"


def mail():
    ret = True
    try:
        msg = MIMEText(context, 'plain', 'utf-8')
        msg['From'] = my_sender
        msg['TO'] = send_her
        msg['Subject'] = Header(header_info, 'utf-8')

        server = SMTP_SSL('smtp.qq.com', 465)
        server.login(my_sender, s_keys)
        server.sendmail(my_sender, send_her, msg.as_string())
        server.quit()
    except Exception as e:
        print(e)
        ret = False
    return ret


while True:
    res = mail()
    print(res)
