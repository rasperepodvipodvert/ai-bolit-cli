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
from bs4 import BeautifulSoup
# Т.к. у нас корпоративное общение все отчеты шлем в слакер (при желании)
from slacker import Slacker

logging.basicConfig(
    level=logging.INFO,
    format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
    # filename = u'mylog.log'
)


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
    if len(path) > 10:
        os.system('find %s -type f -exec chmod 644 {} \;' % path)
        print('[644 FILE DONE ] - ' + path)
        os.system('find %s -type d -exec chmod 755 {} \;' % path)
        print('[755 FOLDER DONE ] - ' + path)
        time.sleep(5)


def report_to_slack():
    pass


def get_aiupdate_url():
    """
    Открываем страничку с обновлениями, ищем там ссылку на веб версию.
    Обязательно нужно прописывать header иначе сайт шлет нафиг!
    :return:
    """
    import requests
    logging.info(u'получаю ссылку для скачивания обновлений')
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
    logging.info(u'Распаковываю обновление: %s' % path)
    import zipfile
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
    logging.info('Сканирую: %s' % SITE_DIR)
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
    logging.info('Сканирование завершено')
    # print(sites)
    # return sites


def remove_report():
    pass


def sent_report_to_slack(title, file_path):
    slack = Slacker(config.slack_key)
    if os.path.isfile(file_path):
        slack.files.upload(
            channels=config.slack_channel,
            file_=file_path,
            title=title,
            filetype='zip',
        )

    else:
        slack.chat.post_message(
            channel=config.slack_channel,
            text='отчет [ %s ] не найден!!! ' % file_path,
            username='AI-BOLIT'
        )


def zip_report(server_name):
    shutil.make_archive('REPORT-'+config.SERVER_NAME, 'zip', config.REPORT_PATH)
    return 'REPORT-'+config.SERVER_NAME+'.zip'


@click.command()
def send_report():
    if os.path.isdir(config.REPORT_PATH):
        sent_report_to_slack(config.SERVER_NAME, zip_report(config.SERVER_NAME))
    else:
        logging.info('Отчеты не обнаружены :(')


@click.group()
def cli():
    os.chdir(config.WORK_DIR)


@click.command()
def update():
    import requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    url = get_aiupdate_url()
    logging.info(u'Скачиваю обновление по ссылке: %s' % url)
    r = requests.get(url, headers=headers)
    with open(config.WORK_DIR+'ai.zip', 'wb') as zip:
        zip.write(r.content)
    logging.info(u'Распаковываю обновления')
    unzip_file(config.WORK_DIR+'ai.zip')
    logging.info(u'Удаляю временные файлы')
    os.remove(config.WORK_DIR+'ai.zip')
    logging.info(u'Обновление завершено!')


@click.command()
# @click.argument('path')
def scan():
    if os.path.isdir(config.REPORT_PATH):
        logging.info('Удаляем старые отчеты')
        shutil.rmtree(config.REPORT_PATH)
        os.mkdir(config.REPORT_PATH)
    else:
        logging.info('Создаем папку report')
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
            logging.info('Удаляем старые отчеты')
            shutil.rmtree(config.REPORT_PATH)
            os.mkdir(config.REPORT_PATH)
        else:
            logging.info('Создаем папку report')
            os.mkdir(config.REPORT_PATH)
        run_ai(path)
    else:
        logging.info('Путь %s не найден!' % path)

def status():
    pass


cli.add_command(send_report)
cli.add_command(update)
cli.add_command(scan)
cli.add_command(scan_manual)

if __name__ == "__main__":
    cli()
