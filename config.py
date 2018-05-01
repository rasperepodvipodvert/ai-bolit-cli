import os
# Общие параметры
path='/var/www'
logFileName = 'ai-bolit.log'

try:
    SERVER_NAME = os.uname()[1]
except:
    SERVER_NAME='NONAME'

# Настройки для Slack
slack_key = 'xoxb-305032156928-lSlI90MIcjUu29cg1W3IM57V2 # введите свой slack key
slack_channel='#4admin'

# Config for e-mail send report
smtp_ssl_host = 'smtp.yandex.ru'
smtp_ssl_port = 465
username = 'spambot@filatovz.ru'
password = 'pass'
sender = 'spambot@filatovz.ru'
targets = ['ivan@filatovz.ru']

# Настройки для работы AI-BOLIT
WORK_DIR = '/opt/ai/'
AI_DIR = WORK_DIR+'/ai-bolit/'
AI = 'ai-bolit.php'
REPORT_PATH = WORK_DIR + 'report/'
SKIP = '--skip=7z,7zip,zip,rar,css,avi,mov'
SCAN = ''  # '--scan=php,php5,pht,phtml,pl,cgi,htaccess,suspected,tpl'
MODE = '--mode=1'  # Режим работы. MODE 1 - диагностика, MODE 2 - лечение
SIZE = '--size=100M'
PROGRESS = '--progress='+WORK_DIR+'progress.json'
