# coding=utf-8
import logging
import smtplib  # 引入SMTP协议包
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # 创建包含多个部分的邮件体
from email.mime.image import MIMEImage
# from concurrent.futures import ThreadPoolExecutor
# from tools_me.parameter import DIR_PATH

# msg_to = "2404052713@qq.com"  # 收件人邮箱


def send(context, pic_list, msg_to):
    msg_from = "2172767522@qq.com"  # 发送方邮箱
    passwd = "atkzoaptyqlaeaaj"  # 填入发送方邮箱的授权码
    subject = "bento"  # 主题
    msg = MIMEMultipart('related')
    image_tent = ""
    for i in range(len(pic_list)):
        image_tent += '<img src="cid:' + str(i) + '" alt="' + str(i) + '">'

    content = MIMEText('<html><body><div>' + context + '</div>' + image_tent + '</body></html>',
                       'html', 'utf-8')  # 正文

    msg.attach(content)
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to

    index = 0
    for pic in pic_list:
        file = open(pic, "rb")
        img_data = file.read()
        file.close()
        img = MIMEImage(img_data)
        imgid = str(index)
        img.add_header('Content-ID', imgid)
        msg.attach(img)
        index += 1
    send_num = 0
    while send_num < 100:
        try:
            s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
            s.login(msg_from, passwd)
            s.sendmail(msg_from, msg_to, msg.as_string())
            break
        except Exception as e:
            logging.error(e)
            continue
        finally:
            send_num += 1
    return True


