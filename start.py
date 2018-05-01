#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import click
import config
import logging
import shutil
import subprocess
import zipfile
import requests
from bs4 import BeautifulSoup
# Т.к. у нас корпоративное общение все отчеты шлем в слакер (при желании)
from slacker import Slacker


os.chdir(config.WORK_DIR)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(u'%(levelname)-8s [%(asctime)s]  %(message)s',))
logging.basicConfig(
    level=logging.INFO,
    format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
    filename='ai-bolit.log',
)
logging.getLogger('').addHandler(console)

def get_site_name(path):
    """
    Функция берет строку пути и отрезает последннее составляющее и возвращает его
    """
    if path[len(path) - 1] == '/':
        path = path[:-1]
    l = len(str(path).split('/'))
    name = str(path).split('/')[l - 1]
    return name


def nonsite(name):
    """
    Функция убирает лишние найденные на VPS директории из сканирования

    :param name: имя директории
    :return: возвращает 0 если не найдено и 1 если соответсвие установлено
    """
    non_scan = ['tmp', 'vds.ru', 'html', 'httpd-logs', 'vds', 'bitrix']
    for n in non_scan:
        if name == n:
            t = 1
            break
        else:
            t = 0
    return t


def set_permission(path):
    """
    Устанавливаем правильные права на сайты. 644 на файлы и 755 на дириктории
    :param path: Путь до сайта
    :return: 1 - если права установлены, 0 - если произошла ошибка
    """
    try:
        if len(path) > 10:
            os.system('find %s -type f -exec chmod 644 {} \;' % path)
            print('[644 FILE DONE ] - ' + path)
            os.system('find %s -type d -exec chmod 755 {} \;' % path)
            print('[755 FOLDER DONE ] - ' + path)
            time.sleep(5)
        return 1
    except  Exception as e:
        return 0



def get_aiupdate_url():
    """
    Открываем страничку с обновлениями, ищем там ссылку на веб версию.
    Обязательно нужно прописывать header иначе сайт шлет нафиг!
    :return:
    """
    import requests
    logging.info(u'Get updates URL')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = "https://revisium.com/ai/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    ai_url = soup.find_all('a')
    for link in ai_url:
        try:
            if link.contents[0] == 'AI-Bolit для сайтов':
                return link.get('href').replace('//', 'http://')
        except:
            pass


def unzip_file(path):
    logging.info(u'Extract updates: %s' % path)
    zip_ref = zipfile.ZipFile(path, 'r')
    zip_ref.extractall(config.WORK_DIR)
    zip_ref.close()


def get_site_list():
    cmd = 'php %s/tools/vps_docroot.php' % config.WORK_DIR
    PIPE = subprocess.PIPE
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True,
        cwd='./'
    )
    sites = p.stdout.read().decode("utf-8").split('\n')
    # print(sites)
    return sites


def run_ai(SITE_DIR):
    logging.info('Scaning: %s' % SITE_DIR)
    SITE_NAME = get_site_name(SITE_DIR)
    REPORT_NAME = SITE_NAME + '.json'
    SERVER_NAME = os.uname()[1]

    cmd = 'php %s --path=%s --json_report=%s --report=%s %s %s %s %s %s' % (
        config.AI_DIR + config.AI,
        SITE_DIR,
        config.REPORT_PATH + REPORT_NAME,
        config.REPORT_PATH + SITE_NAME + '.html',
        config.SKIP,
        config.SCAN,
        config.MODE,
        config.SIZE,
        config.PROGRESS
    )

    PIPE = subprocess.PIPE
    p = subprocess.Popen(
        cmd,
        shell=True,
        stdin=PIPE,
        stdout=PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True,
        cwd=config.WORK_DIR
    )
    sites = p.stdout.read().decode("utf-8",'ignore')
    logging.info('Scan done! VIRUS STATUS: ' + str(p.returncode))


def remove_report():
    pass


def sent_report_to_slack(title, file_path):
    """
    Отправляем отчеты в slack
    :param title: Название сообщения
    :param file_path: путь до файла отчетов
    :return: 1 - если отчет отправлен, 0 - отчет не отправлен
    """
    try:
        logging.info('Send report from slack to: ' + config.slack_channel)
        slack = Slacker(config.slack_key)
        if os.path.isfile(file_path):
            slack.chat.post_message(
                channel=config.slack_channel,
                text=open(config.logFileName, 'rb').read(),
                username='AI-BOLIT'
            )
            slack.files.upload(
                channels=config.slack_channel,
                file_=file_path,
                title=title,
                filetype='zip',
            )
            return 1
        else:
            slack.chat.post_message(
                channel=config.slack_channel,
                text='report [ %s ] not found!!! ' % file_path,
                username='AI-BOLIT'
            )
            return 0
    except Exception as e:
        print(e)
        return 0


