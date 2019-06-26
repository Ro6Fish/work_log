#!/usr/bin/env python

import datetime
import configparser
import os
from os import path
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from simplejson import JSONDecodeError

dir_path = path.dirname(path.realpath(__file__))

conf = configparser.ConfigParser()

conf.read(path.join(dir_path, 'config.ini'))

# base_datetime = datetime.datetime.now()
base_datetime = datetime.datetime.strptime('2019-06-28', '%Y-%m-%d')

# 接口是否正常，默认true正常
is_api_ok = True


# 返回格式化后的当前时间+days天 返回datetime
def date_delay(days):
    days_delay = base_datetime + datetime.timedelta(days=days)
    return days_delay


# 是否是假日 true 是假日 false 不是假日
def is_holiday(date):
    date_format = date.strftime('%Y%m%d')

    request = requests.get('https://tool.bitefu.net/jiari/?d=%s&info=1' % date_format)
    # request = requests.get('https://api.github.com/user')  # for test

    try:
        json = request.json()

        date_type = json['type']  # 0: 工作 1：假日 2：节日

        # 调用接口比对此日期是否是假日 date_format
        if date_type != 0:
            return True

    except (OSError, JSONDecodeError, KeyError):
        # 异常情况发送邮件提醒
        send_error_mail()
        global is_api_ok
        is_api_ok = False

    return False


# 发送报错邮件
def send_error_mail():
    msg_from = conf.get('email', 'msg_from')
    passwd = conf.get('email', 'passwd')
    msg_to = msg_from
    cs_to = conf.get('email', 'cs_to')

    subject = '免费日期信息api异常'
    msg_content = '免费日期信息api异常'
    content = MIMEText('<html>'
                       '<body>'
                       '<div style=white-space:pre-line;>'
                       '%s'
                       '</div>'
                       '</body>'
                       '</html>' % msg_content,  # 邮件内容
                       'html',
                       'utf-8'
                       )

    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    msg['Cc'] = cs_to
    msg.attach(content)

    try:
        s = smtplib.SMTP_SSL('smtp.mxhichina.com', 465)  # 邮件服务器及端口
        s.login(msg_from, passwd)
        s.sendmail(msg_from, msg_to.split(",") + cs_to.split(','), msg.as_string())
        print('api异常邮件发送成功')
        return True
    except OSError:
        print('api异常邮件发送失败')
    finally:
        s.quit()

    return False


# 发送周报邮件
def send_mail(title):
    msg_from = conf.get('email', 'msg_from')
    passwd = conf.get('email', 'passwd')
    msg_to = conf.get('email', 'msg_to')
    cs_to = conf.get('email', 'cs_to')

    subject = title

    log_file = open('./log.md')
    read = log_file.read()
    log_file.close()

    msg_content = read

    content = MIMEText('<html>'
                       '<body>'
                       'Hi, Tom:<br>'
                       '<br>'
                       '这是本周的工作周报，请查阅。<br>'
                       '<br>'
                       '<div style=white-space:pre-line;>'
                       '%s'
                       '</div>'
                       '</body>'
                       '</html>' % msg_content,  # 邮件内容
                       'html',
                       'utf-8'
                       )

    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to
    msg['Cc'] = cs_to
    msg.attach(content)

    try:
        s = smtplib.SMTP_SSL('smtp.mxhichina.com', 465)  # 邮件服务器及端口
        s.login(msg_from, passwd)
        s.sendmail(msg_from, msg_to.split(",") + cs_to.split(','), msg.as_string())
        print('%s发送成功' % title)
        return True
    except OSError:
        print('%s发送失败' % title)
    finally:
        s.quit()

    return False


# 判断是否需要执行脚本
def main():
    cur_date = date_delay(0)

    # 判断当天日期是否是假期，如果是则什么都不做，如果不是则继续判断当前日期的后一天日期
    if not is_holiday(cur_date):
        # 当前日期的后一天日期如果不是假期则什么也不做，如果是假期则计算出当前时间以前最早不是假期的日期
        if is_holiday(date_delay(1)):

            i = 0
            before_date = date_delay(i)
            before_date_is_not_holiday = True

            while before_date_is_not_holiday:
                if is_holiday(date_delay(i)):
                    break
                else:
                    before_date = date_delay(i)
                    i -= 1

            if is_api_ok:
                # 解析上班开始日期和结束日期
                start_date = datetime.datetime.strftime(before_date, '%Y/%m/%d')
                end_date = datetime.datetime.strftime(cur_date, '%Y/%m/%d')

                title = '周报%s-%s' % (start_date, end_date)

                is_send = send_mail(title)

                if is_send:
                    # 文件名 2019_0623-0624.md
                    start_month = datetime.datetime.strftime(before_date, '%m%d')
                    end_month = datetime.datetime.strftime(cur_date, '%m%d')

                    shutil.copy(path.join(dir_path, 'log.md'),
                                path.join(dir_path, 'logs/%s_%s-%s.md' % (base_datetime.year, start_month, end_month)))

                    # 重置文件内容
                    log_init_content = '本周任务:\n\n\n\n\n\n下周任务:\n\n- 日常运维工作  '
                    log_file = open('log.md', 'w')
                    log_file.write(log_init_content)
                    log_file.close()

            else:
                print('api接口异常')

        else:
            print('当前日期不是假期，后天日期%s不是假期，不用发送周报' % datetime.datetime.strftime(date_delay(1), '%Y-%m-%d'))

    else:
        print('当前日期是假期，不用发送周报')


os.popen('git pull')

# 执行程序
main()

os.popen('./git.sh')