def send_report_to_mail(title, file_path):
    try:
        logging.info('Sending report to ' + str(config.targets))
        import smtplib
        from email import encoders
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart

        smtp_ssl_host = config.smtp_ssl_host
        smtp_ssl_port = config.smtp_ssl_port
        username = config.username
        password = config.password
        sender = config.sender
        targets = config.targets

        msg = MIMEMultipart()
        msg['Subject'] = 'ANTIVIRUS REPORT [ %s ]' % title
        msg['From'] = sender
        msg['To'] = ', '.join(targets)

        with open('ai-bolit.log', 'r') as log:
            txt = MIMEText(log.read())
            msg.attach(txt)

        filepath = file_path
        with open(filepath, 'rb') as f:
            img = MIMEBase('application', 'zip')
            img.set_payload(f.read())
            encoders.encode_base64(img)
        img.add_header('Content-Disposition',
                       'attachment',
                       filename=os.path.basename(filepath))
        msg.attach(img)

        server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
        server.login(username, password)
        server.sendmail(sender, targets, msg.as_string())
        server.quit()
        return 1
    except Exception as e:
        return 0


def clear_log_file():
    try:
        with open(config.logFileName, 'w'): pass
        logging.info('Log file has been erased!')
        return 1
    except Exception as e:
        return 0

def zip_report(server_name):
    """
    Архивация отчетов
    :param server_name: Все отчеты помещаются в архив, который называется именем сервера, на котором был запущен
    :return: Путь до файла отчета, если что-то не получилось - 0
    """
    try:
        shutil.make_archive('REPORT-'+config.SERVER_NAME, 'zip', config.REPORT_PATH)
        return 'REPORT-'+config.SERVER_NAME+'.zip'
    except Exception as e:
        return 0

@click.command()
@click.option('--channel', default='slack', help='Channel to send report(slack, email)')
def send_report(channel):
    if os.path.isdir(config.REPORT_PATH):
        if channel=='slack':
            sent_report_to_slack(config.SERVER_NAME, zip_report(config.SERVER_NAME))
        elif channel=='email':
            send_report_to_mail(config.SERVER_NAME, zip_report(config.SERVER_NAME))
            pass
    else:
        logging.info('Report not found :(')


@click.group()
def cli():
    os.chdir(config.WORK_DIR)


@click.command()
def update():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        url = get_aiupdate_url()
        logging.info('Download updates: %s' % url)
        r = requests.get(url, headers=headers)
        with open(config.WORK_DIR+'/ai.zip', 'wb') as zip:
            zip.write(r.content)
        logging.info('Extract updates')
        unzip_file(config.WORK_DIR+'/ai.zip')
        logging.info('Remove temp files')
        os.remove(config.WORK_DIR+'/ai.zip')
        logging.info('Update done!')
    except Exception as e:
        print(e)


@click.command()
# @click.argument('path')
def scan():
    clear_log_file()
    if os.path.isdir(config.REPORT_PATH):
        logging.info('Remove old report')
        shutil.rmtree(config.REPORT_PATH)
        os.mkdir(config.REPORT_PATH)
    else:
        logging.info('Create report folder')
        os.mkdir(config.REPORT_PATH)
    sitelist = get_site_list()
    for site in sitelist:
        if site != '':
            sitename = get_site_name(site)
            if nonsite(sitename) != 1:
                # logging.info(site)
                run_ai(site)
                # send_report()
@click.command()
@click.argument('path')
def scan_manual(path):
    if os.path.isdir(path):
        if os.path.isdir(config.REPORT_PATH):
            logging.info('Remove old report')
            shutil.rmtree(config.REPORT_PATH)
            os.mkdir(config.REPORT_PATH)
        else:
            logging.info('Create report folder')
            os.mkdir(config.REPORT_PATH)
        run_ai(path)
    else:
        logging.info('Path %s not found!' % path)

def status():
    pass


cli.add_command(send_report)
cli.add_command(update)
cli.add_command(scan)
cli.add_command(scan_manual)

if __name__ == "__main__":
    cli()
